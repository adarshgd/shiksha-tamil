import os
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import time

# Flask app initialization
app = Flask(__name__)

# Load API Key and Assistant ID from environment variables
ASSISTANT_ID = os.getenv("ASSISTANT_ID", "asst_fl2z0jnxQDwn0O31CrCsItJS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

client = OpenAI(api_key=OPENAI_API_KEY)

thread_id = None  # Global variable to store thread ID

def create_or_continue_chat(user_message):
    global thread_id

    if thread_id is None:
        thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": user_message,
                }
            ]
        )
        thread_id = thread.id
    else:
        client.beta.threads.messages.create(
            thread_id=thread_id,
            content=user_message,
            role="user"
        )

    run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=ASSISTANT_ID)

    while run.status != "completed":
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        time.sleep(1)

    message_response = client.beta.threads.messages.list(thread_id=thread_id)
    messages = message_response.data

    if messages:
        assistant_message = next((msg for msg in messages if msg.role == 'assistant'), None)
        if assistant_message and assistant_message.content:
            return assistant_message.content[0].text.value
    return "No response from assistant."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    response = create_or_continue_chat(user_message)
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True)
