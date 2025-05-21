# Program to analyze a dataset, generate summary statistics, and create visualizations

import asyncio
import aiohttp
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import os
import google.generativeai as genai

GOOGLE_API_KEY = "AIzaSyAKbj_m5q8HQh8PHoEKxfGokT60oQ6BS6o"
CSV_URL = "https://people.sc.fsu.edu/~jburkardt/data/csv/hw_200.csv" # CSV file loaded directly from a URL instead of a local file path
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("models/gemini-1.5-pro") 

async def gemini_prompt(prompt: str):
    try:
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text
    except Exception as e:
        return f"[Gemini Error] {str(e)}"

# Agent - Datafetcher
class DataFetcherAgent:
    async def fetch_csv(self, url: str) -> pd.DataFrame:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                text = await response.text()
                return pd.read_csv(StringIO(text))

# Agent - Analyst
class AnalystAgent:
    def describe(self, df):
        return df.describe()

    def plot_histogram(self, df):
        df = df.select_dtypes(include='number')
        df.hist(figsize=(10, 8))
        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/histogram.png")

    async def analyze(self, df):
        description = self.describe(df)
        self.plot_histogram(df)
        summary_text = f"Summary Statistics:\n{description.to_string()}"
        gemini_summary = await gemini_prompt(f"Summarize this data:\n\n{description.to_string()}")
        return summary_text, gemini_summary

# RoundRobinGroupChat portion
class RoundRobinGroupChat:
    def __init__(self):
        self.fetcher = DataFetcherAgent()
        self.analyst = AnalystAgent()

    async def run(self, url):
        print("[1/3] Fetching CSV data...")
        df = await self.fetcher.fetch_csv(url)

        print("[2/3] Running analysis...")
        stats, gemini_insight = await self.analyst.analyze(df)

        print("[3/3] Analysis complete.\n")
        print(stats)
        print("\n--- Gemini Summary ---\n")
        print(gemini_insight)
        print(f"\nHistogram saved to `{OUTPUT_DIR}/histogram.png`")

async def main():
    orchestrator = RoundRobinGroupChat()
    await orchestrator.run(CSV_URL)

if __name__ == "__main__":
    asyncio.run(main())
