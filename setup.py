"""
TgCF Pro - Enterprise Setup Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Professional package setup configuration for enterprise deployment
and distribution of TgCF Pro automation platform.

Author: TgCF Pro Team
License: MIT
Version: 1.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from setuptools import setup, find_packages

setup(
    name="tgcf-pro",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "python-telegram-bot>=20.7",
        "telethon>=1.34",
        "python-dotenv>=1.0.0",
        "flask>=3.0.0",
        "gunicorn>=21.2.0",
        "aiohttp>=3.9.1",
        "schedule>=1.2.0",
        "Pillow>=10.1.0",
        "opencv-python-headless>=4.8.1",
        "pytesseract>=0.3.10",
        "ffmpeg-python>=0.2.0",
    ],
    author="TgCF Pro Team",
    author_email="support@tgcfpro.com",
    description="Enterprise Telegram Automation Platform for Business Communications",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/tgcf-pro/enterprise-bot",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Office/Business",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="telegram automation bot business enterprise campaign marketing",
    python_requires=">=3.11",
    project_urls={
        "Documentation": "https://docs.tgcfpro.com",
        "Source": "https://github.com/tgcf-pro/enterprise-bot",
        "Tracker": "https://github.com/tgcf-pro/enterprise-bot/issues",
    },
)