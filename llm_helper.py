from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os

load_dotenv()

llm = ChatGroq(api_key = os.getenv("GORQ_API_KEY"), model = "llama-3.3-70b-versatile")

if __name__ == "__main__":
    response = llm.invoke("who are you and what is your purpose. ans in only one line")
    print(response.content)
