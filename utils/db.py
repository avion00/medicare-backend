import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config

def get_db_connection():
    return psycopg2.connect(
        host=Config.DB_HOST,
        database=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD
    )

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            country_code TEXT NOT NULL,
            mobile_number TEXT NOT NULL,
            company_name TEXT,
            city TEXT,
            state TEXT,
            country TEXT,
            medicare_bot_usage TEXT,
            package TEXT DEFAULT 'free', -- Default package value
            email_verified BOOLEAN NOT NULL DEFAULT FALSE,
            password_hash TEXT NOT NULL,
            date_created TIMESTAMP NOT NULL DEFAULT NOW(),
            account_status TEXT NOT NULL DEFAULT 'active'
        );
    ''')

    # Password Reset Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            expiration TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE -- Clean up tokens on user deletion
        );
    ''')
    # cursor.execute('DROP TABLE IF EXISTS knowledge_base CASCADE;')
    # print("Dropped existing knowledge_base table.")

    # Knowledge Base Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id SERIAL PRIMARY KEY,
            website_url TEXT NOT NULL,
            summary TEXT NOT NULL,
            user_id INTEGER NOT NULL, -- Track which user added the entry
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    ''')

    # Training Data Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS training_data (
            id SERIAL PRIMARY KEY,
            website_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            FOREIGN KEY (website_id) REFERENCES knowledge_base(id) ON DELETE CASCADE
        );
    ''')

    # Conversation History Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_history (
            id SERIAL PRIMARY KEY,
            website_id INTEGER NOT NULL,
            user_message TEXT NOT NULL,
            assistant_response TEXT NOT NULL,
            FOREIGN KEY (website_id) REFERENCES knowledge_base(id) ON DELETE CASCADE
        );
    ''')

    # Integration Credentials Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS integration_credentials (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            api_key TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    ''')

    # Add indexes for frequently queried fields
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_base_user_id ON knowledge_base (user_id);')

    conn.commit()
    conn.close()
def fetch_knowledge_base():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Query to fetch data from knowledge_base
        cursor.execute("SELECT * FROM knowledge_base;")
        rows = cursor.fetchall()

        for row in rows:
            print(row)

    except Exception as e:
        print(f"Error: {e}")
