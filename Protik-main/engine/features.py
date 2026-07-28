import json
import os
from pipes import quote
import re
import sqlite3
import struct
import subprocess
import threading
import time
import webbrowser
import wikipedia
from datetime import datetime, timedelta
from playsound import playsound
import eel
import pyaudio
import pyautogui
from engine.command import speak
from engine.config import ASSISTANT_NAME, LLM_KEY, SYSTEM_PROMPT
# Playing assistant sound function
import pywhatkit as kit
import pvporcupine

from engine.helper import extract_yt_term, markdown_to_text, remove_words
from hugchat import hugchat

con = sqlite3.connect("jarvis.db")
cursor = con.cursor()

@eel.expose
def playAssistantSound():
    music_dir = "www\\assets\\audio\\start_sound.mp3"
    playsound(music_dir)

    
def openCommand(query):
    query = query.replace(ASSISTANT_NAME, "")
    query = query.replace("open", "")
    query = query.strip().lower()
    query = re.sub(r'\b(in this project|on my device|on device|please|app|website|browser|folder|file|open the|open a|open an)\b', '', query)
    app_name = re.sub(r'\s+', ' ', query).strip()

    if app_name == "":
        speak("Please tell me what to open")
        return

    # Special handling for YouTube play commands
    if "youtube" in app_name and "play" in app_name:
        from engine.features import PlayYoutube
        PlayYoutube(query)
        return

    known_websites = {
        'youtube': 'https://www.youtube.com',
        'facebook': 'https://www.facebook.com',
        'google': 'https://www.google.com',
        'gmail': 'https://mail.google.com',
        'twitter': 'https://twitter.com',
        'instagram': 'https://www.instagram.com',
        'amazon': 'https://www.amazon.com',
        'linkedin': 'https://www.linkedin.com',
        'github': 'https://github.com',
        'stackoverflow': 'https://stackoverflow.com',
        'reddit': 'https://www.reddit.com',
        'netflix': 'https://www.netflix.com',
        'chatgpt': 'https://chat.openai.com'
    }

    known_apps = {
        'notepad': 'notepad.exe',
        'calculator': 'calc.exe',
        'paint': 'mspaint.exe',
        'cmd': 'cmd.exe',
        'command prompt': 'cmd.exe',
        'google chrome': 'chrome.exe',
        'chrome': 'chrome.exe',
        'edge': 'msedge.exe',
        'microsoft edge': 'msedge.exe',
        'vlc': 'vlc.exe',
        'visual studio code': 'code',
        'code': 'code',
        'word': 'winword.exe',
        'excel': 'excel.exe',
        'powerpoint': 'powerpnt.exe',
        'spotify': 'spotify.exe',
        'task manager': 'taskmgr.exe',
        'taskbar': 'ms-settings:taskbar',
        'settings': 'ms-settings:',
        'control panel': 'control.exe',
        'device manager': 'devmgmt.msc',
        'microsoft store': 'shell:AppsFolder\\Microsoft.WindowsStore_8wekyb3d8bbwe!App',
        'store': 'shell:AppsFolder\\Microsoft.WindowsStore_8wekyb3d8bbwe!App',
        'clock': 'shell:AppsFolder\\Microsoft.WindowsAlarms_8wekyb3d8bbwe!App',
        'alarms': 'shell:AppsFolder\\Microsoft.WindowsAlarms_8wekyb3d8bbwe!App',
        'alarm': 'shell:AppsFolder\\Microsoft.WindowsAlarms_8wekyb3d8bbwe!App',
        'file explorer': 'explorer.exe',
        'explorer': 'explorer.exe',
        'this pc': 'explorer.exe shell:::{20D04FE0-3AEA-1069-A2D8-08002B30309D}',
        'my computer': 'explorer.exe shell:::{20D04FE0-3AEA-1069-A2D8-08002B30309D}',
        'camera': 'shell:AppsFolder\Microsoft.WindowsCamera_8wekyb3d8bbwe!App',
        'webcam': 'shell:AppsFolder\Microsoft.WindowsCamera_8wekyb3d8bbwe!App'
    }

    try:
        website_key = next((name for name in known_websites if name in app_name), None)
        app_key = next((name for name in known_apps if name in app_name), None)

        if website_key:
            speak("Opening " + website_key)
            webbrowser.open(known_websites[website_key])
            return

        if app_key:
            target = known_apps[app_key]
            speak("Opening " + app_key)
            if target.startswith('shell:') or target.startswith('ms-settings:'):
                os.system('start "" "' + target + '"')
            elif target.startswith('explorer.exe shell:'):
                os.system('start "" "' + target + '"')
            else:
                os.startfile(target)
            return

        # Try to open as an exe file if it contains .exe or is a common executable name
        if '.exe' in app_name or '.msc' in app_name:
            try:
                speak("Opening " + app_name)
                os.system('start "" "' + app_name + '"')
                return
            except Exception:
                pass
        
        # Try opening as program from PATH
        exe_name = app_name if app_name.endswith('.exe') else app_name.replace(' ', '') + '.exe'
        try:
            speak("Opening " + app_name)
            os.startfile(exe_name)
            return
        except Exception:
            pass

        # Try to open as a general website if not recognized
        if '.' in app_name or len(app_name.split()) == 1:
            url = 'https://www.' + app_name.replace(' ', '') + '.com' if '.' not in app_name else 'https://' + app_name.replace(' ', '')
            speak("Opening " + app_name)
            webbrowser.open(url)
            return

        # If the exact query is a folder or path, open it directly.
        if os.path.exists(app_name):
            speak("Opening " + app_name)
            os.startfile(app_name)
            return

        cursor.execute('SELECT path FROM sys_command WHERE name IN (?)', (app_name,))
        results = cursor.fetchall()

        if len(results) != 0:
            speak("Opening " + app_name)
            os.startfile(results[0][0])
            return

        cursor.execute('SELECT url FROM web_command WHERE name IN (?)', (app_name,))
        results = cursor.fetchall()

        if len(results) != 0:
            speak("Opening " + app_name)
            webbrowser.open(results[0][0])
            return

        if '.' in app_name or app_name.startswith('http'):
            speak("Opening " + app_name)
            webbrowser.open(app_name)
            return

        speak("Trying to open " + app_name)
        subprocess.run(f'start "" "{app_name}"', shell=True)
    except Exception:
        speak("Sorry, I could not open " + app_name)


