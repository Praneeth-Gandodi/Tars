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
    UNIQUE(provider, model_name)    
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
    
    ## Create session table.
    ## Stores conversation id and conversatinos based on sessions.
    cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_time DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
        end_time DATETIME NULL,
        title TEXT NULL,
        message_count INTEGER DEFAULT NULL,
        model_id INTEGER NULL,
        is_active BOOLEAN DEFAULT 1,
        FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE SET NULL
    );
    """
    )
    
    ## Conversation table - main table of messages contains main things like messages and tool calls
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
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
def get_or_create_model(provider: str, model_name: str):
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
        SELECT id FROM models
        WHERE provider = ? AND model_name = ?
        """, (provider, model_name)
    )
    row = cursor.fetchone()
    if row:
        conn.close()
        return row['id']
    
    cursor.execute(
    """
    INSERT OR IGNORE INTO models (provider, model_name)
    VALUES (?, ?)
    """, (provider, model_name)
    )
    conn.commit()
    row = cursor.lastrowid
    conn.close()

    return row

## Function that saves user messages 
def save_user_message(text: str,  session_id:int , user_id: int = None, model_id:int = None):
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
    try:
        cursor.execute(
        """
        INSERT INTO conversations(session_id, role, content, user_id, model_id)
        VALUES (?, 'user', ?, ?, ?)
        """, (session_id, text, user_id, model_id)
        )
        conn.commit()
        cid = cursor.lastrowid
        update_session_messag_Count(session_id)
        return cid
    except Exception as e:
        conn.rollback()
        print(f"Error saving the message: {e}")
        return None
    finally:
        conn.close()

  
## Function that saves the LLM replies/content.    
def save_assistant_message(text: str, session_id:int , model_id: int = None):
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
    try:
        cursor.execute(
        """
        INSERT INTO conversations (session_id, role, content, model_id)
        VALUES (?, 'assistant', ?, ?)
        """, (session_id, text, model_id)
        )
        conn.commit()
        aid = cursor.lastrowid
        update_session_messag_Count(session_id)
        return aid
    except Exception as e:
        conn.rollback()
        print(f"Error saving the assistant message {e}")
    finally:
        conn.close()

    

## Insert tools calls into the table. BEFORE RUNNING TOOL
def save_tool_call(tool_name: str, arguments_json: str, session_id:int ,trigger_conversation_id: int = None):
    """
    Insert a tool call into the table BEFORE running the tool.
    Args:
        tool_name (str): Name of the tool that llm thinks to run.
        arguments_json (str): What are arguments that the LLM is passing to the tool it is using.
        trigger_conversation_id (int, optional): Which conversation does it Trigger. Defaults to None.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
        """
        INSERT INTO tool_calls (tool_name, arguments, conversation_id)
        VALUES (?,?,?)
        """, (tool_name, arguments_json, trigger_conversation_id)
        )
        conn.commit()
        tid = cursor.lastrowid
        update_session_messag_Count(session_id)
    
        return tid
    except Exception as e:
        conn.rollback()
        print(f"Error saving the tool call {e}")
    finally:
        conn.close()

def save_tool_response(tool_call_id: int, response_text: str, session_id:int, model_id:int = None):
    """
    Saves tool reponse AND creates a conversation row with role='tool'
    Args:
        tool_call_id (int): The id we get when we save a tool call (id that returns when the save_tool_call function is called)
        response_text (str): what did the tool responded.
        session_id(int): Session id of the session in which tools is used.
        model_id (int): Model id of the session it used.
    Returns:
        cid (int): Returns the id of the save_tool_response
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE tool_calls
            SET response = ?
            WHERE id = ?
            """, (response_text, tool_call_id)
        )
        cursor.execute(
        """
        INSERT INTO conversations (session_id, role, content, tool_call_id, model_id)
        VALUES (?, 'tool', ?, ?, ?)
        """, (session_id, response_text, tool_call_id, model_id)
        )
        
        conn.commit()
        cid = cursor.lastrowid
        return cid
    except Exception as e:
        conn.rollback()
        print(f"Error saving tool response: {e}")
        return None
    finally:
        conn.close()

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

def create_new_session(model_id , title=None):
    """
    Creates new session should pass model_id 
    Args:
        model_id (_type_): _description_
        title (_type_, optional): _description_. Defaults to None.
    Returns:
        session_id (int): The Id of the newly created session.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
        """
        INSERT INTO sessions (model_id, title, is_active)
        VALUES (?, ?, 1)
        """, (model_id, title)
            )
        conn.commit()
        session_id = cursor.lastrowid
        return session_id
    except Exception as e:
        conn.rollback()
        print("Error creating the session.")
        return None
    finally:
        conn.close()
    
        

