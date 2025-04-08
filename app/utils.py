import pymongo
from pymongo import MongoClient
import random
import os
import re
from PIL import Image
import io
import base64
from twilio.rest import Client
from dotenv import load_dotenv
from datetime import datetime
import tempfile
load_dotenv()
import schedule
import time
import streamlit as st
import imaplib
import email
from email.header import decode_header
from deepface import DeepFace
import base64

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
mongodb_uri = os.getenv("MONGODB_URI")
mongodb_database = os.getenv("MONGODB_DATABASE")
collection_name = "companion"
client = pymongo.MongoClient(mongodb_uri)
db = client[mongodb_database]
collection = db[collection_name]

def encode_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")
    
def encode_uploaded_image(image):
    image = Image.open(image)
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="JPEG")
    return base64.b64encode(img_bytes.getvalue()).decode("utf-8")

def get_upcoming_events():
    today = datetime.today().date()
    events_data = collection.find_one({"table_name": "events"})
    if events_data and "events" in events_data:
        events = events_data["events"]
        valid_events = {
            k: v for k, v in events.items() if "date" in v and v["date"].strip()
        }
        sorted_events = sorted(
            valid_events.items(),
            key=lambda x: datetime.strptime(x[1]["date"], "%Y-%m-%d")
        )
        upcoming_events = [
            (event[0], datetime.strptime(event[1]["date"], "%Y-%m-%d").strftime("%d %B %Y"))
            for event in sorted_events if datetime.strptime(event[1]["date"], "%Y-%m-%d").date() >= today
        ]
        return upcoming_events[:3]  
    return []


def get_people(n=8):
    people_data = collection.find_one({"table_name": "people"})
    if people_data and "people" in people_data:
        people_list = sorted(people_data["people"].items(), key=lambda x: x[0]) 
        return people_list[:n]  
    return []

def get_datetime():
    now = datetime.now()
    return now.strftime("%A, %d %B %Y | %I:%M %p")

def get_current_time():
    now = datetime.now()
    formatted_time = now.strftime("%I:%M %p")  
    formatted_date = now.strftime("%A, %d %B %Y")  
    return formatted_time, formatted_date

def get_random_people():
    people_data = collection.find_one({"table_name": "people"})
    if people_data and "people" in people_data:
        people_list = list(people_data["people"].items())
        if people_list:
            return random.choice(people_list)
    return (None, None)

def get_random_memory():
    memories_data = collection.find_one({"table_name": "memories"})
    if memories_data and "memories" in memories_data:
        memories_list = list(memories_data["memories"].items())
        if memories_list:
            return random.choice(memories_list)
    return (None, None)


@st.cache_data(ttl=3600) 
def load_all_text_data():
    user_data = collection.find_one({"table_name": "users"}, {"_id": 0, "users": 1})
    people_data = collection.find_one({"table_name": "people"}, {"_id": 0, "people": 1})
    events_data = collection.find_one({"table_name": "events"}, {"_id": 0, "events": 1})
    memories_data = collection.find_one({"table_name": "memories"}, {"_id": 0, "memories": 1})
    
    documents = []

    if user_data and user_data.get("users"):
        for username, data in user_data["users"].items():
            context = f"USER DETAILS:\nFull Name: {data.get('Full Name', 'N/A')}\nDate of Birth: {data.get('Date of Birth', 'N/A')}\nGender: {data.get('Gender', 'N/A')}\nEmail: {data.get('Email', 'N/A')}\nPhone: {data.get('Phone', 'N/A')}\nAddress: {data.get('Address', 'N/A')}\nDiagnosis Date: {data.get('Diagnosis Date', 'N/A')}\nMedications: {data.get('Medications', 'N/A')}\nMedical History: {data.get('Medical History', 'N/A')}\nKnown Allergies: {data.get('Known Allergies', 'N/A')}\nCognitive Assessment: {data.get('Cognitive Assessment', 'N/A')}\nEmergency Contact: {data.get('Emergency Contact', 'N/A')} ({data.get('Emergency Contact Phone', 'N/A')})\nPreferred Language: {data.get('Preferred Language', 'N/A')}\nHobbies: {data.get('Hobbies', 'N/A')}"
            
            documents.append(context)

    if people_data and people_data.get("people"):
        for name, data in people_data["people"].items():
            context = f"PERSON: {name}\nRelation: {data.get('relation', 'N/A')}\nAge: {data.get('age', 'N/A')}\nGender: {data.get('gender', 'N/A')}\nDescription: {data.get('description', 'N/A')}"
            if "conversations" in data:
                for date, conv in data["conversations"].items():
                    if date:  
                        context += f"\nConversation on {date}: {conv.get('conversation', 'N/A')}"
            
            documents.append(context)

    if events_data and events_data.get("events"):
        for title, data in events_data["events"].items():
            context = f"UPCOMING EVENT: {title}\nDate: {data.get('date', 'N/A')}\nDescription: {data.get('description', 'N/A')}"
            documents.append(context)

    if memories_data and memories_data.get("memories"):
        for title, data in memories_data["memories"].items():
            context = f"PAST MEMORY: {title}\nDate: {data.get('date', 'N/A')}\nDescription: {data.get('description', 'N/A')}"
            documents.append(context)

    return documents

