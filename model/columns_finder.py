import asyncio
import aiohttp
import re
import heapq

import pandas as pd
import numpy as np

from typing import List, Dict

from langchain.document_loaders import DataFrameLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

from configs.configs import (
    DEFAULT_COLUMNS_QUANTITY,
    DEFAULT_IMAGE_QUANTITY_DELIMETER,
    DEFAULT_IMAGE_VALIDATION
)


class SentenceTransformerEmbeddings:
    def __init__(self):
        model_name = "sentence-transformers/all-mpnet-base-v2"
        model_kwargs = {'device': 'cuda'}
        encode_kwargs = {'normalize_embeddings': False}
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )

    @property
    def get_embeddings(self):
        return self.embeddings


class ColumnsFinder:
    def __init__(
            self,
            llava_endpoints: List[str],
            top_k: int = DEFAULT_COLUMNS_QUANTITY,
            embeddings=SentenceTransformerEmbeddings()
    ):
        self.llava_endpoints = llava_endpoints
        self.top_k = top_k
        self.embeddings = embeddings.get_embeddings

        self.questions_stash = []
        self.question_db: FAISS = None

    async def create_faiss_questions(self, image_files: List[str]):
        images_minibatch = list(np.random.choice(
            image_files,
            size=max(len(image_files) // DEFAULT_IMAGE_QUANTITY_DELIMETER, 1)
        ))
        await self.__fill_questions_stash(images_minibatch, self.questions_stash)

        data = pd.DataFrame({'questions': self.questions_stash, 'counts': [0] * len(self.questions_stash)})
        loader = DataFrameLoader(data, page_content_column='questions')
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)

        self.question_db = FAISS.from_documents(texts, self.embeddings)

        return images_minibatch

    async def create_column_names(self, image_files: List[str]) -> List[str]:
        images_minibatch = await self.create_faiss_questions(image_files)
        questions_semantic_counter = {question: 0 for question in self.questions_stash}

        validation_images = np.random.choice(
            validation_qeustions := [question for question in image_files if question not in images_minibatch],
            len(validation_qeustions) // DEFAULT_IMAGE_VALIDATION
        )
        validation_questions = []
        await self.__fill_questions_stash(validation_images, validation_questions)

        for question in validation_questions:
            questions_semantic_counter[self.question_db.max_marginal_relevance_search(question)[0].page_content] += 1

        return self.__top_k_frequently_questions(questions_semantic_counter)

    def __top_k_frequently_questions(self, questions: Dict[str, int]) -> List[str]:
        heap = [(-value, key) for key, value in questions.items()]
        heapq.heapify(heap)

        return [heapq.heappop(heap)[1] for _ in range(min(self.top_k, len(heap)))]

    async def __fill_questions_stash(self, image_files: List[str], questions_stash: List[str]):
        tasks = []

        async with aiohttp.ClientSession() as session:
            for i, image_file in enumerate(image_files):
                url = self._distribute_questions_creation(i, 'create_questions')

                task = asyncio.ensure_future(
                    self._request_handler(session, url, {"image_file": image_file}, questions_stash))
                tasks.append(task)

            await asyncio.gather(*tasks)

    async def _request_handler(self, session: aiohttp.ClientSession, url, payload, questions_stash: List[str]):
        async with session.post(url, data=payload) as response:
            if response.status == 200:
                data = await response.json()
                self._unpack_questions_request(data, questions_stash)
            else:
                print("Request failed with status code:", response.status)

    def _unpack_questions_request(self, response: Dict, questions_stash: List[str]):
        questions = list(map(self.__remove_tokens, response['questions']['outputs'].split('\n')))
        questions_stash += [question for question in questions if question.endswith('?')]

    @staticmethod
    def __remove_tokens(question: str) -> str:
        return re.sub(r'\d+\.\s*|<.*?>', '', question)

    def _distribute_questions_creation(self, index: int, endpoint: str) -> str:
        return self.llava_endpoints[index % len(self.llava_endpoints)] + f'/{endpoint}/'

    def clear_stash(self):
        self.questions_stash = []
        self.question_db = None
