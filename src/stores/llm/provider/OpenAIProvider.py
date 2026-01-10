from ..LLLMInterface import LLMInterface
from openai import OpenAI
import logging
from ..LLMEnums import OpenAIEnum

class OpenAIProvider(LLMInterface):
    def __init__(self , api_key : str , URL : str = None,
                        default_input_max_chars :int = 1000,
                        default_output_max_chars :int = 1000,
                        default_temperature :float =0.1):
        
        self.api_key = api_key
        self.URL = URL

        self.default_input_max_chars = default_input_max_chars
        self.default_output_max_tokens = default_output_max_tokens
        self.default_temperature = default_temperature

        self.generation_model_id = None

        self.emmbeding_model_id = None
        self.emmbeding_size = None

        self.client = OpenAI(
            api_key = self.api_key,
            api_url = self.URL
        )
        
        self.logger = logging.getLogger(__name__)

    def set_generation_model(self,model_id : str):
        self.generation_model_id = model_id
        

    def set_embedding_model(self,model_id : str, emmbeding_size : int):
        self.emmbeding_model_id =model_id
        self.emmbeding_size = emmbeding_size

    def generate_text(self,prompt : str, chat_history : list = [] , max_output_tokens:int= None , temperature:float = None):
        if not self.client:
            self.logger.error("Open Ai client was not set")
            return None

        if not self.generation_model_id:
            self.logger.error("generation model for Open Ai was not found")
            return None
        max_output_tokens = max_output_tokens if max_output_tokens else self.default_output_max_tokens
        temperature = temperature if temperature else self.default_temperature

        chat_history.append(self.construct_prompt(prompt=prompt , role=OpenAIEnum.USER.value))

        response = self.client.chat.completions.create(
            model = self.generation_model_id,
            messages = chat_history,
            max_tokens= max_output_tokens,
            temperature = temperature
        )
        if not response or not response.choices or len(response.choices)==0  or not response.choices[0].messages:
            self.logger.error("error while generation text with openAI")
            return None

        return response.choices[0].messages["content"]


    def emmbed_text(self , text : str , document_type = None):
        if not self.client:
            self.logger.error("Open Ai client was not set")
            return None

        if not self.emmbeding_model_id:
            self.logger.error("emmbeding model for Open Ai was not found")
            return None

        response = self.client.emmbedings.create(
            model = self.emmbeding_model_id,
            input = text
        )
        if not response or not response.data or len(response.data)==0  or not response.data[0].emmbeding:
            self.logger.error("error while emmbeding text with openAI")
            return None

        return response.data[0].emmbeding

    def process_text(self, text:str):
        return text[:self.default_input_max_chars].strip()

    def construct_prompt(self, prompt : str , role :str):
        return {
            "role":role,
            "prompt":self.process_text(text=prompt)
        }
