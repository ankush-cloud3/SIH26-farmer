import os
import json
from fastapi import FastAPI, Form, Response
from twilio.twiml.messaging_response import MessagingResponse
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Define structured schema to prevent parsing failures
class CropListing(BaseModel):
    crop_name: str | None = None
    quantity_kg: float | None = None
    target_price: float | None = None

@app.post("/whatsapp")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(None)
):
    """Webhook endpoint to process incoming WhatsApp messages via Twilio."""
    resp = MessagingResponse()
    bot_reply = resp.message()

    if Body:
        prompt = f"Extract crop details from this message: '{Body}'"
        
        try:
            ai_response = ai_client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=CropListing
                )
            )
            extracted_data = json.loads(ai_response.text)
            
            crop = extracted_data.get("crop_name") or "Produce"
            qty = extracted_data.get("quantity_kg") or "N/A"
            price = extracted_data.get("target_price") or "N/A"

            # Check if all fields were extracted; if not, ask for details
            if qty == "N/A" and price == "N/A":
                bot_reply.body("⚠️ Could not parse crop details. Please mention crop name, quantity, and price.")
            else:
                bot_reply.body(
                    f"🌱 *KrishiConnect Listing Received!*\n\n"
                    f"🌾 Crop: {crop}\n"
                    f"📦 Quantity: {qty} kg\n"
                    f"💰 Offered Price: ₹{price}/kg\n\n"
                    f"Reply 'CONFIRM' to publish this listing live!"
                )
        except Exception as e:
            print(f"Error calling Gemini API: {e}")  # Prints actual error to terminal
            bot_reply.body("⚠️ Server error processing your request. Please try again.")

    return Response(content=str(resp), media_type="application/xml")