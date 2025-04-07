import streamlit as st
from datetime import datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()

mongodb_uri = os.getenv("MONGODB_URI")
mongodb_database = os.getenv("MONGODB_DATABASE")
client = MongoClient(mongodb_uri)
db = client[mongodb_database]
collection = db["companion"]

st.markdown("""
    <style>
    body {
        background-color: #F0F4F8;
        font-family: 'Segoe UI', sans-serif;
    }
    .header {
        background: linear-gradient(120deg, #1f77b4, #4CAF50);
        color: white;
        padding: 20px;
        text-align: center;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 20px;
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

st.markdown("<div class='header'><h1>Patient Registration</h1><p>Provide your details to help us serve you better</p></div>", unsafe_allow_html=True)
with st.form("patient_form", clear_on_submit=True):
    st.markdown("<div class='form-container'>", unsafe_allow_html=True)

    st.subheader("Personal Information")
    full_name = st.text_input("Full Name", placeholder="Enter your full name")
    date_of_birth = st.date_input("Date of Birth", max_value=datetime.today())
    gender = st.selectbox("Gender", ["Prefer not to say", "Male", "Female", "Other"])
    photo = st.file_uploader("Upload your photo", type=["jpg", "png", "jpeg"])

    st.subheader("Contact Information")
    email = st.text_input("Email Address", placeholder="Enter your email")
    phone = st.text_input("Phone Number", placeholder="Enter your phone number")
    address = st.text_area("Address", placeholder="Enter your full address")

    st.subheader("Security Credentials")
    username = st.text_input("Username", placeholder="Choose a username")
    password = st.text_input("Password", type="password", placeholder="Enter a password")
    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")

    st.subheader("Email Retrieval Details")
    user_email = st.text_input("Email Address for Retrieval", placeholder="Enter your Gmail address")
    user_password = st.text_input("Email Password (App Password)", type="password", placeholder="Enter your Gmail App Password")
    num_emails = st.number_input("Number of Recent Emails to Retrieve", min_value=1, max_value=100, value=7)

    with st.expander("❓ How to get Gmail App Password"):
        st.markdown("""
        **Steps to generate your Gmail App Password:**

        1. Go to your [Google Account Security Page](https://myaccount.google.com/security).
        2. Ensure **2-Step Verification** is **enabled**.
        3. Once enabled, you'll see an **App Passwords** section.
        4. Click it, sign in again, and:
            - Choose **Mail** as the app.
            - Choose **Other** or your device name.
        5. Click **Generate** to get a 16-character password.
        6. Paste that here as your Email Password.

        🔐 *Only used for secure Gmail connection and not visible to others.*
        """)

    st.subheader("Medical Background & Memory Info")
    diagnosis_date = st.date_input("Date of Diagnosis", help="When were you diagnosed with memory-related issues?")
    medications = st.text_area("Current Medications", placeholder="List your current medications")
    medical_history = st.text_area("Medical History", placeholder="Provide any relevant medical history")
    known_allergies = st.text_area("Known Allergies", placeholder="List any known allergies")
    cognitive_assessment = st.text_input("Cognitive Assessment Score", placeholder="If available (e.g., MMSE score)")

    st.subheader("Family & Support")
    emergency_contact = st.text_input("Emergency Contact Name", placeholder="Enter a trusted contact's name")
    emergency_phone = st.text_input("Emergency Contact Phone", placeholder="Enter their phone number")

    st.subheader("Preferences & Additional Info")
    preferred_language = st.selectbox("Preferred Language", ["English", "Tamil", "Other"])
    hobbies = st.text_area("Interests / Hobbies", placeholder="List your hobbies or interests")
    consent = st.checkbox("I agree to the terms and privacy policy regarding my data")

    st.markdown("</div>", unsafe_allow_html=True)

    submitted = st.form_submit_button("Register")

    if submitted:
        if password != confirm_password:
            st.error("Passwords do not match. Please try again.")
        elif not consent:
            st.error("Please agree to the terms and privacy policy to register.")
        else:
            user_data = {
                "Full Name": full_name,
                "Date of Birth": str(date_of_birth),
                "Gender": gender,
                "Photo Filename": photo.name if photo else None,
                "Email": email,
                "Phone": phone,
                "Address": address,
                "Username": username,
                "Password": password,
                "Email Retrieval": {
                    "Gmail Address": user_email,
                    "App Password": user_password,
                    "Emails to Retrieve": num_emails
                },
                "Diagnosis Date": str(diagnosis_date),
                "Medications": medications,
                "Medical History": medical_history,
                "Known Allergies": known_allergies,
                "Cognitive Assessment": cognitive_assessment,
                "Emergency Contact": emergency_contact,
                "Emergency Contact Phone": emergency_phone,
                "Preferred Language": preferred_language,
                "Hobbies": hobbies,
                "Consent Given": consent,
                "Registration Time": datetime.now().isoformat()
            }

            collection.insert_one(user_data)
            st.success("Registration successful! Redirecting to sign-in...")
            st.query_params(page="signin")
            st.experimental_rerun()