import os
import time
from pathlib import Path

from dotenv import dotenv_values
from mtranslate import translate
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Load environment variables from .env file.
env_vars = dotenv_values(".env")
INPUT_LANGUAGE = str(env_vars.get("InputLanguage", "en")).strip() or "en"

# Ensure expected directories exist.
DATA_DIR = Path("Data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
FRONTEND_FILES = Path("frontend") / "files"
FRONTEND_FILES.mkdir(parents=True, exist_ok=True)

VOICE_HTML_PATH = DATA_DIR / "Voice.html"
STATUS_FILE_PATH = FRONTEND_FILES / "Status.data"

HTML_CODE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function getSpeechRecognition() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                alert('SpeechRecognition is not supported by this browser. Use Chrome or Edge.');
                return null;
            }
            return new SpeechRecognition();
        }

        function startRecognition() {
            recognition = getSpeechRecognition();
            if (!recognition) {
                return;
            }

            recognition.lang = '%LANG%';
            recognition.continuous = true;
            recognition.interimResults = false;

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent = transcript;
            };

            recognition.onerror = function(event) {
                console.error('Speech recognition error:', event.error);
            };

            recognition.onend = function() {
                if (recognition) {
                    recognition.start();
                }
            };

            recognition.start();
        }

        function stopRecognition() {
            if (recognition) {
                recognition.stop();
            }
            output.innerHTML = "";
        }
    </script>
</body>
</html>'''.replace('%LANG%', INPUT_LANGUAGE)

VOICE_HTML_PATH.write_text(HTML_CODE, encoding="utf-8")


def _create_driver():
    chrome_options = Options()
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    )
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("--allow-file-access-from-files")
    chrome_options.add_argument("--enable-experimental-web-platform-features")
    chrome_options.add_experimental_option(
        "prefs",
        {
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_setting_values.geolocation": 1,
            "profile.default_content_setting_values.notifications": 1,
        },
    )
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def SetAssistantStatus(Status: str):
    STATUS_FILE_PATH.write_text(str(Status), encoding="utf-8")


def UniversalTranslator(Text: str) -> str:
    return translate(Text, 'en', INPUT_LANGUAGE)


def QueryModifier(Query: str) -> str:
    new_query = str(Query).strip().lower()
    if not new_query:
        return ""

    question_words = [
        "what",
        "when",
        "where",
        "who",
        "why",
        "how",
        "which",
        "whom",
        "whose",
        "can you",
        "could you",
        "would you",
        "what's",
        "who's",
        "when's",
        "where's",
        "why's",
    ]

    last_char = new_query[-1]
    if any(word + " " in new_query for word in question_words) or new_query.startswith(tuple(question_words)):
        if last_char not in ["?", ".", "!"]:
            new_query += "?"
        elif last_char != "?":
            new_query = new_query[:-1] + "?"
    else:
        if last_char not in ["?", ".", "!"]:
            new_query += "."

    return new_query.capitalize()


def SpeechRecognition() -> str:
    driver = _create_driver()
    try:
        driver.get(f"file:///{VOICE_HTML_PATH.absolute()}")
        driver.find_element(By.ID, "start").click()

        while True:
            try:
                text = driver.find_element(By.ID, "output").text.strip()
                if text:
                    driver.find_element(By.ID, "end").click()
                    if "en" in INPUT_LANGUAGE.lower():
                        return QueryModifier(text)
                    SetAssistantStatus("Translating...")
                    translated = UniversalTranslator(text)
                    return QueryModifier(translated)
            except Exception:
                pass
            time.sleep(0.5)
    finally:
        driver.quit()


if __name__ == "__main__":
    while True:
        text = SpeechRecognition()
        print(text)
