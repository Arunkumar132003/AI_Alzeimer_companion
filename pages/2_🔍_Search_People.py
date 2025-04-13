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

mongodb_uri = os.getenv("MONGODB_URI")
mongodb_database = os.getenv("MONGODB_DATABASE")
collection_name = "companion"
client = pymongo.MongoClient(mongodb_uri)
db = client[mongodb_database]
collection = db[collection_name]

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
    
def find_matching_name(test_image_path, people_info):
    for name, info in people_info.items():
        known_img_path = info.get("image_path")
        if not known_img_path:
            continue
        try:
            result = DeepFace.verify(
                img1_path=test_image_path,
                img2_path=known_img_path,
                model_name='Facenet',
                enforce_detection=False
            )
            if result["verified"]:
                return info 
        except Exception as e:
            print(f"Error comparing with {name}: {e}")
    return None

def get_people_from_db():
    document = collection.find_one({"table_name": "people"})
    if not document:
        return {}

    people = document.get("people", {})
    name_to_info = {}

    for name, details in people.items():
        img_data = details.get("image")
        if img_data:
            temp_img_path = save_base64_image(img_data, name)
            person_info = details.copy()
            person_info["image_path"] = temp_img_path
            person_info["name"] = name
            name_to_info[name] = person_info
    return name_to_info

st.markdown("""
    <style>
    .result-box {
        background-color: #e8f5e9;
        padding: 1rem;
        border-radius: 12px;
        margin-top: 1rem;
        border-left: 5px solid #4CAF50;
    }
    .error-box {
        background-color: #ffebee;
        padding: 1rem;
        border-radius: 12px;
        margin-top: 1rem;
        border-left: 5px solid #e53935;
    }
    .stExpander {
            margin-top: 20px !important;  
    }
    </style>
""", unsafe_allow_html=True)

st.title("🧠 Alzheimer's Face Recognition")

captured_image = st.camera_input("📸 Capture Image")

if captured_image:
    try:
        bytes_data = captured_image.getvalue()
        nparr = np.frombuffer(bytes_data, np.uint8)
        img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            cv2.imwrite(tmp_file.name, img_cv)
            captured_path = tmp_file.name
        
        st.image(img_cv, caption="🖼️ Captured Image", channels="BGR")
        
        with st.spinner("🔍 Matching face..."):
            people_data = get_people_from_db()
            matched_person = find_matching_name(captured_path, people_data)
            print("matched_person", matched_person)
            if matched_person is None:
                st.markdown("""
                    <div class='error-box'>
                        ❌ <strong>No Match Found</strong>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class='result-box'>
                        ✅ <strong>Match Found:</strong> {matched_person["name"]}
                    </div>
                """, unsafe_allow_html=True)
                with st.expander("About the person", expanded=False):
                    st.write(f"**Age:** {matched_person.get('age', 'N/A')}")
                    st.write(f"**Gender:** {matched_person.get('gender', 'N/A')}")
                    st.write(f"**Relation:** {matched_person.get('relation', 'N/A')}")
                    st.write(f"**Description:** {matched_person.get('description', 'N/A')}")
    
    except Exception as e:
        st.error(f"Processing error: {str(e)}")  
        st.exception(e)  