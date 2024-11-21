from flask import Flask, request, jsonify
from auth import register_user, login_user, token_required, set_password, reset_request
from utils.db import init_db, fetch_knowledge_base
from utils.jwt_utils import decode_access_token
from web_crawler import save_summary_to_db, crawl_major_pages, get_summaries, get_summary_by_website_id, chatbot


app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    return register_user()

@app.route('/login', methods=['POST'])
def login():
    return login_user()


#for password reset
@app.route('/request_password_reset', methods=['POST'])
def request_password_reset():
    response = reset_request()
    return response



@app.route('/reset_password', methods=['POST'])
def reset_password():
    respone = set_password()
    return respone


@app.route('/crawl', methods=['POST'])
@token_required
def crawl(user_id):
    data = request.get_json()
    base_url = data.get('base_url')
    max_pages = data.get('max_pages', 5)

    if not base_url:
        return jsonify({'error': 'base_url is required'}), 400

    try:
        summaries = crawl_major_pages(base_url, max_pages)
        save_summary_to_db(base_url, summaries, user_id)
        return jsonify({'message': 'Crawling completed', 'data': summaries})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/summaries', methods=['GET'])
@token_required
def get_summaries_route(user_id):
    response = get_summaries(user_id)
    return response


@app.route('/summary/<int:website_id>', methods=['GET'])
@token_required
def get_summary_route_by_website_id(user_id, website_id):
    respone = get_summary_by_website_id(user_id, website_id)
    return respone


@app.route('/generate_snippet/<int:website_id>', methods=['GET'])
@token_required
def generate_snippet(user_id, website_id):
    """
    Generate an HTML snippet for embedding a chatbot widget for a specific website.

    Parameters:
    - user_id: The authenticated user ID.
    - website_id: The ID of the website for which the snippet is generated.

    Returns:
    - JSON response containing the HTML snippet.
    """
    snippet = f"""
    <!-- Start of Chatbot Widget -->
    <div id="chatbot-container" style="position: fixed; bottom: 20px; right: 20px; width: 300px; height: 400px; border: 1px solid #ccc; padding: 10px; background-color: white;">
        <div id="chatbot-messages" style="height: 80%; overflow-y: auto; margin-bottom: 10px;"></div>
        <input type="text" id="chatbot-input" placeholder="Type your message..." style="width: 80%;" />
        <button onclick="sendMessage()">Send</button>
    </div>
    <script>
    function sendMessage() {{
        var inputField = document.getElementById('chatbot-input');
        var message = inputField.value;
        if (!message) return;

        // Display user message
        var messagesContainer = document.getElementById('chatbot-messages');
        var userMessage = document.createElement('div');
        userMessage.textContent = "You: " + message;
        messagesContainer.appendChild(userMessage);

        // Clear input
        inputField.value = '';

        // Send message to the Flask server
        fetch('/chat', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json'
            }},
            body: JSON.stringify({{
                message: message, 
                website_id: {website_id}
            }})
        }})
        .then(response => response.json())
        .then(data => {{
            var botMessage = document.createElement('div');
            botMessage.textContent = "Bot: " + (data.response || data.error || "No response");
            messagesContainer.appendChild(botMessage);
        }})
        .catch(error => {{
            var botMessage = document.createElement('div');
            botMessage.textContent = "Bot: Error connecting to the server.";
            messagesContainer.appendChild(botMessage);
        }});
    }}
    </script>
    <!-- End of Chatbot Widget -->
    """
    return jsonify({'snippet': snippet})

@app.route('/chat', methods=['POST'])
@token_required
def chatbot_route(user_id):
    response = chatbot(user_id)
    return response













@app.route('/dashboard', methods=['GET'])
@token_required  # This ensures that only authenticated users can access this route
def dashboard(user_id):
    # Fetch user-specific data from the database or perform any other logic
    return jsonify({"message": f"Welcome to your dashboard, User {user_id}!"})



if __name__ == '__main__':
    init_db()
    fetch_knowledge_base()
    app.run(debug=True)