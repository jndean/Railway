from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name="railway",
    version="1.0.0",
    description="A time-and-memory-linearly reversible imperative "
                "programming language",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jndean/railway",
    packages=find_packages(),
    python_requires='>=3.8',
    entry_points={
        "console_scripts": [
            "railway = lib:run"
        ]
    }
)
