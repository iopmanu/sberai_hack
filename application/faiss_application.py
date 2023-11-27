import sys
import os

from typing import Annotated, List
from fastapi import FastAPI, Form, HTTPException

sys.path.append(os.getcwd() + '/../')
sys.path.append(os.getcwd() + '/../')


from model.columns_finder import ColumnsFinder
from configs.configs import LLAVA_URLS

app = FastAPI()
cf = ColumnsFinder(LLAVA_URLS)


@app.post("/fill_questions_db/")
async def fill_questions_db(
        image_files: Annotated[str, Form()]
):

    image_files = image_files.split(' ')
    if cf.question_db is not None:
        cf.clear_stash()

    columns = await cf.create_column_names(image_files)
    return columns


@app.get("/get_nearest_question/")
async def get_nearest_question(
        question: Annotated[str, Form()]
):
    if cf.question_db is None:
        raise HTTPException(status_code=400, detail="Question database isn't full.")

    return {question: cf.question_db.max_relevance_search(question)[0].page_content}
