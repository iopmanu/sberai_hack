import os

from typing import List, Dict

from configs.configs import GPT_EVALUATION_QUESTIONS_PROMPT, GPT_OPENAI_API_KEY
from gpt_evaluation import get_eval

os.environ['OPENAI_API_KEY'] = GPT_OPENAI_API_KEY


def create_contents(pairs: List[Dict[str, str]], prompt: str):
    contents = []

    for pair in pairs:
        for first, second in pair.items():
            content = (f'[Question1]\n{first}\n\n'
                       f'[Question2]\n{second}\n\n'
                       f'[System]\n{prompt}\n\n')

            contents.append(content)

    return contents


def questions_eval(questions: List[Dict], max_tokens: int, prompt: str = GPT_EVALUATION_QUESTIONS_PROMPT):
    handles = []
    for content in create_contents(questions, prompt):
        handles.append(get_eval.remote(content, max_tokens))

    return handles
