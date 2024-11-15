import asyncio
import aiohttp
import requests
import json

import pandas as pd
import numpy as np

from evaluation.gpt_questions_evaluation import questions_eval
from evaluation.gpt_vqa_evaluation import vqa_eval
from typing import Dict, List

from configs.configs import LLAVA_URLS, EVALUATION_ON, FAISS_APPLICATION_URL, MAIN_PIPELINE_TIMEOUT


class Controller:
    def __init__(self, rudolph_urls=None, llava_urls=LLAVA_URLS, qa_eval_df: pd.DataFrame = None):
        self.llava_urls = llava_urls
        self.rudolph_urls = rudolph_urls if rudolph_urls is not None else []
        self.evaluation_on = EVALUATION_ON
        self.columns = []
        self.vqa_evaluation = []
        self.qa_eval_df = qa_eval_df

    async def main_pipeline(self, image_files: List[str], user_columns: List[str] = None):
        self.columns = user_columns if user_columns is not None else []

        columns = json.loads(
            requests.post(f'{FAISS_APPLICATION_URL[0]}/fill_questions_db/',
                          data={"image_files": ' '.join(image_files)}, timeout=MAIN_PIPELINE_TIMEOUT).text)
        self.columns += columns

        answers_ordered = {column: {} for column in self.columns}
        tasks = []

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=MAIN_PIPELINE_TIMEOUT)) as session:
            for i, image_file in enumerate(image_files):
                url = self._distribute_questions_creation(i, "create_vqa")
                vqa_evaluation_pairs = []

                for question in self.columns:
                    task = asyncio.ensure_future(
                        self._request_vqa_handler(session=session, url=url, answers=answers_ordered, index=i,
                                                  payload={"image_file": image_file,
                                                           "question": question + ' Please answer one number, word or phrase.'},
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
    def _create_dataframe(answers: Dict[str, Dict]):
        data = {}

        for column, responses_ordered in answers.items():
            values = []
            for task_id, response in dict(sorted(responses_ordered.items())).items():
                values.append(response['outputs'].rstrip('</s>'))

            data[column] = values

        return pd.DataFrame(data)

    async def _request_vqa_handler(self, session: aiohttp.ClientSession, url, payload,
                                   answers: Dict[str, Dict[int, str]], index: int, vqa_evaluation_handles: List):
        async with session.post(url, data=payload) as response:
            if response.status == 200:
                data = await response.json()

                if self.evaluation_on and np.random.choice([False, True]):
                    vqa_evaluation_handles.append({data['question']: data['answer']})

                answers[data['question'].rstrip(' Please answer one number, word or phrase.')][index] = data['answer']
            else:
                print("Request failed with status code:", response.status)

    def _distribute_questions_creation(self, index: int, endpoint: str) -> str:
        urls = self.llava_urls + self.rudolph_urls
        return urls[index % len(urls)] + f'/{endpoint}/'

    def _eval_question_pairs(self):
        questions_from_files = list(self.qa_eval_df['question'].values) if self.qa_eval_df is not None else []

        pairs = []
        for question in list(np.random.choice(questions_from_files, size=min(len(questions_from_files), 3))):
            pair = json.loads(requests.get(f'{FAISS_APPLICATION_URL[0]}/get_nearest_question/',
                                           data={'question': question}).text)
            pairs.append(pair)

        return questions_eval(pairs, max_tokens=2048)
