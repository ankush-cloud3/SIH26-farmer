# media_helper.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("WHATSAPP_TOKEN")

def download_whatsapp_media(media_id):
    """Downloads media from WhatsApp given a media_id. Returns (bytes, mime_type)."""
    headers = {"Authorization": f"Bearer {TOKEN}"}

    # Step 1: get the actual download URL for this media_id
    meta_url = f"https://graph.facebook.com/v21.0/{media_id}"
    meta_resp = requests.get(meta_url, headers=headers)
    meta_resp.raise_for_status()
    media_info = meta_resp.json()

    download_url = media_info["url"]
    mime_type = media_info["mime_type"]

    # Step 2: actually download the file bytes
    file_resp = requests.get(download_url, headers=headers)
    file_resp.raise_for_status()

    return file_resp.content, mime_type