# Trainer.py
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import pickle
import os

model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

# Load chat history
with open("chat_history.pkl", "rb") as f:
    chat_history = pickle.load(f)

# Prepare training dataset
training_text = ""
for exchange in chat_history:
    training_text += f"User: {exchange['user']}\nAI: {exchange['ai']}\n"

inputs = tokenizer(training_text, return_tensors="pt", truncation=True, max_length=1024).to(device)

# Training
model.train()
optimizer = torch.optim.AdamW(model.parameters(), lr=3e-5)

outputs = model(**inputs, labels=inputs['input_ids'])
loss = outputs.loss
loss.backward()
optimizer.step()

print(f"Training Done. Loss: {loss.item():.4f}")

# Save updated model
model.save_pretrained("./trained_model/")
tokenizer.save_pretrained("./trained_model/")
