import tkinter as tk
import threading
import queue
import openai
import requests
import os
from bs4 import BeautifulSoup
import json

with open('languages.json') as f:
    lang = json.load(f)

# Set up OpenAI API credentials
file_path = os.path.abspath('openai_api_key.bin')

# Create main window
root = tk.Tk()
root.title("GPTSearcher")
root.geometry('1050x610')

root.resizable(width=False, height=False)

# Create chat window
chat_window = tk.Text(root, height=35, width=120)
chat_window.pack()

# Create input field for user messages
input_field = tk.Entry(root, width=110)
input_field.pack()

# Create send button
send_button = tk.Button(root, text="Send")
send_button.pack()

# Welcome message
with open(file_path, 'r') as file1:
    content = file1.read()
    if not 's' in content:
        chat_window.insert(tk.END,
                           f"Welcome to the GPTSearcher! In this program you can serf the internet by using GPT-3.5 neural network. Please paste your OpenAI API key and press button 'Send'.\n")

# Create queue for sending messages to GPT-3
message_queue = queue.Queue()

messages = [
    {"role": "system",
     "content": f"You are a helpful assistant created to speak with users. You are also a programme for analysing internet links and producing a compact answer to a user's query. Speak {lang['current']}"}
]

def update(messages, role, content):
    messages.append({"role": role, "content": content})
    return messages


def update2(messages, role, content):
    messages.append({"role": role, "content": content})
    return messages


# Function to send message to GPT-3
def send_message():
    with open(file_path, 'r') as file:
        content = file.read()
        if not 's' in content:
            openai_key = input_field.get()
            input_field.delete(0, tk.END)
            chat_window.insert(tk.END, f"System: Key accepted. Please restart the program.\n")
            open('openai_api_key.bin', 'w').write(openai_key)
        else:
            # Get user message from input field
            user_message = input_field.get()
            input_field.delete(0, tk.END)
            chat_window.insert(tk.END, f"User: {user_message}\n")

            # Put message in queue
            message_queue.put(user_message)


# Set up worker thread for sending messages to GPT-3
def worker():
    openai.api_key = open('openai_api_key.bin', 'r').read()
    while True:
        # Get message from queue
        user_message = message_queue.get()
        if user_message == '/delete api_key':
            open(file_path, 'w').write('')
            chat_window.insert(tk.END, f"System: API key has been deleted. Please restart the program.\n")
        elif user_message == '/change lang':
            chat_window.insert(tk.END, f"To change language use command '/change lang (language). For example: /change lang fr'")
        elif user_message == '/change lang ru':
            with open('languages.json', 'w') as f:
                f.write(json.dumps({"current": "Russian"}))
        elif user_message == '/change lang en':
            with open('languages.json', 'w') as f:
                f.write(json.dumps({"current": "English"}))
        elif user_message == '/change lang fr':
            with open('languages.json', 'w') as f:
                f.write(json.dumps({"current": "French"}))
        elif user_message == '/change lang ko':
            with open('languages.json', 'w') as f:
                f.write(json.dumps({"current": "Korean"}))
        elif user_message == '/change lang de':
            with open('languages.json', 'w') as f:
                f.write(json.dumps({"current": "German"}))
        elif user_message == '/change lang uk':
            with open('languages.json', 'w') as f:
                f.write(json.dumps({"current": "Ukrainian"}))
        elif user_message == '/change lang zh':
            with open('languages.json', 'w') as f:
                f.write(json.dumps({"current": "Chinese"}))
        elif user_message == '/change lang ja':
            with open('languages.json', 'w') as f:
                f.write(json.dumps({"current": "Japanese"}))

        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            max_tokens=1,
            messages=[
                {"role": "system",
                 "content": "You are a program which determines whether a user's query is a search query or not. That is: if the user entered a query, for example, 'what is python', you define it as searchable and print only 'y' in the answer and nothing else. If the answer is not a search query, but a normal, conversational query, such as 'hello, how are you?' - you define it as non-searchable and the answer prints just 'n' and nothing else. You are not allowed to give a long answer, your allowed characters are 'y' and 'n'."},
                {"role": "user", "content": user_message}
            ]
        )
        respi = response['choices'][0]['message']['content']

        if respi == 'y' or 'поиск' in user_message:
            chat_window.insert(tk.END, f"\nBrowsing web...\n")
            try:
                from googlesearch import search
            except ImportError:
                print("No module named 'google' found")

            for collected_requests in search(user_message, tld="co.in", num=3, stop=3, pause=0):
                continue

            url = collected_requests
            response4 = requests.get(url)
            soup = BeautifulSoup(response4.text, 'html.parser')
            text1 = soup.get_text()
            text = text1[:4000]

            update2(messages, "user", f"query: {user_message}. Text from site: {text}. Speak {lang['current']}")
            response2 = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=messages
            )
            respi2 = response2['choices'][0]['message']['content']
        else:
            update(messages, "user", user_message)
            response1 = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            respi1 = response1['choices'][0]['message']['content']

        # Put message and response in queue
        response_queue.put((user_message, respi))

        def update_chat_window():
            while True:
                # Get message and response from queue
                user_message, response = response_queue.get()

                # Display message and response in chat window

                if respi == 'y' or 'поиск' in user_message:
                    chat_window.insert(tk.END, f"\nGPT-3: {respi2}\n\nSources: \n{collected_requests}\n\n")
                else:
                    chat_window.insert(tk.END, f"\nGPT-3: {respi1}\n\n")

                # Mark message as done
                response_queue.task_done()

        # Mark message as done
        message_queue.task_done()

        update_thread = threading.Thread(target=update_chat_window, daemon=True)
        update_thread.start()


# Bind send button to send_message function
send_button.config(command=send_message)

# Create queue for receiving responses from GPT-3
response_queue = queue.Queue()

# Start worker threads
worker_thread = threading.Thread(target=worker, daemon=True)
worker_thread.start()

# Start main loop
root.mainloop()