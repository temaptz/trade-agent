"""
Setup script for Bitcoin Trading Agent
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="bitcoin-trading-agent",
    version="1.0.0",
    author="AI Trading Team",
    author_email="trading@example.com",
    description="Advanced AI agent for Bitcoin trading on Bybit using LangGraph, LangChain, and Ollama",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/bitcoin-trading-agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "monitoring": [
            "psutil>=5.9.0",
            "prometheus-client>=0.17.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "bitcoin-trading-agent=main:main",
            "btc-agent=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
    project_urls={
        "Bug Reports": "https://github.com/example/bitcoin-trading-agent/issues",
        "Source": "https://github.com/example/bitcoin-trading-agent",
        "Documentation": "https://github.com/example/bitcoin-trading-agent/wiki",
    },
)