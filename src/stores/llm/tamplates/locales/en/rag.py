### RAG Prompts ###
from string import Template


system_prompt =Template("\n".join(["you are an assistant to generate a response for the user.",
                "you will be provided by a set of documents associated with the user query.",
                "you have to generate the response based on the documents provided.",
                "Ignore the documents that are not relevant to the user's query.",
                "you can applogize the user if you can not generate a response",
                "Be polite and respectful to the user.",
                "you have to generate response in the same languge as the user's query",
                "Be precise in your response"]
))
### Document prompt ###
document_prompt  = Template("\n".join([
    " ## document no : $doc_num",
    "## content : $chunk_text"
]))

### Footer ###

footer_prompt = Template("\n".join(
    ["Based on the above documents , please generate an answer for the user.",
     "## query :$query",
     "## Answer:"]
))