# app.py
import streamlit as st
import pandas as pd
import os
import time
import re
from urllib.parse import urlparse 
try:
    from scraper import run_scraping_only, get_agent_answer
except ImportError as e:
    st.error(f"Error importing from scraper.py: {e}. Make sure scraper.py is updated and in the same folder.")
    st.stop()
except Exception as e:
    st.error(f"An unexpected error occurred during import: {e}")
    st.stop()

# --- Helper Function for Clean Name ---
def get_clean_company_name(title, url):
    """Attempts to extract a cleaner company name from the page title."""
    if title and title != 'N/A':
        try:
            # Split by common separators like |, –, -, :
            # Prioritize splitting by | first as it often separates name from slogan
            potential_names = re.split(r' \| | – | - | : ', title)

            # Filter out generic terms and very short parts
            generic_terms = ['home', 'welcome', 'official site', 'website', 'log in', 'login']
            significant_parts = [
                p.strip() for p in potential_names
                if p.strip().lower() not in generic_terms and len(p.strip()) > 3
            ]

            if significant_parts:
                # Often the first significant part is the name, but sometimes it's the last
                # Let's return the first one for now, but this could be refined further
                name = significant_parts[0]
                # Remove common legal suffixes AFTER selecting the part
                common_suffixes = [' Inc.', ' LLC', ' Ltd.', ' Corp.', ' Corporation', ' Limited', ' GmbH', ' PLC', '.com', '.org', '.net']
                for suffix in common_suffixes: name = name.replace(suffix, '')
                return name.strip() # Return the cleaned significant part

        except Exception as e:
             print(f"Error cleaning title: {e}") # Log error if cleaning fails

    # Fallback: Use formatted domain name if title cleaning failed or title was bad
    try:
        domain = urlparse(url).netloc.replace('www.', '')
        # Take only the main part before the TLD (e.g., 'tower-research' from 'tower-research.com')
        domain_part = domain.split('.')[0]
        # Format it nicely
        return domain_part.replace('-', ' ').title()
    except:
        return url # Absolute fallback is the original URL


# --- Page Configuration ---
st.set_page_config(page_title="AI Website Analyzer", page_icon="🔍", layout="wide")

# --- App Title ---
st.title("AI-Enhanced Website Analyzer 🚀")
st.markdown("""
Enter a website URL to analyze.
1.  **Analyze & Show Details:** Scrapes the site for info (Title, Emails, Social Links, Text Summary) and displays it. Then allows asking the AI Agent questions.
2.  **Ask AI Question Directly:** Scrapes site context in the background and immediately lets you ask the AI Agent questions (using context + web search).
""")
st.markdown("---")

# --- Initialize Session State ---
if 'mode' not in st.session_state: st.session_state['mode'] = None
if 'scrape_results' not in st.session_state: st.session_state['scrape_results'] = None
if 'analyzed_url' not in st.session_state: st.session_state['analyzed_url'] = ""
if 'latest_ai_answer' not in st.session_state: st.session_state['latest_ai_answer'] = None
if 'last_ai_question' not in st.session_state: st.session_state['last_ai_question'] = ""
if 'context_for_ai_direct' not in st.session_state: st.session_state['context_for_ai_direct'] = None
if 'title_for_ai_direct' not in st.session_state: st.session_state['title_for_ai_direct'] = None

# --- Input Section ---
url_input = st.text_input("Enter Website URL:", placeholder="e.g., https://www.example.com", key="url_input_key")

# --- Action Buttons ---
col1_btn, col2_btn = st.columns(2)
with col1_btn: analyze_button = st.button("Analyze & Show Scraped Details", key="analyze_btn")
with col2_btn: ask_ai_direct_button = st.button("Ask AI Question Directly", key="ask_ai_btn")

# --- Processing Logic ---

