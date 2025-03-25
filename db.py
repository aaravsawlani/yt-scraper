import sqlite3
import json
from datetime import datetime

def init_db():
    """Initialize the database and create tables if they don't exist"""
    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    
    # Create searches table
    c.execute('''
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            max_results INTEGER,
            order_by TEXT,
            max_age INTEGER,
            final_summary TEXT
        )
    ''')
    
    # Create videos table
    c.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_id INTEGER,
            video_id TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            url TEXT NOT NULL,
            FOREIGN KEY (search_id) REFERENCES searches (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def save_search(keyword, max_results, order_by, max_age, final_summary, videos):
    """Save a search and its results to the database"""
    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    
    # Insert search
    c.execute('''
        INSERT INTO searches (keyword, max_results, order_by, max_age, final_summary)
        VALUES (?, ?, ?, ?, ?)
    ''', (keyword, max_results, order_by, max_age, final_summary))
    
    search_id = c.lastrowid
    
    # Insert videos
    for video in videos:
        c.execute('''
            INSERT INTO videos (search_id, video_id, title, summary, url)
            VALUES (?, ?, ?, ?, ?)
        ''', (search_id, video['video_id'], video['title'], video['summary'], video['url']))
    
    conn.commit()
    conn.close()
    return search_id

def get_search_history():
    """Get all past searches"""
    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT id, keyword, timestamp, max_results, order_by, max_age
        FROM searches
        ORDER BY timestamp DESC
    ''')
    
    searches = [
        {
            'id': row[0],
            'keyword': row[1],
            'timestamp': row[2],
            'max_results': row[3],
            'order_by': row[4],
            'max_age': row[5]
        }
        for row in c.fetchall()
    ]
    
    conn.close()
    return searches

def get_search_results(search_id):
    """Get results for a specific search"""
    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    
    # Get search details
    c.execute('SELECT * FROM searches WHERE id = ?', (search_id,))
    search = c.fetchone()
    
    # Get videos for this search
    c.execute('SELECT * FROM videos WHERE search_id = ?', (search_id,))
    videos = [
        {
            'video_id': row[2],
            'title': row[3],
            'summary': row[4],
            'url': row[5]
        }
        for row in c.fetchall()
    ]
    
    conn.close()
    
    if not search:
        return None
        
    return {
        'id': search[0],
        'keyword': search[1],
        'timestamp': search[2],
        'max_results': search[3],
        'order_by': search[4],
        'max_age': search[5],
        'final_summary': search[6],
        'videos': videos
    } 