import pyaudio
from google import genai
import room
import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import webbrowser
import asyncio
import json
import os

import azure.cognitiveservices.speech as speechsdk

from dotenv import load_dotenv

load_dotenv()


speech_key = os.getenv("AZURE_KEY")
speech_region = os.getenv("AZURE_REGION")

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, language="ar-MA")

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

MODEL = "models/gemini-2.0-flash-exp"

DEFAULT_MODE = "camera"

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"),http_options={"api_version": "v1alpha"})

CONFIG = {"generation_config": {"response_modalities": ["AUDIO"]}}

pya = pyaudio.PyAudio()

myC = room.ClassifiyIntent()


class AudioLoop:
    def __init__(self):

        self.audio_in_queue = None
        self.out_queue = None

        self.exit_flag = False

        self.session = None
        self.mic_muted = False

        self.send_text_task = None
        self.receive_audio_task = None
        self.play_audio_task = None


    async def terminate(self):
        print("Terminating the application...")
        self.exit_flag = True

    def read(self, text):

        speech_key = os.getenv("AZURE_KEY")
        service_region = os.getenv("AZURE_REGION")

        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        speech_config.speech_synthesis_voice_name = "en-US-AndrewMultilingualNeural"

        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

        result = speech_synthesizer.speak_text_async(text).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print(text)
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print("Speech synthesis canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details: {}".format(cancellation_details.error_details))

    async def reco(self):
        try:
            if self.mic_muted:
                return None

            print("Listening for speech...")
            result = await asyncio.to_thread(recognizer.recognize_once)

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                print(f"Recognized: {result.text}")
                return result.text.strip()  # Return the recognized text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                print("No speech could be recognized.")
                return ""
            else:
                print(f"Recognition failed: {result.reason}")
                return ""
        except Exception as e:
            print(f"Error during speech recognition: {e}")
            return ""

    async def adjust_brightness(self, new_brightness):
        try:

            current_brightness = sbc.get_brightness(display=0)[0]

            self.read(f"your current brightness is set to {current_brightness}%")


            if 0 <= new_brightness <= 100:
                sbc.set_brightness(new_brightness, display=0)
                self.read(f"Brightness set to {new_brightness}%.")
            else:
                print("Please enter a value between 0 and 100.")

        except Exception as e:
            print(f"An error occurred: {e}")

        self.mic_muted = False
        await self.send_text()

    async def open_software_by_name(self,software_name):
        try:
            os.startfile(software_name)
            print(f"Opening {software_name}...")
        except FileNotFoundError:
            print(f"{software_name} not found! Make sure it's a registered app or shortcut.")
        except Exception as e:
            print(f"An error occurred: {e}")

        self.mic_muted = False
        await self.send_text()

    async def adjust_volume(self, change):
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)

            # Get current volume level
            current_volume = volume.GetMasterVolumeLevelScalar() * 100
            self.read(f"your Current Volume is set to {current_volume:.0f}%")

            # Ask the user to increase or decrease volume
            new_volume = min(100, max(0, change))
            volume.SetMasterVolumeLevelScalar(new_volume / 100, None)
            self.read(f"the Volume is now set to {new_volume:.0f}%")

        except Exception as e:
            print(f"An error occurred: {e}")

        self.mic_muted = False
        await self.send_text()

    async def search_browser(self, query):
        try:
            self.read(f"serching for {query}")
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
        except Exception as e:
            print(f"An error occurred: {e}")

        self.mic_muted = False
        await self.send_text()

    async def handleTasks(self,message):
        message = message.replace("'", "\"")
        intents = json.loads(message)
        intent = intents.get("intent")
        if intent in ["volume_up", "volume_down"]:
            await self.adjust_volume(intents.get("level"))
        elif intent in ["light_down", "light_up"]:
            await self.adjust_brightness(intents.get("level")) 
        elif intent == "search_browser":
            await self.search_browser(intents.get("query"))
        elif intent == "open_soft":
            await self.open_software_by_name(intents.get("softname").lower())

    async def send_text(self):
        while not self.exit_flag:
            try:
                if self.mic_muted:
                    await asyncio.sleep(0.5)
                    continue

                text = await self.reco()
                if text:
                    print(f"User input: {text}")
                    self.mic_muted = True
                    self.is_playing_response = True

                    text1 = await myC.sendmessage(text)
                    if not text1:
                        await self.session.send(input=text or ".", end_of_turn=True)
                    else:
                        await self.handleTasks(text1)

                    while self.is_playing_response:
                        await asyncio.sleep(0.1)

                    self.mic_muted = False
                else:
                    print("No valid input recognized.")
            except Exception as e:
                print(f"Error in send_text: {e}")

        print("send_text loop exited.")

    async def send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            await self.session.send(input=msg)


    async def receive_audio(self):
        while True:
            turn = self.session.receive()
            async for response in turn:
                if data := response.data:
                    self.audio_in_queue.put_nowait(data)
                    continue

            while not self.audio_in_queue.empty():
                self.audio_in_queue.get_nowait()

    async def play_audio(self):
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        try:
            while True:

                bytestream = await self.audio_in_queue.get()

                await asyncio.to_thread(stream.write, bytestream)

                if self.audio_in_queue.empty():
                    self.is_playing_response = False
        except Exception as e:
            print(f"Error during audio playback: {e}")
        finally:
            # Ensure proper reset in case of errors
            self.is_playing_response = False

    async def run(self):
        try:
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)

                send_text_task = tg.create_task(self.send_text())
                tg.create_task(self.send_realtime())
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())

                # Wait for the send_text loop to finish
                await send_text_task
        except asyncio.CancelledError:
            print("Run loop cancelled.")
        except Exception as e:
            print(f"Exception in run: {e}")
        finally:
            print("Cleaning up resources...")


def start_functions():
    main = AudioLoop()
    asyncio.run(main.run())
    asyncio.run(main.terminate())
