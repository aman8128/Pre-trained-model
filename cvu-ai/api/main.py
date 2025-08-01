# api/main.py
from fastapi import FastAPI, Request
from services.chat_service import generate_reply
from api.image_converter import router as image_converter_router
from api.generate_image import router as router
from api.update_image import router as update_image_router

app = FastAPI()

@app.post("/cvu/chat")
async def chat(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")
    reply = generate_reply(prompt)
    return {"cvu": reply}

app.include_router(image_converter_router)
app.include_router(router)
app.include_router(update_image_router)