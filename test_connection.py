import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=100,
    messages=[
        {"role": "user", "content": "Olá Claude! Responda confirmando que nossa conexão com a Central de Marketplace está ativa."}
    ]
)

print(response.content[0].text)