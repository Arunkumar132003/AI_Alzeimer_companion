import streamlit as st
import pymongo
from datetime import date
import os
import random
from models import (
    MemoryRecallQuestionandAnswer,
    MemoryRecallResponseValidation,
    invoke_model,
    load_model,
)
from dotenv import load_dotenv
load_dotenv()
import schedule
import threading
from utils import (
    encode_uploaded_image,
    get_upcoming_events,
    get_people,
    get_datetime,
    get_random_memory,
    get_random_people,
    fetch_primary_emails,
    get_people_name,
    schedule_checker,
    check_reminders,
    encode_image_from_bytes, 
    get_user_details
)
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate

os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

st.set_page_config(page_title="AI Alzheimer Companion", page_icon="🧠", layout="wide")
mongodb_uri = os.getenv("MONGODB_URI")
mongodb_database = 'alziemer'
collection_name = "companion"
client = pymongo.MongoClient(mongodb_uri)
db = client[mongodb_database]

collection = db[collection_name]
schedule.every().minute.do(check_reminders)
threading.Thread(target=schedule_checker, daemon=True).start()

if "signed_in" not in st.session_state:
    st.session_state.signed_in = False
if "username" not in st.session_state:
    st.session_state.username = None

def signin():
    st.markdown("""
    <style>
    body {
        background-color: #F0F4F8;
        font-family: 'Segoe UI', sans-serif;
    }
    .header {
        background: linear-gradient(120deg, #1f77b4, #4CAF50);
        color: white;
        padding: 10px;
        text-align: center;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        font-size: 18px;
    }
    .submit-btn {
        background: linear-gradient(120deg, #1f77b4, #4CAF50);
        color: white;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        border-radius: 5px;
        cursor: pointer;
    }
    .submit-btn:hover {
        opacity: 0.9;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='header'><h2>Sign In</h2><p>Access your account</p></div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    with st.form("signin_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Sign In")
        
        if submitted:
            
            user_document = collection.find_one({
                "table_name": "about_user",
                "about_user.Username": username
            })

            if user_document:
                stored_password = user_document["about_user"]["Password"]
                if stored_password == password:
                    st.session_state.signed_in = True
                    st.session_state.username = username
                    st.success("Login successful!")
                    st.rerun()
            else:
                st.error("Username not found. Please register.")
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    name = st.session_state.username
    #print(name,'oooo')
    about_user = get_user_details(name)

    profile_image_base64 = ""
    photo_bytes = about_user.get("image")

    if photo_bytes:
        if isinstance(photo_bytes, str):
            profile_image_base64 = photo_bytes
            # #print(profile_image_base64[:30]) 
        else:
            profile_image_base64 = encode_image_from_bytes(photo_bytes)
    email = about_user.get("Email Retrieval", {})
    mail_id = email.get("Gmail Address", "").strip()
    app_password = email.get("App Password", "").strip()
    no_of_mails = email.get("Emails to Retrieve", "")
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
            <h1 class="profile-name">Hello {name} 👋</h1>
        </div>
        <hr>
        """,
        unsafe_allow_html=True,
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
    # ==========  Header Section  ==========
    marquee_messages = [
        f"Hello {st.session_state.username}! Hope you're having a wonderful day! 😊",
        f"📅 Today is {get_datetime()}",
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
        unsafe_allow_html=True,
    )

    if "activity" not in st.session_state:
        st.session_state.activity = random.choice([1, 2, 3])

    if "question" not in st.session_state or "answer" not in st.session_state:
        st.session_state.question = None
        st.session_state.answer = None

    left_col, middle_col, right_col = st.columns([1, 1, 1])

    # ========== 🧠 Memory Recall Section ==========
    with left_col:
        st.markdown(
            """
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
        """,
            unsafe_allow_html=True,
        )

        if st.session_state.activity == 1:
            # ====== 🔹 Activity 1: Recognizing a Person ======
            person_name, person_info = get_random_people()
            if person_name and person_info:
                image_data = person_info["image"]
                st.markdown(
                    f"""
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
                """,
                    unsafe_allow_html=True,
                )

                with st.form("person_form", clear_on_submit=True):
                    user_input = st.text_input(
                        "Enter their name:", placeholder="Type the name here..."
                    )
                    submitted = st.form_submit_button("Check Answer ➡️")

                    if submitted:
                        if user_input.strip().lower() == person_name.strip().lower():
                            st.success(
                                f"✅ Correct! This is {person_name}, your {person_info['relation']}"
                            )
                        else:
                            st.error(
                                f"This is {person_name}, your ({person_info['relation']})"
                            )

        elif st.session_state.activity == 2:
            # ====== 📖 Activity 2: Recalling a Memory ======
            memory_title, memory_info = get_random_memory()
            if memory_title and memory_info:
                st.markdown(
                    f"""
                    <div style="
                        background: white;
                        padding: 25px;
                        border-radius: 15px;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                        margin: 20px 0;
                        transition: transform 0.3s;
                    ">
                        <h3 style="color: #4CAF50; margin-bottom: 20px;">
                        Do you remember: {memory_title}?
                        </h3>
                    </div>
                """,
                    unsafe_allow_html=True,
                )

                with st.form("memory_form", clear_on_submit=True):
                    user_input = st.text_area(
                        "Share your thoughts:", placeholder="Write your memories here..."
                    )
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
                        response = invoke_model(
                            validation_prompt, MemoryRecallResponseValidation
                        )

                        if response.is_correct:
                            st.success("✅ Great job! Keep rocking. 🎉")
                        else:
                            st.warning(
                                f"That's an interesting perspective! Here's a hint to help you recall: \n\n **{memory_info['description']}** 😊"
                            )

        elif st.session_state.activity == 3:
            # ======  Activity 3: Answering a General Question ======
            prompt = ""
            if not st.session_state.question:
                qna_prompt = "​You are a compassionate cognitive assistant dedicated to aiding individuals with Alzheimer's in memory recall. Your task is to generate simple, clear questions that gently stimulate memory without causing frustration. Each question must be designed to elicit a precise, one-word answer. Avoid questions that require memorization of names, dates, places, specific past events, general knowledge, or historical facts. Ensure that each question is easy to understand and answer, aligning with everyday life scenarios."
                response = invoke_model(qna_prompt, MemoryRecallQuestionandAnswer)
                st.session_state.question = response.question
                st.session_state.answer = response.answer

            question = st.session_state.question
            answer = st.session_state.answer

            st.markdown(
                f"""
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
            """,
                unsafe_allow_html=True,
            )

            with st.form("general_form", clear_on_submit=True):
                user_input = st.text_input(
                    "Your answer:", placeholder="Type your answer here..."
                )
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
                    response = invoke_model(
                        validation_prompt, MemoryRecallResponseValidation
                    )

                    if response.is_correct:
                        st.balloons()
                        st.success("Great Job! Keep going")
                    else:
                        st.error(f"The correct answer is **{answer}**.")

            if submitted:
                st.session_state.question = None
                st.session_state.answer = None
                st.session_state.activity = random.choice([1, 2, 3])


    # =========== Mail Summary Section ============
    with middle_col:
        with st.container():
            st.markdown(
            """
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
                <h2 style="background-color: #1f77b4; font-size: 24px; margin-bottom: 15px; font-weight: 600; border: 2px solid #1f77b4; border-radius: 8px; color: white; height: 45px; padding: 5px;">Email Highlights</h2>
            </div>
        """,
            unsafe_allow_html=True,
        )

            emails = fetch_primary_emails(mail_id, app_password, no_of_mails)

            if not emails:
                st.info("No primary emails found.")
            else:
                documents = [email_data['body'] for email_data in emails if email_data['body']]

                if documents:
                    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
                    vectorstore = FAISS.from_texts(texts=documents, embedding=embeddings)
                    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

                    llm = load_model()
                    if llm is None:
                        st.error("Failed to load the language model.")
                        st.stop()

                    prompt_template = """
                    You are MemoMate, a gentle memory assistant helping users summarize and remember key information from emails.

                    ### Instructions:
                    - AVOID if any promotional messages, spam, or irrelevant content.
                    - Use the context to generate a friendly and helpful summary only highlighting main elements AVOID mentioning all things.
                    - Focus on important parts like names, dates, events, tasks, or anything that might be a helpful memory cue.
                    - Keep it short and conversational.
                    - If the body is too long or unclear, highlight what seems most relevant.

                    ### Context:
                    {text}

                    ### Response:
                    """

                    PROMPT = PromptTemplate(template=prompt_template, input_variables=["text"])

                    summarize_chain = load_summarize_chain(
                        llm=llm,
                        chain_type="map_reduce",
                        map_prompt=PROMPT,
                        combine_prompt=PROMPT
                    )

                    from langchain.schema import Document
                    email_docs = [Document(page_content=body) for body in documents]

                    with st.spinner("Generating consolidated email summary..."):
                        summary_output = summarize_chain.run(email_docs)
                        consolidated_summary = summary_output.strip() if summary_output else "No summary available."

                    st.markdown(f"""
                        <div style="
                            background-color: #f9f9f9; 
                            border-radius: 10px; 
                            padding: 15px; 
                            margin-bottom: 10px; 
                            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                        ">
                            <div style="
                                font-size: 14px; 
                                color: #555; 
                                margin-top: 10px;
                            "><strong>MemoMate Consolidated Summary:</strong> {consolidated_summary}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No email bodies available for processing.")

    # ========== Upcoming Events Section ==========
    with right_col:
        st.markdown(
            """
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
        """,
            unsafe_allow_html=True,
        )

        upcoming_events = get_upcoming_events()

        if upcoming_events:
            for title, event_date in upcoming_events:
                st.markdown(
                    f"""
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
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No upcoming events.")

    # ========== People & Friends Section ==========
    st.markdown(
        "<h2 style='text-align: left; color: #1f77b4; font-size: 27px;'>People & Friends</h2>",
        unsafe_allow_html=True,
    )
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
                        padding: 16px;
                        border-radius: 10px;
                        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
                        text-align: center;
                        width: 100%;
                        height: 220px;
                        margin: 10px;
                        margin-bottom: 40px;
                    ">
                        <img src="data:image/png;base64,{person['image']}" 
                        style="width:100px; height:100px; border-radius:50%; border: 3px solid #4CAF50; margin-bottom: 10px;">
                        <h4 style="color:#1f77b4; margin:4px 0 2px; font-size:16px; text-align: center;">{name}</h4>
                        <p style="color:#444; font-size:14px; margin:0; text-align: center;">{person['relation']}</p>   
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("No people found. Start adding memories!")


    # ========== Medication reminder Section ==========
    with st.expander("💊 Medication Reminder System", expanded=False):
        st.markdown("#### Set a Medication Reminder")

        medication = st.text_input("Medication Name")

        hour = st.selectbox("Hour", options=[f"{i:02d}" for i in range(1, 13)])
        minute = st.selectbox("Minute", options=[f"{i:02d}" for i in range(0, 60)])
        period = st.selectbox("AM/PM", options=["AM", "PM"])

        phone_number = st.text_input("Phone Number", max_chars=15)

        if st.button("Set Reminder"):
            if medication and phone_number:
                formatted_time = f"{hour}:{minute} {period}"
                existing_entry = collection.find_one(
                    {"table_name": "medications", "phone_number": phone_number}
                )
                if existing_entry:
                    if medication in existing_entry["medications"]:
                        existing_entry["medications"][medication].append(formatted_time)
                    else:
                        existing_entry["medications"][medication] = [formatted_time]
                    collection.update_one(
                        {"_id": existing_entry["_id"]},
                        {"$set": {"medications": existing_entry["medications"]}},
                    )
                else:
                    collection.insert_one(
                        {
                            "table_name": "medications",
                            "phone_number": phone_number,
                            "medications": {medication: [formatted_time]},
                        }
                    )
                st.success("Reminder set successfully!")
            else:
                st.error("Please fill all fields.")

if st.session_state.signed_in:
    main()
else:
    signin()