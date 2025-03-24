import streamlit as st
from datetime import datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()


mongodb_uri = os.getenv("MONGODB_URI")
mongodb_database = os.getenv("MONGODB_DATABASE")
collection_name = "companion"

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
    
    st.subheader("Medical Background & Memory Information")
    diagnosis_date = st.date_input("Date of Diagnosis (if applicable)", help="When were you diagnosed with memory-related issues?")
    medications = st.text_area("Current Medications", placeholder="List your current medications")
    medical_history = st.text_area("Medical History", placeholder="Provide any relevant medical history")
    known_allergies = st.text_area("Known Allergies", placeholder="List any known allergies")
    cognitive_assessment = st.text_input("Cognitive Assessment Score", placeholder="If available (e.g., MMSE score)")
    
    st.subheader("Family & Support Network")
    emergency_contact = st.text_input("Emergency Contact Name", placeholder="Enter a trusted contact's name")
    emergency_phone = st.text_input("Emergency Contact Phone", placeholder="Enter their phone number")
    
    st.subheader("Preferences & Additional Information")
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
                "Photo": photo.name if photo else None,
                "Email": email,
                "Phone": phone,
                "Address": address,
                "Username": username,
                "Password": password,
                "Diagnosis Date": str(diagnosis_date),
                "Medications": medications,
                "Medical History": medical_history,
                "Known Allergies": known_allergies,
                "Cognitive Assessment": cognitive_assessment,
                "Emergency Contact": emergency_contact,
                "Emergency Contact Phone": emergency_phone,
                "Preferred Language": preferred_language,
                "Hobbies": hobbies,
                "Consent Given": consent
            }
            collection_name.insert_one(user_data)
            st.success("Registration successful.")