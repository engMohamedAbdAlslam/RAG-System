from typing import Optional
from .LLMEnum import LLMEnum
from .LLLMInterface import LLMInterface
from .providers import OpenAIProvider, CoHereProvider


class LLMProviderFactory:
    def __init__(self, config):
        self.config = config

    def create(self, provider: LLMEnum) -> Optional[LLMInterface]:

        if provider == LLMEnum.OPENAI:
            return OpenAIProvider(
                api_key=self.config.OPENAI_API_KEY,
                api_url=self.config.OPENAI_API_URL,
                default_input_max_chars=self.config.INPUT_DAFAULT_MAX_CHARACTERS,
                default_output_max_tokens=self.config.GENERATION_DAFAULT_MAX_TOKENS,
                default_temperature=self.config.GENERATION_DAFAULT_TEMPERATURE
            )

        if provider == LLMEnum.COHERE.value:
            return CoHereProvider(
                api_key=self.config.COHERE_API_KEY,
                default_input_max_chars=self.config.INPUT_DAFAULT_MAX_CHARACTERS,
                default_output_max_tokens=self.config.GENERATION_DAFAULT_MAX_TOKENS,
                default_temperature=self.config.GENERATION_DAFAULT_TEMPERATURE
            )

        return None
