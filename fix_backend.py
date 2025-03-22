from flask import Flask, request, jsonify,send_file
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import os
import requests
import csv
import datetime
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from dotenv import load_dotenv
from flask_cors import CORS
import time
import threading
import playsound
import pygame
import re
from plyer import notification
import json

# Load API keys
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# Sentiment Analyzer
# File Paths
HEALTH_TRACKER_FILE = "health_data.json"
REMINDERS_FILE = "wellness_reminders.json"
ALARMS = []
sentiment_analyzer = SentimentIntensityAnalyzer()

# Initialize TTS engine
tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 150)  # Adjust speech speed


# CSV file for conversation history
CSV_FILE = "chat_history.csv"
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "User Input", "Bot Response"])

# System Prompt
SYSTEM_PROMPT = """
You are 'ChillBot', a student-focused AI assistant.  
Your job is to give **motivational, practical, and friendly responses** to student queries.  
You can provide study tips, motivational advice, or engage in casual conversation.
If the student asks a **study-related question**, give a **concise and correct** answer.
If they express **stress, demotivation, or personal issues**, provide **empathetic and positive guidance**.
Avoid long-winded explanations—be **clear, friendly, and to the point**.

✨ **Gen Z Vibes Only!** Use emojis, keep it real, and be fun! ✨

Examples:
User: "I'm struggling to focus on studies."
ChillBot: "Try the **Pomodoro technique** – 25 min study, 5 min break. A clean study space helps too! 📚💡"

User: "I'm feeling demotivated about exams."
ChillBot: "It happens! Break it down: small goals, daily targets. Progress matters more than perfection. You've got this! 💪✨"

Now, respond to the user’s query:
"""

# Sentiment Analysis
def analyze_sentiment(user_query):
    sentiment_score = sentiment_analyzer.polarity_scores(user_query)["compound"]
    if sentiment_score < -0.3:
        return "😔 Feeling low"
    elif sentiment_score > 0.3:
        return "😊 Feeling good"
    else:
        return "🙂 Neutral mood"

# Check if a query needs study videos
def needs_study_videos(user_query):
    study_keywords = ["study", "video", "resource", "course", "playlist"]
    return any(keyword in user_query.lower() for keyword in study_keywords)

# Fetch YouTube Study Videos
def fetch_study_videos(query):
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&key={YOUTUBE_API_KEY}"
    response = requests.get(url).json()
    
    video_links = [
        f"https://www.youtube.com/watch?v={item['id']['videoId']}" 
        for item in response.get("items", []) if "videoId" in item.get("id", {})
    ]
    
    return video_links[:3]  # Return top 3 results

# Generate AI Response
def get_gemini_response(user_input):
    prompt = SYSTEM_PROMPT + f"\nUser: {user_input}\nChillBot: "
    response = model.generate_content(prompt)
    return response.text.strip()

# Store Conversation History
def save_to_csv(user_input, bot_response):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, user_input, bot_response])

# Optional: Home route@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "🚀 ChillBot is running! Ready to chat? Send a POST request to /chat."
    })

# Flask Routes
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "🚀 ChillBot is running! Ready to chat? Send a POST request to /chat."})

#chat resonses
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("message", "").strip()

    if not user_input:
        return jsonify({"response": "Oops! Looks like you forgot to type something. Try again! 🤔"})

    bot_response = get_gemini_response(user_input)
    video_links = fetch_study_videos(user_input) if needs_study_videos(user_input) else []
    save_to_csv(user_input, bot_response)

    return jsonify({
        "response": bot_response,
        "mood": analyze_sentiment(user_input),
        "videos": video_links,
        "note": "🔥 Keep going, you're doing amazing!"
    })

# --- 🕰️ Local Alarm System ---
alarms = []  # List to store alarms

# 🔊 Function to play alarm sound reliably
def play_alarm_sound():
    sound_file = "ringtone.mp3"
    if not os.path.exists(sound_file):
        print("🔊 Alarm sound file missing.")
        return
    pygame.mixer.init()
    pygame.mixer.music.load(sound_file)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(1)

# 🕰️ Alarm Checker Thread
def alarm_checker():
    while True:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        triggered_alarms = []  

        for alarm in alarms:
            if alarm["time"] == now:
                print(f"⏰ ALARM: {alarm['message']}")  
                try:
                    play_alarm_sound()
                except Exception as e:
                    print(f"🔊 Alarm sound failed: {e}")
                triggered_alarms.append(alarm)  

        # Remove alarms outside the loop
        for alarm in triggered_alarms:
            alarms.remove(alarm)

        time.sleep(30)

