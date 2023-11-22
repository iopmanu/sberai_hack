import os
import sys

from fastapi import FastAPI
from configs.configs import MODEL_NAME

sys.path.append(os.getcwd() + '/../LLaVA')

from model.TableFormer import TableFormer

app = FastAPI()
former = TableFormer(MODEL_NAME)


@app.post("/create_questions/")
async def create_questions(
        image_file,
        logging: bool = False,
        temperature: float = 0.2,
        max_new_tokens: int = 512
):
    result = await former.create_questions(image_file=image_file, logging=logging,
                                           temperature=temperature, max_new_tokens=max_new_tokens)
    return {"questions": result}


@app.post("/create_vqa")
async def create_vqa(
        image_file,
        question: str,
        logging: bool = False,
        temperature: float = 0.2,
        max_new_tokens: int = 512
):
    result = await former.predict(image_file=image_file, input=question, logging=logging,
                                  temperature=temperature, max_new_tokens=max_new_tokens)
    return {"question": question, "answer": result}
