import sqlite3

def create_database():
    """创建数据库和所需表"""
    conn = sqlite3.connect('poetry_game.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS poems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_input TEXT NOT NULL,
            correct_guesses TEXT,
            attempts INTEGER,
            time_taken REAL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaderboard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            poem_id INTEGER NOT NULL,
            time_taken REAL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (poem_id) REFERENCES poems(id)
        )
    ''')
    conn.commit()
    conn.close()

def load_poems():
    """从数据库加载所有诗句"""
    conn = sqlite3.connect('poetry_game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, text FROM poems')
    poems = cursor.fetchall()
    conn.close()
    return poems

def load_poems_from_file(file_path):
    """从文件导入诗句到数据库"""
    conn = sqlite3.connect('poetry_game.db')
    cursor = conn.cursor()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        poems = [line.strip() for line in f.readlines() if line.strip()]
    
    cursor.executemany('INSERT INTO poems (text) VALUES (?)', [(poem,) for poem in poems])
    conn.commit()
    conn.close()

def verify_user(username, password):
    """验证用户登录信息"""
    conn = sqlite3.connect('poetry_game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

def register_user(username, password):
    """注册新用户"""
    try:
        conn = sqlite3.connect('poetry_game.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def store_user_record(user_id, user_input, correct_guesses, attempts, time_taken):
    """存储用户游戏记录"""
    conn = sqlite3.connect('poetry_game.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO user_records (user_id, user_input, correct_guesses, attempts, time_taken) VALUES (?, ?, ?, ?, ?)',
                  (user_id, user_input, correct_guesses, attempts, time_taken))
    conn.commit()
    conn.close()

def update_leaderboard(user_id, poem_id, time_taken):
    """更新排行榜"""
    conn = sqlite3.connect('poetry_game.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO leaderboard (user_id, poem_id, time_taken) VALUES (?, ?, ?)',
                  (user_id, poem_id, time_taken))
    conn.commit()
    conn.close()

def get_user_fastest_time(user_id):
    """获取用户最快答题时间"""
    conn = sqlite3.connect('poetry_game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT MIN(time_taken) FROM user_records WHERE user_id = ?', (user_id,))
    fastest_time = cursor.fetchone()[0]
    conn.close()
    return fastest_time

def get_poem_leaderboard(poem_id):
    """获取特定诗句的排行榜"""
    conn = sqlite3.connect('poetry_game.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.username, l.time_taken
        FROM leaderboard l
        JOIN users u ON l.user_id = u.id
        WHERE l.poem_id = ?
        ORDER BY l.time_taken ASC
        LIMIT 10
    ''', (poem_id,))
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard