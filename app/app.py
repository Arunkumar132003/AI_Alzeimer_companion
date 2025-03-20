import streamlit as st  
import pymongo
import os
import random
from models import MemoryRecallQuestionandAnswer , MemoryRecallResponseValidation, invoke_model
from dotenv import load_dotenv
load_dotenv()
from utils import encode_image, encode_uploaded_image, get_upcoming_events, get_people, get_datetime, get_random_memory, get_random_people

mongodb_uri = os.getenv("MONGODB_URI")
mongodb_database = os.getenv("MONGODB_DATABASE")
collection_name = "companion"
client = pymongo.MongoClient(mongodb_uri)
db = client[mongodb_database]
collection = db[collection_name]

st.set_page_config(page_title="AI Alzheimer Companion", page_icon="🧠", layout="wide")

patient_name = "John"
profile_image_path = "profile.jpeg"     

profile_image_base64 = encode_image(profile_image_path)
st.sidebar.markdown(
    f"""
    <style>
        .profile-container {{
            text-align: center;
            padding: 20px 0;
        }}
        .profile-img {{
            width: 160px; 
            height: 160px; 
            border-radius: 50%; 
            border: 5px solid #4CAF50;
            box-shadow: 0px 5px 15px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s ease-in-out;
        }}
        .profile-img:hover {{
            transform: scale(1.05);
        }}
        .profile-name {{
            color: #1f77b4;
            font-size: 26px;
            font-weight: bold;
            margin-top: 12px;
        }}
    </style>
    
    <div class="profile-container">
        <img src="data:image/png;base64,{profile_image_base64}" class="profile-img">
        <h1 class="profile-name">Hello {patient_name} 👋</h1>
    </div>
    <hr>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    body {
        background-color: #f4f4f4;
    }
    .sidebar .sidebar-content {
        background-color: #1f77b4;
        padding: 20px;
    }
    .stTextInput, .stTextArea, .stSelectbox {
        border-radius: 5px;
        border: 1px solid black;
        padding: 10px;
    }
    .uploaded-image {
        display: flex;
        justify-content: center;
        margin-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

upcoming_events = get_upcoming_events()



# ========== Add Person Section ==========
with st.sidebar.expander("Add Person", expanded=False):
    uploaded_file = st.file_uploader("Upload a person's image", type=["jpg", "png", "jpeg"])
    name = st.text_input("Name")
    relation = st.selectbox("Relation", ["Father", "Mother", "Sister", "Brother", "Friend", "Other"])
    description = st.text_area("Description")

    if st.button("Add Person"):
        if uploaded_file and name and relation and description:
            image_data = encode_uploaded_image(uploaded_file)
            person_entry = {
                name: {
                    "image": image_data,
                    "relation": relation,
                    "description": description,
                }
            }

            existing_people = collection.find_one({"table_name": "people"})

            if existing_people:
                collection.update_one(
                    {"table_name": "people"},
                    {"$set": {f"people.{name}": person_entry[name]}}
                )
            else:
                collection.insert_one({
                    "table_name": "people",
                    "people": person_entry
                })

            st.success("Added to your memory successfully! Every moment matters and is now part of your cherished memories 🧠.")
        else:
            st.error("Please fill in all details and upload an image.")


# ========== Add Memory Section ==========
with st.sidebar.expander("Add Memory", expanded=False):
    memory_title = st.text_input("Memory Title")
    add_date = st.checkbox("Include memory date?")
    memory_date = st.date_input("Memory Date") if add_date else None
    memory_description = st.text_area("Memory Description")

    if st.button("Add Memory"):
        if memory_title and memory_description:
            memory_entry = {
                "description": memory_description
            }

            if add_date and memory_date:
                memory_entry["date"] = str(memory_date)

            existing_memories = collection.find_one({"table_name": "memories"})

            if existing_memories:
                collection.update_one(
                    {"table_name": "memories"},
                    {"$set": {f"memories.{memory_title}": memory_entry}}
                )
            else:
                collection.insert_one({
                    "table_name": "memories",
                    "memories": {memory_title: memory_entry}
                })

            st.success(f"Memory '{memory_title}' added successfully! 💙")
        else:
            st.error("Please fill in all details to add a memory.")


# ========== Add Event Section ==========
with st.sidebar.expander("Add Upcoming Event", expanded=False):
    event_title = st.text_input("Event Title")
    event_date = st.date_input("Event Date")
    event_description = st.text_area("Event Description")

    if st.button("Add Event"):
        if event_title and event_date and event_description:
            event_entry = {
                "description": event_description,
                "date": str(event_date)  
            }

            existing_events = collection.find_one({"table_name": "events"})

            if existing_events:
                collection.update_one(
                    {"table_name": "events"},
                    {"$set": {f"events.{event_title}": event_entry}}
                )
            else:
                collection.insert_one({
                    "table_name": "events",
                    "events": {event_title: event_entry}
                })

            st.success(f"Event '{event_title}' added successfully! 📅")
        else:
            st.error("Please fill in all details to add an event.")


# ==========  Header Section  ==========
marquee_messages = [
    f"Hello {patient_name}! Hope you're having a wonderful day! 😊",
    f"📅 Today is {get_datetime()}",
    "📌 Reminder: Doctor’s appointment on March 18, 2025, at 3 PM.",
    "💊 Take your heart medication at 2:00 PM.",
    "🎉 Mike's birthday is on March 20! Don't forget to wish him!",
    "☀ Today's Weather: Sunny, 25°C. A great day for a walk!"
]
marquee_content = " " * 50 + " | " + " " * 50  
marquee_content = marquee_content.join(marquee_messages)
marquee_style = """
    <style>
        .marquee-container {
            width: 100%;
            height: 50px;
            overflow: hidden;
            background-color: #1f77b4;
            color: white;
            padding: 8px 0;
            font-size: 18px;
            font-weight: bold;
            border-radius: 5px;
            position: relative;
            margin-bottom: 20px;
        }
        .marquee-text {
            display: inline-block;
            white-space: nowrap;
            position: absolute;
            animation: marquee-scroll 20s linear infinite; /* Increased duration for slower movement */
        }
        @keyframes marquee-scroll {
            from { transform: translateX(100%); }
            to { transform: translateX(-100%); }
        }
    </style>
"""
st.markdown(marquee_style, unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="marquee-container">
        <div class="marquee-text">{marquee_content}</div>
    </div>
    """,
    unsafe_allow_html=True
)

if "activity" not in st.session_state:
    st.session_state.activity = random.choice([1, 2, 3])

if "question" not in st.session_state or "answer" not in st.session_state:
    st.session_state.question = None
    st.session_state.answer = None

left_col, middle_col, right_col = st.columns([1, 1, 1])

# ========== 🧠 Memory Recall Section ==========
with left_col:
    st.markdown("""
        <div style="
            background: linear-gradient(145deg, #ffffff, #f0f0f0);
            padding: 20px;
            border-radius: 15px;
            box-shadow: 6px 6px 12px rgba(0,0,0,0.1), -6px -6px 12px rgba(255,255,255,0.7);
            text-align: center;
            margin-top: 30px; 
            margin-bottom: 20px;
            height: 90px;
            border: 2px solid #e0e0e0; 
        ">
            <h2 style="background-color: #1f77b4; font-size: 24px; margin-bottom: 15px; font-weight: 600; border: 2px solid #1f77b4; border-radius: 8px; color: white; height: 45px; padding: 5px;">Memory Recall</h2>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.activity == 1:
        # ====== 🔹 Activity 1: Recognizing a Person ======
        person_name, person_info = get_random_people()
        if person_name and person_info:
            image_data = person_info["image"]
            st.markdown(f"""
                <div style="
                    background: white;
                    padding: 25px;
                    border-radius: 15px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    margin: 20px 0;
                    transition: transform 0.3s;
                " onmouseover="this.style.transform='scale(1.02)'" 
                onmouseout="this.style.transform='scale(1)'">
                    <h3 style="color: #1f77b4; margin-bottom: 20px;">
                        Do you remember this person?
                    </h3>
                    <img src="data:image/jpeg;base64,{image_data}" 
                    style="
                        width: 200px;
                        height: 200px;
                        border-radius: 50%;
                        border: 5px solid #4CAF50;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
                        margin-bottom: 20px;
                    ">
                </div>
            """, unsafe_allow_html=True)
            
            with st.form("person_form", clear_on_submit=True):
                user_input = st.text_input("Enter their name:", placeholder="Type the name here...")
                submitted = st.form_submit_button("Check Answer ➡️")
                
                if submitted:
                    if user_input.strip().lower() == person_name.strip().lower():
                        st.success(f"✅ Correct! This is {person_name}, your {person_info['relation']}")
                    else:
                        st.error(f"This is {person_name}, your ({person_info['relation']})")

    elif st.session_state.activity == 2:
    # ====== 📖 Activity 2: Recalling a Memory ======
        memory_title, memory_info = get_random_memory()
        if memory_title and memory_info:
            st.markdown(f"""
                <div style="
                    background: white;
                    padding: 25px;
                    border-radius: 15px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    margin: 20px 0;
                    transition: transform 0.3s;
                ">
                    <h3 style="color: #4CAF50; margin-bottom: 20px;">
                       Do you remember this event: {memory_title}?
                    </h3>
                </div>
            """, unsafe_allow_html=True)
            
            with st.form("memory_form", clear_on_submit=True):
                user_input = st.text_area("Share your thoughts:", placeholder="Write your memories here...")
                submitted = st.form_submit_button("Submit Memory 📝")

                if submitted:
                    validation_prompt = f"""
                    You are a compassionate cognitive assistant helping an Alzheimer's patient recall a past event.  
                    Your goal is to validate whether the user’s memory aligns with the expected description of the event.  

                    **Guidelines for Validation:**  
                    - Accept responses that capture the core meaning, even if phrased differently.  
                    - Allow partial recall if key elements are correct.  
                    - Do not penalize minor spelling or grammatical errors.  
                    - ONLY If the response is completely unrelated, gently indicate that it does not match.  

                    **Event Title:** {memory_title}  
                    **Expected Memory Description:** {memory_info['description']}  
                    **User's Recollection:** {user_input}  

                    Determine if the user's response is correct, considering Alzheimer's-related recall difficulties.
                    """
                    response = invoke_model(validation_prompt, MemoryRecallResponseValidation)

                    if response.is_correct:
                        st.success("✅ Great job! Keep rocking. 🎉")
                    else:
                        st.warning(f"That's an interesting perspective! Here's a hint to help you recall: \n\n **{memory_info['description']}** 😊")


    elif st.session_state.activity == 3:
        # ======  Activity 3: Answering a General Question ======
        prompt= ""
        if not st.session_state.question:
            qna_prompt= "You are a compassionate cognitive assistant helping Alzheimer's patients with memory recall. Generate simple, clear questions designed to gently stimulate memory without causing frustration. AVOID asking general knowledge or historical facts and questions that require memorization, such as names, dates, places, or specific past events. Ensure each question is easy to understand and answer. Provide a precise, concise answer that aligns with everyday life scenarios"
            response = invoke_model(qna_prompt, MemoryRecallQuestionandAnswer)
            st.session_state.question = response.question
            st.session_state.answer = response.answer

        question = st.session_state.question
        answer = st.session_state.answer

        st.markdown(f"""
            <div style="
                background: white;
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            ">
                <p style="
                    font-size: 18px;
                    color: #333;
                    background: #fff3e0;
                    padding: 15px;
                    border-radius: 10px;
                    border-left: 5px solid #ff9800;
                ">
                    {question}
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("general_form", clear_on_submit=True):
            user_input = st.text_input("Your answer:", placeholder="Type your answer here...")
            submitted = st.form_submit_button("Submit")
            
            if submitted:
                validation_prompt = f"""
                You are a compassionate cognitive assistant designed to validate memory recall responses for Alzheimer's patients.  
                Your goal is to determine whether the user's response conveys the same meaning as the expected answer, even if phrased differently.  

                Validation Criteria:  
                - Accept responses with minor variations, synonyms, or paraphrased meanings that retain the core intent of the expected answer.  
                - Allow sensory descriptions, emotions, or everyday expressions if they align with the expected response.  
                - Do not penalize minor spelling mistakes or slight grammatical differences.  
                - If the response is partially correct, it should still be considered valid.  
                - Mark the response as incorrect only if it is entirely unrelated or contextually incorrect.  

                Validation Task:  
                Question: {question}  
                Expected Answer: {answer}  
                User's Answer: {user_input}  

                Assess whether the user's response aligns with the expected answer while maintaining a gentle and supportive approach.
                """
                response = invoke_model(validation_prompt, MemoryRecallResponseValidation)

                if response.is_correct:
                    st.balloons()
                    st.success("Great Job! Keep going")
                else:
                    st.error(f"The correct answer is **{answer}**.")

        if submitted:
            st.session_state.question = None
            st.session_state.answer = None
            st.session_state.activity = random.choice([1, 2, 3])


# ========== Upcoming Events Section ==========
with right_col:
    st.markdown("""
        <div style="
            background: linear-gradient(145deg, #ffffff, #f0f0f0);
            padding: 20px;
            border-radius: 15px;
            box-shadow: 6px 6px 12px rgba(0,0,0,0.1), -6px -6px 12px rgba(255,255,255,0.7);
            text-align: center;
            margin-top: 30px; 
            margin-bottom: 20px;
            height: 90px;
            border: 2px solid #e0e0e0; 
        ">
            <h2 style="background-color: #1f77b4; font-size: 24px; margin-bottom: 15px; font-weight: 600; border: 2px solid #1f77b4; border-radius: 8px; color: white; height: 45px; padding: 5px;">Upcoming Events</h2>
        </div>
    """, unsafe_allow_html=True)

    upcoming_events = get_upcoming_events()
    
    if upcoming_events:
        for title, event_date in upcoming_events:
            st.markdown(f"""
                <div style="
                    background: white;
                    padding: 15px;
                    margin: 10px 0;
                    border-left: 5px solid #1f77b4;
                    border-radius: 10px;
                    height: 100px;
                    box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
                    transition: transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out;
                "
                onmouseover="this.style.transform='scale(1.03)'; this.style.boxShadow='4px 4px 12px rgba(0,0,0,0.15)';"
                onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='2px 2px 8px rgba(0,0,0,0.1)';"
                >
                    <h4 style="color: #333; margin-bottom: 8px; font-size: 18px; font-weight: 600;">{title}</h4>
                    <p style="color: #777; font-size: 14px; margin: 0; font-weight: 400;"><i class="fa fa-calendar"></i> {event_date}</p>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No upcoming events.")

# ========== People & Friends Section ==========
st.markdown("<h2 style='text-align: left; color: #1f77b4; font-size: 27px;'>People & Friends</h2>", unsafe_allow_html=True)
random_people = get_people()
if random_people:
    col_count = 4 
    row_count = 2 
    total_slots = col_count * row_count
    random_people = random_people[:total_slots]
    cols = st.columns(col_count)  
    for idx, (name, person) in enumerate(random_people):
        with cols[idx % col_count]:  
            st.markdown(
                f"""
                <div style="
                    background-color: #f9f9f9;
                    padding: 14px;
                    border-radius: 10px;
                    box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
                    text-align: center;
                    width: 300px;
                    height: 200px;
                    margin: auto;
                    margin-top: 20px;
                ">
                    <img src="data:image/png;base64,{person['image']}" 
                    style="width:100px; height:100px; border-radius:50%; border: 3px solid #4CAF50;">
                    <h4 style="color:#1f77b4; margin:4px 0 2px; font-size:16px;">{name}</h4>
                    <p style="color:#444; font-size:14px; margin:0;">{person['relation']}</p>   
                </div>
                """,
                unsafe_allow_html=True
            )
else:
    st.info("No people found. Start adding memories!")