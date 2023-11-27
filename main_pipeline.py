import asyncio
import aiohttp
import requests
import json

import pandas as pd
import numpy as np

from evaluation.gpt_questions_evaluation import questions_eval
from evaluation.gpt_vqa_evaluation import vqa_eval
from typing import Dict, List

from configs.configs import LLAVA_URLS, EVALUATION_ON, FAISS_APPLICATION_URL


class Controller:
    DIRECTORY = '../data/questions.json'

    def __init__(self, rudolph_urls=None, llava_urls=LLAVA_URLS, user_columns=None):
        self.llava_urls = llava_urls
        self.rudolph_urls = rudolph_urls if rudolph_urls is not None else []
        self.evaluation_on = EVALUATION_ON
        self.columns = user_columns if user_columns is not None else []
        self.vqa_evaluation = []

    async def main_pipeline(self, image_files):
        columns = json.loads(
            requests.post(f'{FAISS_APPLICATION_URL[0]}/fill_questions_db/',
                          data={"image_files": ' '.join(image_files)}).text)
        self.columns += columns

        answers_ordered = {column: {} for column in self.columns}
        tasks = []

        async with aiohttp.ClientSession() as session:
            for i, image_file in enumerate(image_files):
                url = self._distribute_questions_creation(i, "create_vqa")
                vqa_evaluation_pairs = []

                for question in self.columns:
                    task = asyncio.ensure_future(
                        self._request_vqa_handler(session=session, url=url, answers=answers_ordered, index=i,
                                                  payload={"image_file": image_file, "question": question},
                                                  vqa_evaluation_handles=vqa_evaluation_pairs)
                    )

                    tasks.append(task)

                self.vqa_evaluation += vqa_evaluation_pairs

            await asyncio.gather(*tasks)

        questions_evaluation = self._eval_question_pairs() if self.evaluation_on else []
        vqa_evaluation = vqa_eval(self.vqa_evaluation, max_tokens=2048) if self.evaluation_on else []

        return {"questions_evaluation": questions_evaluation, "vqa_evaluation": vqa_evaluation,
                "dataframe": self._create_dataframe(answers_ordered)}

    @staticmethod
    def _create_dataframe(answers: Dict[str, Dict[int, str]]):
        return answers

    async def _request_vqa_handler(self, session: aiohttp.ClientSession, url, payload,
                                   answers: Dict[str, Dict[int, str]], index: int, vqa_evaluation_handles: List):
        async with session.post(url, data=payload) as response:
            if response.status == 200:
                data = await response.json()

                if self.evaluation_on and np.random.choice([False, True]):
                    vqa_evaluation_handles.append({data['question']: data['answer']})

                answers[data['question']][index] = data['answer']
            else:
                print("Request failed with status code:", response.status)

    def _distribute_questions_creation(self, index: int, endpoint: str) -> str:
        urls = self.llava_urls + self.rudolph_urls
        return urls[index % len(urls)] + f'/{endpoint}/'

    @staticmethod
    def _eval_question_pairs():
        # TODO: add questions file
        questions_from_file = []

        pairs = []
        for question in list(np.random.choice(questions_from_file, size=min(len(questions_from_file), 3))):
            pair = json.loads(requests.get(f'{FAISS_APPLICATION_URL[0]}/get_nearest_question/',
                                           data={'question': question}).text)
            pairs.append(pair)

        return questions_eval(pairs, max_tokens=2048)
