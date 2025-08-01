from diffusers import StableDiffusionImg2ImgPipeline
from PIL import Image
import torch
import os

# Using a lighter model that works better on CPU
model_id = "runwayml/stable-diffusion-v1-5"

pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.float32,
    safety_checker=None,
    requires_safety_checker=False
).to("cpu")

# Optimizations for CPU
pipe.enable_attention_slicing()
# ❌ pipe.enable_sequential_cpu_offload()  # REMOVE this line for CPU-only setups

def edit_image_with_prompt(image_path, prompt, strength=0.75, guidance_scale=7.5):
    init_image = Image.open(image_path).convert("RGB")

    width, height = init_image.size
    max_size = 512
    if width > height:
        new_width = max_size
        new_height = int(height * (max_size / width))
    else:
        new_height = max_size
        new_width = int(width * (max_size / height))
    
    init_image = init_image.resize((new_width, new_height))

    result = pipe(
        prompt=prompt,
        image=init_image,
        strength=strength,
        guidance_scale=guidance_scale,
        num_inference_steps=25
    ).images[0]
    
    output_path = "output/edited.png"
    os.makedirs("output", exist_ok=True)
    result.save(output_path)
    
    return output_path
