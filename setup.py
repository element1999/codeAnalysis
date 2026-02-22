from setuptools import setup, find_packages

setup(
    name="codemind",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.0.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "pyyaml>=6.0",
        "chromadb>=0.4.0",
        "fastembed>=0.2.0",
        "openai>=1.0.0",
        "tree-sitter>=0.20.0",
        "tree-sitter-python>=0.20.0",
        "aiofiles>=23.0.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "codemind=codemind.main:app",
        ],
    },
    author="CodeMind Team",
    author_email="contact@codemind.dev",
    description="AI-powered code understanding and documentation tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/codemind-dev/codemind",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)