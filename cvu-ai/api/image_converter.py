from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
import os
import shutil
from services.convert_image import convert_image

router = APIRouter()

@router.post("/convert-image/")
async def convert_image_route(
    input_file: UploadFile = File(...),
    output_format: str = Form(...),
    output_filename: str = Form(default="converted_output")
):
    temp_input_path = None
    temp_output_path = None
    try:
        input_ext = input_file.filename.split(".")[-1].lower()
        temp_input_path = f"temp_input.{input_ext}"
        temp_output_path = f"{output_filename}.{output_format.lower()}"

        with open(temp_input_path, "wb") as buffer:
            shutil.copyfileobj(input_file.file, buffer)

        print(f"🔹 Saved temp input file: {temp_input_path}")
        print(f"🔹 Target output path: {temp_output_path}")

        convert_image(temp_input_path, temp_output_path)

        # Step 1: Check if single output file exists
        if os.path.exists(temp_output_path):
            return JSONResponse(content={"message": "File converted successfully", "output_file": temp_output_path}, status_code=200)

        # Step 2: Else check if multiple files generated (for multipage PDFs)
        output_files = []
        base_name, ext = os.path.splitext(temp_output_path)
        page = 1
        while True:
            page_file = f"{base_name}_page{page}{ext}"
            if os.path.exists(page_file):
                output_files.append(page_file)
                page += 1
            else:
                break

        if output_files:
            return JSONResponse(content={"message": "Multiple files generated successfully", "output_files": output_files}, status_code=200)

        # Step 3: Else, no output found
        print("❌ Output file(s) not created!")
        return JSONResponse(content={"error": "Conversion failed or file not found"}, status_code=500)

    except Exception as e:
        print("❌ Exception:", str(e))
        return JSONResponse(content={"error": str(e)}, status_code=500)

    finally:
        if temp_input_path and os.path.exists(temp_input_path):
            os.remove(temp_input_path)
