# Program to build FAQ Chatbot with RAG

import asyncio
import chromadb
import google.generativeai as genai
from chromadb.utils.embedding_functions import GoogleGenerativeAiEmbeddingFunction

GOOGLE_API_KEY = "AIzaSyAKbj_m5q8HQh8PHoEKxfGokT60oQ6BS6o"

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

embedding_function = GoogleGenerativeAiEmbeddingFunction(api_key=GOOGLE_API_KEY)
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="faq", embedding_function=embedding_function)

# Add initial FAQs to the vector database
faq_data = {
    "What is RAG?": "Retrieval-Augmented Generation (RAG) combines retrieval with generation for better responses.",
    "How does ChromaDB work?": "ChromaDB is a vector database that stores and retrieves text via embeddings.",
    "What is Gemini API?": "Gemini is Google's Generative AI model that powers chat and generation tasks."
}

for question, answer in faq_data.items():
    collection.add(documents=[answer], ids=[question])

# Agent - RAG Retriever
class RAGRetriever:
    def __init__(self, collection):
        self.collection = collection

    async def retrieve(self, query):
        results = self.collection.query(query_texts=[query], n_results=1)
        return results['documents'][0][0] if results['documents'] else ""

# Agent - Query Handler
class QueryHandler:
    def __init__(self, model, retriever):
        self.model = model
        self.retriever = retriever

    async def handle_query(self, query):
        context = await self.retriever.retrieve(query)
        prompt = f"Context: {context}\n\nQuestion: {query}\nAnswer:"
        response = self.model.generate_content(prompt)
        return response.text.strip()

# RoundRobinGroupChat
class RoundRobinGroupChat:
    def __init__(self, agents):
        self.agents = agents
        self.index = 0

    async def ask(self, query):
        agent = self.agents[self.index]
        self.index = (self.index + 1) % len(self.agents)
        return await agent.handle_query(query)

async def main():
    retriever = RAGRetriever(collection)
    query_handler = QueryHandler(model, retriever)
    group_chat = RoundRobinGroupChat([query_handler])

    print("FAQ Chatbot (type 'exit' to quit):")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
        answer = await group_chat.ask(user_input)
        print("Bot:", answer)

if __name__ == "__main__":
    asyncio.run(main())