def send_sms(phone_number, message):
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    twilio_client.messages.create(
        body=message,
        from_=TWILIO_PHONE_NUMBER,
        to=phone_number
    )

def get_people_name():
    existing_people = collection.find_one({"table_name": "people"})
    return list(existing_people["people"].keys()) if existing_people and "people" in existing_people else []

def check_reminders():
    now = datetime.now().strftime("%I:%M %p")
    reminders = collection.find({})

    for reminder in reminders:
        for medicine, times in reminder.get("medications", {}).items():
            formatted_times = []
            for t in times:
                try:
                    formatted_time = datetime.strptime(t, "%I:%M:%S %p").strftime("%I:%M %p")
                except ValueError:
                    formatted_time = datetime.strptime(t, "%I:%M %p").strftime("%I:%M %p")
                formatted_times.append(formatted_time)

            if now in formatted_times:
                last_sent = reminder.get("last_sent", {})
                if last_sent.get(medicine) == now:
                    continue
                message = f"Reminder: Take your medication '{medicine}'"
                send_sms(reminder['phone_number'], message)
                st.success(f"Reminder sent to {reminder['phone_number']}")
                last_sent[medicine] = now
                collection.update_one({"_id": reminder["_id"]}, {"$set": {"last_sent": last_sent}})

def schedule_checker():
    while True:
        schedule.run_pending()
        time.sleep(30)


def fetch_primary_emails(username, app_password, num_messages=5):
    emails = []
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(username, app_password)
        mail.select("inbox")
        status, messages = mail.search(None, 'X-GM-RAW "category:primary"')
        email_ids = messages[0].split()

        if not email_ids:
            return emails

        latest_ids = email_ids[-num_messages:]

        for num in reversed(latest_ids):
            res, msg = mail.fetch(num, "(RFC822)")
            for response in msg:
                if isinstance(response, tuple):
                    msg = email.message_from_bytes(response[1])
                    subject = decode_header(msg["Subject"])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    from_ = msg.get("From")
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_dispo = str(part.get("Content-Disposition"))
                            if content_type == "text/plain" and "attachment" not in content_dispo:
                                body_bytes = part.get_payload(decode=True)
                                if body_bytes:
                                    body = body_bytes.decode(errors="ignore")
                                    break
                    else:
                        content_type = msg.get_content_type()
                        if content_type == "text/plain":
                            body_bytes = msg.get_payload(decode=True)
                            if body_bytes:
                                body = body_bytes.decode(errors="ignore")

                    emails.append({"from": from_, "subject": subject, "body": body})

        mail.logout()
    except imaplib.IMAP4.error as e:
        st.error(f"IMAP error: {e}")
    except Exception as ex:
        st.error(f"An error occurred: {ex}")
    return emails


def save_base64_image(b64_str, name):
    if os.path.isfile(b64_str):
        return b64_str  
    try:
        img_bytes = base64.b64decode(b64_str)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg", prefix=name + "_") as tmp_file:
            tmp_file.write(img_bytes)
            return tmp_file.name
    except Exception as e:
        print(f"Error decoding image for {name}: {e}")
        return None
    
def get_people_from_db():
    document = collection.find_one({"table_name": "people"})
    if not document:
        return {}

    people = document.get("people", {})
    name_to_path = {}

    for name, details in people.items():
        img_data = details.get("image")
        if img_data:
            temp_img_path = save_base64_image(img_data, name)
            name_to_path[name] = temp_img_path

    return name_to_path

def save_temp_image(image_bytes_or_path):
    if isinstance(image_bytes_or_path, str) and os.path.exists(image_bytes_or_path):
        return image_bytes_or_path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(image_bytes_or_path)
        return tmp.name
    
def find_matching_name(test_image_path, name_to_image_map):
    for name, known_img_path in name_to_image_map.items():
        try:
            result = DeepFace.verify(
                img1_path=test_image_path,
                img2_path=known_img_path,
                model_name='Facenet',
                enforce_detection=False
            )
            if result["verified"]:
                return name
        except Exception as e:
            print(f"Error comparing with {name}: {e}")
    return "No match found"

def sanitize_identifier(identifier):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', identifier)