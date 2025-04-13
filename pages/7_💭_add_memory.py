import streamlit as st
from datetime import date
from pymongo import MongoClient
import os
# Assuming you have a MongoDB client setup
from pymongo import MongoClient
import os

# Mongo setup
mongodb_uri = os.getenv("MONGODB_URI")
mongodb_database = os.getenv("MONGODB_DATABASE")
collection_name = "companion"
client = MongoClient(mongodb_uri)
db = client[mongodb_database]
collection = db[collection_name]

def get_memories():
    doc = collection.find_one({"table_name": "memories"})
    return doc.get("memories", {}) if doc else {}



# Function to fetch people from DB (Updated from your code)
def get_people_from_db():
    document = collection.find_one({"table_name": "people"})
    if not document:
        return {}

    people = document.get("people", {})
    name_to_info = {}

    for name, details in people.items():
        img_data = details.get("image")
    
        person_info = details.copy()
        
        person_info["name"] = name
        name_to_info[name] = person_info
    return name_to_info


st.title("🧠 Add Memory")

memory_title = st.text_input("Memory Title")
add_date = st.checkbox("Include memory date?")
memory_date = st.date_input("Memory Date") if add_date else None
memory_description = st.text_area("Memory Description")

if st.button("➕ Add Memory"):
    if memory_title and memory_description:
        memory_entry = {"description": memory_description}
        if add_date and memory_date:
            memory_entry["date"] = str(memory_date)

        existing_memories = collection.find_one({"table_name": "memories"})
        if existing_memories:
            collection.update_one(
                {"table_name": "memories"},
                {"$set": {f"memories.{memory_title}": memory_entry}},
            )
        else:
            collection.insert_one(
                {"table_name": "memories", "memories": {memory_title: memory_entry}}
            )

        st.success(f"Memory '{memory_title}' added successfully! 💙")
    else:
        st.error("⚠️ Please fill in all details to add a memory.")

# Show past memories
st.markdown("### 📝 Recent Memories")
memories = get_memories()
if memories:
    for title, mem in list(memories.items())[-3:][::-1]:  # last 3
        st.subheader(f"📌 {title}")
        if "date" in mem:
            st.caption(f"🗓 Date: {mem['date']}")
        st.write(mem["description"])
        st.markdown("---")
else:
    st.info("No memories available.")
