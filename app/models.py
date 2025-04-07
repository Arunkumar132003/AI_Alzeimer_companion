import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.pydantic_v1 import BaseModel, Field
from dotenv import load_dotenv  
load_dotenv()

class MemoryRecallResponseValidation(BaseModel):
    is_correct: bool = Field(description="Validate if the user answer is correct or not")

class MemoryRecallQuestionandAnswer(BaseModel):
    question: str = Field(description="A simple and familiar question designed to stimulate memory recall.")
    answer: str = Field(description="The correct and concise answer to the question")

def load_model():
    llm= ChatGoogleGenerativeAI(
      model= 'gemini-1.5-flash',
      api_key= os.getenv("GEMINI_API_KEY")
    )
    return llm 

def invoke_model(prompt, validation_class):
    llm= load_model()
    model = llm.with_structured_output(validation_class)
    response = model.invoke(prompt)
    return response