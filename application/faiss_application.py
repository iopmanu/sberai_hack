from typing import Annotated, List
from fastapi import FastAPI, Form, HTTPException

from model.columns_finder import ColumnsFinder
from configs.configs import LLAVA_ENDPOINTS

app = FastAPI()
cf = ColumnsFinder(LLAVA_ENDPOINTS)


@app.post("/fill_questions_db/")
async def fill_questions_db(
        image_files: List[str]
):
    if cf.question_db is not None:
        cf.clear_stash()

    return {"questions": cf.create_column_names(image_files)}


@app.get("/get_nearest_question/")
async def get_nearest_question(
        question: Annotated[str, Form()]
):
    if cf.question_db is None:
        raise HTTPException(status_code=400, detail="Question database isn't full.")

    return {question: cf.question_db.max_relevance_search(question)[0].page_content}
