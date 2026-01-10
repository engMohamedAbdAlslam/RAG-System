from abc import ABC ,abstractclassmethod

class LLMInterface(ABC):
    
    @abstractclassmethod
    def set_generation_model(self,model_id : str):
        pass

    @abstractclassmethod
    def set_embedding_model(self,model_id : str , emmbeding_size :int):
        pass

    @abstractclassmethod
    def generate_text(self, prompt : str, chat_history : list = [] , max_output_tokens:int = None, temperature:float = None):
        pass

    @abstractclassmethod
    def emmbed_text(self , text : str , document_type = None):
        pass

    @abstractclassmethod
    def construct_prompt(self, prompt : str , role :str):
        pass