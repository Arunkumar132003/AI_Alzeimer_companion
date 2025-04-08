import streamlit as st
import numpy as np
import tempfile
import os
import cv2
from app.utils import get_people_from_db, find_matching_name

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
            matched_name = find_matching_name(captured_path, people_data)
            if matched_name == "No match found":
              st.markdown(f"<div class='error-box'>❌ <strong>No Match Found</strong></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='result-box'>✅ <strong>Matched Found:</strong> {matched_name}</div>", unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Processing error: {str(e)}")  
        st.exception(e)  