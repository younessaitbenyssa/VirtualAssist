import customtkinter as ctk
import requests
import os
from PIL import Image
import threading
from customtkinter import CTkScrollableFrame
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()

class ChatInterface:
    def __init__(self, app, root):
        self.url = os.getenv("LLM_END_POINT")
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('LLM_API_KEY')}"
        }
        self.conversation_history = [
            {"role": "system", "content": "You are a virtual assistant. Your primary purpose is to provide responses "
                                          "that"
                                          "are concise, logically connected, and conversational, as if you are speaking"
                                          "directly to the user. Avoid using symbols, abbreviations (like 'e.g.' or "
                                          "'etc.'),"
                                          "or bullet points. Instead, structure your answers as complete sentences "
                                          "and ensure they flow naturally, like a storyteller explaining something "
                                          "clearly."
                                          "Always prioritize clarity and natural speech patterns for optimal listening "
                                          "experience."}
        ]

        # Main Chat Frame
        self.Bot_frame = ctk.CTkFrame(master=app, width=950, height=630)
        self.Bot_frame.pack(side="right", fill="both")
        self.Bot_frame.pack_propagate(False)
        self.frame_color = self.Bot_frame.cget("fg_color")

        # Input Textbox
        self.placeHolder = "Message Bolt"
        self.inpuText = ctk.CTkEntry(
            self.Bot_frame,
            width=800,
            height=50,
            corner_radius=15,
            placeholder_text=self.placeHolder,
            font=("Segoe UI", 14, "bold")
        )

        self.entry_color = self.inpuText.cget("fg_color")
        self.inpuText.pack(side="bottom", pady=(0,25))

        # Send Button
        self.image3 = ctk.CTkImage(light_image=Image.open("images/uparrow.png"), size=(15, 20))
        self.send_button = ctk.CTkButton(
            self.inpuText,
            text="",
            width=35,
            height=35,
            corner_radius=17,
            fg_color="white",
            image=self.image3,
            command=self.handleSendMessage
        )
        self.send_button.place(x=730, y=8)
        self.send_button.pack_propagate(False)
        root.bind("<Return>", lambda event: self.handleSendMessage(event, None))

        # Audio Button
        self.image4 = ctk.CTkImage(light_image=Image.open("images/audio.png"))
        self.audio_Button = ctk.CTkButton(
            self.inpuText,
            text="",
            width=35,
            height=35,
            corner_radius=17,
            fg_color="white",
            image=self.image4,
            command=self.recording
        )
        self.audio_Button.place(x=660, y=8)

        # Message Frame
        self.message_frame = CTkScrollableFrame(
            self.Bot_frame,
            width=850,
            height=600,
            fg_color=self.frame_color
        )
        self.message_frame.pack(side="left", pady=(40, 0), padx=20, fill="both")

        # Placeholder Handling
        self.inpuText.bind("<FocusOut>", self.show_placeholder)
        self.typing_animation_active = False

    def show_placeholder(self, event):
        if not self.inpuText.get():
            self.inpuText.configure(placeholder_text=self.placeHolder)

    def handleSendMessage(self, event=None, audioResult=None):
        global Usermessage
        Usermessage = self.inpuText.get().strip() if audioResult is None else audioResult

        if Usermessage:
            user_frame = ctk.CTkFrame(self.message_frame, fg_color=self.entry_color, corner_radius=10)
            user_frame.pack(anchor="e", padx=10, pady=5)
            user_label = ctk.CTkLabel(
                user_frame,
                text=f"{Usermessage}",
                anchor="e",
                font=("Segoe UI Emoji", 14, "bold"),
                wraplength=400
            )
            user_label.pack(padx=10, pady=5)

            self.inpuText.delete(0, "end")
            self.inpuText.configure(state="disabled")
            self.send_button.configure(state="disabled")
            self.message_frame._parent_canvas.yview_moveto(1.0)

            self.typing_indicator_frame = ctk.CTkFrame(self.message_frame, fg_color=self.frame_color, corner_radius=30)
            self.typing_indicator_frame.pack(anchor="w", padx=10, pady=5)

            bot_icon_image = ctk.CTkImage(light_image=Image.open("images/LLMIcon1White.png"), size=(30, 30))
            bot_icon_label = ctk.CTkLabel(self.typing_indicator_frame, image=bot_icon_image, text="", anchor="nw")
            bot_icon_label.grid(row=0, column=0, padx=(5, 10), pady=(5, 0), sticky="nw")

            self.typing_label = ctk.CTkLabel(
                self.typing_indicator_frame,
                text="Thinking",
                anchor="w",
                font=("Segoe UI Emoji", 14, "bold"),
                justify="left",
                wraplength=775
            )
            self.typing_label.grid(row=0, column=1, padx=5, pady=(5, 0), sticky="nw")

            self.typing_animation_active = True
            self.animate_typing_dots()

            threading.Thread(target=self.sendToAPI, args=(Usermessage,)).start()

    def animate_typing_dots(self):
        if not self.typing_animation_active:
            return
        dots = ["Thinking", "Thinking.", "Thinking..", "Thinking..."]
        current_dot = self.typing_label.cget("text")
        next_index = (dots.index(current_dot) + 1) % len(dots)
        self.typing_label.configure(text=dots[next_index])
        self.message_frame._parent_canvas.yview_moveto(1.0)
        self.message_frame.after(500, self.animate_typing_dots)

    def recording(self):
        threading.Thread(target=self.record_audio).start()
        self.listening()

    def record_audio(self):
        speech_key = os.getenv("AZURE_KEY")
        service_region = os.getenv("AZURE_REGION")
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, language="ar-MA")
        result = speech_recognizer.recognize_once()
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            self.inpuText.configure(state="normal", placeholder_text=self.placeHolder)
            self.handleSendMessage(None, result.text)
        elif result.reason == speechsdk.ResultReason.NoMatch:
            print(f"No speech could be recognized: {result.no_match_details}")
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"Speech Recognition canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print(f"Error details: {cancellation_details.error_details}")

    def listening(self):
        self.inpuText.configure(placeholder_text="Listening...", state="disabled")

    def sendToAPI(self, message):
        self.conversation_history.append({"role": "user", "content": message})
        data = {
            "messages": self.conversation_history,
            "model": "deepseek-ai/DeepSeek-V3",
            "max_tokens": 512,
            "temperature": 0.1,
            "top_p": 0.9,
        }

        try:
            response = requests.post(self.url, headers=self.headers, json=data)
            response.raise_for_status()
            reply = response.json().get('choices')[0]['message']['content'].replace("*", "").replace("#", "")

            print(reply)


            self.conversation_history.append({"role": "assistant", "content": reply})
            #thread1 = threading.Thread(target=test.read, args=(reply,))
            thread2 = threading.Thread(target=self.type_text, args=(self.typing_label, reply))

            #thread1.start()
            thread2.start()
        except requests.exceptions.RequestException as e:
            self.displayError(f"Error: Unable to contact the server. {str(e)}")
        except (KeyError, IndexError) as e:
            self.displayError(f"Error: Unexpected response format. {str(e)}")
        finally:
            self.typing_animation_active = False
            self.typing_label.configure(text="")
            self.Bot_frame.after(0, lambda: self.inpuText.configure(state="normal"))
            self.Bot_frame.after(0, lambda: self.send_button.configure(state="normal"))

    def type_text(self, label, text, index=0):
        if index < len(text):
            label.configure(text=text[:index + 1])
            self.message_frame._parent_canvas.yview_moveto(1.0)
            self.message_frame.after(10, self.type_text, label, text, index + 1)

    def displayError(self, error_message):
        error_frame = ctk.CTkFrame(self.message_frame, fg_color="lightPink", corner_radius=10)
        error_frame.pack(anchor="w", padx=10, pady=5)
        error_label = ctk.CTkLabel(
            error_frame,
            text=error_message,
            anchor="w",
            font=("Segoe UI Emoji", 14, "bold"),
            wraplength=1000
        )
        error_label.pack(padx=10, pady=5)