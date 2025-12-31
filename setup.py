# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


setup(
    name="shopify_sdk",
    version="0.1.6",
    author="Pk whiting",
    author_email="patten.whiting@gmail.com",
    description="An updated OO Sdk for Shopify GQL",
    url="https://github.com/Pikt-inc/Shopify",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
