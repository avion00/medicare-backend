from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
from utils.jwt_utils import generate_access_token, decode_access_token
from functools import wraps
import datetime
import secrets

def register_user():
    data = request.get_json()
    password_hash = generate_password_hash(data['password'])

    conn  =get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (first_name, last_name, username, email, country_code, mobile_number,
                               company_name, city, state, country, medicare_bot_usage, package, 
                               email_verified, password_hash, account_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (data['first_name'], data['last_name'], data['username'], data['email'], 
              data['country_code'], data['mobile_number'], data['company_name'], 
              data['city'], data['state'], data['country'], data['medicare_bot_usage'], 
              data['package'], data.get('email_verified', False), password_hash, 'active'))
        conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()
    return jsonify({"success": True, "message": "User registered successfully"})


def login_user():
    data = request.get_json()
    username = data['username']
    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username= %s',(username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[14], password):
        user_id = user[0]
        token = generate_access_token(user_id)
        print(token)
        return jsonify({'message':'Login successful', 'token' : token})
    return jsonify({"error": "Invalid credentials"}), 401


def token_required(f):
    """Decorator function to protect routes with JWT token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header is missing"}), 403

        # Check for "Bearer" prefix and split the token
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({"error": "Invalid Authorization header format"}), 403

        # Decode and verify the token
        token = parts[1]
        user_id = decode_access_token(token)
        if not user_id:
            return jsonify({"error": "Invalid or expired token"}), 403

        # Pass the user_id to the wrapped function
        return f(user_id, *args, **kwargs)
    return decorated_function

# Password reset request
def reset_request():
    data = request.get_json()
    email = data.get('email')

    # Fetch user from the database using email
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"message": "User not found"}), 404

    user_id = user[0]

    # Generate a secure token
    token = secrets.token_urlsafe(32)
    expiration = datetime.datetime.now() + datetime.timedelta(hours=1)  # Token valid for 1 hour

    # Store the token in the database
    cursor.execute('''
        INSERT INTO password_reset_tokens (user_id, token, expiration)
        VALUES (%s, %s, %s)
    ''', (user_id, token, expiration))
    conn.commit()
    conn.close()

    # Send the reset link to the user's email (mocking the email sending here)
    reset_link = f"http://localhost:5000/reset_password?token={token}"
    print(f"Password reset link (send via email): {reset_link}")  # Replace this with actual email sending logic

    return jsonify({"message": "Password reset link has been sent to your email."})


# Set password from reset link
def set_password():
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')

    if not token or not new_password:
        return jsonify({"message": "Token and new password are required"}), 400

    # Validate the token
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, expiration FROM password_reset_tokens WHERE token = %s', (token,))
    token_data = cursor.fetchone()

    if not token_data:
        return jsonify({"message": "Invalid or expired token"}), 400

    user_id, expiration = token_data
    if datetime.datetime.now() > expiration:
        return jsonify({"message": "Token has expired"}), 400

    # Hash the new password
    hashed_password = generate_password_hash(new_password)

    # Update the user's password
    cursor.execute('UPDATE users SET password_hash = %s WHERE id = %s', (hashed_password, user_id))
    conn.commit()

    # Delete the used token
    cursor.execute('DELETE FROM password_reset_tokens WHERE token = %s', (token,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Password has been reset successfully."})