if analyze_button and url_input:
    if not url_input.startswith('http://') and not url_input.startswith('https://'): st.error("Please enter a valid URL.")
    else:
        with st.spinner(f"Analyzing {url_input}..."):
            try:
                results_dict = run_scraping_only(url_input)
                st.session_state['scrape_results'] = results_dict
                st.session_state['analyzed_url'] = url_input
                st.session_state['mode'] = 'show_details'
                st.session_state['latest_ai_answer'] = None; st.session_state['last_ai_question'] = ""
                st.success("Analysis complete!")
                st.rerun()
            except Exception as e: st.error(f"Scraping error: {e}"); st.session_state.clear();

if ask_ai_direct_button and url_input:
    if not url_input.startswith('http://') and not url_input.startswith('https://'): st.error("Please enter a valid URL.")
    else:
        with st.spinner(f"Preparing context for AI from {url_input}..."):
            try:
                temp_results = run_scraping_only(url_input)
                st.session_state['context_for_ai_direct'] = temp_results.get('about_text')
                st.session_state['analyzed_url'] = url_input
                st.session_state['title_for_ai_direct'] = temp_results.get('title', url_input)
                st.session_state['scrape_results'] = None # Don't show full results
                st.session_state['mode'] = 'ask_ai_direct'
                st.session_state['latest_ai_answer'] = None; st.session_state['last_ai_question'] = ""
                # st.session_state['chat_history'] = [] # Reset history removed
                st.info("Context prepared. Enter question below.")
                st.rerun()
            except Exception as e: st.error(f"Context prep error: {e}"); st.session_state.clear();

# --- Display Area Based on Mode ---
current_mode = st.session_state.get('mode')

# --- Shared AI Q&A Logic (Function to avoid repetition) ---
def handle_ai_question(mode_key_suffix):
    """Handles input and execution for AI questions (single-shot)."""
    st.markdown("---")
    display_name_ai = "this Company"
    url_for_ai_context = st.session_state.get('analyzed_url', '')
    context_text_for_ai = None

    if current_mode == 'show_details' and st.session_state.get('scrape_results'):
        title_display = st.session_state['scrape_results'].get('title', 'N/A')
        display_name_ai = get_clean_company_name(title_display, url_for_ai_context)
        context_text_for_ai = st.session_state['scrape_results'].get('about_text')
    elif current_mode == 'ask_ai_direct':
        title_for_header_raw = st.session_state.get('title_for_ai_direct', url_for_ai_context)
        display_name_ai = get_clean_company_name(title_for_header_raw, url_for_ai_context)
        context_text_for_ai = st.session_state.get('context_for_ai_direct')

    st.subheader(f"💬 Ask AI Agent about: {display_name_ai}")


    ai_question_input = st.text_input(
        "Enter your question:",
        key=f"ai_question_input_{mode_key_suffix}",
        placeholder="e.g., Who are key executives? Main services? Recent news?"
        )
    ask_ai_button = st.button("Ask AI Agent", key=f"ask_ai_button_{mode_key_suffix}")

    if ask_ai_button and ai_question_input:
        with st.spinner("AI Agent is thinking..."):
             try:
                
                if context_text_for_ai and len(context_text_for_ai) > 50:
                     agent_input_prompt = f"""You have the following CONTEXT scraped from {url_for_ai_context}. Answer the user's QUESTION comprehensively. Use your search tool if needed for information not in the CONTEXT or for recent details (like news, filings, personnel changes). If standard reports (like 10-Q) are requested for a private entity, check for alternative filings (like 13F) via search. After answering, state clearly if the answer came primarily from CONTEXT or web search. If search was used, try to cite 1-2 main source URLs. If answer not found, say so.

                     CONTEXT: {context_text_for_ai[:3000]}

                     QUESTION: {ai_question_input}"""
                else: # No context
                     agent_input_prompt = f"Answer the following question using web search regarding the company associated with {url_for_ai_context}: {ai_question_input}. After answering, state that web search was used and try to cite 1-2 main source URLs."

                # Call agent (ensure get_agent_answer is imported)
                ai_answer = get_agent_answer(agent_input_prompt)

                # Store only the latest Q&A for immediate display
                st.session_state['latest_ai_answer'] = ai_answer
                st.session_state['last_ai_question'] = ai_question_input

                st.rerun() # Rerun to display the new answer

             except Exception as e:
                 st.error(f"An error occurred during AI processing: {e}")
                 st.session_state['latest_ai_answer'] = f"Error during AI processing: {e}"
                 st.session_state['last_ai_question'] = ai_question_input
                 st.rerun()

    # Display ONLY the latest AI Q&A below the button
    if st.session_state.get('latest_ai_answer'):
        st.markdown("**Last Question Asked:**")
        st.write(st.session_state.get('last_ai_question', ''))
        st.markdown("**AI Agent Answer:**")
        if "Error:" in str(st.session_state['latest_ai_answer']):
            st.error(st.session_state['latest_ai_answer'])
        else:
            st.info(st.session_state['latest_ai_answer'])


