import os
import streamlit as st
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from models import load_model
from utils import load_all_text_data
from dotenv import load_dotenv
load_dotenv()

os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

documents = load_all_text_data()
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
vectorstore = FAISS.from_texts(texts=documents, embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

prompt = """You are MemoMate, a friendly and patient memory assistant designed to help individuals with Alzheimer's recall memories, recognize familiar people, and engage in warm, supportive conversations.

### Instructions:
- Use ONLY the provided context to answer memory-related or emotionally supportive questions.
- If the user clearly says "no", "no need", "leave me alone", "not now", "I'm fine", or expresses disinterest, acknowledge and gracefully disengage without pushing further.
- Do NOT suggest topics or ask follow-up questions if the user declines to continue the conversation.
- If the user shares a feeling (e.g., sadness, frustration, peace), respond with empathy. But if they say they don't want to talk, stop the conversation respectfully.
- If the information is not available in the context, respond with: "I don't remember this information, but I'm here if you ever want to talk."
- DO NOT infer or introduce unrelated topics.
- Keep responses short, kind, and supportive.
- Engage in friendly conversation only when the user invites it.

### Special Cases:
- If the user asks "Who are you?", respond:  
  "I'm MemoMate, your friendly memory assistant! I'm here to support you and help you remember things that matter to you. Feel free to talk to me anytime."

### Context:
{context}

### Question:
{question}

### Response:
- Answer based only on the context provided.
- If unsure, express support without guessing or redirecting.
- If the user says not to continue, simply acknowledge and stop responding with: "Okay, I’m here whenever you need me."
"""

PROMPT = PromptTemplate(template=prompt, input_variables=["context", "question"])

qa_chain = RetrievalQA.from_chain_type(
    llm=load_model(),  
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs={"prompt": PROMPT},
    return_source_documents=False
)

st.markdown("""
    <style>
    body {
        background-color: #E3F2FD;
    }
    .chat-bubble {
        padding: 12px 16px;
        border-radius: 18px;
        margin-bottom: 10px;
        display: inline-block;
        font-size: 16px;
        max-width: 80%;
        word-wrap: break-word;
        animation: fadeIn 0.3s ease-in-out;
    }
    .user-message {
        background: linear-gradient(to right, #0078FF, #00C6FF);
        color: white;
        text-align: right;
        float: right;
        clear: both;
    }
    .assistant-message {
        background: #f9f9f9;
        color: black;
        text-align: left;
        float: left;
        clear: both;
    }
    .chat-input {
        width: 100%;
        padding: 12px;
        border-radius: 10px;
        border: none;
        font-size: 16px;
        box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.1);
    }
    .chat-input:focus {
        outline: none;
        box-shadow: 0px 4px 14px rgba(0, 120, 255, 0.3);
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(5px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <h2 style='
        background: linear-gradient(120deg, #1f77b4, #4CAF50);
        color: white;
        text-align: center;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin: 20px 0;
    '>Memory Assistant Chat</h2>
""", unsafe_allow_html=True)

st.markdown('<div class="chat-container">', unsafe_allow_html=True)

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

for message in st.session_state.chat_messages:
    role_class = "user-message" if message["role"] == "user" else "assistant-message"
    st.markdown(f'<div class="chat-bubble {role_class}">{message["content"]}</div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  

query = st.chat_input("💬 Ask your queries...")

if query:
    st.session_state.chat_messages.append({"role": "user", "content": query})
    st.markdown(f'<div class="chat-bubble user-message">{query}</div>', unsafe_allow_html=True)

    with st.spinner("Thinking..."):
        response = qa_chain.invoke({"query": query})

    answer = response.get("result", "Hmm, I need more information to answer that.")
    st.session_state.chat_messages.append({"role": "assistant", "content": answer})

    st.markdown(f'<div class="chat-bubble assistant-message">{answer}</div>', unsafe_allow_html=True)