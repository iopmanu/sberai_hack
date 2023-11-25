import os
import ray
import time
import openai

from typing import List

from configs.configs import GPT_JSON, NUM_SECONDS_TO_SLEEP

os.environ['OPENAI_API_KEY'] = GPT_JSON['openai_api_key']


@ray.remote(num_cpus=1)
def get_eval(content: str, max_tokens: int):
    while True:
        try:
            responce = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[{
                    'role': 'system',
                    'content': 'You are a helpful and precise assistant for checking relevance of the question to the given sentence.'
                }, {
                    'role': 'user',
                    'content': content,
                }],
                temperature=0.2,
                max_tokens=max_tokens
            )
            break
        except openai.error.RateLimitError:
            pass
        except Exception as e:
            print(e)
        time.sleep(NUM_SECONDS_TO_SLEEP)

    print('success!')
    return responce['choices'][0]['message']['content']


def create_contents(sentence: str, questions: List[str], prompt: str):
    contents = []

    for question in questions:
        content = (f'[Question]\n{question}\n\n'
                   f'[Sentence]\n{sentence}\n\n'
                   f'[System]\n{prompt}\n\n')

        contents.append(content)

    return contents


def eval(sentence, questions, prompt, max_tokens: int):
    handles = []
    for content in create_contents(sentence, questions, prompt):
        handles.append(get_eval.remote(content, max_tokens))

    return handles
