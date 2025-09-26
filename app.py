import streamlit as st
from chatbot_gemini import BookStoreChatbotGemini
import subprocess
import os

# Chạy init_db.py để tạo database
if not os.path.exists("bookstore.db"):
    subprocess.run(["python", "init_db.py"])

st.title("📚 Chatbot Nhà Sách (Gemini Version)")
st.caption("Chatbot có thể giúp bạn tìm sách và đặt hàng")

# Lấy API key
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("Lỗi secrets.toml. Thêm GOOGLE_API_KEY.")
    st.stop()

# Khởi tạo chatbot
if "chatbot" not in st.session_state:
    st.session_state.chatbot = BookStoreChatbotGemini(api_key=api_key)

# Khởi tạo history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "parts": ["Xin chào! Tôi có thể giúp gì cho bạn?"]}]

# Hiển thị messages
for message in st.session_state.messages:
    role = "user" if message["role"] == "user" else "assistant"
    with st.chat_message(role):
        st.markdown("".join(message["parts"]))

# Input user
if prompt := st.chat_input("Bạn cần tìm sách gì hoặc muốn đặt hàng?"):
    st.session_state.messages.append({"role": "user", "parts": [prompt]})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Bot đang suy nghĩ..."):
            response_text = st.session_state.chatbot.get_response(st.session_state.messages)
            st.markdown(response_text)
    
    st.session_state.messages.append({"role": "model", "parts": [response_text]})