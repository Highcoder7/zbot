import config

print("--- Testing Key Parsing ---")
print(f"Bot Token found: {config.TG_BOT_TOKEN is not None}")
if config.TG_BOT_TOKEN:
    print(f"Bot Token: {config.TG_BOT_TOKEN[:10]}...{config.TG_BOT_TOKEN[-10:]}")
else:
    print("Bot Token is missing!")

print(f"OpenAI Key found: {config.OPENAI_API_KEY is not None}")
print(f"OpenAI Model: {config.OPENAI_MODEL}")

print(f"Claude Key found: {config.CLAUDE_API_KEY is not None}")
print(f"Claude Model: {config.CLAUDE_MODEL}")
print("---------------------------")
