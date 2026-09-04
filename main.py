import os
import requests
from fastapi import FastAPI, Request
from dotenv import load_dotenv

from media_helper import download_whatsapp_media
from gemini_helper import parse_produce_text, parse_produce_image, parse_produce_audio, extract_short_answer, answer_general_message
from firestore_helper import get_farmer_state, set_farmer_state, is_message_processed, mark_message_processed
from geocode_helper import reverse_geocode

load_dotenv()

app = FastAPI()

VERIFY_TOKEN = "anaajbot123"
TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

WELCOME_MESSAGE = (
    "Namaste! 🌾 Welcome to Anaaj — helping farmers list their produce for buyers to find, in minutes. "
    "Just say what you have, like 'Tomato 50kg' — or send a photo or voice note, any language works. "
    "A few quick questions follow (pickup date, location, price), then the listing goes live."
)

LOCATION_PROMPT = "Please share your pickup location — tap 'Send Location' below, or type a pin code / address instead."


def send_whatsapp_message(to, body):
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body}
    }
    response = requests.post(url, headers=headers, json=payload)
    print("Send status:", response.status_code, response.text)


def send_location_request(to, body_text):
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "location_request_message",
            "body": {"text": body_text},
            "action": {"name": "send_location"}
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print("Send status:", response.status_code, response.text)


def start_listing_flow(sender, crop, quantity):
    if quantity:
        set_farmer_state(sender, {"stage": "awaiting_pickup_date", "crop": crop, "quantity": quantity})
        return f"Got it — {crop}, {quantity}. When will this be available for pickup?"
    else:
        set_farmer_state(sender, {"stage": "awaiting_quantity", "crop": crop})
        return f"Got it — {crop}. How much do you have? (e.g. 50kg)"


@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(params.get("hub.challenge"))
    return {"error": "verification failed"}


@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()

    try:
        entry = data["entry"][0]
        change = entry["changes"][0]
        value = change["value"]

        if "messages" not in value:
            print("Status update, ignoring.")
            return {"status": "received"}

        message = value["messages"][0]
        message_id = message["id"]

        if is_message_processed(message_id):
            print("Duplicate webhook event, ignoring:", message_id)
            return {"status": "duplicate ignored"}
        mark_message_processed(message_id)

        sender = message["from"]
        msg_type = message["type"]
        text = None
        reply_type = "text"

        state = get_farmer_state(sender)
        is_new_farmer = state is None
        if is_new_farmer:
            send_whatsapp_message(sender, WELCOME_MESSAGE)
            set_farmer_state(sender, {"stage": None})

        if msg_type == "text":
            text = message["text"]["body"].strip()

        elif msg_type == "image":
            media_id = message["image"]["id"]
            caption = message["image"].get("caption", "")
            image_bytes, mime_type = download_whatsapp_media(media_id)
            parsed = parse_produce_image(image_bytes, mime_type, caption)
            print("Gemini image parsed:", parsed)

            if parsed["crop"]:
                reply = start_listing_flow(sender, parsed["crop"], parsed.get("quantity"))
            else:
                reply = "I couldn't clearly identify the produce in that photo. Could you also type the crop name and quantity?"
            send_whatsapp_message(sender, reply)
            return {"status": "received"}

        elif msg_type == "audio":
            media_id = message["audio"]["id"]
            audio_bytes, mime_type = download_whatsapp_media(media_id)
            parsed = parse_produce_audio(audio_bytes, mime_type)
            print("Gemini audio parsed:", parsed)

            if parsed["crop"]:
                reply = start_listing_flow(sender, parsed["crop"], parsed.get("quantity"))
            else:
                reply = "I couldn't clearly understand that voice message. Could you type the crop name and quantity instead?"
            send_whatsapp_message(sender, reply)
            return {"status": "received"}

        elif msg_type == "location":
            loc = message["location"]
            lat = loc.get("latitude")
            lon = loc.get("longitude")
            address = loc.get("address")
            name = loc.get("name")

            if address:
                location_str = address
            elif name:
                location_str = name
            else:
                location_str = reverse_geocode(lat, lon) or f"{lat},{lon}"

            current_stage = state.get("stage") if state else None
            if current_stage == "awaiting_location":
                set_farmer_state(sender, {
                    "stage": "awaiting_price",
                    "location": location_str,
                    "location_lat": lat,
                    "location_lng": lon
                })
                reply = "What is your expected price per kg?"
            else:
                reply = "Got your location, but I wasn't expecting that just now. Type 'help' to see what Anaaj can do."
            send_whatsapp_message(sender, reply)
            return {"status": "received"}

        else:
            send_whatsapp_message(sender, "I can understand text, photos, voice messages, and shared locations — please try one of those.")
            return {"status": "received"}

        print(f"Message from {sender}: {text}")

        stage = state.get("stage") if state else None

        if stage is None or stage == "listed":
            parsed = parse_produce_text(text)
            print("Gemini parsed:", parsed)

            if is_new_farmer and parsed["intent"] == "greeting":
                reply = None

            elif parsed["intent"] == "produce_listing" and parsed["crop"] and parsed["confidence"] == "high":
                reply = start_listing_flow(sender, parsed["crop"], parsed.get("quantity"))

            elif parsed["intent"] == "produce_listing":
                reply = f"Did you mean {parsed['crop']}? Please re-type your crop and quantity clearly (e.g. 'Tomato 30kg')."

            else:
                reply = answer_general_message(text)

        else:
            if stage == "awaiting_quantity":
                set_farmer_state(sender, {"stage": "awaiting_pickup_date", "quantity": text})
                reply = "When will this be available for pickup?"

            elif stage == "awaiting_pickup_date":
                clean_date = extract_short_answer("pickup date", text)
                set_farmer_state(sender, {"stage": "awaiting_location", "pickup_date": clean_date})
                reply = LOCATION_PROMPT
                reply_type = "location_request"

            elif stage == "awaiting_location":
                clean_location = extract_short_answer("pickup location", text)
                set_farmer_state(sender, {"stage": "awaiting_price", "location": clean_location})
                reply = "What is your expected price per kg?"

            elif stage == "awaiting_price":
                set_farmer_state(sender, {"stage": "awaiting_confirmation", "price": text})
                reply = (
                    f"Product: {state['crop']}\n"
                    f"Qty: {state['quantity']}\n"
                    f"Pickup: {state['pickup_date']}\n"
                    f"Location: {state['location']}\n"
                    f"Price: ₹{text}/kg\n\n"
                    f"Reply YES to confirm and publish this listing."
                )

            elif stage == "awaiting_confirmation":
                if text.lower() in ["yes", "y", "confirm"]:
                    set_farmer_state(sender, {"stage": "listed"})
                    reply = "Your listing is now live! Buyers nearby can see it."
                else:
                    reply = "Reply YES to confirm, or tell me what needs to change."

            else:
                reply = "Something went wrong — let's start over. Tell me what produce you have."
                set_farmer_state(sender, {"stage": None})

        if reply:
            if reply_type == "location_request":
                send_location_request(sender, reply)
            else:
                send_whatsapp_message(sender, reply)

    except (KeyError, IndexError) as e:
        print("Payload didn't match expected shape:", e)

    return {"status": "received"}