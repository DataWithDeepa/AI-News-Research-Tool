from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv

load_dotenv()

def summarize_news(user_query, articles_text, extra_context="", language="en"):
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in .env")

    llm = ChatGroq(
        groq_api_key=groq_api_key,
        model_name="llama-3.3-70b-versatile",  # Latest working model
        temperature=0.3,
        max_tokens=4096
    )

    lang_instruction = {
        "en": "Write in clear professional English.",
        "hi": "पूरी समरी सरल हिंदी में लिखें।",
        "mr": "सारांश सोपी मराठीत लिहा."
    }.get(language, "Write in clear English.")

    system_prompt = f"""
You are a senior financial research analyst.
{lang_instruction}
Create a concise 4-7 paragraph summary focusing on key facts, implications, risks, and drivers.
"""

    human_prompt = """
Query: {user_query}

News: {articles_text}

Documents: {extra_context}

Write professional research summary.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({
        "user_query": user_query,
        "articles_text": articles_text,
        "extra_context": extra_context
    })