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

# --- Configuration ---
api_keys = []
if "api_keys" in st.secrets:
    api_keys = st.secrets["api_keys"]
elif "GOOGLE_API_KEY" in st.secrets:
    api_keys = [st.secrets["GOOGLE_API_KEY"]]
else:
    api_keys = ["YOUR_API_KEY_HERE"]

# --- Page Setup ---
st.set_page_config(page_title="Smart Agri Pro", page_icon="🌾", layout="wide")

st.markdown("""
    <style>
    .main-title {
        text-align: center; color: #2E8B57; font-size: 3em; font-weight: bold; margin-bottom: 10px;
    }
    @media (max-width: 600px) {
        .main-title { font-size: 1.8em !important; margin-top: 0px; }
        section[data-testid="stSidebar"] { width: 250px !important; }
    }
    </style>
    <h1 class="main-title">🌾 Smart Agri - စိုက်ပျိုးရေး လက်ထောက်</h1>
""", unsafe_allow_html=True)

# --- Session State ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- Helper Functions ---
def clean_text_for_speech(text):
    # အသံဖတ်တဲ့အခါ အနှောင့်အယှက်ဖြစ်စေမယ့် သင်္ကေတတွေကို ဖယ်မယ်
    clean = re.sub(r'[\*\#\-\_]', '', text)
    clean = " ".join(clean.split())
    return clean

def text_to_speech(text):
    try:
        clean_text = clean_text_for_speech(text)
        # gTTS က အမြန်နှုန်းချိန်လို့မရပေမယ့် စာသားတိုရင် ပိုသွက်ပါတယ်။
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

# --- Smart AI Response Function ---
def get_ai_response_smart_rotate(prompt, image=None):
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
            
            # 🔥 (၁) AI က ပြန်ဖြေလာတဲ့ စာထဲမှာ "ခင်ဗျာ" ပါရင် "ရှင်" နဲ့ အစားထိုးမယ်
            final_text = response.text.replace("ခင်ဗျာ", "ရှင်").replace("ခဗျာ", "ရှင်").replace("ครับ", "ရှင်")
            return final_text
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "Quota" in error_msg or "403" in error_msg:
                continue
            return f"စနစ်ချို့ယွင်းချက်: {e}"
    
    return "⚠️ ခဏလေး စောင့်ပေးပါရှင်... (၁) မိနစ်ခန့် နားပြီးမှ ပြန်မေးပေးပါရှင်။"

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ ဆက်တင်များ")
    app_mode = st.radio("လုပ်ဆောင်ချက် ရွေးချယ်ပါ:",
        ["🏡 အိမ်ခြံသီးနှံ (Garden)", "🌾 စပါးစိုက်ခင်း (Paddy)", "🍂 ရောဂါစစ်ဆေး (Doctor)"])
    
    st.divider()
    if st.button("🔄 အသစ်ပြန်မေးမယ် (Clear)"):
        st.session_state.history = []
        st.rerun()
    
    enable_voice = st.checkbox("🔊 အသံဖြင့် ပြန်ဖတ်ပြပါ", value=True)

# --- Main Logic ---
current_image = None 
context_prompt = ""