def get_session_by_id(session_id):
    """
    Returns session details by session ID.
    
    Args:
        session_id: The ID of the session to retrieve
    
    Returns:
        dict: Session details or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            SELECT 
                s.id,
                s.start_time,
                s.end_time,
                s.title,
                s.message_count,
                s.is_active,
                m.model_name,
                m.provider
            FROM sessions s
            LEFT JOIN models m ON s.model_id = m.id
            WHERE s.id = ?
            """,
            (session_id,)
        )
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row['id'],
                'start_time': row['start_time'],
                'end_time': row['end_time'],
                'title': row['title'],
                'message_count': row['message_count'],
                'is_active': row['is_active'],
                'model_name': row['model_name'],
                'provider': row['provider']
            }
        return None
    except Exception as e:
        print(f"Error getting session: {e}")
        return None
    finally:
        conn.close()
        
## Gets all sessions.
def get_all_session(limit = 20):
    """
    Get last 20 sessions or for N last sessions if limit is passed.
    Args:
        limit (int, optional): Maximum number of sessions to return.. Defaults to 20.
    Returns:
        list : List of seesion dictionaries.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            SELECT 
                s.id,
                s.start_time,
                s.end_time,
                s.title,
                s.message_count,
                s.is_active,
                m.model_name,
                m.provider
            FROM sessions s
            LEFT JOIN models m ON s.model_id = m.id
            ORDER BY s.start_time DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = cursor.fetchall()
        
        sessions = []
        for row in rows:
            sessions.append({
                'id': row['id'],
                'start_time': row['start_time'],
                'end_time': row['end_time'],
                'title': row['title'],
                'message_count': row['message_count'],
                'is_active': row['is_active'],
                'model_name': row['model_name'],
                'provider': row['provider']
            })
        return sessions
    except Exception as e:
        print(f"Error getting sessions: {e}")
        return []
    finally:
        conn.close()


def end_session(session_id):
    """
    Marks session as ended and sets end_time.
    
    Args:
        session_id: The ID of the session to end
    
    Returns:
        bool: True if successful, False otherwise
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            UPDATE sessions
            SET end_time = strftime('%Y-%m-%d %H:%M:%f', 'now'),
                is_active = 0
            WHERE id = ?
            """,
            (session_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"Error ending session: {e}")
        return False
    finally:
        conn.close()

def update_session_messag_Count(session_id):
    """
    Updates the message count for a session by counting 
    user and assistant messages.
    
    Args:
        session_id: The ID of the session to update
    
    Returns:
        bool: True if successful, False otherwise
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Count user and assistant messages only
        cursor.execute(
            """
            SELECT COUNT(*) as count
            FROM conversations
            WHERE session_id = ?
            AND role IN ('user', 'assistant')
            """,
            (session_id,)
        )
        row = cursor.fetchone()
        message_count = row['count'] if row else 0
        
        # Update the session
        cursor.execute(
            """
            UPDATE sessions
            SET message_count = ?
            WHERE id = ?
            """,
            (message_count, session_id)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error updating message count: {e}")
        return False
    finally:
        conn.close()
