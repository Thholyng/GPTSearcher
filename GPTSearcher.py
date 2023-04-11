import tkinter as tk
import threading
import queue
import openai
import requests
import os
from bs4 import BeautifulSoup

# Set up OpenAI API credentials
file_path = os.path.abspath('openai_api_key.bin')


def search_str():
    with open(file_path, 'r') as file:
        content = file.read()
        if not 's' in content:
            print("Welcome to GPTSearcher! In this program you can search information in the internet by using GPT-3.5")
            openai_key = input("Paste your OpenAI API key: ")
            open('openai_api_key.bin', 'w').write(openai_key)

search_str()

openai.api_key = open('openai_api_key.bin', 'r').read()

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

# Create queue for sending messages to GPT-3
message_queue = queue.Queue()


# Function to send message to GPT-3
def send_message():
    # Get user message from input field
    user_message = input_field.get()
    input_field.delete(0, tk.END)
    chat_window.insert(tk.END, f"User: {user_message}\n")

    # Put message in queue
    message_queue.put(user_message)


# Set up worker thread for sending messages to GPT-3
def worker():
    while True:
        # Get message from queue
        user_message = message_queue.get()

        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            max_tokens=1,
            messages=[
                {"role": "system", "content": "You are a program which determines whether a user's query is a search query or not. That is: if the user entered a query, for example, 'what is python', you define it as searchable and print only 'y' in the answer and nothing else. If the answer is not a search query, but a normal, conversational query, such as 'hello, how are you?' - you define it as non-searchable and the answer prints just 'n' and nothing else. You are not allowed to give a long answer, your allowed characters are 'y' and 'n'."},
                {"role": "user", "content": user_message}
            ]
        )
        respi = response['choices'][0]['message']['content']

        if respi == 'y' or 'поиск' in user_message:
            chat_window.insert(tk.END, f"\nBrowsing web...")
            try:
                from googlesearch import search
            except ImportError:
                print("No module named 'google' found")

            for collected_requests in search(user_message, tld="co.in", num=3, stop=3, pause=0):
                continue

            chat_window.insert(tk.END, f"\nReading articles...")
            url = collected_requests
            response4 = requests.get(url)
            soup = BeautifulSoup(response4.text, 'html.parser')
            text1 = soup.get_text()
            text = text1[:4000]
            chat_window.insert(tk.END, f"\nResponding...\n")

            response2 = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[
                    {"role": "system",
                     "content": "You are a programme for analysing internet links and producing a compact answer to a user's query. Speak Russian."},
                    {"role": "user", "content": "query: " + user_message + " text from sites: " + text}
                ]
            )
            respi2 = response2['choices'][0]['message']['content']
        else:
            response1 = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": user_message}
                ]
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