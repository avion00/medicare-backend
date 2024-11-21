import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from utils.db import get_db_connection
import openai
from flask import jsonify, request
from psycopg2.extras import RealDictCursor



IGNORE_EXTENSIONS = (
    '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg',
    '.ico', '.mp4', '.mp3', '.wav', '.avi', '.mov', '.pdf',
    '.zip', '.rar', '.tar', '.gz'
)

def is_valid_url(url, base_domain):
    parsed_url = urlparse(url)
    if parsed_url.netloc != base_domain:
        return False
    if any(url.lower().endswith(ext) for ext in IGNORE_EXTENSIONS):
        return False
    return True

def clean_text(soup):
    for script_or_style in soup(['script', 'style', 'meta', 'link']):
        script_or_style.decompose()
    text = soup.get_text(separator=' ', strip=True)
    return ' '.join(text.split())

def summarize_text(text, max_tokens=100):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a summarization assistant."},
                {"role": "user", "content": f"Summarize the following text:\n\n{text}"}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error summarizing text: {e}")
        return text[:max_tokens]  # Fallback to truncation if summarization fails


def crawl_major_pages(base_url, max_pages=5):
    """
    Crawl a website, extract content, and summarize it.

    Parameters:
    - base_url: The root URL to start crawling from.
    - max_pages: Maximum number of pages to crawl.

    Returns:
    - List of dictionaries with 'url' and 'summary' keys.
    """
    visited = set()  # To track visited URLs
    to_visit = [base_url]  # Queue of URLs to visit
    base_domain = urlparse(base_url).netloc  # Extract base domain
    all_summaries = []  # Store results as dictionaries

    while to_visit and len(visited) < max_pages:
        current_url = to_visit.pop(0)  # Get the next URL to crawl
        if current_url in visited:  # Skip if already visited
            continue
        visited.add(current_url)

        try:
            response = requests.get(current_url, timeout=10)
            response.raise_for_status()  # Raise an error for non-200 responses

            # Ensure the response contains HTML content
            if 'text/html' in response.headers.get('Content-Type', ''):
                soup = BeautifulSoup(response.text, 'html.parser')
                content = clean_text(soup)  # Clean text content from the page
                if content:
                    summary = summarize_text(content, max_tokens=100)
                    all_summaries.append({'url': current_url, 'summary': summary})

                # Extract valid links for further crawling
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    next_url = urljoin(base_url, href)  # Resolve relative URLs
                    if is_valid_url(next_url, base_domain):
                        next_url = next_url.split('#')[0]  # Remove fragment identifiers
                        if next_url not in visited:
                            to_visit.append(next_url)
        except requests.exceptions.RequestException as e:
            print(f"Error crawling {current_url}: {e}")

    return all_summaries



