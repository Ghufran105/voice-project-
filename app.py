"""Voice Code Generator: speak in Urdu or English, get Python or C++ code."""
import hashlib
import os

import streamlit as st

import helpers as h

st.set_page_config(page_title="Voice Code Generator", page_icon="🎙️", layout="wide")

# Let Urdu text show right-to-left inside text boxes
st.markdown(
    "<style>textarea{unicode-bidi:plaintext;font-size:1.05rem;}</style>",
    unsafe_allow_html=True,
)


def get_secret(name: str, default: str = "") -> str:
    """Read from Streamlit secrets, then environment variables."""
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass  # no secrets file (normal on a local machine)
    return os.environ.get(name, default)


# ------------------------------------------------------------ session state
st.session_state.setdefault("history", [])
st.session_state.setdefault("request_text", "")
st.session_state.setdefault("last_audio_hash", None)
st.session_state.setdefault("stt_error", "")
st.session_state.setdefault("generation_count", 0)

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    speech_label = st.selectbox("I will speak in", list(h.SPEECH_LANGUAGES))
    target = st.radio("Generate code in", list(h.CODE_LANGUAGES), horizontal=True)
    explain_label = st.selectbox("Explain the code in", ["English", "Urdu (اردو)"])
    model = st.text_input("Claude model", value=get_secret("CLAUDE_MODEL", h.DEFAULT_MODEL))

    st.divider()
    user_key = st.text_input(
        "Your Anthropic API key (optional)",
        type="password",
        help="If you paste your own key it is used instead of the server key. It is never stored.",
    )
    if st.button("🗑️ Clear history", use_container_width=True):
        st.session_state.history = []
        st.session_state.request_text = ""
        st.rerun()

server_key = get_secret("ANTHROPIC_API_KEY")
api_key = user_key.strip() or server_key
using_server_key = bool(server_key) and not user_key.strip()
max_requests = int(get_secret("MAX_REQUESTS_PER_SESSION", "25") or 25)

# --------------------------------------------------------------------- main
st.title("🎙️ Voice Code Generator")
st.caption("Speak in Urdu or English → get working Python or C++ code. Built with Streamlit + Claude.")

st.subheader("1. Speak")
if hasattr(st, "audio_input"):
    audio = st.audio_input("Press the mic, speak your request, then press stop")
else:  # older Streamlit versions
    audio = st.file_uploader("Upload a WAV recording", type=["wav"])

if audio is not None:
    audio_bytes = audio.getvalue()
    audio_hash = hashlib.md5(audio_bytes).hexdigest()
    if audio_hash != st.session_state.last_audio_hash:  # only transcribe new recordings
        st.session_state.last_audio_hash = audio_hash
        with st.spinner("Listening..."):
            try:
                st.session_state.request_text = h.transcribe_audio(
                    audio_bytes, h.SPEECH_LANGUAGES[speech_label]
                )
                st.session_state.stt_error = ""
            except h.SpeechError as exc:
                st.session_state.stt_error = str(exc)

if st.session_state.stt_error:
    st.warning(st.session_state.stt_error + " You can also type your request below.")

st.subheader("2. Check what I heard (edit if needed)")
st.text_area(
    "Your request",
    key="request_text",
    height=110,
    placeholder="Example: 1 se 10 tak numbers print karne ka loop banao  /  write a function to check prime numbers",
)

st.subheader("3. Generate")
if st.button("✨ Generate code", type="primary"):
    if not api_key:
        st.error("No API key. Paste your Anthropic API key in the sidebar.")
    elif using_server_key and st.session_state.generation_count >= max_requests:
        st.error(f"Session limit of {max_requests} requests reached. Paste your own API key in the sidebar to continue.")
    else:
        with st.spinner("Claude is writing your code..."):
            try:
                result = h.generate_code(
                    request=st.session_state.request_text,
                    target=target,
                    explain_in="Urdu" if explain_label.startswith("Urdu") else "English",
                    api_key=api_key,
                    model=model.strip() or h.DEFAULT_MODEL,
                    history=st.session_state.history,
                )
                ok, message = h.check_syntax(result["code"], target)
                st.session_state.history.append(
                    {
                        "request": st.session_state.request_text.strip(),
                        "target": target,
                        "code": result["code"],
                        "explanation": result["explanation"],
                        "raw": result["raw"],
                        "user_message": result["user_message"],
                        "check_ok": ok,
                        "check_message": message,
                    }
                )
                st.session_state.generation_count += 1
            except h.CodeGenError as exc:
                st.error(str(exc))


def show_result(entry: dict, index: int) -> None:
    st.markdown(f"**Request:** {entry['request']}")
    if entry["code"]:
        st.code(entry["code"], language=h.CODE_LANGUAGES[entry["target"]], line_numbers=True)
        if entry["check_ok"] is True:
            st.success(entry["check_message"])
        elif entry["check_ok"] is False:
            st.error(f"{entry['check_message']}  (Try generating again, or ask Claude to fix it.)")
        else:
            st.info(entry["check_message"])
        st.download_button(
            f"⬇️ Download .{h.FILE_EXTENSIONS[entry['target']]} file",
            data=entry["code"],
            file_name=f"generated_code.{h.FILE_EXTENSIONS[entry['target']]}",
            key=f"download_{index}",
        )
    if entry["explanation"]:
        st.markdown("**Explanation**")
        st.write(entry["explanation"])


history = st.session_state.history
if history:
    st.divider()
    st.subheader("Result")
    show_result(history[-1], len(history) - 1)
    st.caption("Tip: record a follow-up like “make it faster” or “ab isay C++ mein likho” and Claude will use the earlier code.")
    if len(history) > 1:
        with st.expander(f"Earlier results ({len(history) - 1})"):
            for i in range(len(history) - 2, -1, -1):
                show_result(history[i], i)
                st.divider()

st.divider()
st.caption("⚠️ AI-generated code can contain mistakes. The app only checks syntax and never runs the code. Review it before you use it.")
