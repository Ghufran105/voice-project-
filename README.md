# 🎙️ Voice Code Generator

Speak in **Urdu** or **English** and get working **Python** or **C++** code.
Built with Streamlit, the free Google Web Speech API for voice, and Claude for code generation.

## Features
- 🎙️ Record your voice in the browser (Urdu or English, Roman Urdu also works when typed)
- ✏️ Edit the transcript before generating, because speech recognition is never perfect
- 💻 Generates Python 3 or C++17 code with explanations in English or Urdu
- ✅ Automatic **syntax check** (Python `ast`, C++ `g++ -fsyntax-only`). The code is **never executed**
- 🔁 Follow-up requests: say "make it faster" or "ab isay C++ mein likho" and Claude uses the earlier code
- ⬇️ Download the result as a `.py` or `.cpp` file
- 🔑 Use the server's API key or paste your own in the sidebar

## How it works
```
Voice → Google Speech-to-Text → editable text → Claude → code
                                                          ↓
                                           syntax check → display + download
```

## Project structure
```
app.py                          Streamlit user interface
helpers.py                      Speech, Claude, and syntax-check logic
tests/                          26 automated tests (Claude and speech are mocked)
requirements.txt                Python packages
packages.txt                    System packages for Streamlit Cloud (g++ for C++ checking)
.streamlit/secrets.toml.example Template for your API key
```

## Run locally
1. Install Python 3.12 and get an API key from https://console.anthropic.com
2. In a terminal inside the project folder:
```bash
python -m venv venv
venv\Scripts\activate            # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
```
3. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and put your real key inside.
4. Start the app:
```bash
streamlit run app.py
```
5. Run the tests (optional): `pip install pytest` then `python -m pytest tests`

For the C++ syntax check on your own computer, install g++ (MinGW on Windows, `build-essential` on Linux, Xcode tools on Mac). Without it, the app simply skips that check.

## Deploy on Streamlit Community Cloud
1. Push this project to a public GitHub repository.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **Create app**, choose your repo, branch `main`, main file `app.py`.
4. Open **Advanced settings**: choose **Python 3.12** and paste your secret:
```toml
ANTHROPIC_API_KEY = "sk-ant-your-real-key"
```
5. Click **Deploy**. The first build takes a few minutes.

## Settings (optional secrets)
| Name | Default | Meaning |
|---|---|---|
| `ANTHROPIC_API_KEY` | none | Server API key |
| `CLAUDE_MODEL` | `claude-sonnet-5-5` | Model name |
| `MAX_REQUESTS_PER_SESSION` | `25` | Limit when the server key is used |

## Security notes
- **Never commit your API key.** `.gitignore` already blocks `secrets.toml`.
- If your deployed app uses *your* key, anyone with the link spends *your* credit. Set a monthly spend limit in the Anthropic Console, or leave the key out of secrets so visitors paste their own.
- Generated code is shown, never run. Always review it before using it.

## Known limitations
- The free Google speech endpoint is unofficial: it can be rate-limited and it sends your audio to Google. Fine for a demo; use a proper speech service for production.
- Urdu speech mixed with English technical words ("array", "pointer") can be misheard. Use the edit box.
- AI-generated code can be wrong even if the syntax check passes.
- Only Urdu and English input, and Python and C++ output, for now.

## Ideas to extend
- Add your own command parser so common requests work without an AI call
- Add Pashto input and more output languages
- Replace Google speech with Whisper
- Run generated code safely in a sandbox and show the output
