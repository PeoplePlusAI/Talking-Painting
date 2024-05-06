from dotenv import load_dotenv
from utils.file import convert_to_base64
from core.face_detection import detect_people_yolo
from core.voice import text_to_speech, dubverse_tts
from utils.openai_utils import get_openai_response
import base64
import random
import requests
import time
import os

load_dotenv(dotenv_path="ops/.env")

LLAVA_URL = os.getenv("LLAVA_URL")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

with open("prompts/main.txt", "r") as f:
    prompt = f.read()

# with open("prompts/COSTAR.txt", "r") as f:
#     prompt = f.read().replace('\n', ' ')

def compose_body(encoded_img, prompt=prompt, model="llava"):
    return {
        "model": model,
        "prompt": prompt,
        "images": [encoded_img],
        "stream": False
    }


def get_ai_response(encoded_img):
    body = compose_body(encoded_img)
    response = get_openai_response(OPENAI_API_KEY, prompt, body)
    if not response:
      response = requests.post(LLAVA_URL, json=body)
      print(response.json())
      if response.status_code != 200:
        print(f"Something went wrong. Status code is {response.status_code}")
        return ""
      response = response.json().get("response", "").replace("</s>", "").strip()
    else:
      print(response)
    return response



def respond_voice(contents, person_detected=False):
    person_detected = detect_people_yolo(contents)
    if person_detected:
        encoded_img = convert_to_base64(contents)
        response_text = get_ai_response(encoded_img)
    else:
        response_text = ""
    if response_text:
        audio_response = dubverse_tts(response_text)
        encoded_audio = base64.b64encode(audio_response.content).decode("utf-8")
        return {"response": response_text, "audio": encoded_audio, "expression": "talking"}
    else:
        expression = random.choice(["deadface", "surprised", "idle"])
        return {"response": "", "audio": "", "expression": expression}
