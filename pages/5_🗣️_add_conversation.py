import streamlit as st
from datetime import date
import os
import tempfile
import pymongo
from dotenv import load_dotenv
import assemblyai as aai
from audio_recorder_streamlit import audio_recorder

# Load environment variables
load_dotenv()

# MongoDB setup
mongodb_uri = os.getenv("MONGODB_URI")
mongodb_database = os.getenv("MONGODB_DATABASE")
collection_name = "companion"
client = pymongo.MongoClient(mongodb_uri)
db = client[mongodb_database]
collection = db[collection_name]

# AssemblyAI setup
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
transcriber = aai.Transcriber()

# Session state
if "conversation_text" not in st.session_state:
    st.session_state.conversation_text = ""
if "utterances" not in st.session_state:
    st.session_state.utterances = []
if "speaker_options" not in st.session_state:
    st.session_state.speaker_options = []

# Streamlit UI
st.set_page_config(page_title="Add conversation", layout="centered")
st.title("🗣️ Add Conversation")

# Get people from DB
def get_people_from_db():
    document = collection.find_one({"table_name": "people"})
    return {name: {**details, "name": name} for name, details in document.get("people", {}).items()} if document else {}

people_data = get_people_from_db()
existing_person = list(people_data.keys())
person_name = st.selectbox("👤 Select a Person who you are speaking with", existing_person)
conversation_date = st.date_input("📅 Conversation Date", date.today())

# Choose input method
st.markdown("### 🎧 Choose Audio Input Method")
input_method = st.radio("Select input method:", ["🎙️ Record Audio", "📁 Upload Audio File"])

audio_bytes = None

if input_method == "🎙️ Record Audio":
    audio_bytes = audio_recorder(pause_threshold=2.0, sample_rate=44100)
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")

elif input_method == "📁 Upload Audio File":
    uploaded_file = st.file_uploader("Upload an audio file (WAV, MP3, M4A)", type=["wav", "mp3", "m4a"])
    if uploaded_file:
        audio_bytes = uploaded_file.read()
        st.audio(audio_bytes)

# Transcription
if audio_bytes:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_bytes)
        temp_audio_path = temp_audio.name

    if st.button("🧠 Transcribe Audio"):
        with st.spinner("Transcribing..."):
            try:
                config = aai.TranscriptionConfig(speaker_labels=True)
                transcript = transcriber.transcribe(temp_audio_path, config=config)

                # Store speaker options and utterances
                utterances = transcript.utterances
                speaker_ids = sorted(set([f"Speaker {utt.speaker}" for utt in utterances]))
                st.session_state.utterances = utterances
                st.session_state.speaker_options = speaker_ids
                st.success("✅ Transcription complete! Select who you were in the conversation below.")

            except Exception as e:
                st.error(f"❌ Transcription failed: {e}")

# If transcription was done
if st.session_state.speaker_options:
    selected_speaker = st.radio("🗣️ Who is the person conversation?", st.session_state.speaker_options,index=None)

    # Extract only the user's lines
    if selected_speaker:
        utt=[f"Speaker {utt.speaker}: {utt.text}" for utt in st.session_state.utterances]
        user_utterances=[i.replace(selected_speaker,person_name) for i in utt]
        # iam=st.session_state.speaker_options.copy()
        # iam.remove(selected_speaker)

        # user_utterances=[i.replace(iam,person_name) for i in utt]
        full_user_text = "\n".join(user_utterances)
        st.session_state.conversation_text = full_user_text
    else:
        utterances = [f"Speaker {utt.speaker}: {utt.text}" for utt in st.session_state.utterances]
        st.session_state.conversation_text = "\n".join(utterances)
        st.success("✅ Transcription complete!")

# Show conversation text editor
conversation_text = st.text_area("✏️ Edit or Add Conversation Text", value=st.session_state.conversation_text, height=200)

# Save to DB
if st.button("💾 Save Conversation"):
    if person_name and conversation_text.strip():
        date_str = conversation_date.strftime("%Y-%m-%d")
        conversation_entry = {"conversation": conversation_text.strip()}

        update_result = collection.update_one(
            {"table_name": "people", f"people.{person_name}": {"$exists": True}},
            {"$set": {f"people.{person_name}.conversations.{date_str}": conversation_entry}},
        )

        if update_result.modified_count > 0:
            st.success(f"✅ Conversation saved for {person_name} on {date_str}.")
        else:
            st.error("❌ Failed to update conversation in DB.")
    else:
        st.warning("⚠️ Please provide all required details.")
