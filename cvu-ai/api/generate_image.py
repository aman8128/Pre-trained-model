from fastapi import APIRouter
from pydantic import BaseModel
import torch
from diffusers import DiffusionPipeline
import os
from services.convert_image import convert_image_to_svg

router = APIRouter()

device = "cuda" if torch.cuda.is_available() else "cpu"

pipe = DiffusionPipeline.from_pretrained(
    "segmind/SSD-1B",
    torch_dtype=torch.float32,
)
pipe = pipe.to(device)

class PromptRequest(BaseModel):
    prompt: str
    filename: str

@router.post("/generate-image/")
async def generate_image(data: PromptRequest):
    try:
        prompt = data.prompt
        filename = data.filename

        os.makedirs("generated", exist_ok=True)
        save_path = os.path.join("generated", filename)

        # Generate image
        output = pipe(
            prompt=prompt,
            num_inference_steps=15,
            guidance_scale=7.5
        )

        image = output.images[0]

        if filename.endswith(".svg"):
            # 1. Save temporary PNG
            temp_png_path = save_path.replace(".svg", ".png")
            image.save(temp_png_path)

            # 2. Now convert that PNG to SVG
            convert_image_to_svg(temp_png_path, save_path)

            # (Optional) delete temp_png_path after conversion
            os.remove(temp_png_path)

        elif not filename.endswith(".png") or filename.endswith(".svg"):
            filename += ".png"
            
        else:
            # Directly save if not SVG
            image.save(save_path)

        print(f"Image saved at: {save_path}")
        
        return {"message": "Image generated successfully", "filepath": save_path}

    except Exception as e:
        return {"detail": str(e)}
