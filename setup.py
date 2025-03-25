from setuptools import setup, find_packages

setup(
    name="learni",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "langchain-core",
        "langchain-google-genai",
        "langchain-community",
        "python-dotenv",
        "pydantic",
        "cryptography",
        "langsmith"
    ],
    python_requires=">=3.8",
) 