def _parse_alarm_time(query):
    query = query.lower()
    query = query.replace('set alarm', '')
    query = query.replace('set alerm', '')
    query = query.replace('set an alarm', '')
    query = query.replace('set the alarm', '')
    query = query.replace('for', '')
    query = query.replace('at', '')
    query = query.replace('to', '')
    query = query.replace('a m', 'am')
    query = query.replace('p m', 'pm')
    query = query.replace('a.m.', 'am')
    query = query.replace('p.m.', 'pm')
    query = query.replace('tomorrow', 'tomorrow ')
    query = re.sub(r'\s+', ' ', query).strip()

    pattern = r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?'
    match = re.search(pattern, query)
    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    ampm = match.group(3)

    if ampm:
        ampm = ampm.lower()
        if ampm == 'pm' and hour != 12:
            hour += 12
        if ampm == 'am' and hour == 12:
            hour = 0
    else:
        if hour == 24:
            hour = 0
        if hour < 0 or hour > 23:
            return None

    now = datetime.now()
    alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if 'tomorrow' in query or alarm_time <= now:
        alarm_time += timedelta(days=1)

    return alarm_time


def _alarm_thread(alarm_time):
    wait_seconds = (alarm_time - datetime.now()).total_seconds()
    if wait_seconds > 0:
        time.sleep(wait_seconds)

    speak('Alarm time reached. Opening Clock app.')
    try:
        os.system('start "" "shell:AppsFolder\\Microsoft.WindowsAlarms_8wekyb3d8bbwe!App"')
    except Exception:
        pass

    try:
        alarm_sound = 'www\\assets\\audio\\start_sound.mp3'
        playsound(alarm_sound)
    except Exception:
        speak('Alarm ringing')


@eel.expose
def setAlarm(query):
    alarm_time = _parse_alarm_time(query)
    if alarm_time is None:
        speak('I could not understand the alarm time. Please say set alarm for 7 a m or set alarm at 18 30.')
        return

    formatted_time = alarm_time.strftime('%I:%M %p')
    speak('Setting alarm for ' + formatted_time)
    os.system('start "" "shell:AppsFolder\\Microsoft.WindowsAlarms_8wekyb3d8bbwe!App"')
    threading.Thread(target=_alarm_thread, args=(alarm_time,), daemon=True).start()

       

def PlayYoutube(query):
    search_term = extract_yt_term(query)
    if search_term:
        speak("Playing "+search_term+" on YouTube")
        kit.playonyt(search_term)
    else:
        speak("Opening YouTube")
        webbrowser.open("https://www.youtube.com")