# 1. Input Form
with st.expander("📝 အချက်အလက်နှင့် ဓာတ်ပုံ ဖြည့်ရန် (နှိပ်ပါ)", expanded=True):
    col1, col2 = st.columns([1, 1])
    uploaded_file = st.file_uploader("📸 ဓာတ်ပုံ (Camera/Gallery):", type=["jpg", "png", "jpeg"], key="main_uploader")
    if uploaded_file:
        current_image = Image.open(uploaded_file)
        st.image(current_image, caption="တင်ထားသောပုံ", width=200)

    if app_mode == "🏡 အိမ်ခြံသီးနှံ (Garden)":
        with col1: plant_name = st.text_input("အပင်အမည် (ဥပမာ- ရုံးပတီ):")
        with col2: tank_size = st.number_input("ရေကန် (ဂါလံ):", value=50)
        field_desc = st.text_input("စိုက်ခင်း အနေအထား:")
        if plant_name: context_prompt = f"အပင်: {plant_name}. ရေကန်: {tank_size} ဂါလံ. မြေ: {field_desc}. (စိုက်ပျိုးနည်း အကြံပေးပါ)"

    elif app_mode == "🌾 စပါးစိုက်ခင်း (Paddy)":
        days = st.slider("စပါးသက်တမ်း (ရက်):", 1, 120, 30)
        acres = st.number_input("စိုက်ဧက:", value=5)
        status = st.text_input("အပင် အခြေအနေ:")
        context_prompt = f"စပါးသက်တမ်း: {days} ရက်. စိုက်ဧက: {acres} ဧက. အခြေအနေ: {status}. (လိုအပ်သည်များ အကြံပေးပါ)"

    elif app_mode == "🍂 ရောဂါစစ်ဆေး (Doctor)":
        st.info("အပင်ရောဂါ ပုံကို အပေါ်က Upload ခလုတ်မှာ တင်ပေးပါရှင်။")
        context_prompt = "ဒီပုံထဲက အပင်ရောဂါကို စစ်ဆေးပြီး ကုသနည်း ပြောပြပါ။"

# 2. Voice Input
st.write("🎙️ **အသံဖြင့် မေးရန်:**")
audio_blob = mic_recorder(start_prompt="🔴 ပြောမည် (Start)", stop_prompt="⬛ ရပ်မည် (Stop)", key='recorder')

voice_text = ""
if audio_blob:
    with st.spinner("နားထောင်နေပါတယ်ရှင်..."):
        voice_text = transcribe_audio(audio_blob['bytes'])

# 3. Chat Interface
chat_container = st.container()
with chat_container:
    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if "audio_path" in msg and msg["audio_path"]:
                st.audio(msg["audio_path"], format="audio/mp3")

# 4. Inputs Handling
user_query = None
if voice_text: user_query = voice_text
if prompt := st.chat_input("မေးမြန်းလိုသည်များ ရေးပါ..."): user_query = prompt

# Chat Attachment
with st.expander("📎 ဓာတ်ပုံ ပူးတွဲတင်ရန် (Chat Attachment)", expanded=False):
    chat_upload = st.file_uploader("Chat အတွက် ပုံရွေးပါ:", type=["jpg", "png", "jpeg"], key="chat_uploader")
    if chat_upload:
        current_image = Image.open(chat_upload)
        st.image(current_image, width=150, caption="ပူးတွဲမည့်ပုံ")

# Processing
if user_query:
    final_prompt = user_query
    if len(st.session_state.history) == 0 and context_prompt:
        final_prompt = f"{context_prompt} \n\n အသုံးပြုသူမေးခွန်း: {user_query}"

    st.session_state.history.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.write(user_query)
        if current_image and chat_upload: st.image(current_image, width=200)

    with st.chat_message("assistant"):
        with st.spinner("စဉ်းစားနေပါတယ်ရှင်..."):
            
            # 🔥 (၂) AI ကို အမျိုးသမီးလို ပြောဖို့ အမိန့်ပေးစာ (System Prompt)
            system_instruction = (
                "You are a friendly female agricultural expert. "
                "You cannot generate images. If asked for photos, politely explain that you can only provide text advice. "
                "IMPORTANT: Speak naturally, actively, and warmly like a real person. "
                "Use 'Shin' (ရှင်) instead of 'Khin-byar' (ခင်ဗျာ) at the end of sentences. "
                "Do not use overly formal language. Keep sentences short and clear."
            )
            
            full_prompt = f"{system_instruction} \n\n User Question: {final_prompt} (Please answer in Burmese language.)"
            if 'current_image' not in locals(): current_image = None
            
            response_text = get_ai_response_smart_rotate(full_prompt, current_image)
            st.write(response_text)
            
            audio_file = None
            if enable_voice and "Error" not in response_text:
                audio_file = text_to_speech(response_text)
                if audio_file: st.audio(audio_file, format="audio/mp3")

            st.session_state.history.append({
                "role": "assistant", 
                "content": response_text,
                "audio_path": audio_file
            })
