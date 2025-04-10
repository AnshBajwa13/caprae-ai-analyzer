# scraper.py
import requests
from bs4 import BeautifulSoup
import re
import sys
import os
import time
from urllib.parse import urljoin, urlparse # Added urlparse import
import traceback

# LangChain & Google Imports
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_community.tools.tavily_search import TavilySearchResults
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain_core.tools import Tool
    from langchain import hub
    import google.generativeai as genai
except ImportError:
    print("ERROR: Required libraries not found. Please run: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred during import: {e}")
    sys.exit(1)


# --- Constants ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
REQUEST_TIMEOUT = 15
EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
SOCIAL_DOMAINS = ['linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com', 'youtube.com'] # Refined Youtube domain check needed

# --- Core Scraping Functions ---

def fetch_page(url):
    """Fetches content for a given URL. Returns response object or None."""
    print(f"Attempting to fetch: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        response.raise_for_status()
        final_url = response.url
        print(f"Successfully fetched: {final_url} (Original: {url})")
        return response
    except requests.exceptions.Timeout:
        print(f"Error: Timeout fetching {url}", file=sys.stderr); return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr); return None
    except Exception as e:
        print(f"An unexpected error during fetch for {url}: {e}", file=sys.stderr); return None

def parse_html(response):
    """Parses HTML from a response object. Returns soup object or None."""
    if not response: return None
    try:
        soup = BeautifulSoup(response.content, 'lxml')
        return soup
    except Exception as e:
        print(f"Error parsing HTML for {response.url}: {e}", file=sys.stderr); return None

def find_relevant_links(soup, base_url):
    """Finds About, Contact, and Social links. Returns a dict."""
    links = {'about': None, 'contact': None, 'social': set()}
    if not soup: return links
    print("Searching for relevant links on page...")
    found_social_count = 0
    for link in soup.find_all('a', href=True):
        try:
            link_text = link.get_text().lower().strip()
            href = link.get('href', '') # Use get with default
            if not href or href.startswith(('javascript:', '#', 'tel:', 'mailto:')): continue

            full_url = urljoin(base_url, href)
            href_lower = href.lower()

            # Find About link
            is_about_link = ('about' in link_text or '/about' in href_lower or 'company' in link_text or 'who we are' in link_text or 'who-we-are' in href_lower) and not any(kw in href_lower for kw in ['blog', 'news', 'press', 'careers', 'jobs', 'events'])
            if not links['about'] and is_about_link:
                links['about'] = full_url
                print(f"  Found potential 'About Us' link: {full_url}")

            # Find Contact link
            if not links['contact'] and ('contact' in link_text or '/contact' in href_lower or 'get-in-touch' in href_lower or 'get in touch' in link_text or 'support' in link_text):
                links['contact'] = full_url
                print(f"  Found potential 'Contact Us' link: {full_url}")

            # Find Social links
            try:
                 domain_of_link = urlparse(full_url).netloc.replace('www.', '')
                 path_str = urlparse(full_url).path.lower()
                 is_social = False
                 if any(social_domain in domain_of_link for social_domain in SOCIAL_DOMAINS):
                    if not any(word in path_str for word in ['/share', '/intent', '/addtoany', '/login', '/post', '/status', '/jobs', '/careers', '/legal', '/privacy']):
                         # Check if path is minimal or user/company profile like
                         path_parts = [p for p in path_str.split('/') if p]
                         if len(path_parts) <= 2 or any(p in ['company', 'in', 'user', 'channel'] for p in path_parts):
                              is_social = True
                 if is_social and full_url not in links['social']:
                    links['social'].add(full_url); found_social_count +=1
            except Exception: pass # Ignore URL parsing errors

        except Exception as e: pass # Ignore errors processing individual links
    if found_social_count > 0: print(f"  Found {found_social_count} potential social media link(s).")
    return links

def extract_emails(soup):
    """Extracts unique email addresses from a soup object. Returns a set."""
    if not soup: return set()
    emails_found = set()
    try:
        # Look in text nodes only first, potentially more accurate
        text_nodes = soup.find_all(string=True)
        for text in text_nodes:
            emails_in_text = re.findall(EMAIL_REGEX, text)
            emails_found.update(set(emails_in_text))

        # Fallback: search within mailto links specifically
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if href.startswith('mailto:'):
                email_part = href[7:].split('?')[0]
                if re.fullmatch(EMAIL_REGEX, email_part): emails_found.add(email_part)

        if emails_found: print(f"  Found {len(emails_found)} unique email(s) on this page.")
    except Exception as e: print(f"Error extracting emails: {e}", file=sys.stderr)
    return emails_found

def extract_relevant_text(soup):
    """Extracts main text content. Returns string or None."""
    if not soup: return None
    print("Extracting relevant text...")
    text = None
    try:
        selectors = ['main', 'article', 'section[role="main"]', 'div[role="main"]', '.main-content', '#main-content', '.content', '#content']
        for selector in selectors:
             content_area = soup.select_one(selector)
             if content_area:
                  tag_text = content_area.get_text(separator=' ', strip=True)
                  if len(tag_text) > 200: # Increased min length for main content
                       text = tag_text
                       print(f"  Extracted text using selector: '{selector}'.")
                       break
        if not text: # Fallback
            body = soup.find('body')
            if body:
                 body_copy = BeautifulSoup(str(body), 'lxml').find('body')
                 for tag_name in ['nav', 'header', 'footer', 'script', 'style', 'aside', 'form', 'noscript', 'iframe', 'button', '.sidebar', '#sidebar']:
                      for tag in body_copy.select(tag_name): tag.decompose() # Use select for class/id
                 text = body_copy.get_text(separator=' ', strip=True)
                 print("  Warning: Used fallback text extraction from cleaned body.")
        if text: return ' '.join(text.split()) # Collapse whitespace
        else: print("  Warning: Could not extract relevant text."); return None
    except Exception as e: print(f"Error extracting relevant text: {e}", file=sys.stderr); return None

