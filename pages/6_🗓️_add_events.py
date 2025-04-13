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


def get_events():
    doc = collection.find_one({"table_name": "events"})
    return doc.get("events", {}) if doc else {}



st.title("📅 Add Upcoming Event")

event_title = st.text_input("Event Title")
event_date = st.date_input("Event Date")
event_description = st.text_area("Event Description")

if st.button("➕ Add Event"):
    if event_title and event_date and event_description:
        event_entry = {"description": event_description, "date": str(event_date)}

        existing_events = collection.find_one({"table_name": "events"})
        if existing_events:
            collection.update_one(
                {"table_name": "events"},
                {"$set": {f"events.{event_title}": event_entry}},
            )
        else:
            collection.insert_one(
                {"table_name": "events", "events": {event_title: event_entry}}
            )

        st.success(f"Event '{event_title}' added successfully! 📅")
    else:
        st.error("⚠️ Please fill in all details to add an event.")

# Show upcoming events
st.markdown("### 🔔 Upcoming Events")
events = get_events()
if events:
    for title, evt in sorted(events.items(), key=lambda x: x[1].get("date", ""), reverse=False)[-3:]:
        st.subheader(f"📌 {title}")
        st.caption(f"🗓 Date: {evt.get('date', 'N/A')}")
        st.write(evt["description"])
        st.markdown("---")
else:
    st.info("No upcoming events found.")
