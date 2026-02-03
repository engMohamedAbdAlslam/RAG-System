from ..LLLMInterface import LLMInterface 
import cohere
import logging
from ..LLMEnum import CoHereEnum,DocumentTypeEnum 

class CoHereProvider(LLMInterface):
    def __init__(self , api_key : str , 
                        default_input_max_chars :int = 1000,
                        default_output_max_tokens :int = 1000,
                        default_temperature :float =0.1):
        
        self.api_key = api_key
        self.enums = CoHereEnum
        self.default_input_max_chars = default_input_max_chars
        self.default_output_max_tokens = default_output_max_tokens
        self.default_temperature = default_temperature

        self.generation_model_id = None

        self.emmbeding_model_id = None
        self.emmbeding_size = None

        self.client = cohere.Client(api_key=self.api_key)
        
        self.logger = logging.getLogger(__name__)

    def set_generation_model(self,model_id : str):
        self.generation_model_id = model_id
        

    def set_embedding_model(self,model_id : str, emmbeding_size : int):
        self.emmbeding_model_id =model_id
        self.emmbeding_size = emmbeding_size

    def generate_text(self,prompt : str, chat_history : list = [] , max_output_tokens:int= None , temperature:float = None): # type: ignore
       
        if not self.client:
            self.logger.error("Co here client was not set")
            return None

        if not self.generation_model_id:
            self.logger.error("generation model for co here was not found")
            return None
       
        max_output_tokens = max_output_tokens if max_output_tokens else self.default_output_max_tokens
        temperature = temperature if temperature else self.default_temperature

        
        response = self.client.chat(
            model = self.generation_model_id,
            chat_history = chat_history,
            message = self.process_text(text= prompt), # type: ignore
            max_tokens= max_output_tokens,
            temperature = temperature
        )
        if not response or not response.text:
            self.logger.error("error while generation text with CoHere")
            return None

        return response.text


    def emmbed_text(self , text : str , document_type = None):
        if not self.client:
            self.logger.error("CoHere client was not set")
            return None

        if not self.emmbeding_model_id:
            self.logger.error("emmbeding model for Cohere was not found")
            return None

        input_type = CoHereEnum.DOCUMENT.value
        if document_type==DocumentTypeEnum.QUERY:
            input_type = CoHereEnum.QUERY.value

        response = self.client.embed(model=self.emmbeding_model_id,
                                     texts=[text],
                                     input_type=input_type,
                                     embedding_types=["float"])
        
        if  (
                response is None
                or response.embeddings is None
                or response.embeddings.float is None # type: ignore
                or len(response.embeddings.float) == 0 # type: ignore
            ):
            raise ValueError("Empty embedding response from Cohere")


        return response.embeddings.float[0] # type: ignore


    def process_text(self, text:str):
        return text[:self.default_input_max_chars].strip()
    
   

    

    def construct_prompt(self, prompt : str , role :str):
        return {
            "role":role,
            "text":prompt
        }
