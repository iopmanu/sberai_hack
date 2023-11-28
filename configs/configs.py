MODEL_NAME = '4bit/llava-v1.5-7b-5GB'

DEFAULT_COLUMNS_QUANTITY = 5
DEFAULT_IMAGE_QUANTITY_DELIMETER = 5
DEFAULT_IMAGE_VALIDATION = DEFAULT_IMAGE_QUANTITY_DELIMETER * 2

NUM_SECONDS_TO_SLEEP = 3

LLAVA_URLS = ['http://localhost:8000']
FAISS_APPLICATION_URL = ['http://localhost:8010']

EVALUATION_ON = True
GPT_EVALUATION_QUESTIONS_PROMPT = 'We would like to request your feedback on the perfomance of our AI assistant in responce of simmilarity in meaning of common theme of these questions.\n Please rate simmilarity with an overall score on a scale of 1 to 10, where higher score indicates better overall relevance.\n Please output a single line containing only one value indicating a score.'
GPT_EVALUATION_QUESTIONS_RELEVANCE_PROMPT = 'We would like to request your feedback on the perfomance of our AI assistant in responce of relevance of generated question to picture description.\n Please rate relevance with an overall score on a scale of 1 to 10, where higher score indicates better overall relevance.\n Please output a single line containing only one value indicating a score.'
GPT_EVALUATION_VQA_PROMPT = 'We would like to request your feedback on the perfomance of our AI assistant in responce of relevance answer to the given question.\n Please rate relevance with an overall score on a scale of 1 to 10, where higher score indicates better overall relevance.\n Please output a single line containing only one value indicating a score.'

MAIN_PIPELINE_TIMEOUT = 7200
