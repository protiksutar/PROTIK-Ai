import datetime
import json
import os
from pathlib import Path

import groq
from googlesearch import search
from dotenv import dotenv_values

# Load environment variables from .env file
env_vars = dotenv_values(".env")

# Retrieve environment variables for the chatbot configuration
Username = env_vars.get("Username")
AssistantName = env_vars.get("AssistantName")
GroqApiKey = env_vars.get("GroqAPIKey")

# Initialize the Groq client with the API key
client = groq.Client(api_key=GroqApiKey)

System = f"""Hello, I am Protik Sutar, You are a very accurate and advanced AI chatbot named jarvis which has real-time up-to-date information from the internet.
*** IMPORTANT: Reply with ONLY 1-2 sentences answering the main point. NO elaboration or details unless specifically asked.***
*** Provide Answers In a Professional Way with proper grammar.***
*** Never exceed 2 sentences in your response.***"""

def GetSystemContext():
    """Get a fresh system context for each conversation"""
    return [{"role": "system", "content": System}]

DATA_DIR = Path("Data")
CHAT_LOG_PATH = DATA_DIR / "ChatLog.json"

def _ensure_chat_log_file():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CHAT_LOG_PATH.exists():
        CHAT_LOG_PATH.write_text("[]", encoding="utf-8")

def _load_chat_log():
    _ensure_chat_log_file()
    with CHAT_LOG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def _save_chat_log(messages):
    _ensure_chat_log_file()
    with CHAT_LOG_PATH.open("w", encoding="utf-8") as f:
        json.dump(messages, f, indent=4)

# Function to perform a google search and return the results.
def GoogleSearch(query):
    results = list(search(query, advanced=True, num_results=5))
    answer = f"The search results for '{query}' are:\n[start]\n"

    for i in results:
        answer += f"Title: {i.title}\nDescription: {i.description}\n\n"
    answer += "[end]"
    return answer

# Functioon to clean up the answer by removing empty lines.
def AnswerModifier(Answer):
    lines = Answer.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = "\n".join(non_empty_lines)
    return modified_answer

# Function to get real-time information like the current date and time.
def Information():
    data = ""
    current_data_time = datetime.datetime.now()
    day = current_data_time.strftime("%A")
    date = current_data_time.strftime("%d")
    month = current_data_time.strftime("%B")
    year = current_data_time.strftime("%Y")
    hour = current_data_time.strftime("%H")
    minute = current_data_time.strftime("%M")
    second = current_data_time.strftime("%S")
    data += f"Use This Real-time Information if needed:\n"
    data += f"Day: {day}\n"
    data += f"Date: {date}\n"
    data += f"Month: {month}\n"
    data += f"Year: {year}\n"
    data += f"Time: {hour} hours, {minute} minutes, {second} seconds\n"
    return data

# Function to handle real-time search queries and generation.
def RealTimeSearchEngine(prompt):
    # Load the chat log from the json file.
    messages = _load_chat_log()
    messages.append({"role": "user", "content": f"{prompt}"})

    # Get fresh system context
    system_context = GetSystemContext()
    
    # Add Google search results and real-time information
    system_context.append({"role": "system", "content": GoogleSearch(prompt)})
    system_context.append({"role": "system", "content": Information()})

    # Generate search results using the Groq client.
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=system_context + messages,
        temperature=0.7,
        max_tokens=256,
        top_p=1,
        stream=True,
        stop=None
    )

    Answer = ""

    # Concatenate response chunks to form the stream output.
    for response in completion:
        if response.choices[0].delta.content:
            Answer += response.choices[0].delta.content

    # Clean up the response.
    Answer = Answer.strip().replace("</s>", "")
    messages.append({"role": "assistant", "content": f"{Answer}"})

    # Save the updated chat log back to the json file.
    _save_chat_log(messages)

    return AnswerModifier(Answer=Answer)

def RealtimeInformation():
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")

    data = "Please use this real-time information if needed,\n"
    data += f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Time: {hour} hour:{minute} minute:{second} second.\n"
    return data

def AnswerModifier_old(answer):
    lines = answer.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = "\n".join(non_empty_lines)
    return modified_answer

def ChatBot(Query, retry=True):
    """Send the user query to Groq chat completions and return the formatted assistant response."""
    try:
        messages = _load_chat_log()
        messages.append({"role": "user", "content": str(Query)})

        # Get fresh system context for each query
        system_context = GetSystemContext()
        system_context.append({"role": "system", "content": RealtimeInformation()})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=system_context + messages,
            max_tokens=256,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None,
        )

        answer = ""
        for chunk in completion:
            delta = getattr(chunk.choices[0], "delta", None)
            if delta is not None and getattr(delta, "content", None):
                answer += delta.content

        answer = answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": answer})
        _save_chat_log(messages)
        return AnswerModifier_old(answer)

    except Exception as e:
        print(f"Error: {e}")
        _save_chat_log([])
        if retry:
            return ChatBot(Query, retry=False)
        return "Sorry, I couldn't process your request right now."