def hotword():
    porcupine=None
    paud=None
    audio_stream=None
    try:
       
        # pre trained keywords    
        porcupine=pvporcupine.create(keywords=["jarvis","alexa"]) 
        paud=pyaudio.PyAudio()
        audio_stream=paud.open(rate=porcupine.sample_rate,channels=1,format=pyaudio.paInt16,input=True,frames_per_buffer=porcupine.frame_length)
        
        # loop for streaming
        while True:
            keyword=audio_stream.read(porcupine.frame_length)
            keyword=struct.unpack_from("h"*porcupine.frame_length,keyword)

            # processing keyword comes from mic 
            keyword_index=porcupine.process(keyword)

            # checking first keyword detetcted for not
            if keyword_index>=0:
                print("hotword detected")

                # pressing shorcut key win+j
                import pyautogui as autogui
                autogui.keyDown("win")
                autogui.press("j")
                time.sleep(2)
                autogui.keyUp("win")
                
    except:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if paud is not None:
            paud.terminate()



# find contacts
def findContact(query):
    
    words_to_remove = [ASSISTANT_NAME, 'make', 'a', 'to', 'phone', 'call', 'send', 'message', 'wahtsapp', 'video']
    query = remove_words(query, words_to_remove)

    try:
        query = query.strip().lower()
        cursor.execute("SELECT mobile_no FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?", ('%' + query + '%', query + '%'))
        results = cursor.fetchall()
        print(results[0][0])
        mobile_number_str = str(results[0][0])

        if not mobile_number_str.startswith('+91'):
            mobile_number_str = '+91' + mobile_number_str

        return mobile_number_str, query
    except:
        speak('not exist in contacts')
        return 0, 0
    
def whatsApp(mobile_no, message, flag, name):
    

    if flag == 'message':
        target_tab = 12
        jarvis_message = "message send successfully to "+name

    elif flag == 'call':
        target_tab = 7
        message = ''
        jarvis_message = "calling to "+name

    else:
        target_tab = 6
        message = ''
        jarvis_message = "staring video call with "+name


    # Encode the message for URL
    encoded_message = quote(message)
    print(encoded_message)
    # Construct the URL
    whatsapp_url = f"whatsapp://send?phone={mobile_no}&text={encoded_message}"

    # Construct the full command
    full_command = f'start "" "{whatsapp_url}"'

    # Open WhatsApp with the constructed URL using cmd.exe
    subprocess.run(full_command, shell=True)
    time.sleep(5)
    subprocess.run(full_command, shell=True)
    
    pyautogui.hotkey('ctrl', 'f')

    for i in range(1, target_tab):
        pyautogui.hotkey('tab')

    pyautogui.hotkey('enter')
    speak(jarvis_message)

# chat bot 
def chatBot(query):
    user_input = query.lower()
    chatbot = hugchat.ChatBot(cookie_path="engine\cookies.json")
    id = chatbot.new_conversation()
    chatbot.change_conversation(id)
    response =  chatbot.chat(user_input)
    print(response)
    speak(response)
    return response

# android automation

def makeCall(name, mobileNo):
    mobileNo =mobileNo.replace(" ", "")
    speak("Calling "+name)
    command = 'adb shell am start -a android.intent.action.CALL -d tel:'+mobileNo
    os.system(command)


# to send message
def sendMessage(message, mobileNo, name):
    from engine.helper import replace_spaces_with_percent_s, goback, keyEvent, tapEvents, adbInput
    message = replace_spaces_with_percent_s(message)
    mobileNo = replace_spaces_with_percent_s(mobileNo)
    speak("sending message")
    goback(4)
    time.sleep(1)
    keyEvent(3)
    # open sms app
    tapEvents(136, 2220)
    #start chat
    tapEvents(819, 2192)
    # search mobile no
    adbInput(mobileNo)
    #tap on name
    tapEvents(601, 574)
    # tap on input
    tapEvents(390, 2270)
    #message
    adbInput(message)
    #send
    tapEvents(957, 1397)
    speak("message send successfully to "+name)

import google.generativeai as genai
def _wikipedia_answer(query):
    search_query = query
    search_query = search_query.replace(ASSISTANT_NAME, "")
    search_query = search_query.replace("what is", "")
    search_query = search_query.replace("who is", "")
    search_query = search_query.replace("tell me about", "")
    search_query = search_query.replace("define", "")
    search_query = re.sub(r'\b(please|tell me|about|define|search for)\b', '', search_query)
    search_query = re.sub(r'\s+', ' ', search_query).strip()

    if not search_query:
        return None

    results = wikipedia.search(search_query, results=3)
    if not results:
        return None

    try:
        summary = wikipedia.summary(results[0], sentences=2)
        return markdown_to_text(summary)
    except Exception:
        return None


