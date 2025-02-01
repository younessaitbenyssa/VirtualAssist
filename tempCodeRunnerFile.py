import asyncio
import sys
import traceback
import pyaudio
import azure.cognitiveservices.speech as speechsdk
from google import genai
import os
from dotenv import load_dotenv
import room

# Load Azure keys from environment
load_dotenv()

if sys.version_info < (3, 11, 0):
    import taskgroup, exceptiongroup

    asyncio.TaskGroup = taskgroup.TaskGroup
    asyncio.ExceptionGroup = exceptiongroup.ExceptionGroup

# Constants for audio
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

MODEL = "models/gemini-2.0-flash-exp"

client = genai.Client(api_key="AIzaSyCnqkgLvWJ9BwxC9SesOqrPoITb4QCdh8Y", http_options={"api_version": "v1alpha"})
CONFIG = {"generation_config": {"response_modalities": ["AUDIO"]}}

pya = pyaudio.PyAudio()

class AudioLoop:
    def __init__(self):
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None
        self.speech_recognizer = None

    async def send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            print(msg)
            await self.session.send(input=msg)

    async def listen_audio(self):
        mic_info = pya.get_default_input_device_info()
        self.audio_stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=CHUNK_SIZE,
        )
        while True:
            data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE)
            await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})

    async def receive_audio(self):
        while True:
            turn = self.session.receive()
            async for response in turn:
                if data := response.data:
                    self.audio_in_queue.put_nowait(data)
                if text := response.text:
                    print(text, end="")

    async def play_audio(self):
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        while True:
            bytestream = await self.audio_in_queue.get()
            await asyncio.to_thread(stream.write, bytestream)

    def start_speech_recognition(self):
        speech_key = os.getenv("AZURE_KEY")
        service_region = os.getenv("AZURE_REGION")
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        self.speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, language="en-US")

        async def recognized_handler(evt):
            intent = room.ClassifiyIntent()
            resp = intent.sendmessage(evt.result.text)

            if evt.result.text:
                # Put the recognized text into the queue and ensure it's awaited properly
                await self.out_queue.put(evt.result.text)

        def canceled_handler(evt):
            print(f"Speech recognition canceled: {evt.reason}")
            if evt.reason == speechsdk.CancellationReason.Error:
                print(f"Error details: {evt.error_details}")

        # Attach event handlers
        self.speech_recognizer.recognized.connect(recognized_handler)
        self.speech_recognizer.canceled.connect(canceled_handler)

        print("Starting speech recognition...")
        self.speech_recognizer.start_continuous_recognition()

    async def run(self):
        try:
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session

                # Start speech recognition in a separate thread
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.start_speech_recognition)

                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)

                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())

        except asyncio.CancelledError:
            pass
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)
        finally:
            if self.speech_recognizer:
                self.speech_recognizer.stop_continuous_recognition()
                print("Speech recognition stopped.")

if __name__ == "__main__":
    main = AudioLoop()
    asyncio.run(main.run())
