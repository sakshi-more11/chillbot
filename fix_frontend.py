import streamlit as st
import requests
import tempfile
import sounddevice as sd
import wave
import time
import os
import json
import csv
from datetime import datetime, date, timedelta
import random
from streamlit_extras.switch_page_button import switch_page
from streamlit_lottie import st_lottie
from streamlit_quill import st_quill
from streamlit_calendar import calendar
import speech_recognition as sr
from plyer import notification
import threading

# Backend API URL
FLASK_API_URL = "http://127.0.0.1:5000"

# Function to load Lottie animations
def load_lottie(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

def load_lottie_file(filepath):
    with open(filepath, "r") as f:
        return json.load(f)

# Load animations
chat_animation = load_lottie("https://assets9.lottiefiles.com/packages/lf20_q5pk6p1k.json")
chatbot_logo = load_lottie_file("Animation - chatbot.json")

st.set_page_config(
    page_title="ChillBot - Your Sukh Dukh Ka Sathi",
    page_icon="🤖",
    layout="wide"
)

# Function to show desktop notifications
def show_notification(title, message):
    notification.notify(
        title=title,
        message=message,
        app_name="Goal Tracker",
        timeout=10  # Notification stays for 10 seconds
    )

# Function to record user speech
def record_audio(duration=5, sample_rate=44100):
    st.info("🎙️ Recording... Speak now!")
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=2, dtype="int16")
    sd.wait()

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    with wave.open(temp_file.name, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data)

    return temp_file.name

GOALS_FILE = "goals.json"

