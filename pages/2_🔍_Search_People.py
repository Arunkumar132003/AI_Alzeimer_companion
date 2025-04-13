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
        #print(f"Error decoding image for {name}: {e}")
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
            raise e
            #print(f"Error comparing with {name}: {e}")
    return None

def get_people_from_db():
    document = collection.find_one({"table_name": "people"})
    if not document:
        return {}
    #print(document,'docs')
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
        else:
            person_info = details.copy()
            person_info["name"] = name
            name_to_info[name] = person_info

    return name_to_info
def get_people_from_db_by_entity(name,phone,relation,gender,):
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

def search_by_partial_appearance(filters, people_data):
    matched_people = []
    
    #print(type(people_data))
    for person in people_data:
        #print('person',person)
        match_found = False
        person_app=people_data[person].get('appearance')
        for key, value in filters.items(): 
            #print(person_app[key])
            if person_app.get(key) == value:
                match_found = True
                break  # One match is enough

        if match_found:
            matched_people.append(person)

    return matched_people

def search_by_name_or_entity(query, people_data):
    query_lower = query.lower()
    results = []

    for name, info in people_data.items():
        if query_lower in name.lower() or query_lower in str(info.get("relation", "")).lower():
            person_info = info.copy()
            person_info["name"] = name
            results.append(person_info)

    return results

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

# --- Option Selector ---
search_mode = st.radio(
    "Choose Search Mode:",
    ("📷 By Image", "🔠 By Name/Entity", "👤 By Appearance"),
    horizontal=True
)

# --- Search by Image ---
if search_mode == "📷 By Image":
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

                if matched_person is None:
                    st.error("❌ No Match Found")
                else:
                    st.success(f"✅ Match Found: {matched_person['name']}")
                    with st.expander("About the person", expanded=False):
                        st.write(f"**Age:** {matched_person.get('age', 'N/A')}")
                        st.write(f"**Gender:** {matched_person.get('gender', 'N/A')}")
                        st.write(f"**Relation:** {matched_person.get('relation', 'N/A')}")
                        st.write(f"**Description:** {matched_person.get('description', 'N/A')}")
        except Exception as e:
            st.error(f"Processing error: {str(e)}")
            st.exception(e)

# --- Search by Name or Entity ---
# --- Search by Name or Entity ---
elif search_mode == "🔠 By Name/Entity":
    st.subheader("Search by Specific Entity")
    entity_options = ["name", "phone", "age", "gender", "relation"]
    selected_entity = st.selectbox("Select entity to search by:", entity_options)

    search_value = st.text_input(f"Enter the {selected_entity.capitalize()}")

    if st.button("🔍 Search"):
        people_data = get_people_from_db()
        matches = []
        #print(people_data,'pppeeeeee')
        for name, info in people_data.items():
            #print('namessssssss',name)
            entity_value = str(info.get(selected_entity, "")).lower()
            if search_value.lower() in entity_value:
                person_info = info.copy()
                person_info["name"] = name
                matches.append(person_info)

        if not matches:
            st.warning("No match found.")
        elif len(matches) == 1:
            person = matches[0]
            st.success(f"✅ Match Found: {person['name']}")
            with st.expander("About the person", expanded=True):
                st.write(f"**Age:** {person.get('age', 'N/A')}")
                st.write(f"**Gender:** {person.get('gender', 'N/A')}")
                st.write(f"**Relation:** {person.get('relation', 'N/A')}")
                st.write(f"**Description:** {person.get('description', 'N/A')}")
        else:
            st.info(f"🔎 {len(matches)} matches found:")
            for person in matches:
                st.success(f"✅ Match Found: {person['name']}")
                with st.expander(f"About {person['name']}", expanded=True):
                    st.write(f"**Age:** {person.get('age', 'N/A')}")
                    st.write(f"**Gender:** {person.get('gender', 'N/A')}")
                    st.write(f"**Relation:** {person.get('relation', 'N/A')}")
                    st.write(f"**Description:** {person.get('description', 'N/A')}")
                    if 'image_path' in person and os.path.exists(person['image_path']):
                        st.image(person['image_path'], width=200)
                st.markdown("---")


# --- Search by Appearance ---
elif search_mode == "👤 By Appearance":
    st.subheader("Select Appearance Traits")
    skin_tone = st.selectbox("Skin Tone", ["Not Sure", "Light", "Medium", "Dark"])
    hair_style = st.selectbox("Hair Style", ["Not Sure", "Straight", "Wavy", "Curly", "Bald"])
    beard = st.selectbox("Beard", ["Not Sure", "Yes", "No"])
    mustache = st.selectbox("Mustache", ["Not Sure", "Yes", "No"])

    if st.button("🔍 Search by Appearance"):
        people_data = get_people_from_db()

        # Only include traits that were actually selected (not "Not Sure")
        filters = {}
        if skin_tone != "Not Sure":
            filters["skin_tone"] = skin_tone
        if hair_style != "Not Sure":
            filters["hair_style"] = hair_style
        if beard != "Not Sure":
            filters["beard"] = beard
        if mustache != "Not Sure":
            filters["mustache"] = mustache

        matches = search_by_partial_appearance(filters, people_data)

        if matches:
            st.info(f"🔍 Found {len(matches)} matching person(s) based on appearance traits.")
            #print(matches,'uuuuuuu')
            for persons in matches:
                person=people_data[persons]
                #print(person,'iiiiiiiiii')
                st.markdown(f"✅ **{person['name']}**")
                st.write(f"**Relation:** {person['relation']}")
                st.write(f"**Description:** {person.get('description', 'N/A')}")
                st.markdown("---")
        else:
            st.warning("No match found by these traits.")