# --- AI Summarizer Function ---
def summarize_text(text_to_summarize, max_length=100):
    """Uses Gemini directly to summarize text concisely."""
    print("Attempting to summarize extracted text...")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key: return "API Key Error: GOOGLE_API_KEY not set."
    if not text_to_summarize or len(text_to_summarize) < 75: return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"Concisely summarize the following text about a company in 1-3 short sentences, focusing on its core business or purpose:\n\nTEXT:\n{text_to_summarize[:4000]}\n\nSUMMARY:"
        safety_settings=[ {"category": c, "threshold": "BLOCK_MEDIUM_AND_ABOVE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
        response = model.generate_content(prompt, safety_settings=safety_settings)

        if response.parts:
            summary = response.text.strip()
            print("Summary generated.")
            return summary
        else: print("Warning: Summarizer response was empty or blocked."); return None
    except Exception as e: print(f"Error during summarization API call: {e}", file=sys.stderr); return f"Error: {e}"

# --- AI Agent Function ---
_agent_executor = None # Global variable for agent executor cache

def get_agent_answer(agent_input_prompt):
    """Uses LangChain agent with Tavily search to answer a question based on input prompt."""
    global _agent_executor
    print("\n--- Invoking AI Agent ---")
    if _agent_executor is None:
        print("Initializing agent executor (one-time setup)...")
        google_api_key = os.getenv("GOOGLE_API_KEY")
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not google_api_key or not tavily_api_key: return "API Key Error: Ensure GOOGLE_API_KEY and TAVILY_API_KEY are set."
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2, convert_system_message_to_human=True, google_api_key=google_api_key)
            search_tool = TavilySearchResults(max_results=3, tavily_api_key=tavily_api_key)
            tools = [Tool(name="tavily_search_results_json", description="A search engine useful for finding current information about companies, news, competitors, funding, AUM, people, etc.", func=search_tool.invoke)]
            prompt_template = hub.pull("hwchase17/react")
            agent = create_react_agent(llm, tools, prompt_template)
            _agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors="Check your output and make sure it conforms!", max_iterations=8) # Keep iterations=8
            print("Agent executor initialized.")
        except Exception as e: return f"Error initializing AI Agent: {e}"
    try:
        print(f"Invoking agent...")
        if not os.getenv("LANGCHAIN_API_KEY"):
             os.environ["LANGCHAIN_TRACING_V2"] = "false"
        response = _agent_executor.invoke({"input": agent_input_prompt})
        print("Agent finished execution.")
        return response.get("output", "Agent did not provide an output.")
    except Exception as e:
        print(f"Error during LangChain Agent execution: {e}", file=sys.stderr); traceback.print_exc()
        return f"Error during AI Agent processing: {e}"

# --- Scraping Orchestrator ---
def run_scraping_only(target_url):
    """Orchestrates ONLY the scraping process. Returns results dict including 'about_summary'."""
    start_time = time.time()
    results = { 'url': target_url, 'title': 'N/A', 'emails': set(), 'social_links': set(), 'about_text': None, 'about_summary': None, 'technologies': set(), 'processing_time': 0 }

    print("\n--- Processing Homepage ---")
    homepage_response = fetch_page(target_url)
    homepage_soup = parse_html(homepage_response)

    if not homepage_soup:
        print("Failed to fetch or parse the homepage.")
        results['processing_time'] = time.time() - start_time
        return results

    results['title'] = homepage_soup.title.string.strip() if homepage_soup.title and homepage_soup.title.string else "N/A"
    results['emails'].update(extract_emails(homepage_soup))
    links_dict = find_relevant_links(homepage_soup, target_url)
    results['social_links'] = links_dict['social']

    # results['technologies'] = identify_technologies(homepage_response.text if homepage_response else "") 

    about_url = links_dict.get('about')
    if about_url:
        print("\n--- Processing About Page ---")
        about_response = fetch_page(about_url)
        about_soup = parse_html(about_response)
        if about_soup:
            results['about_text'] = extract_relevant_text(about_soup)
            if results['about_text']:
                 results['about_summary'] = summarize_text(results['about_text'])
            results['emails'].update(extract_emails(about_soup))
    else: print("\n--- Skipping About Page (No link found) ---")

    contact_url = links_dict.get('contact')
    if contact_url:
         print("\n--- Processing Contact Page ---")
         contact_response = fetch_page(contact_url)
         contact_soup = parse_html(contact_response)
         if contact_soup: results['emails'].update(extract_emails(contact_soup))
    else: print("\n--- Skipping Contact Page (No link found) ---")

    results['processing_time'] = time.time() - start_time
    print(f"Scraping finished in {results['processing_time']:.2f} seconds.")
    return results