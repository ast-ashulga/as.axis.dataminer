import anthropic  # Anthropic Python / Agent SDK base

client = anthropic.Anthropic(
    base_url="http://localhost:11434",  # Ollama Anthropic-compatible endpoint
    api_key="ollama",                   # required but ignored by Ollama
)

resp = client.messages.create(
    model="nemotron-3-super:cloud",  # or whatever model you picked in `ollama launch claude`
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Tell me a joke about AI."},
    ],
)
print(resp)
