# AI-Enhanced Website Analyzer for Acquisition Screening

[![Status](https://img.shields.io/badge/status-prototype-yellow)](https://shields.io/)

## Introduction

This tool was developed as part of the pre-work assignment for the Caprae Capital internship program. Inspired by lead generation concepts and Caprae's focus on leveraging AI for M&A and empowering acquisition entrepreneurs, this application analyzes a company's website to provide quick insights for initial screening. It scrapes key data points and utilizes a Generative AI agent (powered by Google Gemini and Tavily Search via LangChain) to answer specific user questions about the target company.

## Features

* **Website Scraping:** Analyzes Homepage, About Us, and Contact Us pages (if found).
* **Data Extracted:**
    * Page Title
    * Contact Emails (from text and `mailto:` links)
    * Social Media Links (LinkedIn, Facebook, Twitter/X, Instagram, YouTube)
    * Main descriptive text content (from About Us or main body)
* **AI-Generated Summary:** Provides a concise (1-3 sentence) summary of the scraped descriptive text using Gemini Flash.
* **AI Agent Q&A:** Answers user questions about the company using:
    * Scraped website text as primary context.
    * Tavily web search as a fallback or for external/recent information.
    * Attempts to cite source (Context vs. Web Search).
* **Interactive UI:** nteractive Streamlit UI with two modes:
    * *Analyze & Show Details:* Displays all scraped data + AI Summary first, then allows AI Q&A.
    * *Ask AI Question Directly:* Scrapes context in the background and goes straight to AI Q&A.
* **Clickable Links:** Emails (`mailto:`) and Social Media links are clickable in the UI.
* **CSV Export:** Allows downloading scraped data (including AI Summary) as a CSV file.

## Tech Stack

* **Language:** Python 3.9+
* **Web Scraping:** `requests`, `BeautifulSoup4` (`lxml` parser)
* **Web Framework:** `Streamlit`
* **AI Agent Framework:** `LangChain`
* **LLM:** Google Gemini Pro (via `langchain-google-genai`)
* **Web Search:** Tavily Search API (via `langchain-tavily`)
* **Data Handling:** `pandas` (for CSV export)
* **Utilities:** `os`, `time`, `re`, `urllib`

## Setup Instructions

1.  **Prerequisites:**
    * Python (version 3.9 or higher recommended)
    * Git
2.  **Clone Repository:**
    ```bash
    git clone <your_github_repo_url>
    cd <your_repo_name>
    ```
3.  **Create Virtual Environment:**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS / Linux
    python3 -m venv venv
    source venv/bin/activate
    ```
4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **API Key Setup (CRITICAL):**
    This tool requires API keys for Google Gemini and Tavily Search to function.
    * **Google Gemini API Key:** Obtain from [Google AI Studio](https://aistudio.google.com/) or your Google Cloud Console project.
    * **Tavily API Key:** Obtain from [Tavily AI](https://tavily.com/) (free tier available).
    * **Set Environment Variables:** You **MUST** set these keys as environment variables **before** running the application. **DO NOT paste your keys directly into the code.**
        * **Windows (Command Prompt):**
            ```cmd
            set GOOGLE_API_KEY=YOUR_GEMINI_API_KEY
            set TAVILY_API_KEY=YOUR_TAVILY_API_KEY
            ```
            (Use `setx` for permanent setting, requires new terminal)
        * **Windows (PowerShell):**
            ```powershell
            $env:GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
            $env:TAVILY_API_KEY="YOUR_TAVILY_API_KEY"
            ```
        * **macOS / Linux (Bash/Zsh):**
            ```bash
            export GOOGLE_API_KEY='YOUR_GEMINI_API_KEY'
            export TAVILY_API_KEY='YOUR_TAVILY_API_KEY'
            ```
            (Add these export lines to your `.bashrc`, `.zshrc`, or `.profile` for persistence across terminal sessions).

## How to Run

1.  Ensure your virtual environment is activated and API keys are set.
2.  Run the Streamlit application from your terminal:
    ```bash
    streamlit run app.py
    ```
3.  The application will open in your web browser.
4.  Enter a target website URL (e.g., `https://www.capraecapital.com/`).
5.  Choose either "Analyze & Show Scraped Details" or "Ask AI Question Directly".
6.  Interact with the results or the AI Agent Q&A section.

## Limitations

* Web scraping may fail on websites heavily reliant on JavaScript for rendering content or those with strong anti-scraping protections (like Cloudflare).
* The quality of extracted text (`about_text`) varies depending on website structure; the AI Summary and Agent answers depend on this quality.
* The AI Agent's performance depends on the LLM (eg.I used Gemini-2.0-flash), the quality of Tavily search results, and the complexity of the question. Answers may occasionally be inaccurate, incomplete, or fail safety checks.
* Source citation by the AI Agent is experimental and may not always be accurate or comprehensive.
* The Q&A feature is single-turn per query (it doesn't maintain conversational memory across multiple separate clicks of the "Ask AI Agent" button *after the page reruns*). [NOTE: Earlier I attached history feature , now removed the complex history feature].
* Requires users to provide their own API keys. Free tier limits for APIs may apply.

## Future Improvements (Optional)

* Implement Technology Identification feature.
* Add multi-round conversational memory to the AI Agent.
* More robust scraping techniques (e.g., using Selenium for JS-heavy sites).
* Direct Google Sheets export option.

