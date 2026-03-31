from setuptools import setup, find_packages
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="validkit",
    version="1.2.0",
    author="ValidKit",
    author_email="developers@validkit.com",
    description="Python SDK for ValidKit Email Verification API - Built for AI Agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ValidKit/validkit-python-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Email",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: AsyncIO",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "flake8>=6.0.0",
        ]
    },
    keywords="email verification validation api async ai agents batch",
    project_urls={
        "Documentation": "https://docs.validkit.com/sdks/python",
        "PyPI": "https://pypi.org/project/validkit/",
        "Homepage": "https://validkit.com",
        "Source": "https://github.com/ValidKit/validkit-python-sdk",
        "Bug Tracker": "https://github.com/ValidKit/validkit-python-sdk/issues",
    },
)