# --- Mode 1: Show Full Scraped Details + AI Section ---
if current_mode == 'show_details' and st.session_state.get('scrape_results'):
    results = st.session_state['scrape_results']
    analyzed_url = st.session_state['analyzed_url']

    st.divider()
    title_display = results.get('title', 'N/A')
    display_name_header = get_clean_company_name(title_display, analyzed_url)
    st.header(f"Results for: {display_name_header}")
    st.caption(f"Source URL: {analyzed_url} | Scraping Time: {results.get('processing_time', 0):.2f} seconds")

    # Display AI Summary
    summary = results.get('about_summary')
    if summary and "Error" not in summary : st.success(f"**AI Generated Summary:** {summary}")
    elif summary: st.warning(f"AI Summary Error: {summary}")
    st.markdown("---")

    # Scraped Data Expanders
    col1_res, col2_res = st.columns(2)
    with col1_res:
        emails = results.get('emails', set())
        with st.expander(f"📧 Emails ({len(emails)})", expanded=len(emails) > 0):
            if emails:
                 for email in sorted(list(emails)): st.markdown(f"[{email}](mailto:{email})")
            else: st.caption("None found")
        social_links = results.get('social_links', set())
        with st.expander(f"🔗 Social Links ({len(social_links)})", expanded=len(social_links) > 0):
            if social_links:
                 for link in sorted(list(social_links)): st.markdown(f"[{link}]({link})")
            else: st.caption("None found")

    with col2_res:
        about_text_display = results.get('about_text')
        with st.expander("📄 Extracted Context Text", expanded=False):
            if about_text_display: st.text_area("Raw Scraped Content", about_text_display[:3000]+"..." if len(about_text_display)>3000 else about_text_display, height=150, key="about_text_area_display", disabled=True)
            else: st.caption("Not extracted.")
        # CSV Download Button
        st.divider()
        try:
            export_data = { 'url': analyzed_url, 'title': results.get('title', ''), 'ai_summary': results.get('about_summary', ''), 'emails': "; ".join(sorted(list(emails))), 'social_links': "; ".join(sorted(list(social_links))), 'raw_about_text': about_text_display }
            df = pd.DataFrame([export_data]); csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(label="Download Scraped Data as CSV", data=csv, file_name=f"scraped_{display_name_header.replace(' ','_')}.csv", mime='text/csv', key='download-csv-details')
        except Exception as e: st.error(f"Error generating CSV: {e}")

    # --- Call Shared AI Q&A Logic ---
    handle_ai_question("details")


# --- Mode 2: Ask AI Directly ---
elif current_mode == 'ask_ai_direct':
    st.divider()
    title_for_header_raw = st.session_state.get('title_for_ai_direct', st.session_state.get('analyzed_url', 'this company'))
    url_for_header = st.session_state.get('analyzed_url', '')
    display_name_header = get_clean_company_name(title_for_header_raw, url_for_header)
    st.header(f"Ask AI Agent about: {display_name_header}")

    # --- Call Shared AI Q&A Logic ---
    handle_ai_question("direct")


# --- Initial State ---
elif not analyze_button and not ask_ai_direct_button and current_mode is None:
    st.info("Enter a website URL above and choose an action.")