def geminai(query):
    query = query.replace(ASSISTANT_NAME, "")
    query = query.replace("search", "")
    query = query.strip()

    # Try Wikipedia first for simple factual questions.
    if any(trigger in query.lower() for trigger in ["what is", "who is", "tell me about", "define", "what are", "what was", "what were"]):
        wiki_text = _wikipedia_answer(query)
        if wiki_text:
            speak(wiki_text)
            return

    try:
        # Set your API key
        genai.configure(api_key=LLM_KEY)

        # Select a model with a system prompt for Jarvis behavior
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=SYSTEM_PROMPT)

        # Generate a response
        response = model.generate_content(query)
        filter_text = markdown_to_text(response.text)
        if filter_text:
            speak(filter_text)
            return
    except Exception as e:
        print("Error:", e)

        # Try a secondary LLM path if the primary API failed.
        try:
            from engine.groq_chatbot import ChatBot
            fallback_response = ChatBot(query)
            if fallback_response and fallback_response.strip():
                speak(fallback_response)
                return
        except Exception as fallback_error:
            print("Fallback error:", fallback_error)

    # Final fallback: open a web search if no answer could be generated.
    if query.strip():
        speak("I could not answer that directly, but I found results in your browser.")
        search_url = f"https://www.google.com/search?q={quote(query)}"
        webbrowser.open(search_url)
    else:
        speak("Please ask me a question.")

# Settings Modal 



# Assistant name
@eel.expose
def assistantName():
    name = ASSISTANT_NAME
    return name


@eel.expose
def personalInfo():
    try:
        cursor.execute("SELECT * FROM info")
        results = cursor.fetchall()
        jsonArr = json.dumps(results[0])
        eel.getData(jsonArr)
        return 1    
    except:
        print("no data")


@eel.expose
def updatePersonalInfo(name, designation, mobileno, email, city):
    cursor.execute("SELECT COUNT(*) FROM info")
    count = cursor.fetchone()[0]

    if count > 0:
        # Update existing record
        cursor.execute(
            '''UPDATE info 
               SET name=?, designation=?, mobileno=?, email=?, city=?''',
            (name, designation, mobileno, email, city)
        )
    else:
        # Insert new record if no data exists
        cursor.execute(
            '''INSERT INTO info (name, designation, mobileno, email, city) 
               VALUES (?, ?, ?, ?, ?)''',
            (name, designation, mobileno, email, city)
        )

    con.commit()
    personalInfo()
    return 1



@eel.expose
def displaySysCommand():
    cursor.execute("SELECT * FROM sys_command")
    results = cursor.fetchall()
    jsonArr = json.dumps(results)
    eel.displaySysCommand(jsonArr)
    return 1


@eel.expose
def deleteSysCommand(id):
    cursor.execute("DELETE FROM sys_command WHERE id = ?", (id,))
    con.commit()


@eel.expose
def addSysCommand(key, value):
    cursor.execute(
        '''INSERT INTO sys_command VALUES (?, ?, ?)''', (None,key, value))
    con.commit()


@eel.expose
def displayWebCommand():
    cursor.execute("SELECT * FROM web_command")
    results = cursor.fetchall()
    jsonArr = json.dumps(results)
    eel.displayWebCommand(jsonArr)
    return 1


@eel.expose
def addWebCommand(key, value):
    cursor.execute(
        '''INSERT INTO web_command VALUES (?, ?, ?)''', (None, key, value))
    con.commit()


@eel.expose
def deleteWebCommand(id):
    cursor.execute("DELETE FROM web_command WHERE Id = ?", (id,))
    con.commit()


@eel.expose
def displayPhoneBookCommand():
    cursor.execute("SELECT * FROM contacts")
    results = cursor.fetchall()
    jsonArr = json.dumps(results)
    eel.displayPhoneBookCommand(jsonArr)
    return 1


@eel.expose
def deletePhoneBookCommand(id):
    cursor.execute("DELETE FROM contacts WHERE Id = ?", (id,))
    con.commit()


@eel.expose
def InsertContacts(Name, MobileNo, Email, City):
    cursor.execute(
        '''INSERT INTO contacts VALUES (?, ?, ?, ?, ?)''', (None,Name, MobileNo, Email, City))
    con.commit()