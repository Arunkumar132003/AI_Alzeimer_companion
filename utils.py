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
mongodb_database = 'alziemer'
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
    #print('events',events_data)
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
        #print(upcoming_events,'ppor')
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
    people_data = collection.find_one({"table_name": "people"}, {"_id": 0, "people": 1})
    events_data = collection.find_one({"table_name": "events"}, {"_id": 0, "events": 1})
    memories_data = collection.find_one({"table_name": "memories"}, {"_id": 0, "memories": 1})
    user_data = collection.find_one({"table_name": "about_user"}, {"_id": 0, "about_user": 1})

    documents = []

    if user_data and user_data.get("about_user"):
        user = user_data["about_user"]
        email_retrieval = user.get("Email Retrieval", {})
        context = f"""ABOUT THE USER:
Full Name: {user.get("Full Name", "N/A")}
Date of Birth: {user.get("Date of Birth", "N/A")}
Gender: {user.get("Gender", "N/A")}
Email: {user.get("Email", "N/A")}
Phone: {user.get("Phone", "N/A")}
Address: {user.get("Address", "N/A")}
Username: {user.get("Username", "N/A")}
Password: {user.get("Password", "N/A")}
Diagnosis Date: {user.get("Diagnosis Date", "N/A")}
Medications: {user.get("Medications", "N/A")}
Medical History: {user.get("Medical History", "N/A")}
Known Allergies: {user.get("Known Allergies", "N/A")}
Cognitive Assessment: {user.get("Cognitive Assessment", "N/A")}
Emergency Contact: {user.get("Emergency Contact", "N/A")}
Emergency Contact Phone: {user.get("Emergency Contact Phone", "N/A")}
Preferred Language: {user.get("Preferred Language", "N/A")}
Hobbies: {user.get("Hobbies", "N/A")}
Consent Given: {user.get("Consent Given", False)}
Registration Time: {user.get("Registration Time", "N/A")}

EMAIL RETRIEVAL:
Gmail Address: {email_retrieval.get("Gmail Address", "N/A")}
App Password: {email_retrieval.get("App Password", "N/A")}
Emails to Retrieve: {email_retrieval.get("Emails to Retrieve", "N/A")}
"""
        documents.append(context)

    if people_data and people_data.get("people"):
        for idx, (name, data) in enumerate(people_data["people"].items(), start=1):
            context = f"""USER KNOWS PERSON {idx} - {name}:
Relation: {data.get('relation', 'N/A')}
Age: {data.get('age', 'N/A')}
Gender: {data.get('gender', 'N/A')}
Mobile Number: {data.get('mobile_number', 'N/A')}
Date of first meet: {data.get('first_met',"")}
Home Town: {data.get('home_town', 'N/A')}
Description: {data.get('description', 'N/A')}
Skin Tone: {data.get('appearance', {}).get('skin_tone', 'N/A')}
Hair Style: {data.get('appearance', {}).get('hair_style', 'N/A')}
Hair Color: {data.get('appearance', {}).get('hair_color', 'N/A')}
Glasses: {data.get('appearance', {}).get('glasses', 'N/A')}
Moles or Marks: {data.get('appearance', {}).get('moles_or_marks', 'N/A')}
Beard: {data.get('appearance', {}).get('beard', 'N/A')}
Mustache: {data.get('appearance', {}).get('mustache', 'N/A')}
Conversation: {data.get("conversations", {})}
"""
            documents.append(context)

    if events_data and events_data.get("events"):
        for idx, (title, data) in enumerate(events_data["events"].items(), start=1):
            context = f"""UPCOMING EVENT {idx} - {title}:
Date: {data.get('date', 'N/A')}
Description: {data.get('description', 'N/A')}"""
            documents.append(context)

    if memories_data and memories_data.get("memories"):
        for idx, (title, data) in enumerate(memories_data["memories"].items(), start=1):
            context = f"""PAST MEMORY {idx} - {title}:
Date: {data.get('date', 'N/A')}
Description: {data.get('description', 'N/A')}"""
            documents.append(context)
    #print("Documents:", documents)
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

def save_temp_image(image_bytes_or_path):
    if isinstance(image_bytes_or_path, str) and os.path.exists(image_bytes_or_path):
        return image_bytes_or_path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(image_bytes_or_path)
        return tmp.name
    
def get_user_details(username):
    document = collection.find_one({
    "table_name": "about_user",
    "about_user.Username": username
    })
    #print(document,'yyyyyyyyy')
    if document:
        return document["about_user"]
    else:
        return None
    
def encode_image_from_bytes(image_bytes):
    return base64.b64encode(image_bytes).decode("utf-8")