import sqlite3
from sqlite3 import Connection
from datetime import datetime
import os 

db_file = os.path.join(os.path.dirname(__file__), "tars.db")

def get_connection() -> Connection:
    """
    Create a Sqlite3 Connection.
    Ensures Foreign keys are enforced for this connection.
    Can use this function anywhere to create the db connection.
    """
    conn = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_key = ON;")
    return conn

def create_tables():
    """
    Create required database tables if they do not exist.
    Normally executed once during initial setup.
    """
    conn = get_connection()
    cursor = conn.cursor()

    ## Creating Models table - this table can used to track and model and model usage
    cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_version TEXT NULL,
    UNIQUE(provider, model_name, model_version)    
    );
    """
    )
    
    ## Users: Optional user profiles and preferences. Can be used when we want the LLM to behave differently or when we need to support multiple users.
    cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NULL,
        display_name TEXT NULL,
        prefs TEXT NULL,
        create_at DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
    );
    """
    )
    
    ## Tool Calls: Logs each time a tools is called by the LLM.
    ## Tool calls: table that stores the metadata of the tools called by the model.
    cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS tool_calls(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tool_name TEXT NOT NULL,
        arguments TEXT NULL,
        response TEXT NULL,
        timestamp DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
        conversation_id INTEGER NULL,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
    );
    """
    )
    
    ## Conversation table - main table of messages contains main things like messages and tool calls
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
        role TEXT NOT NULL CHECK(role IN ('user','assistant','tool','system')),
        content TEXT,
        tool_call_id INTEGER NULL,
        model_id INTEGER NULL,
        summary_flag BOOLEAN DEFAULT 0,
        tts_file TEXT NULL,
        user_id INTEGER NULL,
        FOREIGN KEY (tool_call_id) REFERENCES tool_call(id) ON DELETE SET NULL,
        FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE SET NULL,
        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL      
    );
    """
    )
    
    ## media_files: optional table for files like audio and video 
    ## Note: Currently this table exists but this table is mostly not used this is only used when I integrate TTS or decided to store current STT audio files or any audio/video files.
    cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS media_files(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NULL,
        file_path TEXT NOT NULL,
        file_type TEXT NOT NULL CHECK(file_type IN ('audio', 'video', 'image', 'other')),
        created_at DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
        metadata TEXT NULL,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
    );
    """
    )
    
    # Indexes to speed up common queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_calls_timestamp ON tool_calls(timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_role ON conversations(role);")
    
    conn.commit()
    conn.close()

## Function that saves model details into the models table.
def get_or_create_model(provider: str, model_name: str, version:str = None):
    """
    Make sure a model exists in the db.    
    Args:
        provider (str): Name of the model provider Example: Groq, OpenAI, Claude, Google
        model_name (str): like "openai/gpt-oss-120b" which is used for this current project.
        version (str, optional): version of the Model mostly Null. Defaults to None.
    Returns:
        Retuns the id of the model.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
    """
    INSERT OR IGNORE INTO models (provider, model_name , model_version)
    VALUES (?, ?, ?)
    """, (provider, model_name, version)
    )
    conn.commit()

    cursor.execute(
    """
    SELECT id from models
    WHERE provider = ? AND model_name = ? AND model_version IS ?
    """, (provider, model_name, version)
    )
    
    row = cursor.fetchone()
    conn.close()

    return row["id"] if row else None

## Function that saves user messages 
def save_user_message(text: str, user_id: int = None):
    """
    Insert a user message and return the conversation_id.
    Args:
        text (str): The message entered by the user that is passed as input to the LLM.
        user_id (int, optional): User_id from the users table this helps to give Preferences. Defaults to None.

    Returns:
        cid (int): Returns the last row id of the user_message.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
    """
    INSERT INTO conversations(role, content, user_id)
    VALUES ('user', ? ,?)
    """, (text, user_id)
    )
    conn.commit()
    cid = cursor.lastrowid
    conn.close()
    return cid
  
## Function that saves the LLM replies/content.    
def save_assistant_message(text: str, model_id: int = None):
    """
    Insert an assistant message and link it to the model it generated it 
    Args:
        text (str): Reply given by the model.
        model_id (int, optional): Name of the model which gave that reply. Defaults to None.
    Returns:
        cid (int): returns the last row id of the model_reply.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
    """
    INSERT INTO conversations (role, content, model_id)
    VALUES ('assistant', ?, ?)
    """, (text, model_id)
    )
    conn.commit()
    aid = cursor.lastrowid
    conn.close()

    return aid

## Insert tools calls into the table. BEFORE RUNNING TOOL
def save_tool_call(tool_name: str, arguments_json: str, trigger_conversation_id: int = None):
    """
    Insert a tool call into the table BEFORE running the tool.
    Args:
        tool_name (str): Name of the tool that llm thinks to run.
        arguments_json (str): What are arguments that the LLM is passing to the tool it is using.
        trigger_conversation_id (int, optional): Which conversation does it Trigger. Defaults to None.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
    """
    INSERT INTO tool_calls (tool_name, arguments, conversation_id)
    VALUES (?,?,?)
    """, (tool_name, arguments_json, trigger_conversation_id)
    )
    conn.commit()
    tid = cursor.lastrowid
    conn.close
    
    return tid

def save_tool_response(tool_call_id: int, response_text: str):
    """
    Saves tool reponse AND creates a conversation row with role='tool'
    Args:
        tool_call_id (int): The id we get when we save a tool call (id that returns when the save_tool_call function is called)
        response_text (str): what did the tool responded.
    Returns:
        cid (int): Returns the id of the save_tool_response
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
    """
    INSERT INTO conversations (role, content, tool_call_id)
    VALUES ('tool', ?, ?)
    """, (response_text, tool_call_id)
    )
    
    conn.commit()
    cid = cursor.lastrowid
    conn.close()

    return cid

## Function to get last N messages 
def get_last_messages(limit: int = 20):
    """
    Returns the last N messages give by timestamp.
    Args:
        limit (int, optional): No of previous message you Need. Defaults to 20.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
    """
    SELECT * 
    FROM conversations
    ORDER BY id DESC
    LIMIT ?
    """, (limit,)
    )
    
    row = cursor.fetchall()
    conn.close()
    return list(reversed(row))

## Saves media files and metadata (For future purpose)
def save_media_file(conversation_id: int, file_path: str, file_type: str, metadata_json: str = None):
    """
    Saves media files and metadata for things like screenshots and tts integration audio files.
    Args:
        conversation_id (int): Conversation id,
        file_path (str): Path of the file where it saved.
        metadata_json = metadata of the file 
    Returns:
        mid (int): Returns the media id 
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO media_files (conversation_id, file_path, file_type, metadata)
        VALUES (?, ?, ?, ?)
    """, (conversation_id, file_path, file_type, metadata_json))

    conn.commit()
    mid = cur.lastrowid
    conn.close()
    return mid
