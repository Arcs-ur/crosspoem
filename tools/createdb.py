import sqlite3

def create_database():
    conn = sqlite3.connect('poetry_game.db')
    cursor = conn.cursor()

    # 创建诗词表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS poems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def load_poems_from_file(file_path):
    conn = sqlite3.connect('poetry_game.db')
    cursor = conn.cursor()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        poems = [line.strip() for line in f.readlines() if line.strip()]  # 读取非空行
    
    cursor.executemany('INSERT INTO poems (text) VALUES (?)', [(poem,) for poem in poems])
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()  # 创建数据库和表
    load_poems_from_file('./poem.txt')  # 从文件导入诗句