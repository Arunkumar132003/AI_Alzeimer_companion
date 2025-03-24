import streamlit as st

st.set_page_config(page_title="Welcome", page_icon="👋", layout="centered")
st.markdown(
    """
    <style>
    body {
        background-color: #F0F4F8;
        font-family: 'Segoe UI', sans-serif;
    }
    .header {
        background: linear-gradient(120deg, #1f77b4, #4CAF50);
        color: white;
        padding: 15px;
        text-align: center;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 30px;
        font-size: 24px;
    }
    .btn-container {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-top: 30px;
    }
    .custom-btn {
        background: linear-gradient(120deg, #1f77b4, #4CAF50);
        color: white;
        padding: 15px 30px;
        font-size: 18px;
        border-radius: 8px;
        cursor: pointer;
        text-align: center;
        width: 200px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        transition: 0.3s;
    }
    .custom-btn:hover {
        transform: scale(1.05);
        opacity: 0.9;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<div class='header'><h2>Welcome to Companion App</h2></div>", unsafe_allow_html=True)

st.markdown("<div class='btn-container'>", unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    st.page_link("pages/signin.py", label="🔐 Sign In", help="Already have an account? Log in here!")

with col2:
    st.page_link("pages/signup.py", label="📝 Sign Up", help="New here? Create an account!")

st.markdown("</div>", unsafe_allow_html=True)
