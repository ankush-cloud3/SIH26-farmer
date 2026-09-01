import os
import json
from fastapi import FastAPI, Form, Response
from twilio.twiml.messaging_response import MessagingResponse
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load keys from .env
load_dotenv()

app = FastAPI()

# Initialize Gemini Client
ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@app.post("/whatsapp")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(None)
):
    """Webhook endpoint to process incoming WhatsApp messages via Twilio."""
    resp = MessagingResponse()
    bot_reply = resp.message()

    if Body:
        prompt = f"""
        Extract structured details from this farmer's message:
        Message: "{Body}"

        Respond ONLY in valid JSON format with keys:
        - "crop_name": name of crop or null
        - "quantity_kg": numerical quantity or null
        - "target_price": price per kg or null
        """
        
        try:
            ai_response = ai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            extracted_data = json.loads(ai_response.text)
            
            crop = extracted_data.get("crop_name") or "Produce"
            qty = extracted_data.get("quantity_kg") or "N/A"
            price = extracted_data.get("target_price") or "N/A"

            bot_reply.body(
                f"🌱 *KrishiConnect Listing Received!*\n\n"
                f"🌾 Crop: {crop}\n"
                f"📦 Quantity: {qty} kg\n"
                f"💰 Offered Price: ₹{price}/kg\n\n"
                f"Reply 'CONFIRM' to publish this listing live!"
            )
        except Exception:
            bot_reply.body("⚠️ Could not parse crop details. Please mention crop name, quantity, and price.")

    return Response(content=str(resp), media_type="application/xml")