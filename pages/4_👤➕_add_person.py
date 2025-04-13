import streamlit as st
from datetime import date
from utils import encode_uploaded_image  # Assuming your helper functions & DB are imported

import streamlit as st
import numpy as np
import tempfile
import os
import cv2
import base64
import pymongo
from deepface import DeepFace
from dotenv import load_dotenv
load_dotenv()

# MongoDB setup
mongodb_uri = os.getenv("MONGODB_URI")
mongodb_database = os.getenv("MONGODB_DATABASE")
collection_name = "companion"
client = pymongo.MongoClient(mongodb_uri)
db = client[mongodb_database]
collection = db[collection_name]

# Streamlit page config
st.set_page_config(page_title="Add Person", layout="centered")
st.title("🧍 Add a New Person")

# Input fields
uploaded_file = st.file_uploader("Upload a person's image", type=["jpg", "png", "jpeg"])
name = st.text_input("Name")
age = st.number_input("Age", min_value=0, max_value=120, step=1)
gender = st.selectbox("Gender", ["Male", "Female"])
relation = st.selectbox("Relation", ["Father", "Mother", "Sister", "Brother", "Friend", "Other"])
description = st.text_area("Description")
mobile_number = st.text_input("Mobile Number")
home_town = st.text_input("Home Town")
skin_tone = st.selectbox("Skin Tone", ["Not Sure", "Light", "Medium", "Dark"])
hair_style = st.selectbox("Hair Style", ["Not Sure", "Straight", "Wavy", "Curly", "Bald"])
hair_color = st.selectbox("Hair Color", ["Not Sure", "Black", "Brown", "Blonde", "Grey", "Dyed", "Other"])
glasses = st.selectbox("Wears Glasses?", ["Not Sure", "Yes", "No"])
moles_or_marks = st.text_input("Moles or Distinct Marks (if any)")
beard = st.selectbox("Beard", ["Not Sure", "Yes", "No"])
mustache = st.selectbox("Mustache", ["Not Sure", "Yes", "No"])

# Button and logic
if st.button("Add Person"):
    if mobile_number and name and relation and description:
        if uploaded_file:
            image_data = encode_uploaded_image(uploaded_file)
        else:
            image_data=None
        person_entry = {
            "age": age,
            "gender": gender,
            "image": image_data,
            "relation": relation,
            "mobile_number": mobile_number,
            "home_town": home_town,
            "description": description,
            "conversations": {},
            "appearance": {
                "skin_tone": skin_tone,
                "hair_style": hair_style,
                "hair_color": hair_color,
                "glasses": glasses,
                "moles_or_marks": moles_or_marks,
                "beard": beard,
                "mustache": mustache
            }
        }

        existing_people = collection.find_one({"table_name": "people"})
        #print(existing_people,'999999999999999')
        if existing_people:
            (collection.update_one(
                {"table_name": "people"}, {"$set": {f"people.{name}": person_entry}}
            ),'pppppppppppp')
            
        else:
            (collection.insert_one(
                {"table_name": "people", "people": {name: person_entry}}
            ),'00000000000000000000000000000000')

        st.success(
            "Added to your memory successfully! Every moment matters and is now part of your cherished memories 🧠."
        )
    else:
        st.error("Please fill in all details")
