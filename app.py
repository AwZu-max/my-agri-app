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

# --- Configuration ---
# ⚠️ ⚠️ ⚠️ ဤနေရာတွင် သင်၏ API Key အမှန်ကို မဖြစ်မနေ ထည့်ပါ ⚠️ ⚠️ ⚠️
GOOGLE_API_KEY = "AIzaSyAZPKm775hHrXDatQmrLwESFVx1Xb5kiWg"

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"API Key Error: {e}")
    st.stop()

# --- Page Setup ---
st.set_page_config(page_title="Smart Agri Pro Voice", page_icon="🌾", layout="wide")

st.markdown("""
    <h1 style='text-align: center; color: #2E8B57; font-size: 2.5em; font-weight: bold;'>
        🌾 Smart Agri - စွယ်စုံသုံး စိုက်ပျိုးရေးလက်ထောက်
    </h1>
""", unsafe_allow_html=True)

# --- Session State Management ---
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
        print(f"Audio Error: {e}")
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
        return f"စနစ်ချို့ယွင်းချက် ရှိနေပါသည်: {e}"

# --- Sidebar ---
with st.sidebar:
    st.header("ဆက်တင်များ")
    app_mode = st.radio("လုပ်ဆောင်ချက် ရွေးချယ်ပါ:",
        ["🏡 အိမ်ခြံသီးနှံ (Garden)", "🌾 စပါးစိုက်ခင်း (Paddy)", "🍂 ရောဂါစစ်ဆေး (Doctor)"])
    
    st.divider()
    if st.button("🔄 နောက်တစ်မျိုး ပြောင်းမေးမည် (Clear)"):
        st.session_state.history = []
        st.rerun()
    
    enable_voice = st.checkbox("အသံဖြင့် ပြန်ဖတ်ပြပါ", value=True)

# --- Main Logic ---

# ⚠️ 1. Variable Initialization (Error မတက်အောင် ကြိုတင် ကြေညာခြင်း)
user_image = None       # Default အနေနဲ့ None ပေးထားမယ်
context_prompt = ""

# 2. User Input Section
with st.expander("📝 အချက်အလက် ဖြည့်သွင်းရန် (နှိပ်ပါ)", expanded=True):
    col_input1, col_input2 = st.columns([2, 1])

    if app_mode == "🏡 အိမ်ခြံသီးနှံ (Garden)":
        with col_input1:
            plant_name = st.text_input("အပင်အမည် (ဥပမာ- ရုံးပတီ):")
            field_desc = st.text_input("စိုက်ခင်း အနေအထား:")
        with col_input2:
            tank_size = st.number_input("ရေကန် (ဂါလံ):", value=50)
        if plant_name:
            context_prompt = f"အပင်: {plant_name}. ရေကန်: {tank_size} ဂါလံ. မြေအနေအထား: {field_desc}. (မြေသြဇာစပ်နည်းနှင့် ပြုစုနည်း တွက်ပေးပါ)"

    elif app_mode == "🌾 စပါးစိုက်ခင်း (Paddy)":
        with col_input1:
            days = st.slider("စပါးသက်တမ်း (ရက်):", 1, 120, 30)
            status = st.text_input("အပင် အခြေအနေ:")
        with col_input2:
            acres = st.number_input("စိုက်ဧက:", value=5)
        context_prompt = f"စပါးသက်တမ်း: {days} ရက်. စိုက်ဧက: {acres} ဧက. အခြေအနေ: {status}. (လိုအပ်သော ရေ၊ မြေသြဇာနှင့် ဆေး အကြံပေးပါ)"

    elif app_mode == "🍂 ရောဂါစစ်ဆေး (Doctor)":
        uploaded_file = st.file_uploader("ရောဂါဖြစ်နေသော ပုံတင်ပါ:", type=["jpg", "png", "jpeg"])
        if uploaded_file:
            user_image = Image.open(uploaded_file) # ဓာတ်ပုံတင်မှ user_image က ပုံဖြစ်သွားမယ်
            st.image(user_image, caption="တင်ထားသောပုံ", width=200)
            context_prompt = "ဒီပုံထဲက အပင်ရောဂါကို စစ်ဆေးပြီး ကုသနည်း ပြောပြပါ။"

# 3. Voice & Chat Section
col_voice, col_display = st.columns([1, 4])
with col_voice:
    st.write("🎙️ **အသံဖြင့် မေးရန်:**")
    audio_blob = mic_recorder(start_prompt="🔴 Start", stop_prompt="⬛ Stop", key='recorder')

voice_text = ""
if audio_blob:
    with st.spinner("အသံဖတ်နေသည်..."):
        voice_text = transcribe_audio(audio_blob['bytes'])

chat_container = st.container()
with chat_container:
    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if "audio_path" in msg and msg["audio_path"]:
                st.audio(msg["audio_path"], format="audio/mp3")

# 4. Processing Query
user_query = None
if voice_text:
    user_query = voice_text
if prompt := st.chat_input("သိလိုသည်များကို ဆက်လက်မေးမြန်းပါ..."):
    user_query = prompt

if user_query:
    final_prompt = user_query
    
    # ပထမဆုံးအကြိမ်ဆိုရင် Context ပါ ထည့်ပေါင်းမယ်
    if len(st.session_state.history) == 0 and context_prompt:
        final_prompt = f"{context_prompt} \n\n အသုံးပြုသူမေးခွန်း: {user_query}"

    st.session_state.history.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.write(user_query)

    with st.chat_message("assistant"):
        with st.spinner("AIပညာရှင် စဉ်းစားနေပါသည်..."):
            full_prompt = f"{final_prompt} (Please answer in Burmese...)"
            
            # ⚠️ SAFETY CHECK (အရေးကြီးဆုံး အဆင့်)
            # user_image မရှိသေးရင် None ဟု အတင်းသတ်မှတ်မည်
            if 'user_image' not in locals():
                user_image = None
            
            response_text = get_ai_response(full_prompt, user_image)
            st.write(response_text)
            
            audio_file = None
            if enable_voice:
                audio_file = text_to_speech(response_text)
                if audio_file:
                    st.audio(audio_file, format="audio/mp3")

            st.session_state.history.append({
                "role": "assistant", 
                "content": response_text,
                "audio_path": audio_file
            })
