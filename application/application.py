import os
import sys

from fastapi import FastAPI

sys.path.append(os.getcwd() + '/../LLaVA')
sys.path.append(os.getcwd() + '/../LLaVA/llava')
sys.path.append(os.getcwd() + '/../')
sys.path.append(os.getcwd() + '/../configs')
sys.path.append(os.getcwd() + '/../model')


from configs.configs import MODEL_NAME
from configs_app import MODEL_LOGGING, MODEL_TEMPERATURE, MODEL_MAX_NEW_TOKENS
from TableFormer import TableFormer

app = FastAPI()
former = TableFormer(MODEL_NAME)


@app.post("/create_questions/")
async def create_questions(
        image_file: str,
):
    result = await former.create_questions(image_file=image_file, logging=MODEL_LOGGING,
                                           temperature=MODEL_TEMPERATURE, max_new_tokens=MODEL_MAX_NEW_TOKENS)
    return {"questions": result}


@app.post("/create_vqa")
async def create_vqa(
        image_file,
        question: str,

):
    result = await former.predict(image_file=image_file, input=question, logging=MODEL_LOGGING,
                                  temperature=MODEL_TEMPERATURE, max_new_tokens=MODEL_MAX_NEW_TOKENS)
    return {"question": question, "answer": result}
