
"""Setup script for multimodal RAG agents."""

from setuptools import setup, find_packages

setup(
    name="rag-agents",
    version="0.1.0",
    description="Multimodal RAG agents system",
    author="RAG Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "openai>=1.0.0",
        "instructor>=0.3.0",
        "astrapy>=0.7.0",
        "voyageai>=0.1.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.0.0",
        "tqdm>=4.64.0",
    ],
    extras_require={
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
        ],
        "dev": [
            "ruff>=0.1.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
