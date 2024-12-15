import ast
import torch
from PIL import Image, ImageDraw
from qwen_vl_utils import process_vision_info
from transformers import Qwen2VLForConditionalGeneration, AutoTokenizer, AutoProcessor
from fastapi import FastAPI
from typing import List

app = FastAPI()

MODEL_PATH = "./ShowUI-2B"
DEVICE = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")


model = Qwen2VLForConditionalGeneration.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
    device_map=None
).to(DEVICE)

min_pixels = 256*28*28
max_pixels = 1344*28*28

processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-2B-Instruct",
                                          min_pixels=min_pixels, max_pixels=max_pixels)

@app.post("/generate")
async def generate(messages:List[dict]):
    print(f'messages: {messages}')
    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True,
    )
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = inputs.to(DEVICE)

    generated_ids = model.generate(**inputs, max_new_tokens=128)
    generated_ids_trimmed = [
        out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]

    print(f'output_text: {output_text}')

    parsed_list = ast.literal_eval(f"[{output_text}]")

    return {"showui_res": parsed_list}
