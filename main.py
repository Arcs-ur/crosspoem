import sys
import random
import sqlite3
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QHBoxLayout
from PyQt5.QtCore import Qt
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity
from transformers import BertTokenizer, BertModel
import opencc

# 初始化 BERT
tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
model = BertModel.from_pretrained('bert-base-chinese')

def create_database():
    conn = sqlite3.connect('poetry_game.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS poems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT NOT NULL,
            correct_guesses TEXT,
            attempts INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def load_poems():
    conn = sqlite3.connect('poetry_game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT text FROM poems')
    poems = [row[0] for row in cursor.fetchall()]
    conn.close()
    return poems

def load_poems_from_file(file_path):
    conn = sqlite3.connect('poetry_game.db')
    cursor = conn.cursor()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        poems = [line.strip() for line in f.readlines() if line.strip()]  # 读取非空行
    
    cursor.executemany('INSERT INTO poems (text) VALUES (?)', [(poem,) for poem in poems])
    conn.commit()
    conn.close()

def get_embedding(sentence):
    inputs = tokenizer(sentence, return_tensors='pt')
    outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).detach().numpy()

def calculate_similarity(user_input, correct_poem):
    user_embedding = get_embedding(user_input)
    correct_embedding = get_embedding(correct_poem)
    similarity = cosine_similarity(user_embedding, correct_embedding)
    return similarity[0][0]  # 返回相似度值

if __name__ == "__main__":
    create_database()  # 创建数据库和表
    if not load_poems():
        load_poems_from_file('./poem.txt')  # 从文件导入诗句

    poems = load_poems()  # 从数据库中加载诗句
    poem = random.choice(poems)  # 随机选择一首诗

    class PoetryGame(QWidget):
        def __init__(self):
            super().__init__()

            self.language = 'simplified'  # 默认语言为简体中文
            self.previous_attempts = []
            self.attempt_counter = 0  
            self.correct_guesses = set()  
            self.initUI()

        def initUI(self):
            self.setWindowTitle("中文诗句填字游戏")
            self.setGeometry(100, 100, 400, 300)

            layout = QVBoxLayout()

            self.full_input = QLineEdit(self)
            self.full_input.setPlaceholderText("请输入完整句子，这句有{}个字".format(len(poem)))
            layout.addWidget(self.full_input)

            self.attempts_layout = QVBoxLayout()
            layout.addLayout(self.attempts_layout)

            self.submit_button = QPushButton("提交", self)
            self.submit_button.clicked.connect(self.check_answer)
            layout.addWidget(self.submit_button)

            # 添加语言切换按钮
            self.switch_language_button = QPushButton("繁体中文", self)
            self.switch_language_button.clicked.connect(self.switch_language)
            layout.addWidget(self.switch_language_button)

            self.setLayout(layout)

        def switch_language(self):
            if self.language == 'simplified':
                self.language = 'traditional'
                self.setWindowTitle("中文詩句填字遊戲")
                self.submit_button.setText("提交")
                self.switch_language_button.setText("简体中文")
                self.full_input.setPlaceholderText("請輸入完整句子，這句有{}個字".format(len(poem)))
            else:
                self.language = 'simplified'
                self.setWindowTitle("中文诗句填字游戏")
                self.submit_button.setText("提交")
                self.switch_language_button.setText("繁体中文")
                self.full_input.setPlaceholderText("请输入完整句子，这句有{}个字".format(len(poem)))

        def is_valid_poem(self, user_input):
            """检查输入的诗句是否在诗词库中"""
            converter = opencc.OpenCC('t2s')  # 繁体转简体
            simplified_input = converter.convert(user_input)
            print(simplified_input)
            return simplified_input in poems

        def check_answer(self):
            user_input = self.full_input.text()
            self.attempt_counter += 1  
            converter = opencc.OpenCC('t2s')  # 繁体转简体
            user_input = converter.convert(user_input)
            # 检查输入的诗句是否有效
            if not self.is_valid_poem(user_input):
                similarity = calculate_similarity(user_input, poem)
                if similarity > 0.95:  # 设置一个阈值
                    QMessageBox.information(self, "提示", f"你输入的句子与正确句子相似度为 {similarity:.2f}，请再尝试一下！")
                    self.full_input.clear()
                else:
                    QMessageBox.warning(self, "错误", "请输入诗词库中的有效诗句！")
                    self.full_input.clear()
                    return

            if self.attempt_counter > 10:
                self.show_results()
                return
            if self.language == 'traditional':
                converter = opencc.OpenCC('t2s')
                user_input = converter.convert(user_input)
                
            self.previous_attempts.append(user_input)

            attempt_container = QHBoxLayout()

            for i, char in enumerate(user_input):
                char_input = QLineEdit(self)
                char_input.setReadOnly(True)
                char_input.setFixedSize(40, 40)
                char_input.setAlignment(Qt.AlignCenter)

                if i < len(poem):  
                    if char == poem[i]:
                        if self.language == 'traditional':
                            converter = opencc.OpenCC('s2t')
                            char = converter.convert(char)
                        char_input.setStyleSheet("background-color: darkgreen;")
                        self.correct_guesses.add(char)  # 记录正确猜测
                    elif char in poem:
                        if self.language == 'traditional':
                            converter = opencc.OpenCC('s2t')
                            char = converter.convert(char)
                        char_input.setStyleSheet("background-color: lightgreen;")
                    else:
                        if self.language == 'traditional':
                            converter = opencc.OpenCC('s2t')
                            char = converter.convert(char)
                        char_input.setStyleSheet("background-color: lightgray;")
                    char_input.setText(char)
                else:
                    char_input.setText(char)

                attempt_container.addWidget(char_input)

            self.attempts_layout.addLayout(attempt_container)

            if user_input == poem:
                self.show_results()
            else:
                QMessageBox.warning(self, "结果", "很遗憾，填字错误。请再试一次！")
                self.full_input.clear()

        def show_results(self):
            correct_chars = ''.join(self.correct_guesses)
            all_guesses = ''.join(self.previous_attempts)
            char_count = Counter(all_guesses)
            most_common = char_count.most_common(1)

            result_message = f"正确猜中的字：{correct_chars}\n"
            if most_common:
                result_message += f"重复最多的字：{most_common[0][0]} (出现次数: {most_common[0][1]})"

            # 存储用户记录
            self.store_user_record(all_guesses, correct_chars)

            QMessageBox.information(self, "游戏结束", f"正确答案是：{poem}\n{result_message}")
            self.close()  

        def store_user_record(self, user_input, correct_guesses):
            conn = sqlite3.connect('poetry_game.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO user_records (user_input, correct_guesses, attempts) VALUES (?, ?, ?)',
                           (user_input, correct_guesses, self.attempt_counter))
            conn.commit()
            conn.close()

    app = QApplication(sys.argv)
    game = PoetryGame()
    game.show()
    print(poem)
    sys.exit(app.exec_())