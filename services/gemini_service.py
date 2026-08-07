import os
import json
import re
import traceback
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise Exception("GEMINI_API_KEY not found in .env")

print("API KEY:", API_KEY)

client = genai.Client(api_key=API_KEY)


def ask_gemini(prompt: str):

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        print("\n========== GEMINI RAW RESPONSE ==========")
        print(response)
        print("=========================================\n")

        if not getattr(response, "text", None):
            raise Exception("Gemini returned an empty response.")

        return response.text

    except Exception:
        traceback.print_exc()
        raise


def ask_gemini_json(prompt: str):
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        print("\n========== GEMINI RAW RESPONSE ==========")
        print(response)
        print("=========================================\n")

        text = getattr(response, "text", None)

        if not text:
            raise Exception("Gemini returned an empty response.")

        print("\n========== GEMINI TEXT ==========")
        print(text)
        print("=================================\n")

        text = text.strip()

        # Remove markdown fences
        text = re.sub(r"^```json", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^```", "", text)
        text = re.sub(r"```$", "", text)
        text = text.strip()

        try:
            return json.loads(text)

        except json.JSONDecodeError:
            # Try extracting JSON object
            match = re.search(r"\{.*\}", text, re.DOTALL)

            if match:
                return json.loads(match.group())

            raise Exception(
                f"Gemini did not return valid JSON.\n\n{text}"
            )

    except Exception:
        traceback.print_exc()
        raise