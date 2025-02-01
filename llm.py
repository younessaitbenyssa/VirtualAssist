import os
from dotenv import load_dotenv
import requests
import azure.cognitiveservices.speech as speechsdk
load_dotenv()


def ask_llm(message):
    url = os.getenv("LLM_END_POINT")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('LLM_API_KEY')}"
    }
    conversation_history = [
        {"role": "system", "content": "You are a virtual assistant. Your primary purpose is to provide responses "
                                      "that"
                                      "are concise, logically connected, and conversational, as if you are speaking"
                                      "directly to the user. Avoid using symbols, abbreviations (like 'e.g.' or "
                                      "'etc.'),"
                                      "or bullet points. Instead, structure your answers as complete sentences "
                                      "and ensure they flow naturally, like a storyteller explaining something "
                                      "clearly."
                                      "Always prioritize clarity and natural speech patterns for optimal listening "
                                      "experience."}, {"role": "user", "content": message}]
    data = {
        "messages": conversation_history,
        "model": "deepseek-ai/DeepSeek-V3",
        "max_tokens": 512,
        "temperature": 0.1,
        "top_p": 0.9,
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    reply = response.json().get('choices')[0]['message']['content'].replace("*", "").replace("#", "")

    read(reply)

    conversation_history.append({"role": "assistant", "content": reply})


def read(text):

    speech_key = os.getenv("AZURE_KEY")
    service_region = os.getenv("AZURE_REGION")

    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_synthesis_voice_name = "en-US-AndrewMultilingualNeural"

    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

    result = speech_synthesizer.speak_text_async(text).get()
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized for text [{}]".format(text))
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))


