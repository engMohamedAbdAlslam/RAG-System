### RAG Prompts ###
from string import Template


system_prompt = Template("\n".join([
    "You are a helpful AI assistant answering user questions using retrieved documents.",
    "Your goal is to give a clear, natural, human-like answer — not a document summary.",
    "Rules:",
    "- Use simple and fluent language",
    "- Answer directly without mentioning documents or sources",
    "- Do not copy text verbatim from the documents",
    "- Combine relevant information into a coherent answer",
    "- Ignore irrelevant or noisy text",
    "- Be concise and precise",
    "- Write the answer in the same language as the user's query"
]))
### Document prompt ###
document_prompt = Template("\n".join([
    "[Document $doc_num]",
    "$chunk_text"
]))

### Footer ###

footer_prompt = Template("\n".join([
    "User question: $query",
    "",
    "Answer guidelines:",
    "- Start with a short introductory sentence",
    "- Then list the key points as bullet points",
    "- Use clear and simple language",
    "- Limit the answer to 3–5 bullet points",
    "",
    "Answer:"
]))
