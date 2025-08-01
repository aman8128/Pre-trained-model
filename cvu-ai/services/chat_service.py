import torch, re, os, pickle, time
from transformers import AutoTokenizer, AutoModelForCausalLM

# 🧠 Ultra Fast Rule-Based Mode
ultra_fast_mode = True

# Device setup
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Model Load
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")

# File paths
HISTORY_FILE = "chat_history.pkl"
MEMORY_FILE = "bot_memory.pkl"

# Load/save utilities
def load_pickle(file_path, default):
    """Load pickle file and handle any exception"""
    if os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                return pickle.load(f)
        except (pickle.UnpicklingError, EOFError, Exception) as e:
            print(f"Error loading pickle file {file_path}: {e}")
    return default

def save_pickle(file_path, data):
    """Save object to pickle file in binary format"""
    try:
        with open(file_path, "wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)  # Use highest protocol for better performance
        print(f"Data successfully saved to {file_path}")
    except Exception as e:
        print(f"Error saving data to pickle file {file_path}: {e}")

# Load memory and chat
chat_history = load_pickle(HISTORY_FILE, [])
bot_memory = load_pickle(MEMORY_FILE, {
    "name": "Cvu-ai",
    "user_name": ""
})

# Ultra fast rule-based replies
def fast_reply(prompt):
    small_talk = {
        "hi": "Hey there! How can I help you today?",
        "hii": "Hii! How are you?",
        "hey": "Hey! How can I assist you?",
        "hello": "Hello! How can I help you?",
        "how are you": "I'm doing great thanks! How about you?",
        "how are you doing": "I'm doing great thanks! How about you?",
        "what's your name": f"My name is {bot_memory['name']}.",
        "who made you": "I was built by my creator using TinyLlama model!",
        "thank you": "You're most welcome!",
    }
    prompt_clean = prompt.lower().strip("?!. ")
    return small_talk.get(prompt_clean, None)

# Build full prompt with history
def build_prompt(prompt):
    memory_context = f"You are a helpful assistant named {bot_memory['name']}. Respond quickly and briefly.\n"
    memory_context += "Use past chat history for better replies. Be friendly, concise, and smart.\n\n"

    history = ""
    for exchange in chat_history[-4:]:
        history += f"User: {exchange['user']}\nAI: {exchange['ai']}\n"

    return memory_context + history + f"User: {prompt}\nAI:"

# Clean model output (remove extra junk)
def clean_generated_text(raw_output, final_prompt):
    text = raw_output[len(final_prompt):]  # Remove the prompt part
    text = text.strip()

    # Split by known patterns if extra stuff
    text = text.split("User:")[0]
    text = text.split("user:")[0]
    text = text.split("AI:")[0]

    # Clean unwanted leftovers
    text = text.strip("\n ").replace("\n", " ").strip()

    return text

# Generate AI reply
def generate_reply(prompt):
    global chat_history, bot_memory

    print(f"\n🧠 USER: {prompt}")

    # Save user name if mentioned
    if "my name is" in prompt.lower():
        match = re.search(r"my name is\s+([A-Za-z0-9_-]+)", prompt, re.IGNORECASE)
        if match:
            bot_memory["user_name"] = match.group(1)
            save_pickle(MEMORY_FILE, bot_memory)
            ai_reply = f"Nice to meet you, {bot_memory['user_name']}!"
            _save_chat(prompt, ai_reply)
            print("🤖 AI:", ai_reply)
            return ai_reply

    # Save bot name if mentioned
    if "your name is" in prompt.lower():
        match = re.search(r"your name is\s+([A-Za-z0-9_-]+)", prompt, re.IGNORECASE)
        if match:
            bot_memory["name"] = match.group(1)
            save_pickle(MEMORY_FILE, bot_memory)
            ai_reply = f"Alright! You can call me {bot_memory['name']}."
            _save_chat(prompt, ai_reply)
            print("🤖 AI:", ai_reply)
            return ai_reply

    # Ultra fast small-talk
    if ultra_fast_mode:
        fast = fast_reply(prompt)
        if fast:
            _save_chat(prompt, fast)
            print("⚡ FAST REPLY:", fast)
            return fast

    # Full model generation
    final_prompt = build_prompt(prompt)
    inputs = tokenizer(final_prompt, return_tensors="pt", truncation=True, max_length=512).to(device)

    start = time.time()
    model.eval()
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=100,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )
    end = time.time()

    raw_output = tokenizer.decode(output[0], skip_special_tokens=True)
    ai_reply = clean_generated_text(raw_output, final_prompt)

    _save_chat(prompt, ai_reply)

    print(f"🤖 AI (in {round(end-start,2)}s): {ai_reply}")
    return ai_reply

# Save conversation
def _save_chat(user, ai):
    chat_history.append({"user": user, "ai": ai})
    save_pickle(HISTORY_FILE, chat_history)
