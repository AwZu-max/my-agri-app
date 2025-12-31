import streamlit as st
import google.generativeai as genai
from PIL import Image
import speech_recognition as sr
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder
import tempfile
import os
import re
from pydub import AudioSegment
import io
import random
import time

# --- Page Config ---
st.set_page_config(page_title="Smart Agri Pro", page_icon="🌾", layout="wide")

# --- CSS for Mobile Polish (ဖုန်းအတွက် ဒီဇိုင်းပြင်ဆင်ချက်) ---
st.markdown("""
    <style>
    /* Desktop Title */
    .main-title {
        text-align: center; color: #2E8B57; font-size: 2.5em; font-weight: bold; margin-bottom: 20px;
    }
    
    /* Sub-header Styling */
    h2, h3 {
        color: #444 !important;
    }

    /* Mobile Responsive Fixes */
    @media (max-width: 600px) {
        /* ခေါင်းစဉ်ကြီးကို ဖုန်းမှာ သေးမယ် */
        .main-title { 
            font-size: 1.6em !important; 
            margin-bottom: 10px;
        }
        /* အပိုင်းခေါင်းစဉ်တွေကိုလည်း သေးမယ် */
        h2 {
            font-size: 1.3em !important;
        }
        h3 {
            font-size: 1.1em !important;
        }
        /* Sidebar ကို ဖုန်းမှာ အပြည့်မပေါ်အောင် */
        section[data-testid="stSidebar"] {
            width: 250px !important;
        }
        /* Chat Message တွေကို ဖုန်းမှာ နေရာချောင်အောင်လုပ်မယ် */
        .stChatMessage {
            padding: 5px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# --- Configuration & API Keys ---
api_keys = []
if "api_keys" in st.secrets:
    api_keys = st.secrets["api_keys"]
elif "GOOGLE_API_KEY" in st.secrets:
    api_keys = [st.secrets["GOOGLE_API_KEY"]]
else:
    api_keys = ["YOUR_API_KEY_HERE"]

# --- Session State ---
if "garden_history" not in st.session_state: st.session_state.garden_history = []
if "paddy_history" not in st.session_state: st.session_state.paddy_history = []
if "doctor_history" not in st.session_state: st.session_state.doctor_history = []

# --- Helper Functions ---
def clean_text_for_speech(text):
    clean = re.sub(r'[\*\#\-\_]', '', text)
    clean = " ".join(clean.split())
    return clean

def text_to_speech(text):
    try:
        clean_text = clean_text_for_speech(text)
        tts = gTTS(text=clean_text, lang='my')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            return fp.name
    except:
        return None

def transcribe_audio(audio_bytes):
    r = sr.Recognizer()
    try:
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as fp:
            audio_segment.export(fp.name, format="wav")
            temp_filename = fp.name
        with sr.AudioFile(temp_filename) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language="my-MM")
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        return text
    except:
        return None

def get_ai_response_smart(prompt, image=None):
    shuffled_keys = api_keys.copy()
    random.shuffle(shuffled_keys)
    
    for key in shuffled_keys:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            chat = model.start_chat(history=[])
            if image:
                response = chat.send_message([prompt, image])
            else:
                response = chat.send_message(prompt)
            
            final_text = response.text.replace("ခင်ဗျာ", "ရှင်").replace("ခဗျာ", "ရှင်").replace("ครับ", "ရှင်")
            return final_text
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "Quota" in error_msg or "403" in error_msg:
                continue
            return f"စနစ်ချို့ယွင်းချက်: {e}"
    return "⚠️ ခဏလေး စောင့်ပေးပါရှင်... (၁) မိနစ်ခန့် နားပြီးမှ ပြန်မေးပေးပါရှင်။"

# --- Main Layout ---
st.markdown('<h1 class="main-title">🌾 Smart Agri - စိုက်ပျိုးရေး လက်ထောက်</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ ဆက်တင်")
    app_mode = st.radio("လုပ်ဆောင်ချက် ရွေးချယ်ပါ:",
        ["🏡 အိမ်ခြံသီးနှံ (Garden)", "🌾 စပါးစိုက်ခင်း (Paddy)", "🍂 ရောဂါစစ်ဆေး (Doctor)"])
    
    st.divider()
    enable_voice = st.checkbox("🔊 အသံဖြင့် ပြန်ဖတ်ပြပါ", value=True)
    
    if st.button("🗑️ မှတ်တမ်းဖျက်မည် (Clear)"):
        if app_mode == "🏡 အိမ်ခြံသီးနှံ (Garden)": st.session_state.garden_history = []
        elif app_mode == "🌾 စပါးစိုက်ခင်း (Paddy)": st.session_state.paddy_history = []
        elif app_mode == "🍂 ရောဂါစစ်ဆေး (Doctor)": st.session_state.doctor_history = []
        st.rerun()

# Dashboard Layout
col_control, col_chat = st.columns([1, 2], gap="large")

# --- COLUMN 1: Inputs (Expander Added for Mobile) ---
with col_control:
    # 🔥 ဖုန်းမှာ နေရာမယူအောင် Expander နဲ့ အုပ်လိုက်ပါပြီ
    with st.expander(f"📝 {app_mode} အချက်အလက်ဖြည့်ရန် (နှိပ်ပါ)", expanded=True):
        
        context_prompt = ""
        current_image = None
        
        if app_mode == "🏡 အိမ်ခြံသီးနှံ (Garden)":
            plant_name = st.text_input("အပင်အမည်:", placeholder="ဥပမာ- ရုံးပတီ")
            tank_size = st.number_input("ရေကန် (ဂါလံ):", value=50)
            field_desc = st.text_input("မြေအနေအထား:", placeholder="နေရောင်ရ/မရ")
            if plant_name:
                context_prompt = f"Context: အပင်={plant_name}, ရေကန်={tank_size}ဂါလံ, မြေ={field_desc}."

        elif app_mode == "🌾 စပါးစိုက်ခင်း (Paddy)":
            days = st.slider("စပါးသက်တမ်း (ရက်):", 1, 120, 30)
            acres = st.number_input("စိုက်ဧက:", value=5)
            status = st.text_input("အပင် အခြေအနေ:", placeholder="အရွက်ဝါ၊ ပိုးကျ..")
            context_prompt = f"Context: စပါးသက်တမ်း={days}ရက်, စိုက်ဧက={acres}, အခြေအနေ={status}."

        elif app_mode == "🍂 ရောဂါစစ်ဆေး (Doctor)":
            st.info("ဓာတ်ပုံတင်ပေးပါရှင် 👇")
            uploaded_file = st.file_uploader("ပုံရွေးပါ:", type=["jpg", "png", "jpeg"], key="doc_upload")
            if uploaded_file:
                current_image = Image.open(uploaded_file)
                st.image(current_image, caption="တင်ထားသောပုံ", use_column_width=True)
                context_prompt = "Context: This is a plant disease image diagnosis request."

        # Common Upload & Voice
        if app_mode != "🍂 ရောဂါစစ်ဆေး (Doctor)":
            st.write("---")
            uploaded_file = st.file_uploader("ဓာတ်ပုံ (Optional):", type=["jpg", "png", "jpeg"], key="common_upload")
            if uploaded_file:
                current_image = Image.open(uploaded_file)
                st.image(current_image, caption="တင်ထားသောပုံ", use_column_width=True)

        st.write("🎙️ **အသံဖြင့် ပြောရန်:**")
        audio_blob = mic_recorder(start_prompt="🔴 Start", stop_prompt="⬛ Stop", key='recorder')

# --- COLUMN 2: Chat ---
with col_chat:
    if app_mode == "🏡 အိမ်ခြံသီးနှံ (Garden)":
        current_history = st.session_state.garden_history
    elif app_mode == "🌾 စပါးစိုက်ခင်း (Paddy)":
        current_history = st.session_state.paddy_history
    else:
        current_history = st.session_state.doctor_history

    if len(current_history) == 0:
        st.info(f"မင်္ဂလာပါရှင်.. '{app_mode}' အတွက် အကြံဉာဏ်များ စတင်မေးမြန်းနိုင်ပါပြီ။")

    chat_container = st.container()
    with chat_container:
        for msg in current_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if "image" in msg and msg["image"]:
                    st.image(msg["image"], width=200)
                if "audio_path" in msg and msg["audio_path"]:
                    st.audio(msg["audio_path"], format="audio/mp3")

    # Inputs Handling
    voice_text = ""
    if audio_blob:
        with st.spinner("အသံဖတ်နေပါတယ်ရှင်..."):
            voice_text = transcribe_audio(audio_blob['bytes'])
    
    user_query = None
    if voice_text: user_query = voice_text
    
    # Input box fixed styling
    if prompt := st.chat_input("မေးခွန်း ရေးပါ..."):
        user_query = prompt

    if user_query:
        current_history.append({"role": "user", "content": user_query, "image": current_image})
        with st.chat_message("user"):
            st.write(user_query)
            if current_image: st.image(current_image, width=200)

        with st.chat_message("assistant"):
            with st.spinner("စဉ်းစားနေပါတယ်ရှင်..."):
                system_instruction = (
                    "You are a friendly female agricultural expert. "
                    "Speak naturally using 'Shin' (ရှင်). Keep sentences short."
                )
                full_prompt = f"{system_instruction}\n\n{context_prompt}\n\nUser Question: {user_query} (Answer in Burmese)"
                
                response_text = get_ai_response_smart(full_prompt, current_image)
                st.write(response_text)
                
                audio_file = None
                if enable_voice and "Error" not in response_text:
                    audio_file = text_to_speech(response_text)
                    if audio_file: st.audio(audio_file, format="audio/mp3")

                current_history.append({
                    "role": "assistant", 
                    "content": response_text,
                    "audio_path": audio_file
                })
