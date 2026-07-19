# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


with open("README.md", encoding="utf-8") as readme_file:
    long_description = readme_file.read()


setup(
    name="shopify_sdk",
    version="0.3.14",
    author="Patten Whiting",
    author_email="patten.whiting@gmail.com",
    description="Typed Python SDK for the Shopify Admin GraphQL API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Pikt-inc/Shopify",
    project_urls={
        "Documentation": "https://github.com/Pikt-inc/Shopify#readme",
        "Source": "https://github.com/Pikt-inc/Shopify",
        "Issues": "https://github.com/Pikt-inc/Shopify/issues",
    },
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.6.0,<3.0.0",
        "python-dotenv>=1.0.0,<2.0.0",
        "requests>=2.31.0,<3.0.0",
    ],
    extras_require={
        "dev": [
            "mypy>=1.11.0",
            "pytest>=8.0.0",
            "ruff>=0.0.289",
            "types-requests>=2.32.0.20240622",
            "types-urllib3>=1.26.25.14",
            "vulture",
        ],
    },
    license="MIT",
    keywords=[
        "shopify",
        "graphql",
        "sdk",
        "pydantic",
        "ecommerce",
        "admin-api",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.10",
)
