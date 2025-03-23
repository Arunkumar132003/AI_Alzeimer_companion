import pymongo
from pymongo import MongoClient
import random
import os
import re
from PIL import Image
import io
import base64
from dotenv import load_dotenv
from datetime import datetime
import streamlit as st
load_dotenv()

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
    people_data = collection.find_one({"table_name": "people"}, {"_id": 0, "people": 1})
    events_data = collection.find_one({"table_name": "events"}, {"_id": 0, "events": 1})
    memories_data = collection.find_one({"table_name": "memories"}, {"_id": 0, "memories": 1})
    
    documents = []
    
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
            context = f"UPCOMING EVENTS: {title}\nDate: {data.get('date', 'N/A')}\nDescription: {data.get('description', 'N/A')}"
            documents.append(context)
    
    if memories_data and memories_data.get("memories"):
        for title, data in memories_data["memories"].items():
            context = f"PAST MEMORY: {title}\nDate: {data.get('date', 'N/A')}\nDescription: {data.get('description', 'N/A')}"
            documents.append(context)
    
    return documents


def get_people_name():
    existing_people = collection.find_one({"table_name": "people"})
    return list(existing_people["people"].keys()) if existing_people and "people" in existing_people else []