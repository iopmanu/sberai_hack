import torch

from typing import List, Dict

from llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN, DEFAULT_IM_START_TOKEN, DEFAULT_IM_END_TOKEN
from llava.conversation import conv_templates, SeparatorStyle
from llava.model.builder import load_pretrained_model
from llava.utils import disable_torch_init
from llava.mm_utils import process_images, tokenizer_image_token, get_model_name_from_path, KeywordsStoppingCriteria

from PIL import Image

from transformers import TextStreamer


class TableFormer:
    NUM_THREADS = 3

    def __init__(self,
                 model_path: str, model_base=None, load_8bit: bool = False,
                 load_4bit: bool = True, device: str = 'cuda', conv=conv_templates["llava_v0"]
                 ):
        self.model_name = get_model_name_from_path(model_path)
        self.tokenizer, self.model, self.image_processor, self.context_len = load_pretrained_model(
            model_path, model_base, self.model_name, load_8bit, load_4bit, device=device)
        self.conv = conv

        self.questions = []

        self.image_file = None
        self.image_tuple = None

    def image_tensor(self, image_file: str):
        image = Image.open(image_file).convert('RGB')
        disable_torch_init()

        image_tensor = process_images([image], self.image_processor, self.model.config)
        if type(image_tensor) is list:
            image_tensor = [image.to(self.model.device, dtype=torch.float16) for image in image_tensor]
        else:
            image_tensor = image_tensor.to(self.model.device, dtype=torch.float16)

        return image_tensor, image

    def make_prompt(self, image, input):
        self.conv.messages = []
        input = f"{self.conv.roles[0]}: {input}"

        if image is not None:
            if self.model.config.mm_use_im_start_end:
                input = DEFAULT_IM_START_TOKEN + DEFAULT_IMAGE_TOKEN + DEFAULT_IM_END_TOKEN + '\n' + input
            else:
                input = DEFAULT_IMAGE_TOKEN + '\n' + input
            self.conv.append_message(self.conv.roles[0], input)
            image = None
        else:
            self.conv.append_message(self.conv.roles[0], input)

        self.conv.append_message(self.conv.roles[1], None)
        prompt = self.conv.get_prompt()
        return prompt

    async def predict(self,
                      image_file: str, input: str, logging: bool = False,
                      temperature: float = 0.2, max_new_tokens: int = 512) -> Dict:
        torch.cuda.empty_cache()

        image_tensor, image = self.image_tensor(image_file) if not self.image_file else self.image_tuple
        self.image_file = image_file
        self.image_tuple = (image_tensor, image)
        prompt = self.make_prompt(image, input)

        input_ids = tokenizer_image_token(prompt, self.tokenizer, IMAGE_TOKEN_INDEX,
                                          return_tensors='pt').unsqueeze(0).to(self.model.device)
        stop_str = self.conv.sep if self.conv.sep_style != SeparatorStyle.TWO else self.conv.sep2
        keywords = [stop_str]
        stopping_criteria = KeywordsStoppingCriteria(keywords, self.tokenizer, input_ids)
        streamer = TextStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)

        with torch.inference_mode():
            output_ids = self.model.generate(
                input_ids,
                images=image_tensor,
                do_sample=True if temperature > 0 else False,
                temperature=temperature,
                max_new_tokens=max_new_tokens,
                streamer=streamer,
                use_cache=True,
                stopping_criteria=[stopping_criteria])

        outputs = self.tokenizer.decode(output_ids[0, input_ids.shape[1]:]).strip()
        self.conv.messages[-1][-1] = outputs

        prompt_outputs = {"prompt": prompt, "outputs": outputs}

        if logging:
            print("\n", prompt_outputs, "\n")

        return prompt_outputs

    async def make_captions(self, image_file: str, logging: bool = False,
                            temperature: float = 0.2, max_new_tokens: int = 512):
        input = "Please make a detailed caption of this picture."
        return await self.predict(image_file, input, logging, temperature, max_new_tokens)

    async def create_questions(self, image_file: str, logging: bool = False,
                               temperature: float = 0.2, max_new_tokens: int = 512):
        input = f'Please create 5 questions which you can ask about this picture \
                  separated by "\n" without enumeration.'
        return await self.predict(image_file, input, logging, temperature, max_new_tokens)
