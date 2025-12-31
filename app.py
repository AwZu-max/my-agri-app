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
# Secrets ထဲက Key စာရင်းကို ယူပါမယ်
# စမ်းသပ်ရန်အတွက် Key တစ်ခုတည်း ရှိရင်လည်း ["KEY"] ပုံစံနဲ့ ထည့်လို့ရပါတယ်
api_keys = []

if "api_keys" in st.secrets:
    api_keys = st.secrets["api_keys"]
elif "GOOGLE_API_KEY" in st.secrets:
    # အကယ်၍ Key အဟောင်းပုံစံပဲ ရှိသေးရင် List အဖြစ် ပြောင်းမယ်
    api_keys = [st.secrets["GOOGLE_API_KEY"]]
else:
    # Secrets မရှိရင် Code ထဲကဟာ ယူမယ် (မလုံခြုံပါ)
    api_keys = ["YOUR_FALLBACK_API_KEY_HERE"]

# --- Page Setup ---
st.set_page_config(page_title="Smart Agri Pro", page_icon="🌾", layout="wide")

# --- CSS for Responsive Design ---
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

# --- ⚠️ The Magic Function (Auto Key Rotator) ---
def get_ai_response_smart_rotate(prompt, image=None):
    """
    Key တစ်ခု Error တက်ရင် နောက်တစ်ခုကို အလိုအလျောက် ပြောင်းသုံးမည့် Function
    """
    # Key တွေကို မွှေလိုက်ပါ (ဒါမှ အမြဲတမ်း ပထမအကောင့်ပဲ ဝန်ပိမနေမှာပါ)
    shuffled_keys = api_keys.copy()
    random.shuffle(shuffled_keys)
    
    last_error = None
    
    # Key တစ်ခုချင်းစီကို လိုက်စမ်းပါမယ်
    for key in shuffled_keys:
        try:
            # 1. Key အသစ်နဲ့ ချိတ်မယ်
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.0-flash') # 2.0 ကိုပဲ ဦးစားပေးသုံးမယ်
            
            # 2. မေးခွန်းထုတ်မယ်
            chat = model.start_chat(history=[])
            if image:
                response = chat.send_message([prompt, image])
            else:
                response = chat.send_message(prompt)
            
            # 3. အောင်မြင်ရင် ချက်ချင်း အဖြေပြန်ပို့မယ် (Loop ရပ်မယ်)
            return response.text
            
        except Exception as e:
            error_msg = str(e)
            last_error = error_msg
            # Error 429 (Quota) သို့မဟုတ် 403 (Permission) ဖြစ်ရင် နောက် Key ကို ကူးမယ်
            if "429" in error_msg or "Quota" in error_msg or "403" in error_msg:
                print(f"Key Failed ({key[:5]}...), Switching to next key...")
                continue # Loop ကို ဆက်ပတ်မယ် (နောက် Key တပ်မယ်)
            else:
                # Quota ပြဿနာ မဟုတ်ဘဲ တခြား Error (ဥပမာ အင်တာနက်ပြတ်တာ) ဆိုရင်တော့ ရပ်လိုက်မယ်
                return f"စနစ်ချို့ယွင်းချက် ရှိနေပါသည်: {e}"
    
    # Key အားလုံး စမ်းပြီးလို့မှ မရရင်တော့ တကယ် ကုန်သွားပါပြီ
    return "⚠️ ခဏလေး စောင့်ပေးပါ... စနစ်အလုပ်များနေပါသည်။ (၁) မိနစ်ခန့် နားပြီးမှ ပြန်မေးပေးပါခင်ဗျာ။"

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
        field_desc = st.text_input("စိုက်ခင်း အနေအထား (နေရောင်/မြေ):")
        if plant_name: context_prompt = f"အပင်: {plant_name}. ရေကန်: {tank_size} ဂါလံ. မြေ: {field_desc}. (စိုက်ပျိုးနည်းနှင့် မြေသြဇာ အကြံပေးပါ)"

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

# 4. Handle Inputs
user_query = None
if voice_text: user_query = voice_text
if prompt := st.chat_input("ဆက်လက် မေးမြန်းလိုသည်များ ရေးပါ..."): user_query = prompt

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
        with st.spinner("AI စဉ်းစားနေပါသည် (Smart Loading)..."):
            full_prompt = f"{final_prompt} (Please answer in Burmese language.)"
            if 'current_image' not in locals(): current_image = None
            
            # 🔥 ဒီနေရာမှာ Function အသစ်ကို ခေါ်သုံးထားပါတယ်
            response_text = get_ai_response_smart_rotate(full_prompt, current_image)
            st.write(response_text)
            
            audio_file = None
            if enable_voice and "Error" not in response_text and "စောင့်ပေးပါ" not in response_text:
                audio_file = text_to_speech(response_text)
                if audio_file: st.audio(audio_file, format="audio/mp3")

            st.session_state.history.append({
                "role": "assistant", 
                "content": response_text,
                "audio_path": audio_file
            })
