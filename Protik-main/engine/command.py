import pyttsx3
import speech_recognition as sr
import eel
import time
from urllib.parse import quote_plus
def speak(text):
    text = str(text)
    engine = pyttsx3.init('sapi5')
    voices = engine.getProperty('voices') 
    engine.setProperty('voice', voices[0].id)
    engine.setProperty('rate', 174)
    eel.DisplayMessage(text)
    engine.say(text)
    eel.receiverText(text)
    engine.runAndWait()


def takecommand():

    r = sr.Recognizer()

    with sr.Microphone() as source:
        print('listening....')
        eel.DisplayMessage('listening....')
        r.pause_threshold = 1
        r.adjust_for_ambient_noise(source)
        
        audio = r.listen(source, 10, 6)

    try:
        print('recognizing')
        eel.DisplayMessage('recognizing....')
        query = r.recognize_google(audio, language='en-in')
        print(f"user said: {query}")
        eel.DisplayMessage(query)
        time.sleep(2)
       
    except Exception as e:
        return ""
    
    return query.lower()


def _get_decision_tasks(query):
    try:
        from engine.decision_model import FirstLayerDMM
        return FirstLayerDMM(query)
    except Exception as e:
        print("Decision model unavailable:", e)
        return []


@eel.expose
def allCommands(message=1):

    if message == 1:
        query = takecommand()
        print(query)
        eel.senderText(query)
    else:
        query = message
        eel.senderText(query)

    query = str(query).strip().lower()

    if "hello jarvis" in query:
        eel.showSiriWave()
        speak("Hello Sir, I am ready. How can I help you")
        return

    if "who is your developer" in query or "who developed you" in query or "your developer" in query or "who is your creator" in query or "who created you" in query or "your creator" in query:
        speak("My developer is Protik Sutar")
        return

    if "tell me about your creator and developer" in query or "tell me about your developer" in query or "about your creator" in query:
        speak("Protik Sutar is a Computer Science & Engineering (CSE) student currently attending the University of Global Village in Bangladesh")
        return

    decision_tasks = _get_decision_tasks(query)
    if decision_tasks:
        from engine.features import geminai
        pending = []
        realtime_pending = []
        for task in decision_tasks:
            task_text = task.strip()
            task_lower = task_text.lower()
            if task_lower == "exit":
                speak("Goodbye")
                return

            if task_lower.startswith("open "):
                from engine.features import openCommand
                openCommand(task_text[5:])
                continue

            if task_lower.startswith("play "):
                from engine.features import PlayYoutube
                PlayYoutube(task_text)
                continue

            if task_lower.startswith("google search "):
                search_term = quote_plus(task_text[14:].strip())
                if search_term:
                    import webbrowser
                    webbrowser.open(f"https://www.google.com/search?q={search_term}")
                    speak("Searching Google for " + task_text[14:].strip())
                continue

            if task_lower.startswith("youtube search "):
                search_term = quote_plus(task_text[15:].strip())
                if search_term:
                    import webbrowser
                    webbrowser.open(f"https://www.youtube.com/results?search_query={search_term}")
                    speak("Searching YouTube for " + task_text[15:].strip())
                continue

            if task_lower.startswith("reminder "):
                from engine.features import setAlarm
                setAlarm("set alarm " + task_text[9:].strip())
                continue

            if task_lower.startswith("realtime "):
                realtime_pending.append(task_text.split(" ", 1)[1] if " " in task_text else "")
                continue

            if task_lower.startswith("general ") or task_lower.startswith("content ") or task_lower.startswith("system "):
                pending.append(task_text.split(" ", 1)[1] if " " in task_text else "")
                continue

            pending.append(task_text)

        if realtime_pending:
            from engine.groq_chatbot import RealTimeSearchEngine
            response = RealTimeSearchEngine(" ".join(realtime_pending))
            speak(response)
            return

        if pending:
            geminai(" ".join([item for item in pending if item]))
            return

    try:

        if "set alarm" in query or "set alerm" in query or ("alarm" in query and "set" in query):
            from engine.features import setAlarm
            setAlarm(query)
        elif "open" in query:
            from engine.features import openCommand
            openCommand(query)
        elif "on youtube" in query or ("youtube" in query and "play" in query) or query.startswith("play "):
            from engine.features import PlayYoutube
            PlayYoutube(query)
        
        elif "send message" in query or "phone call" in query or "video call" in query:
            from engine.features import findContact, whatsApp, makeCall, sendMessage
            contact_no, name = findContact(query)
            if(contact_no != 0):
                speak("Which mode you want to use whatsapp or mobile")
                preferance = takecommand()
                print(preferance)

                if "mobile" in preferance:
                    if "send message" in query or "send sms" in query: 
                        speak("what message to send")
                        message = takecommand()
                        sendMessage(message, contact_no, name)
                    elif "phone call" in query:
                        makeCall(name, contact_no)
                    else:
                        speak("please try again")
                elif "whatsapp" in preferance:
                    message = ""
                    if "send message" in query:
                        message = 'message'
                        speak("what message to send")
                        query = takecommand()
                                        
                    elif "phone call" in query:
                        message = 'call'
                    else:
                        message = 'video call'
                                        
                    whatsApp(contact_no, query, message, name)

        else:
            from engine.features import geminai
            geminai(query)
    except:
        print("error")
    
    eel.ShowHood()