from fastapi import APIRouter, UploadFile, File, Form
from services.image_editor import edit_image_with_prompt
import shutil
import os

router = APIRouter()

@router.post("/update_image")
async def update_image(
    image: UploadFile = File(...),
    prompt: str = Form(...),
    strength: float = Form(0.75),
    guidance_scale: float = Form(7.5)
):
    os.makedirs("temp", exist_ok=True)
    image_path = f"temp/{image.filename}"
    
    # Save uploaded file
    with open(image_path, "wb") as f:
        shutil.copyfileobj(image.file, f)
    
    # Edit the image with prompt
    output_path = edit_image_with_prompt(
        image_path=image_path,
        prompt=prompt,
        strength=strength,
        guidance_scale=guidance_scale
    )
    
    return {
        "output_image_path": output_path,
        "message": "Image edited successfully"
    }