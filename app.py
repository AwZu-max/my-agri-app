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
import time

# --- Configuration ---
# ⚠️ Secrets မသုံးဘဲ Code ထဲထည့်မယ်ဆိုရင် ဒီနေရာမှာ Key ထည့်ပါ
GOOGLE_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

# Setup API Key (Secrets ရှိရင် Secrets ကို ဦးစားပေးမယ်)
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    # 1.5 အဆင်မပြေရင် 2.0 ကိုပဲ ပြန်သုံးပါမယ် (Error 429 တက်ရင် ၁ မိနစ်လောက် နားပြီးမှ သုံးပါ)
    model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    st.error(f"API Key Error: {e}")
    st.stop()

# --- Page Setup ---
st.set_page_config(page_title="Smart Agri Pro", page_icon="🌾", layout="wide")

# --- CSS for Responsive Design (ဖုန်းနှင့် ကွန်ပျူတာ အလိုအလျောက် ချိန်ညှိခြင်း) ---
st.markdown("""
    <style>
    /* ကွန်ပျူတာ Screen (PC) အတွက် ဒီဇိုင်း */
    .main-title {
        text-align: center; 
        color: #2E8B57; 
        font-size: 3em; 
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    /* ဖုန်း Screen (Mobile) အတွက် ဒီဇိုင်း - စာလုံးဆိုဒ်ကို လျှော့ချမယ် */
    @media (max-width: 600px) {
        .main-title {
            font-size: 1.8em !important; /* ဖုန်းမှာ 1.8 ပဲ ရှိမယ် */
            margin-top: 0px;
        }
        /* Sidebar ကို ဖုန်းမှာ နည်းနည်း ကျဉ်းမယ် */
        section[data-testid="stSidebar"] {
            width: 250px !important;
        }
    }
    </style>

    <h1 class="main-title">
        🌾 Smart Agri - စိုက်ပျိုးရေး လက်ထောက်
    </h1>
""", unsafe_allow_html=True)

# --- Session State ---
if "history" not in st.session_state:
    st.session_state.history = []

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
    except Exception as e:
        return None

def get_ai_response(prompt, image=None):
    try:
        chat = model.start_chat(history=[])
        if image:
            response = chat.send_message([prompt, image])
        else:
            response = chat.send_message(prompt)
        return response.text
    except Exception as e:
        # Error 429 (Quota Exceeded) ကို မြန်မာလို ရှင်းပြမယ်
        if "429" in str(e):
            return "⚠️ ခဏလေး စောင့်ပေးပါ... Google AI က တစ်မိနစ်ကို မေးခွန်းကန့်သတ်ချက် ပြည့်သွားလို့ပါ။ (၁) မိနစ်လောက် နားပြီးမှ ပြန်မေးပေးပါခင်ဗျာ။"
        return f"Error: {e}"

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

# Global Variable
current_image = None 
context_prompt = ""

# 1. Input Form Section
with st.expander("📝 အချက်အလက်နှင့် ဓာတ်ပုံ ဖြည့်ရန် (နှိပ်ပါ)", expanded=True):
    # Responsive Column Layout
    col1, col2 = st.columns([1, 1])
    
    uploaded_file = st.file_uploader("📸 ဓာတ်ပုံ (Camera/Gallery):", type=["jpg", "png", "jpeg"], key="main_uploader")
    if uploaded_file:
        current_image = Image.open(uploaded_file)
        st.image(current_image, caption="တင်ထားသောပုံ", width=200)

    if app_mode == "🏡 အိမ်ခြံသီးနှံ (Garden)":
        with col1:
            plant_name = st.text_input("အပင်အမည် (ဥပမာ- ရုံးပတီ):")
        with col2:
            tank_size = st.number_input("ရေကန် (ဂါလံ):", value=50)
        field_desc = st.text_input("စိုက်ခင်း အနေအထား (နေရောင်/မြေ):")
        
        if plant_name:
            context_prompt = f"အပင်: {plant_name}. ရေကန်: {tank_size} ဂါလံ. မြေ: {field_desc}. (စိုက်ပျိုးနည်းနှင့် မြေသြဇာ အကြံပေးပါ)"

    elif app_mode == "🌾 စပါးစိုက်ခင်း (Paddy)":
        days = st.slider("စပါးသက်တမ်း (ရက်):", 1, 120, 30)
        acres = st.number_input("စိုက်ဧက:", value=5)
        status = st.text_input("လက်ရှိ အပင်အခြေအနေ:")
        context_prompt = f"စပါးသက်တမ်း: {days} ရက်. စိုက်ဧက: {acres} ဧက. အခြေအနေ: {status}. (လိုအပ်သော ရေ၊ မြေသြဇာနှင့် ဆေး အကြံပေးပါ)"

    elif app_mode == "🍂 ရောဂါစစ်ဆေး (Doctor)":
        st.info("အပင်ရောဂါ ပုံကို အပေါ်က Upload ခလုတ်မှာ တင်ပေးပါ။")
        context_prompt = "ဒီပုံထဲက အပင်ရောဂါကို စစ်ဆေးပြီး ကုသနည်း ပြောပြပါ။ (Burmese Language)"

# 2. Voice Input
st.write("🎙️ **အသံဖြင့် မေးရန်:**")
# Mobile Responsive Voice UI: Column မခွဲဘဲ တန်းစီလိုက်တယ်
audio_blob = mic_recorder(start_prompt="🔴 နှိပ်၍ ပြောပါ (Start)", stop_prompt="⬛ ရပ်မည် (Stop)", key='recorder')

voice_text = ""
if audio_blob:
    with st.spinner("အသံဖတ်နေသည်..."):
        voice_text = transcribe_audio(audio_blob['bytes'])

# 3. Chat Interface
chat_container = st.container()
with chat_container:
    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if "audio_path" in msg and msg["audio_path"]:
                st.audio(msg["audio_path"], format="audio/mp3")

# 4. Handle Chat Inputs
user_query = None

if voice_text:
    user_query = voice_text

if prompt := st.chat_input("ဆက်လက် မေးမြန်းလိုသည်များ ရေးပါ..."):
    user_query = prompt

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
        if current_image and chat_upload:
            st.image(current_image, width=200)

    with st.chat_message("assistant"):
        with st.spinner("AIပညာရှင် စဉ်းစားနေပါသည်..."):
            full_prompt = f"{final_prompt} (Please answer in Burmese language.)"
            
            # Safety Check
            if 'current_image' not in locals():
                current_image = None
                
            response_text = get_ai_response(full_prompt, current_image)
            st.write(response_text)
            
            # Audio
            audio_file = None
            if enable_voice and "Error" not in response_text:
                audio_file = text_to_speech(response_text)
                if audio_file:
                    st.audio(audio_file, format="audio/mp3")

            st.session_state.history.append({
                "role": "assistant", 
                "content": response_text,
                "audio_path": audio_file
            })
