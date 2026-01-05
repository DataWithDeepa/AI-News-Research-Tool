import streamlit as st
from datetime import datetime
import os
from dotenv import load_dotenv
import pdfplumber
import docx
import io
import numpy as np
from PIL import Image
import easyocr

from news_client import fetch_news, fetch_ticker_headlines, fetch_world_news
from summarizer_chain import summarize_news
from config import translations

load_dotenv()

st.set_page_config(page_title="AI News & Research Tool", page_icon="📰🤖", layout="wide")

# Red + Grayish Black Theme + Perfect Login Visibility
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700;900&family=Roboto:wght@700&display=swap');
    
    .big-title {
        font-family: 'Poppins', sans-serif;
        font-size: 4.2rem !important;
        font-weight: 900;
        text-align: center;
        color: #FFFFFF;
        margin: 10px 0 20px 0;
        text-shadow: 0 0 15px #DC2626;
    }
    .summary-box {
        background: #2D2D2D !important;
        color: #FFFFFF !important;
        font-size: 1.5rem !important;
        font-weight: 800 !important;
        font-family: 'Roboto', sans-serif;
        padding: 35px;
        border-radius: 20px;
        border: 6px solid #DC2626;
        box-shadow: 0 15px 40px rgba(220,38,38,0.4);
        margin: 30px 0;
        line-height: 1.9;
    }
    .ticker {
        background: #DC2626;
        color: white;
        padding: 20px;
        font-size: 1.4rem;
        font-weight: bold;
        white-space: nowrap;
        overflow: hidden;
        border-radius: 15px;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 10px 25px rgba(220,38,38,0.5);
    }
    .ticker span {
        display: inline-block;
        padding-left: 100%;
        animation: scroll 70s linear infinite;
    }
    @keyframes scroll {
        0% { transform: translateX(0); }
        100% { transform: translateX(-100%); }
    }
    .top-right {
        position: fixed;
        top: 15px;
        right: 15px;
        background: rgba(220,38,38,0.9);
        color: white;
        padding: 18px 28px;
        border-radius: 15px;
        z-index: 999;
        text-align: center;
        font-size: 1.4rem;
        font-weight: bold;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
    }
    .stApp {
        background: linear-gradient(rgba(30,30,30,0.6), rgba(45,45,45,0.65)),
                    url('https://images.stockcake.com/public/c/3/8/c38a77ef-0aed-43a7-b746-62fbcbc75bbf_large/robot-analyzing-data-stockcake.jpg');
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }
    /* Sidebar Medium Gray + White Text */
    .css-1d391kg {
        background-color: #363636 !important;
    }
    .css-1v3fvcr, .css-1cpxl0t, .css-10trblm, .css-1offfwp p, .css-1offfwp div {
        color: #FFFFFF !important;
        font-weight: bold !important;
    }
    .stTextArea > div > div > textarea {
        background: #2A2A2A !important;
        color: white !important;
        font-size: 1.3rem !important;
        border: 4px solid #DC2626;
        border-radius: 15px;
    }
    .stFileUploader > div > div {
        background: #2A2A2A;
        border: 4px dashed #EF4444;
        border-radius: 15px;
        color: white;
    }
    .stButton > button {
        background: linear-gradient(45deg, #DC2626, #B91C1C);
        color: white;
        font-weight: bold;
        font-size: 1.5rem;
        border-radius: 20px;
        height: 4em;
        border: none;
        box-shadow: 0 10px 30px rgba(220,38,38,0.5);
    }
    .sidebar-date {
        background: #991B1B;
        color: white;
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 20px;
    }
    /* FIX: Login screen inputs - white text + better placeholder visibility */
    .stTextInput > div > div > input {
        color: white !important;
        background-color: #2A2A2A !important;
        -webkit-text-fill-color: white !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: rgba(255,255,255,0.7) !important;
    }
    .stSelectbox > div > div {
        color: white !important;
        background-color: #2A2A2A !important;
    }
    .stSelectbox > div > div > div {
        color: white !important;
    }
    /* Related Articles text white */
    .stExpander > div > div > div {
        color: white !important;
    }
    .stExpander summary {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# बाकी कोड बिल्कुल वैसा ही है – कोई बदलाव नहीं
@st.cache_resource
def get_ocr_reader(lang):
    lang_map = {"en": ['en'], "hi": ['hi','en'], "mr": ['mr','en']}
    return easyocr.Reader(lang_map.get(lang, ['en']), gpu=False)

def extract_text_from_image(file_bytes, lang="en"):
    reader = get_ocr_reader(lang)
    img_np = np.array(Image.open(io.BytesIO(file_bytes)))
    results = reader.readtext(img_np, detail=0, paragraph=True)
    return "\n\n".join(results) if results else "No text detected"

def read_uploaded_files(uploaded_files, lang):
    all_text = []
    for file in uploaded_files:
        bytes_data = file.read()
        name = file.name.lower()
        if name.endswith(".pdf"):
            text = "\n\n".join([page.extract_text() or "" for page in pdfplumber.open(io.BytesIO(bytes_data)).pages][:15])
        elif name.endswith(".docx"):
            text = "\n".join([p.text for p in docx.Document(io.BytesIO(bytes_data)).paragraphs if p.text.strip()][:200])
        elif name.endswith((".png",".jpg",".jpeg")):
            text = extract_text_from_image(bytes_data, lang)[:6000]
        else:
            text = bytes_data.decode("utf-8", errors="ignore")[:12000]
        if text.strip():
            all_text.append(f"--- From {file.name} ---\n{text[:10000]}")
    return "\n\n".join(all_text)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.language = "en"
    st.session_state.search_history = []
    st.session_state.chat_history = []
    st.session_state.news_page = 0

if not st.session_state.authenticated:
    st.markdown("<div class='big-title'>📰 AI News & Research Tool</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:#DC2626; font-weight:bold;'>Namaste! Welcome</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        login_id = st.text_input("Login ID", placeholder="Enter your ID")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        lang_choice = st.selectbox("Language / भाषा", ["English", "Hindi", "Marathi"])
        lang_map = {"English": "en", "Hindi": "hi", "Marathi": "mr"}
        if st.button("Login Now", type="primary"):
            if login_id and password:
                st.session_state.authenticated = True
                st.session_state.language = lang_map[lang_choice]
                st.rerun()
            else:
                st.error("Please enter both Login ID and Password")

else:
    lang = st.session_state.language
    t = translations.get(lang, translations["en"])

    ticker_text = fetch_ticker_headlines()
    st.markdown(f"""
    <div class="ticker">
        <span>🔴 LIVE NEWS: {ticker_text}</span>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f"<div class='sidebar-date'>📅 {datetime.now().strftime('%B %d, %Y')}</div>", unsafe_allow_html=True)
        
        st.markdown("### 📜 Search History")
        for item in reversed(st.session_state.search_history[-10:]):
            st.write(f"• {item or 'File Analysis'}")

        st.markdown("### 💾 Save & Export")
        if st.session_state.chat_history:
            latest = st.session_state.chat_history[-1]
            st.download_button("📥 Download Summary", latest["summary"], "summary.txt")
            st.download_button("📰 Download Raw News", latest["raw_news"], "raw_news.txt")

        st.markdown("### 🌍 Recent World News")
        world_news = fetch_world_news(20)
        page = st.session_state.news_page
        start = page * 4
        end = start + 4
        current = world_news[start:end]

        for a in current:
            st.markdown(f"**[{a['title']}]({a['url']})**")
            st.caption(f"{a['source']} • {a['published_at']}")

        col_p, col_n = st.columns(2)
        if col_p.button("← Previous") and page > 0:
            st.session_state.news_page -= 1
            st.rerun()
        if col_n.button("Next →") and end < len(world_news):
            st.session_state.news_page += 1
            st.rerun()

    st.markdown(f"<div class='big-title'>{t.get('title', 'AI News & Research Tool')}</div>", unsafe_allow_html=True)

    col_query, col_file = st.columns([2,1])
    with col_query:
        user_query = st.text_area("🔍 Search Query or Theme", height=140, placeholder="e.g., RBI monetary policy...")
    with col_file:
        uploaded_files = st.file_uploader("📎 Attach Files (PDF/DOCX/Image)", type=["pdf","docx","png","jpg","jpeg"], accept_multiple_files=True)

    col_btn1, col_btn2 = st.columns([1,1])
    with col_btn1:
        run = st.button("Generate Summary & Research", type="primary", use_container_width=True)
    with col_btn2:
        if "summary" in st.session_state:
            st.download_button("📄 Export Summary", st.session_state.summary, "summary.md")
            st.download_button("📰 Export Raw News", st.session_state.raw_news, "raw_news.txt")

    if run:
        if not user_query and not uploaded_files:
            st.warning("Please enter a query or upload files.")
        else:
            with st.spinner("Generating instant research..."):
                query = user_query or "latest news"
                news = fetch_news(query, lang)[:5]
                articles_text = "\n\n".join([f"{a['title']}\n{a['description'] or ''}" for a in news]) if news else ""

                extra_context = read_uploaded_files(uploaded_files, lang) if uploaded_files else ""

                summary = summarize_news(user_query or "Summarize uploaded files with latest news", articles_text, extra_context, lang)

                st.session_state.summary = summary
                st.session_state.raw_news = articles_text
                st.session_state.search_history.append(user_query or "File Analysis")
                st.session_state.chat_history.append({"summary": summary, "raw_news": articles_text})

                st.markdown("### 📊 AI Research Summary")
                st.markdown(f"<div class='summary-box'>{summary}</div>", unsafe_allow_html=True)

                st.markdown("<h3 style='color:white;'>📰 Related Latest Articles</h3>", unsafe_allow_html=True)
                if news:
                    for a in news:
                        with st.expander(f"**{a['title']}** • {a['source']}"):
                            st.markdown(f"<span style='color:white;'>{a['description'] or ''}</span>", unsafe_allow_html=True)
                            st.markdown(f"[🔗 Read Full Article]({a['url']})")
                else:
                    st.info("No matching news found.")