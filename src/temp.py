from dotenv import load_dotenv, find_dotenv
import sys
import os

load_dotenv(find_dotenv())

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.core.graph import CodeGenGraph


if __name__ == "__main__":
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())
    code_gen = CodeGenGraph(
        model = "gemini-2.0-flash-lite",
        temperature = 0.0
    )
    output = code_gen.run("Write a function to calculate the sum of two numbers")
    print(output)