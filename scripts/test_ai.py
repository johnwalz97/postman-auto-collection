import os

import dotenv
import openai

dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

file_paths = []
for root, _, files in os.walk("../postman-docs-ai/"):
    for file in files:
        file_paths.append(os.path.join(root, file))

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {
            "role": "user",
            "content": f"""Consider your knowledge of how REST APIs are commonly built using Python.
Which of the following files are likely candidates for containing the code for an API and its endpoints?
Please respond with only the list of files.
Do not respond with any acknowledgement or explanation.
Please respond with the plain raw text of the list of files.
Please order the files you respond with by their likelihood to have important API code in them.
{''.join(file_paths)}""",
        },
    ],
    temperature=0.8,
)

print(response.choices[0].message.content.strip().split("\n"))