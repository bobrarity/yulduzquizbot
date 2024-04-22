import requests
from dotenv import load_dotenv
import os

load_dotenv()
openai_api_key = os.getenv('openai_api_key')
telegram_key = os.getenv('telegram_key')


def quiz(text, lang, q_type):
    openai_url = "https://api.openai.com/v1"

    headers = {"Authorization": f"Bearer {openai_api_key}"}

    if text == '.':
        return None

    url = f"{openai_url}/chat/completions"

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": f'''
                         If '{text}' is related to programming topic (like Python, Java, and it's subtopics like Data 
                         Science, Spring framework etc.) then:
                         You will need to create quiz in {lang} language, which will contain 3 questions for the topic {text}
                         in a type {q_type}. If the multiple choice questions are asked, then provide only 4 options (3 incorrect, and one correct).
                         Provide the response in yaml format this way:
                         questions:
                          - id: 1
                            q: "The question you provide"
                            a:
                              - "True"
                              - correct: "False"
                        
                          - id: 2
                            q: "How many bytes are in the string \"b\0\x00\t\n\"?"
                            a:
                              - "1"
                              - "4"
                              - "6"
                              - correct: "5"
                        ... and so on until final question (no need to write: ```yaml```). No need to ask which information exactly to ask the user,
                        just make up some questions related to topic '{text}'.
                         otherwise, answer: 'the topic you've provided doesn't relate to any programming'.
                        '''
            }
        ]
    }

    response = requests.post(url, json=data, headers=headers)

    print("Status Code", response.status_code)
    chatgpt_response = response.json()["choices"][0]["message"]["content"]
    print("Response from LLM ", chatgpt_response)
    print(chatgpt_response)
    with open('questions.yaml', 'w') as file:
        file.write(chatgpt_response)
        print('YAML file saved successfully')