def load_goals():
    if os.path.exists(GOALS_FILE):
        with open(GOALS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return []

def save_goals(goals):
    with open(GOALS_FILE, "w", encoding="utf-8") as file:
        json.dump(goals, file, indent=4)

# Sidebar Navigation
st.sidebar.title("🚀 ChillBot Menu")
menu = st.sidebar.radio("📌 Select an option", [
    "🏠 Welcome",
    "💬 Chat",
    "🧘‍♂️ Healthy Day Planner", 
    "📝 SoulSpace Diary",
    "🎯 Goal Tracker",
    "📜 Chat History",
    "ℹ️ About"
])
# Welcome Page
# Welcome Page (Default Home Screen)
if menu == "🏠 Welcome":
    # Custom CSS for styling
    st.markdown(
        """
        <style>
        .center {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-top: 10px;
        }
        .typing {
            font-size: 18px;
            font-weight: bold;
            color: #333;
            border-right: 3px solid black;
            white-space: nowrap;
            overflow: hidden;
            width: 100%;
            animation: typing 3s steps(30, end), blink 0.8s infinite;
        }
        @keyframes typing {
            from { width: 0 }
            to { width: 100% }
        }
        @keyframes blink {
            50% { border-color: transparent }
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Title
    st.markdown("<h1 style='text-align: center;'>🤖 Chillbot - Your Sukh Dukh Ka Saathi</h1>", unsafe_allow_html=True)
    
    # Chatbot logo animation (Centered)
    st.markdown("<div class='center'>", unsafe_allow_html=True)
    st_lottie(chatbot_logo, speed=1, height=200, key="chatbot_logo")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Tagline
    st.markdown("<h3 style='text-align: center; color: gray;'>Chill, Chat, and Learn – The Smartest Study Buddy!</h3>", unsafe_allow_html=True)
    
    # Typing Effect for Chatbot's Greeting
    st.markdown("<div class='typing'>Hey there! I'm Chillbot, your study & emotional support buddy. Let's get started! 😊</div>", unsafe_allow_html=True)
    time.sleep(2)
    
    # User Input Form
    with st.form("user_info_form"):
        name = st.text_input("Enter your name:")
        study_level = st.selectbox("Select your study level:", ["School", "College", "Graduation", "Post-Graduation", "Other"])
        chatbot_expectation = st.selectbox("What do you expect from this chatbot?", ["Learning", "Productivity", "Fun", "Emotional Support"])
        
        # New Inputs
        hobbies = st.text_area("What are your hobbies?", placeholder="E.g., Reading, Gaming, Painting, Music, etc.")
        favorite_activity = st.text_area("What do you love to do when you're feeling nervous, sad, or demotivated?",
                                         placeholder="E.g., Listening to music, talking to a friend, watching movies, journaling, etc.")
        used_chatbot_before = st.radio("Have you used any chatbot like this before?", ["Yes", "No"])

        submit = st.form_submit_button("Submit")
        
        if submit:
            # Response based on chatbot experience
            if used_chatbot_before == "Yes":
                chatbot_response = "Wow, great! Now you can experience ChillBot in a whole new way! 🚀"
            else:
                chatbot_response = "Yay! This is your first time. Welcome!! Enjoy chatting! 😊"
            
            st.success(f" {chatbot_response}🎉")
            st.markdown(f"I see you enjoy {hobbies}, and when you're feeling low, you love {favorite_activity}. That's amazing! 😊")
            st.markdown("I'm here to help you in every way – whether it's *studies, motivation, or just chilling!* 🚀")
            st.balloons()

# Chat Page
elif menu == "💬 Chat":
    st.title("🤖 ChillBot - Your Sukh Dukh Ka Sathi")

    if chat_animation:
        st_lottie(chat_animation, height=200)

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    chat_container = st.container()
    with chat_container:
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    # Speech recognition function
    def recognize_speech():
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.write("🎙️ Speak now...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)
            try:
                text = recognizer.recognize_google(audio)
                return text
            except sr.UnknownValueError:
                return "Sorry, I couldn't understand that."
            except sr.RequestError:
                return "Speech recognition service is unavailable."

    col1, col2 = st.columns([4, 1])

    # Text input (left) and Mic button (right)
    with col1:
        user_input = st.chat_input("Type your message...")

    with col2:
        if st.button("🎤"):
            user_input = recognize_speech()
            st.write(f"🗣️ {user_input}")  # Display spoken text

    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})

        with chat_container:
            with st.chat_message("user"):
                st.write(user_input)

        with st.spinner("ChillBot is thinking... 🤖"):
            response = requests.post(f"{FLASK_API_URL}/chat", json={"message": user_input}).json()
            bot_response = response.get("response", "I'm here to help! Ask me anything!")
            videos = response.get("videos", [])

        st.session_state["messages"].append({"role": "assistant", "content": bot_response})

        with chat_container:
            with st.chat_message("assistant"):
                st.write(bot_response)

                if videos:
                    st.subheader("🎥 Recommended Videos")
                    for video in videos:
                        st.video(video)
                        st.markdown(f"[🔗 Watch Here]({video})", unsafe_allow_html=True)

# Healthy Day Planner Page
elif menu == "🧘‍♂️ Healthy Day Planner":

    st.title("🧘‍♂ Healthy Day Planner")

    # Fetch health data from backend
    health_data = requests.get(f"{FLASK_API_URL}/get_health_data").json()

    # Self-Care Habits Tracking
    st.subheader("💪 Track Your Self-Care Habits")
    habits = ["Meditation", "Exercise", "Journaling", "Sleep Tracking"]  # Removed "Drinking Water"
    
    for habit in habits:
        streak = health_data.get(habit, {}).get("streak", 0)
        checked = st.checkbox(f"✔ {habit} ({streak}🔥)", value=streak > 0)
        if checked and streak == 0:
            requests.post(f"{FLASK_API_URL}/update_health_habit", json={"habit": habit})
            st.success(f"🎉 You completed {habit} today! Streak updated!")
            st.rerun()

    # Nature & Outdoor Activities Tracking
    st.subheader("🌿 Nature & Outdoor Activities")
    outdoor_activities = ["Sunlight Exposure", "Gardening & Plant Care"]
    
    for activity in outdoor_activities:
        completed = st.checkbox(f"✔ {activity}", value=False)
        if completed:
            st.success(f"🌞 You spent time on {activity} today! Keep it up!")
    st.subheader("⏰ Set an Alarm")
    alarm_name = st.text_input("Alarm Name")
    alarm_time = st.text_input("Enter alarm time (YYYY-MM-DD HH:MM)")
    alarm_message = st.text_area("Alarm Message (Optional)", "Time to act! 🚀")

    if st.button("Set Alarm 🚀"):
        try:
            alarm_datetime = datetime.strptime(alarm_time, "%Y-%m-%d %H:%M")
            response = requests.post(f"{FLASK_API_URL}/set_alarm", json={
                "name": alarm_name,
                "time": alarm_time,
                "message": alarm_message
            })
            if response.status_code == 200:
                st.success(f"✅ Alarm '{alarm_name}' set for {alarm_datetime} ⏰")
            else:
                st.error("❌ Failed to set alarm. Try again!")
        except ValueError:
            st.error("❌ Invalid time format! Use YYYY-MM-DD HH:MM")

#Souldiary Page
elif menu == "📝 SoulSpace Diary":
    st.title("📝 SoulSpace Diary - Reflect, Express, Heal")

    DIARY_FILE = "soulspace_diary.json"

    def load_diary():
        if os.path.exists(DIARY_FILE):
            with open(DIARY_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        return {"entries": []}

    def save_diary(entries):
        with open(DIARY_FILE, "w", encoding="utf-8") as file:
            json.dump(entries, file, indent=4)

    motivational_quotes = [
    "Believe in yourself, you’re unstoppable! 🌟",
    "Every day is a new beginning. Take a deep breath and start again. 🌅",
    "You are capable of amazing things. 💪",
    "Progress, not perfection. Keep going. 🚀",
    "Your feelings are valid. 🌈",
    "You are stronger than you think—keep fighting! 💖",
    "Celebrate your small victories; they lead to big achievements. 🏆",
    "Your potential is limitless. Don’t hold back! 🌌",
    "Mistakes are proof that you're trying. 📚",
    "Focus on the positives; the rest will sort itself out. ☀️",
    "Every challenge is an opportunity to grow. 🌱",
    "It’s okay to pause, but never quit. ⏳",
    "The hardest paths lead to the most beautiful destinations. 🛤️",
    "Your hard work will pay off; trust the process. 🙌",
    "Every day is another chance to make your dreams come true. 🌟",
    "Embrace your uniqueness—it’s your superpower! 🦸",
    "Success is built on the foundation of persistence and courage. 🏗️",
    "You’re already halfway there, keep going! 🏃",
    "Strength grows in the moments you think you can't go on but do. 💥",
    "Turn every doubt into determination. You've got this! 🛠️",
    "Kindness is never wasted—it always comes back to you. 🌈",
    "Believe in your dreams, even if others don’t. 🌙",
    "Keep shining your light—someone out there needs it. 💡",
    ]

    #  Random Motivational Quote
    st.subheader("🌟 Quote of the Day")
    st.success(random.choice(motivational_quotes))

    # Load existing diary entries
    diary_data = load_diary()
    
    # New Diary Entry Section
    with st.expander("➕ New Diary Entry"):
        entry_date = st.date_input("📅 Select the date for your entry:", datetime.now().date())
        entry_title = st.text_input("📝 Title of your entry")
        entry_text = st.text_area("Express yourself here...", height=200)

        if st.button("💾 Save Entry"):
            if entry_text.strip():
                diary_data["entries"].append({
                    "timestamp": entry_date.strftime("%Y-%m-%d"),
                    "title": entry_title.strip() if entry_title.strip() else "Untitled",
                    "content": entry_text.strip(),
                })
                save_diary(diary_data)
                st.success(f"Entry for {entry_date.strftime('%Y-%m-%d')} saved successfully! 🌸")
                st.rerun()
            else:
                st.warning("Please write something to save.")
    
    # Display Diary Entries
    st.subheader("📜 Your Diary Entries")
    if diary_data["entries"]:
        sorted_entries = sorted(diary_data["entries"], key=lambda x: x['timestamp'], reverse=True)

        for idx, entry in enumerate(sorted_entries):
            with st.expander(f"📖 {entry['title']} - {entry['timestamp']}"):
                st.markdown(entry["content"], unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑 Delete", key=f"del_{idx}"):
                        diary_data["entries"].pop(idx)
                        save_diary(diary_data)
                        st.success("Entry deleted successfully. 🗑️")
                        st.rerun()
                with col2:
                    st.download_button("⬇️ Download", entry["content"], file_name=f"{entry['title']}.txt", mime="text/plain", key=f"download_{entry['title']}")
    else:
        st.info("No diary entries yet. Start expressing yourself above! ✍️")

# Goal Tracker Page
elif menu == "🎯 Goal Tracker":
    st.title("🎯 Goal Tracker")
    st.subheader("Set & Track Your Goals with Smart Reminders")

    # Long-Term Goal Section
    st.header("📅 Long-Term Goals")
    if "long_term_goals" not in st.session_state:
        st.session_state.long_term_goals = []

    long_term_goal = st.text_input("Enter Long-Term Goal:")
    start_date = st.date_input("Start Date:")
    end_date = st.date_input("End Date:")

    if st.button("Add Long-Term Goal"):
        st.session_state.long_term_goals.append((long_term_goal, start_date, end_date))
        st.success(f"✅ Added Long-Term Goal: '{long_term_goal}'")

    for goal, s_date, e_date in st.session_state.long_term_goals:
        st.write(f"📌 {goal} (From {s_date} to {e_date})")

        while True:
            current_date = date.today()
            if current_date == e_date:
                show_notification("📌 Long-Term Goal Reminder", f"Today is the deadline for: {goal}")
                break
            time.sleep(86400)  # Check every 24 hours

    # Short-Term Goal Section
    st.header("📆 Short-Term Goals")
    if "short_term_goals" not in st.session_state:
        st.session_state.short_term_goals = []

    short_term_goal = st.text_input("Enter Short-Term Goal:")
    reminder_time = st.time_input("Set Reminder Time:")

    day_option = st.radio("Set for:", ("Today", "Tomorrow", "Custom Date"))
    reminder_date = date.today() if day_option == "Today" else date.today() + timedelta(days=1)
    if day_option == "Custom Date":
        reminder_date = st.date_input("Select Date:")

    if st.button("Add Short-Term Goal"):
        st.session_state.short_term_goals.append((short_term_goal, reminder_date, reminder_time))
        st.success(f"✅ Added Short-Term Goal: '{short_term_goal}'")

    for goal, r_date, r_time in st.session_state.short_term_goals:
        st.write(f"⏳ {goal} (On {r_date} at {r_time.strftime('%H:%M')})")

        while True:
            current_datetime = datetime.now()
            reminder_datetime = datetime.combine(r_date, r_time)
            if current_datetime >= reminder_datetime:
                show_notification("⏳ Short-Term Goal Reminder", f"Time for: {goal}")
                break
            time.sleep(10)  # Check every 10 second
# Calendar View for Reminders
    
    st.write("## 📅 Reminder Calendar")

    goals = []

    # Retrieve Long-Term Goals
    if "long_term_goals" in st.session_state:
       for goal, s_date, e_date in st.session_state.long_term_goals:
         goals.append({"title": goal, "start": str(s_date), "end": str(e_date)})

    # Retrieve Short-Term Goals
    if "short_term_goals" in st.session_state:
      for goal, r_date, r_time in st.session_state.short_term_goals:
        goals.append({"title": goal, "start": str(r_date), "end": str(r_date)})  # One-day event

    # Display Calendar
    calendar(goals, options={"initialView": "dayGridMonth", "editable": False})
       

# Chat History Page
elif menu == "📜 Chat History":
    st.title("📜 Your Chat History")

    if "messages" in st.session_state and st.session_state["messages"]:
        st.subheader("🗨️ Recent Conversations")
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
    else:
        st.info("No recent chat history available.")

    chat_log_file = "chat_history.csv"
    if os.path.exists(chat_log_file):
        st.subheader("🕰️ Saved Conversation History")
        try:
            with open(chat_log_file, "r", encoding="utf-8") as csvfile:
                csv_reader = csv.reader(csvfile)
                headers = next(csv_reader, None)
                rows = list(csv_reader)

                if rows:
                    rows.reverse()
                    for row in rows:
                        if len(row) >= 3:
                            user_msg, bot_msg, timestamp = row
                            st.markdown(f"👤 **User:** {user_msg}")
                            st.markdown(f"🤖 **ChillBot:** {bot_msg}")
                            st.markdown(f"🕒 **Time:** {timestamp}")
                            st.markdown("---")
                else:
                    st.info("No saved chat history available.")
        except Exception as e:
            st.error(f"Error reading chat history: {e}")
    else:
        st.info("No saved conversations yet.")

# Alarm Feature
elif menu == "⏰ Alarm":
    st.subheader("⏰ Set an Alarm")
    alarm_name = st.text_input("Alarm Name")
    alarm_time = st.text_input("Enter alarm time (YYYY-MM-DD HH:MM)")
    alarm_message = st.text_area("Alarm Message (Optional)", "Time to act! 🚀")

    if st.button("Set Alarm 🚀"):
        try:
            alarm_datetime = datetime.datetime.strptime(alarm_time, "%Y-%m-%d %H:%M")
            response = requests.post(f"{FLASK_API_URL}/set_alarm", json={
                "name": alarm_name,
                "time": alarm_time,
                "message": alarm_message
            })
            if response.status_code == 200:
                st.success(f"✅ Alarm '{alarm_name}' set for {alarm_datetime} ⏰")
            else:
                st.error("❌ Failed to set alarm. Try again!")
        except ValueError:
            st.error("❌ Invalid time format! Use YYYY-MM-DD HH:MM")

# About Page
elif menu == "ℹ️ About":
    st.write("### About ChillBot 🚀")
    st.write("""
    - **AI-Powered Chatbot**
    - **SoulSpace Diary feature to express feelings**
    - **Goal Tracker with Progress Monitoring**
    - **YouTube API for Videos**
    - **Speech Recognition for Voice Input**
    - **Desktop Notifications**
    - **Health Tracker & Alarm Features**
     - **Built with ❤️ by Team ChillBot**
            - @Vedika Sardeshmukh
            - @Sakshi More
            - @Dnyaneshwari Pawar
            - @Vedanti Ghongade
    """)