import customtkinter as ctk
import pygame
import pyaudio
import numpy as np
from PIL import Image, ImageTk
import geminiAssistant
import threading
global muted

class Voice:
    def __init__(self, parent_frame):
        self.audio_loop = geminiAssistant.AudioLoop()  # Save the AudioLoop instance

        self.main_container = ctk.CTkFrame(parent_frame)
        self.main_container.pack(side="right", fill="both", expand=True)

        # Create a sub-container to hold the canvas and entry
        self.sub_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.sub_container.pack(expand=True, anchor="center")

        # Create a Canvas for displaying pygame graphics
        self.canvas = ctk.CTkCanvas(self.sub_container, width=500, height=200, bg="black", highlightthickness=0)
        self.canvas.pack(pady=20, padx=20)

        self.input_label = ctk.CTkFrame(
            self.sub_container,
            width=380,
            height=100,
            fg_color="#343638",
            corner_radius=20
        )

        self.input_label.pack(pady=20, padx=150)

        # Create the entry widget
        self.input_text = ctk.CTkEntry(
            self.input_label,
            width=290,
            height=40,
            placeholder_text="start a conversation",
            border_width=0
        )

        self.input_text.grid(row=0, column=0, pady=0, padx=20, sticky="w")

        self.unmuted_mic_icon = ctk.CTkImage(Image.open("images/unmute.png"), size=(24, 24))
        self.muted_mic_icon = ctk.CTkImage(Image.open("images/muted.png"), size=(24, 24))
        self.button_mode = False  # True: unmuted, False: muted

        self.mic_label = ctk.CTkButton(
            self.input_label,
            text="",  # No text
            width=40,
            height=40,
            image=self.muted_mic_icon,  # Mic icon for unmuted state
            corner_radius=20,
            fg_color="#343638",
            hover_color="#343638",
            command=self.toggle_mic
        )

        self.mic_label.grid(row=0, column=1, pady=0)

        # Initialize pygame and other settings
        pygame.init()
        self.WIDTH, self.HEIGHT = 500, 200
        self.screen = pygame.Surface((self.WIDTH, self.HEIGHT))
        # Bar settings
        self.num_bars = 7
        self.bar_width = 40
        self.spacing = 20
        self.max_height = 80
        self.bar_colors = (255, 255, 255)  # White

        # Audio input settings
        self.CHUNK = 1024  # Number of audio samples per frame
        self.RATE = 44100  # Sampling rate
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=self.RATE, input=True,
                                  frames_per_buffer=self.CHUNK)

        # Start the animation loop
        self.running = True
        self.update_graphics()


    def toggle_mic(self):
        # Update button state
        if self.button_mode:  # Currently unmuted, mute the mic
            self.mic_label.configure(image=self.muted_mic_icon, hover_color="#343638")
            self.button_mode = False
            self.audio_loop.terminate()
        else:  # Currently muted, unmute the mic
            self.mic_label.configure(image=self.unmuted_mic_icon, hover_color="#343638")
            self.button_mode = True
            threading.Thread(target=self.start_voice_assistant, daemon=True).start()

        # Notify AudioLoop of the mic state



    def start_voice_assistant(self):
        try:
            geminiAssistant.start_functions()
        except Exception as e:
            print(f"Error in voice assistant: {e}")

    def update_graphics(self):
        if not self.running:
            return

        self.screen.fill((43, 43, 43))  # Black background

        if self.button_mode:  # If unmuted
            # Read audio data from the microphone
            data = np.frombuffer(self.stream.read(self.CHUNK, exception_on_overflow=False), dtype=np.int16)
            amplitude = np.abs(data).mean()  # Compute the mean amplitude

            # Normalize amplitude to fit bar heights
            normalized_amplitude = min(amplitude / 500, 1)  # Scale between 0 and 1
            bar_heights = [int(normalized_amplitude * self.max_height) for _ in range(self.num_bars)]
        else:  # If muted
            bar_heights = [10 for _ in range(self.num_bars)]  # Small static bars

        
        for i in range(self.num_bars):
            x = i * (self.bar_width + self.spacing) + 50  # X position of each bar
            y = (self.HEIGHT // 2) - (bar_heights[i] // 2)  # Center the bar vertically
            pygame.draw.rect(self.screen, self.bar_colors, (x, y, self.bar_width, bar_heights[i]), border_radius=10)

        # Convert pygame surface to an image for Tkinter
        pygame_image = pygame.surfarray.array3d(self.screen)
        pygame_image = pygame_image.swapaxes(0, 1)  # Convert to correct orientation
        image = Image.fromarray(pygame_image)
        tk_image = ImageTk.PhotoImage(image=image)

        # Update the Tkinter canvas
        self.canvas.create_image(0, 0, anchor="nw", image=tk_image)
        self.tk_image = tk_image  # Save reference to avoid garbage collection

        # Schedule the next update
        self.main_container.after(30, self.update_graphics)
