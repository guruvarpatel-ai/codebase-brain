from setuptools import setup, find_packages

setup(
    name="codebase-brain",
    version="0.3.1",
    description="An AI brain that lives inside your codebase",
    package_dir={"": "."},
    packages=find_packages(where="."),
    install_requires=[
        "watchdog",
        "networkx",
        "matplotlib",
        "pyvis",
        "groq",
        "tree-sitter",
        "tree-sitter-python",
        "tree-sitter-javascript",
        "tree-sitter-java",
        "tree-sitter-typescript",
        "python-dotenv",
    ],
    py_modules=["brain_cli"],
    entry_points={
        "console_scripts": [
            "brain=brain_cli:main",
        ],
    },
    python_requires=">=3.8",
)