# Start alarm checking thread
threading.Thread(target=alarm_checker, daemon=True).start()

#  API to Set an Alarm
@app.route("/set_alarm", methods=["POST"])
def set_alarm():
    data = request.json
    alarm_message = data.get("message", "Reminder ⏰")
    alarm_time = data.get("time", "")

    # Validate time format
    if not re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", alarm_time):
        return jsonify({"error": "Invalid format! Use 'YYYY-MM-DD HH:MM'."}), 400

    alarms.append({"time": alarm_time, "message": alarm_message})
    return jsonify({"response": f"Alarm set for {alarm_time}"}), 200

# API to Get Active Alarms
@app.route("/alarms", methods=["GET"])
def get_alarms():
    return jsonify({"active_alarms": alarms}), 200

#Goal tracking logic
GOAL_FILE = "goals.json"


def load_goals():
    try:
        with open(GOAL_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_goals(goals):
    with open(GOAL_FILE, "w") as f:
        json.dump(goals, f, indent=4)


@app.route("/add_goal", methods=["POST"])
def add_goal():
    data = request.json
    goals = load_goals()
    goals.append(data)
    save_goals(goals)
    return jsonify({"message": "Goal added successfully"}), 200

@app.route("/update_goal", methods=["POST"])
def update_goal():
    updated_goal = request.json
    goals = load_goals()
    for i, g in enumerate(goals):
        if g["goal"] == updated_goal["goal"]:
            goals[i] = updated_goal
            break
    save_goals(goals)
    return jsonify({"message": "Goal updated successfully"}), 200

@app.route("/delete_goal", methods=["POST"])
def delete_goal():
    data = request.json
    goals = [g for g in load_goals() if g["goal"] != data["goal"]]
    save_goals(goals)
    return jsonify({"message": "Goal deleted successfully"}), 200

@app.route("/get_goals", methods=["GET"])
def get_goals():
    return jsonify(load_goals()), 200

# Retrieve Conversation History
@app.route("/history", methods=["GET"])
def get_history():
    try:
        df = pd.read_csv(CSV_FILE)
        return jsonify(df.to_dict(orient="records"))
    except Exception:
        return jsonify({"error": "Could not retrieve history. Try again later!"})
    
@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    recognizer = sr.Recognizer()
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    audio_file = request.files['audio']
    audio_path = "temp_audio.wav"
    audio_file.save(audio_path)

    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio)  # Convert speech to text
        return jsonify({"text": text})
    except sr.UnknownValueError:
        return jsonify({"text": "Could not understand audio"})
    except sr.RequestError:
        return jsonify({"text": "Speech service unavailable"})

# Healthy Day Planner - Habit Tracking
@app.route("/get_health_data", methods=["GET"])
def get_health_data():
    if os.path.exists(HEALTH_TRACKER_FILE):
        with open(HEALTH_TRACKER_FILE, "r") as f:
            return jsonify(json.load(f))
    return jsonify({})

@app.route("/update_health_habit", methods=["POST"])
def update_health_habit():
    data = request.json
    habit = data.get("habit")
    if not habit:
        return jsonify({"error": "Invalid habit"})
    
    health_data = {}
    if os.path.exists(HEALTH_TRACKER_FILE):
        with open(HEALTH_TRACKER_FILE, "r") as f:
            health_data = json.load(f)
    
    health_data[habit] = {"streak": health_data.get(habit, {}).get("streak", 0) + 1}
    with open(HEALTH_TRACKER_FILE, "w") as f:
        json.dump(health_data, f)
    
    return jsonify({"success": True, "habit": habit})

@app.route("/set_wellness_reminder", methods=["POST"])
def set_wellness_reminder():
    data = request.json
    message = data.get("message")
    time = data.get("time")
    
    reminders = []
    if os.path.exists(REMINDERS_FILE):
        with open(REMINDERS_FILE, "r") as f:
            reminders = json.load(f)
    
    reminders.append({"message": message, "time": time})
    with open(REMINDERS_FILE, "w") as f:
        json.dump(reminders, f)
    
    return jsonify({"success": True, "message": message})

# Run Flask App
if __name__ == "__main__":
    print("🎉 Chillbot Backend is Live! 🚀")
    app.run(host="0.0.0.0", port=5000, debug=True)