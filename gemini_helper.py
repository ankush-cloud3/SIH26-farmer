import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def parse_produce_text(text):
    prompt = f"""
You are the parsing engine for a WhatsApp bot that helps farmers list produce for sale.
A farmer just sent this message: "{text}"

First, classify the intent of this message as one of:
- "produce_listing" — mentions a crop/vegetable/fruit name and/or quantity
- "greeting" — hi, hello, hey, good morning, etc.
- "unclear" — anything else (questions, random text, unrelated chat)

If intent is "produce_listing", also extract crop name (typo-corrected, proper capitalization) and quantity with unit.

Respond ONLY with valid JSON, no markdown, no explanation, in this exact format:
{{"intent": "produce_listing/greeting/unclear", "crop": "<crop name or null>", "quantity": "<quantity with unit or null>", "confidence": "<high/low>"}}
"""
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    raw_text = response.text.strip()
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        print("Failed to parse Gemini response as JSON:", raw_text)
        return {"intent": "unclear", "crop": None, "quantity": None, "confidence": "low"}


def parse_produce_image(image_bytes, mime_type, caption=""):
    prompt = f"""
You are the parsing engine for a WhatsApp bot that helps farmers list produce for sale.
A farmer sent a photo of their produce, with this optional caption: "{caption}"

Identify the crop/vegetable/fruit shown in the image. If the caption mentions a quantity, extract it too.

Respond ONLY with valid JSON, no markdown, no explanation, in this exact format:
{{"crop": "<crop name or null>", "quantity": "<quantity with unit or null>", "confidence": "<high/low>"}}
"""
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            {"inline_data": {"mime_type": mime_type, "data": image_bytes}},
            prompt
        ]
    )
    raw_text = response.text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        print("Failed to parse Gemini image response:", raw_text)
        return {"crop": None, "quantity": None, "confidence": "low"}


def parse_produce_audio(audio_bytes, mime_type):
    prompt = """
You are the parsing engine for a WhatsApp bot that helps farmers list produce for sale.
A farmer sent a voice message. Listen to it and extract the crop/vegetable/fruit name and quantity they mention.
The message may be in Hindi, Kannada, or other Indian languages, or English, possibly mixed.

Respond ONLY with valid JSON, no markdown, no explanation, in this exact format:
{"crop": "<crop name in English, or null>", "quantity": "<quantity with unit or null>", "confidence": "<high/low>"}
"""
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            {"inline_data": {"mime_type": mime_type, "data": audio_bytes}},
            prompt
        ]
    )
    raw_text = response.text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        print("Failed to parse Gemini audio response:", raw_text)
        return {"crop": None, "quantity": None, "confidence": "low"}


def extract_short_answer(field_name, raw_text):
    prompt = f"""
The user answered a question about their produce listing's "{field_name}".
Their raw reply was: "{raw_text}"

Extract just the relevant {field_name} value, cleanly stated, removing filler words, repeated labels, or unrelated text.
Respond with ONLY the cleaned value as plain text. No quotes, no explanation, no extra words.
"""
    response = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
    return response.text.strip()


def answer_general_message(text):
    prompt = f"""
You are the conversational assistant for Anaaj, a WhatsApp bot that helps Indian farmers list their produce for sale directly to buyers.

Current features of Anaaj you can tell farmers about, if relevant to what they asked:
- List produce by typing the crop name and quantity (e.g. "Tomato 50kg"), sending a photo of the crop, or sending a voice note — any Indian language works.
- After the crop is recognized, Anaaj asks for pickup date, pickup location (or pin code), and expected price per kg.
- Anaaj shows a summary and the farmer replies YES to publish the listing so nearby buyers can see it.

A farmer just sent this message: "{text}"

Reply naturally and helpfully, in 1-3 short sentences suitable for a WhatsApp chat. Answer whatever they actually asked — greetings, "how does this work", unrelated small talk, anything. If it fits naturally, gently point them toward listing their produce, but don't force it on unrelated messages. Do not invent features that aren't listed above.
"""
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return response.text.strip()