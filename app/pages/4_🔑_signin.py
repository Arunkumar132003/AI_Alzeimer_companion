import streamlit as st
from pymongo import MongoClient
import os 

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
        user = collection_name.find_one({"Username": username})
        if user:
            if user["Password"] == password:
                st.success(f"Welcome back, {user['Full Name']}! 🎉")
            else:
                st.error("Incorrect password. Please try again.")
        else:
            st.error("Username not found. Please register.")
st.markdown("</div>", unsafe_allow_html=True)