def save_summary_to_db(base_url, summaries, user_id):
    """
    Save crawled summaries combined into a single string to the database.

    Parameters:
    - base_url: The root URL that was crawled.
    - summaries: A list of dictionaries with 'url' and 'summary'.
    - user_id: The ID of the user requesting the crawl.
    """
    # Combine all summaries into one single string
    combined_summary = " ".join([summary['summary'] for summary in summaries])

    # Save the combined summary to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO knowledge_base (website_url, summary, user_id)
            VALUES (%s, %s, %s)
        ''', (base_url, combined_summary, user_id))

        conn.commit()  # Commit the transaction after the insert
    except Exception as e:
        print(f"Error saving combined summary to the database: {e}")
        conn.rollback()  # Rollback the transaction on error


def get_summaries(user_id):
    """
    Retrieve all summaries for the authenticated user from the knowledge base.

    Parameters:
    - user_id: The ID of the authenticated user.

    Returns:
    - JSON response containing the summaries.
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Fetch all summaries for the authenticated user
        cursor.execute('''
            SELECT * FROM knowledge_base WHERE user_id = %s
        ''', (user_id,))
        
        # Fetch all rows from the query
        rows = cursor.fetchall()

        # Check if there are any rows
        if not rows:
            return jsonify({'message': 'No summaries found for this user.'}), 404

        # Return the summaries as a JSON response
        return jsonify(rows), 200

    except Exception as e:
        # Handle any errors and return a 500 response
        return jsonify({'error': str(e)}), 500


def get_summary_by_website_id(user_id, website_id):
    """
    Retrieve a specific summary by website ID for the authenticated user.

    Parameters:
    - user_id: The ID of the authenticated user.
    - website_id: The ID of the website summary to retrieve.

    Returns:
    - JSON response containing the website summary.
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Fetch the summary for the given website_id and user_id
        cursor.execute('''
            SELECT * FROM knowledge_base
            WHERE id = %s AND user_id = %s
        ''', (website_id, user_id))

        # Fetch the single row (summary) from the query
        row = cursor.fetchone()

        # Check if a summary was found
        if not row:
            return jsonify({'message': 'Summary not found for this website.'}), 404

        # Return the summary as a JSON response
        return jsonify(row), 200

    except Exception as e:
        # Handle any errors and return a 500 response
        return jsonify({'error': str(e)}), 500

def clean_question(question):
    # Remove question mark and normalize whitespace
    question = question.strip().lower()
    question = re.sub(r'[^\w\s]', '', question)  # Remove punctuation (except spaces)
    return question


def chatbot(user_id):
    """
    Handles user queries, retrieves website knowledge and training data, 
    and generates a response using OpenAI's GPT model.

    Parameters:
    - user_id: The authenticated user ID.
    - website_id: The ID of the website from the knowledge base.
    - message: The user's query message.

    Returns:
    - JSON response with the chatbot's answer or an error message.
    """
    user_message = request.json.get('message')
    website_id = request.json.get('website_id')

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    # Retrieve knowledge base (summarized website content)
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the website summary from the knowledge base table
    cursor.execute('SELECT summary FROM knowledge_base WHERE id = %s', (website_id,))
    knowledge_base = cursor.fetchone()

    if not knowledge_base:
        conn.close()
        return jsonify({"error": "No knowledge base found for the given website."}), 404

    # Retrieve training data (questions & answers) for the specific website
    cursor.execute('SELECT question, answer FROM training_data WHERE website_id = %s', (website_id,))
    training_data = cursor.fetchall()

    # Retrieve the last 4 conversations from the conversation history
    cursor.execute('''
        SELECT user_message, assistant_response 
        FROM conversation_history 
        WHERE website_id = %s 
        ORDER BY id DESC LIMIT 4
    ''', (website_id,))
    conversation_history = cursor.fetchall()

    conn.close()

    # Clean the user input (optional function for preprocessing)
    cleaned_user_message = clean_question(user_message)

    # Check if the user message matches any of the questions in the training data
    matched_answer = None
    for question, answer in training_data:
        cleaned_question = clean_question(question)
        if cleaned_question == cleaned_user_message:  # Case-insensitive match
            matched_answer = answer
            break

    # If there's a matched answer in training data, use that as the response
    if matched_answer:
        return jsonify({"response": matched_answer})

    # Create context for OpenAI based on website summary and training data
    context = [{"role": "system", "content": 
                "You are a helpful chatbot that answers user queries based on the provided website knowledge."}]

    # Add website knowledge summary to the context
    context.append({"role": "assistant", "content": f"Website Knowledge: {knowledge_base[0]}"})

    # Add training data to the context (questions and answers)
    for question, answer in training_data:
        context.append({"role": "user", "content": f"Question: {question}"})
        context.append({"role": "assistant", "content": f"Answer: {answer}"})

    # Add the last 4 conversations to the context
    for user_msg, assistant_resp in reversed(conversation_history):
        context.append({"role": "user", "content": user_msg})
        context.append({"role": "assistant", "content": assistant_resp})

    # Add the current user message to the context
    context.append({"role": "user", "content": f"User asked: {user_message}"})

    # Generate response using OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=context,
        max_tokens=150,
        temperature=0.7
    )

    # Save this new conversation in the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert the conversation into the conversation_history table
    cursor.execute('''
        INSERT INTO conversation_history (website_id, user_message, assistant_response) 
        VALUES (%s, %s, %s)
    ''', (website_id, user_message, response['choices'][0]['message']['content'].strip()))
    conn.commit()
    conn.close()

    return jsonify({"response": response['choices'][0]['message']['content'].strip()})
