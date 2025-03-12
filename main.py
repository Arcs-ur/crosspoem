# import sys
# import random
# import sqlite3
# import numpy as np
# from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QHBoxLayout, QLabel
# from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QTimer
# from collections import Counter
# from sklearn.metrics.pairwise import cosine_similarity
# from transformers import BertTokenizer, BertModel
# import opencc
# import time  # 导入时间模块

# # 初始化 BERT
# tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
# model = BertModel.from_pretrained('bert-base-chinese')

# def create_database():
#     conn = sqlite3.connect('poetry_game.db')
#     cursor = conn.cursor()
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             username TEXT UNIQUE NOT NULL,
#             password TEXT NOT NULL
#         )
#     ''')
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS poems (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             text TEXT NOT NULL
#         )
#     ''')
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS user_records (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_id INTEGER NOT NULL,
#             user_input TEXT NOT NULL,
#             correct_guesses TEXT,
#             attempts INTEGER,
#             time_taken REAL,  -- 新增字段，记录答题时间
#             FOREIGN KEY (user_id) REFERENCES users(id)
#         )
#     ''')
#     conn.commit()
#     conn.close()

# def load_poems():
#     conn = sqlite3.connect('poetry_game.db')
#     cursor = conn.cursor()
#     cursor.execute('SELECT text FROM poems')
#     poems = [row[0] for row in cursor.fetchall()]
#     conn.close()
#     return poems

# def load_poems_from_file(file_path):
#     conn = sqlite3.connect('poetry_game.db')
#     cursor = conn.cursor()
    
#     with open(file_path, 'r', encoding='utf-8') as f:
#         poems = [line.strip() for line in f.readlines() if line.strip()]  # 读取非空行
    
#     cursor.executemany('INSERT INTO poems (text) VALUES (?)', [(poem,) for poem in poems])
#     conn.commit()
#     conn.close()

# def get_embedding(sentence):
#     inputs = tokenizer(sentence, return_tensors='pt')
#     outputs = model(**inputs)
#     return outputs.last_hidden_state.mean(dim=1).detach().numpy()

# def calculate_similarity(user_input, correct_poem):
#     user_embedding = get_embedding(user_input)
#     correct_embedding = get_embedding(correct_poem)
#     similarity = cosine_similarity(user_embedding, correct_embedding)
#     return similarity[0][0]  # 返回相似度值

# class PoetryGame(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.current_user = None
#         self.poem = self.load_random_poem()
#         self.initUI()

#     def load_random_poem(self):
#         poems = load_poems()
#         return random.choice(poems) if poems else ""

#     def initUI(self):
#         self.setWindowTitle("中文诗句填字游戏")
#         self.setGeometry(100, 100, 400, 300)

#         layout = QVBoxLayout()

#         self.username_input = QLineEdit(self)
#         self.username_input.setPlaceholderText("用户名")
#         layout.addWidget(self.username_input)

#         self.password_input = QLineEdit(self)
#         self.password_input.setPlaceholderText("密码")
#         self.password_input.setEchoMode(QLineEdit.Password)
#         layout.addWidget(self.password_input)

#         self.login_button = QPushButton("登录", self)
#         self.login_button.clicked.connect(self.login)
#         layout.addWidget(self.login_button)

#         self.register_button = QPushButton("注册", self)
#         self.register_button.clicked.connect(self.register)
#         layout.addWidget(self.register_button)

#         self.setLayout(layout)

#     def login(self):
#         username = self.username_input.text()
#         password = self.password_input.text()
        
#         conn = sqlite3.connect('poetry_game.db')
#         cursor = conn.cursor()
#         cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
#         user = cursor.fetchone()
#         conn.close()
        
#         if user:
#             self.current_user = user[0]  # 用户ID
#             QMessageBox.information(self, "成功", "登录成功！")
#             self.start_game()
#         else:
#             QMessageBox.warning(self, "错误", "用户名或密码错误！")

#     def register(self):
#         username = self.username_input.text()
#         password = self.password_input.text()
        
#         conn = sqlite3.connect('poetry_game.db')
#         cursor = conn.cursor()
#         try:
#             cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
#             conn.commit()
#             QMessageBox.information(self, "成功", "注册成功！请登录。")
#         except sqlite3.IntegrityError:
#             QMessageBox.warning(self, "错误", "用户名已存在！")
#         finally:
#             conn.close()

#     def start_game(self):
#         self.game_window = GameWindow(self.current_user, self.load_random_poem())
#         self.game_window.show()
#         self.close()

# class GameWindow(QWidget):
#     def __init__(self, user_id, poem):
#         super().__init__()
#         self.user_id = user_id
#         self.poem = poem
#         self.language = 'simplified'
#         self.previous_attempts = []
#         self.attempt_counter = 0  
#         self.correct_guesses = set()  
#         self.time_left = 15  # 设置初始时间为15秒
#         self.timer = QTimer()
#         self.timer.timeout.connect(self.update_timer)
#         self.initUI()

#         self.start_time = time.time()  # 开始计时

#         # 打印当前诗句以便调试
#         print(f"当前诗句: {self.poem}")

#     def initUI(self):
#         self.setWindowTitle("游戏窗口")
#         self.setGeometry(100, 100, 400, 300)

#         layout = QVBoxLayout()

#         self.timer_label = QLabel(f"剩余时间: {self.time_left}秒", self)
#         layout.addWidget(self.timer_label)

#         self.full_input = QLineEdit(self)
#         self.full_input.setPlaceholderText("请输入完整句子，这句有{}个字".format(len(self.poem)))
#         layout.addWidget(self.full_input)

#         self.attempts_layout = QVBoxLayout()
#         layout.addLayout(self.attempts_layout)

#         self.submit_button = QPushButton("提交", self)
#         self.submit_button.clicked.connect(self.check_answer)
#         layout.addWidget(self.submit_button)

#         # 添加语言切换按钮
#         self.switch_language_button = QPushButton("繁体中文", self)
#         self.switch_language_button.clicked.connect(self.switch_language)
#         layout.addWidget(self.switch_language_button)

#         # 添加查看记录按钮
#         self.view_records_button = QPushButton("查看最快答题记录", self)
#         self.view_records_button.clicked.connect(self.view_records)
#         layout.addWidget(self.view_records_button)

#         self.setLayout(layout)

#         # 启动计时器
#         self.timer.start(1000)  # 每秒更新

#     def update_timer(self):
#         self.time_left -= 1
#         self.timer_label.setText(f"剩余时间: {self.time_left}秒")
#         if self.time_left <= 0:
#             self.timer.stop()
#             self.show_results()  # 时间到时显示结果

#     def switch_language(self):
#         if self.language == 'simplified':
#             self.language = 'traditional'
#             self.setWindowTitle("中文詩句填字遊戲")
#             self.submit_button.setText("提交")
#             self.switch_language_button.setText("简体中文")
#             self.full_input.setPlaceholderText("請輸入完整句子，這句有{}个字".format(len(self.poem)))
#         else:
#             self.language = 'simplified'
#             self.setWindowTitle("中文诗句填字游戏")
#             self.submit_button.setText("提交")
#             self.switch_language_button.setText("繁体中文")
#             self.full_input.setPlaceholderText("请输入完整句子，这句有{}个字".format(len(self.poem)))

#     def is_valid_poem(self, user_input):
#         """检查输入的诗句是否在诗词库中"""
#         converter = opencc.OpenCC('t2s')  # 繁体转简体
#         simplified_input = converter.convert(user_input)
#         return simplified_input in load_poems()

#     def check_answer(self):
#         user_input = self.full_input.text()
#         self.attempt_counter += 1  
#         converter = opencc.OpenCC('t2s')  # 繁体转简体
#         user_input = converter.convert(user_input)

#         # 检查输入的诗句是否有效
#         if not self.is_valid_poem(user_input):
#             similarity = calculate_similarity(user_input, self.poem)
#             if similarity > 0.9:  # 设置一个阈值
#                 self.animate_result(f"你输入的句子与正确句子相似度为 {similarity:.2f}，请再尝试一下！")
#                 self.full_input.clear()
#             else:
#                 QMessageBox.warning(self, "错误", "请输入诗词库中的有效诗句！")
#                 self.full_input.clear()
#                 return

#         if self.attempt_counter > 10:
#             self.show_results()
#             return

#         self.previous_attempts.append(user_input)

#         attempt_container = QHBoxLayout()

#         for i, char in enumerate(user_input):
#             char_input = QLineEdit(self)
#             char_input.setReadOnly(True)
#             char_input.setFixedSize(40, 40)
#             char_input.setAlignment(Qt.AlignCenter)

#             if i < len(self.poem):  
#                 if char == self.poem[i]:
#                     char_input.setStyleSheet("background-color: darkgreen;")
#                     self.correct_guesses.add(char)  # 记录正确猜测
#                 elif char in self.poem:
#                     char_input.setStyleSheet("background-color: lightgreen;")
#                 else:
#                     char_input.setStyleSheet("background-color: lightgray;")
#                 char_input.setText(char)

#             attempt_container.addWidget(char_input)

#         self.attempts_layout.addLayout(attempt_container)

#         if user_input == self.poem:
#             self.show_results()
#         else:
#             self.animate_result("很遗憾，填字错误。请再试一次！")
#             self.full_input.clear()

#     def show_results(self):
#         correct_chars = ''.join(self.correct_guesses)
#         all_guesses = ''.join(self.previous_attempts)
#         char_count = Counter(all_guesses)
#         most_common = char_count.most_common(1)

#         result_message = f"正确猜中的字：{correct_chars}\n"
#         if most_common:
#             result_message += f"重复最多的字：{most_common[0][0]} (出现次数: {most_common[0][1]})"

#         # 计算答题时间
#         time_taken = time.time() - self.start_time

#         # 存储用户记录
#         self.store_user_record(all_guesses, correct_chars, time_taken)

#         result_box = QMessageBox(self)
#         result_box.setText(f"游戏结束\n正确答案是：{self.poem}\n{result_message}\n答题时间: {time_taken:.2f}秒")
#         result_box.setWindowTitle("提示")

#         # 添加“再来一局”按钮
#         replay_button = result_box.addButton("再来一局", QMessageBox.ActionRole)
#         exit_button = result_box.addButton("退出", QMessageBox.RejectRole)

#         result_box.exec_()  # 显示消息框

#         # 根据用户选择的按钮执行相应操作
#         if result_box.clickedButton() == replay_button:
#             self.replay_game()
#         else:
#             self.close()  # 退出游戏窗口

#     def replay_game(self):
#         self.poem = random.choice(load_poems())  # 重新加载随机诗句
#         self.attempt_counter = 0
#         self.previous_attempts.clear()  # 清空尝试记录
#         self.correct_guesses.clear()  # 清空正确猜测记录
#         self.time_left = 15  # 重置时间
#         self.full_input.setPlaceholderText("请输入完整句子，这句有{}个字".format(len(self.poem)))

#         # 清空尝试的输入框和显示区域
#         for i in reversed(range(self.attempts_layout.count())): 
#             widget = self.attempts_layout.itemAt(i).widget()
#             if widget is not None:
#                 widget.deleteLater()
        
#         self.full_input.clear()  # 清空输入框
#         self.start_time = time.time()  # 重新开始计时
#         print(f"当前诗句: {self.poem}")  # 打印当前诗句以便调试
#         self.timer.start()  # 重新启动计时器
#         self.show()  # 显示游戏窗口

#     def store_user_record(self, user_input, correct_guesses, time_taken):
#         conn = sqlite3.connect('poetry_game.db')
#         cursor = conn.cursor()
#         cursor.execute('INSERT INTO user_records (user_id, user_input, correct_guesses, attempts, time_taken) VALUES (?, ?, ?, ?, ?)',
#                        (self.user_id, user_input, correct_guesses, self.attempt_counter, time_taken))
#         conn.commit()
#         conn.close()

#     def view_records(self):
#         conn = sqlite3.connect('poetry_game.db')
#         cursor = conn.cursor()
#         cursor.execute('SELECT MIN(time_taken) FROM user_records WHERE user_id = ?', (self.user_id,))
#         fastest_time = cursor.fetchone()[0]
#         conn.close()
        
#         if fastest_time is not None:
#             QMessageBox.information(self, "最快答题记录", f"你的最快答题时间是: {fastest_time:.2f}秒")
#         else:
#             QMessageBox.information(self, "最快答题记录", "你还没有答题记录。")

#     def animate_result(self, message):
#         result_box = QMessageBox(self)
#         result_box.setText(message)
#         result_box.setWindowTitle("提示")
        
#         # 动画效果
#         animation = QPropertyAnimation(result_box, b"geometry")
#         animation.setDuration(500)
#         animation.setStartValue(QRect(100, 100, 0, 0))
#         animation.setEndValue(QRect(100, 100, 300, 100))
#         animation.start()
        
#         result_box.exec_()  # 显示消息框

# if __name__ == "__main__":
#     create_database()  # 创建数据库和表
#     if not load_poems():
#         load_poems_from_file('./poem.txt')  # 从文件导入诗句

#     app = QApplication(sys.argv)
#     game = PoetryGame()
#     game.show()
#     sys.exit(app.exec_())

# import sys
# import random
# import sqlite3
# import numpy as np
# from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QHBoxLayout, QLabel
# from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QTimer
# from collections import Counter
# from sklearn.metrics.pairwise import cosine_similarity
# from transformers import BertTokenizer, BertModel
# import opencc
# import time  # 导入时间模块

# # 初始化 BERT
# tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
# model = BertModel.from_pretrained('bert-base-chinese')

# def create_database():
#     conn = sqlite3.connect('poetry_game.db')
#     cursor = conn.cursor()
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             username TEXT UNIQUE NOT NULL,
#             password TEXT NOT NULL
#         )
#     ''')
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS poems (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             text TEXT NOT NULL
#         )
#     ''')
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS user_records (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_id INTEGER NOT NULL,
#             user_input TEXT NOT NULL,
#             correct_guesses TEXT,
#             attempts INTEGER,
#             time_taken REAL,  -- 新增字段，记录答题时间
#             FOREIGN KEY (user_id) REFERENCES users(id)
#         )
#     ''')
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS leaderboard (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_id INTEGER NOT NULL,
#             poem_text TEXT NOT NULL,
#             time_taken REAL,
#             FOREIGN KEY (user_id) REFERENCES users(id)
#         )
#     ''')
#     conn.commit()
#     conn.close()

# def load_poems():
#     conn = sqlite3.connect('poetry_game.db')
#     cursor = conn.cursor()
#     cursor.execute('SELECT text FROM poems')
#     poems = [row[0] for row in cursor.fetchall()]
#     conn.close()
#     return poems

# def load_poems_from_file(file_path):
#     conn = sqlite3.connect('poetry_game.db')
#     cursor = conn.cursor()
    
#     with open(file_path, 'r', encoding='utf-8') as f:
#         poems = [line.strip() for line in f.readlines() if line.strip()]  # 读取非空行
    
#     cursor.executemany('INSERT INTO poems (text) VALUES (?)', [(poem,) for poem in poems])
#     conn.commit()
#     conn.close()

# def get_embedding(sentence):
#     inputs = tokenizer(sentence, return_tensors='pt')
#     outputs = model(**inputs)
#     return outputs.last_hidden_state.mean(dim=1).detach().numpy()

# def calculate_similarity(user_input, correct_poem):
#     user_embedding = get_embedding(user_input)
#     correct_embedding = get_embedding(correct_poem)
#     similarity = cosine_similarity(user_embedding, correct_embedding)
#     return similarity[0][0]  # 返回相似度值

# class PoetryGame(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.current_user = None
#         self.poem = self.load_random_poem()
#         self.initUI()

#     def load_random_poem(self):
#         poems = load_poems()
#         return random.choice(poems) if poems else ""

#     def initUI(self):
#         self.setWindowTitle("中文诗句填字游戏")
#         self.setGeometry(100, 100, 400, 300)

#         layout = QVBoxLayout()

#         self.username_input = QLineEdit(self)
#         self.username_input.setPlaceholderText("用户名")
#         layout.addWidget(self.username_input)

#         self.password_input = QLineEdit(self)
#         self.password_input.setPlaceholderText("密码")
#         self.password_input.setEchoMode(QLineEdit.Password)
#         layout.addWidget(self.password_input)

#         self.login_button = QPushButton("登录", self)
#         self.login_button.clicked.connect(self.login)
#         layout.addWidget(self.login_button)

#         self.register_button = QPushButton("注册", self)
#         self.register_button.clicked.connect(self.register)
#         layout.addWidget(self.register_button)

#         self.setLayout(layout)

#     def login(self):
#         username = self.username_input.text()
#         password = self.password_input.text()
        
#         conn = sqlite3.connect('poetry_game.db')
#         cursor = conn.cursor()
#         cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
#         user = cursor.fetchone()
#         conn.close()
        
#         if user:
#             self.current_user = user[0]  # 用户ID
#             QMessageBox.information(self, "成功", "登录成功！")
#             self.start_game()
#         else:
#             QMessageBox.warning(self, "错误", "用户名或密码错误！")

#     def register(self):
#         username = self.username_input.text()
#         password = self.password_input.text()
        
#         conn = sqlite3.connect('poetry_game.db')
#         cursor = conn.cursor()
#         try:
#             cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
#             conn.commit()
#             QMessageBox.information(self, "成功", "注册成功！请登录。")
#         except sqlite3.IntegrityError:
#             QMessageBox.warning(self, "错误", "用户名已存在！")
#         finally:
#             conn.close()

#     def start_game(self):
#         self.game_window = GameWindow(self.current_user, self.load_random_poem())
#         self.game_window.show()
#         self.close()

# class GameWindow(QWidget):
#     def __init__(self, user_id, poem):
#         super().__init__()
#         self.user_id = user_id
#         self.poem = poem
#         self.language = 'simplified'
#         self.previous_attempts = []
#         self.attempt_counter = 0  
#         self.correct_guesses = set()  
#         self.time_left = 15  # 设置初始时间为15秒
#         self.timer = QTimer()
#         self.timer.timeout.connect(self.update_timer)
#         self.initUI()

#         self.start_time = time.time()  # 开始计时

#         # 打印当前诗句以便调试
#         print(f"当前诗句: {self.poem}")

#     def initUI(self):
#         self.setWindowTitle("游戏窗口")
#         self.setGeometry(100, 100, 400, 300)

#         layout = QVBoxLayout()

#         self.timer_label = QLabel(f"剩余时间: {self.time_left}秒", self)
#         layout.addWidget(self.timer_label)

#         self.full_input = QLineEdit(self)
#         self.full_input.setPlaceholderText("请输入完整句子，这句有{}个字".format(len(self.poem)))
#         layout.addWidget(self.full_input)

#         self.attempts_layout = QVBoxLayout()
#         layout.addLayout(self.attempts_layout)

#         self.submit_button = QPushButton("提交", self)
#         self.submit_button.clicked.connect(self.check_answer)
#         layout.addWidget(self.submit_button)

#         # 添加语言切换按钮
#         self.switch_language_button = QPushButton("繁体中文", self)
#         self.switch_language_button.clicked.connect(self.switch_language)
#         layout.addWidget(self.switch_language_button)

#         # 添加查看记录按钮
#         self.view_records_button = QPushButton("查看最快答题记录", self)
#         self.view_records_button.clicked.connect(self.view_records)
#         layout.addWidget(self.view_records_button)

#         # 添加查看排行榜按钮
#         self.view_leaderboard_button = QPushButton("查看排行榜", self)
#         self.view_leaderboard_button.clicked.connect(self.view_leaderboard)
#         layout.addWidget(self.view_leaderboard_button)

#         self.setLayout(layout)

#         # 启动计时器
#         self.timer.start(1000)  # 每秒更新

#     def update_timer(self):
#         self.time_left -= 1
#         self.timer_label.setText(f"剩余时间: {self.time_left}秒")
#         if self.time_left <= 0:
#             self.timer.stop()
#             self.show_results()  # 时间到时显示结果

#     def switch_language(self):
#         if self.language == 'simplified':
#             self.language = 'traditional'
#             self.setWindowTitle("中文詩句填字遊戲")
#             self.submit_button.setText("提交")
#             self.switch_language_button.setText("简体中文")
#             self.full_input.setPlaceholderText("請輸入完整句子，這句有{}个字".format(len(self.poem)))
#         else:
#             self.language = 'simplified'
#             self.setWindowTitle("中文诗句填字游戏")
#             self.submit_button.setText("提交")
#             self.switch_language_button.setText("繁体中文")
#             self.full_input.setPlaceholderText("请输入完整句子，这句有{}个字".format(len(self.poem)))

#     def is_valid_poem(self, user_input):
#         """检查输入的诗句是否在诗词库中"""
#         converter = opencc.OpenCC('t2s')  # 繁体转简体
#         simplified_input = converter.convert(user_input)
#         return simplified_input in load_poems()

#     def check_answer(self):
#         user_input = self.full_input.text()
#         self.attempt_counter += 1  
#         converter = opencc.OpenCC('t2s')  # 繁体转简体
#         user_input = converter.convert(user_input)

#         # 检查输入的诗句是否有效
#         if not self.is_valid_poem(user_input):
#             similarity = calculate_similarity(user_input, self.poem)
#             if similarity > 0.9:  # 设置一个阈值
#                 self.animate_result(f"你输入的句子与正确句子相似度为 {similarity:.2f}，请再尝试一下！")
#                 self.full_input.clear()
#             else:
#                 QMessageBox.warning(self, "错误", "请输入诗词库中的有效诗句！")
#                 self.full_input.clear()
#                 return

#         if self.attempt_counter > 10:
#             self.show_results()
#             return

#         self.previous_attempts.append(user_input)

#         attempt_container = QHBoxLayout()

#         for i, char in enumerate(user_input):
#             char_input = QLineEdit(self)
#             char_input.setReadOnly(True)
#             char_input.setFixedSize(40, 40)
#             char_input.setAlignment(Qt.AlignCenter)

#             if i < len(self.poem):  
#                 if char == self.poem[i]:
#                     char_input.setStyleSheet("background-color: darkgreen;")
#                     self.correct_guesses.add(char)  # 记录正确猜测
#                 elif char in self.poem:
#                     char_input.setStyleSheet("background-color: lightgreen;")
#                 else:
#                     char_input.setStyleSheet("background-color: lightgray;")
#                 char_input.setText(char)

#             attempt_container.addWidget(char_input)

#         self.attempts_layout.addLayout(attempt_container)

#         if user_input == self.poem:
#             self.show_results()
#         else:
#             self.animate_result("很遗憾，填字错误。请再试一次！")
#             self.full_input.clear()

#     def show_results(self):
#         correct_chars = ''.join(self.correct_guesses)
#         all_guesses = ''.join(self.previous_attempts)
#         char_count = Counter(all_guesses)
#         most_common = char_count.most_common(1)

#         result_message = f"正确猜中的字：{correct_chars}\n"
#         if most_common:
#             result_message += f"重复最多的字：{most_common[0][0]} (出现次数: {most_common[0][1]})"

#         # 计算答题时间
#         time_taken = time.time() - self.start_time

#         # 存储用户记录
#         self.store_user_record(all_guesses, correct_chars, time_taken)

#         # 更新排行榜
#         self.update_leaderboard(time_taken)

#         result_box = QMessageBox(self)
#         result_box.setText(f"游戏结束\n正确答案是：{self.poem}\n{result_message}\n答题时间: {time_taken:.2f}秒")
#         result_box.setWindowTitle("提示")

#         # 添加“再来一局”按钮
#         replay_button = result_box.addButton("再来一局", QMessageBox.ActionRole)
#         exit_button = result_box.addButton("退出", QMessageBox.RejectRole)

#         result_box.exec_()  # 显示消息框

#         # 根据用户选择的按钮执行相应操作
#         if result_box.clickedButton() == replay_button:
#             self.replay_game()
#         else:
#             self.close()  # 退出游戏窗口

#     def replay_game(self):
#         self.poem = random.choice(load_poems())  # 重新加载随机诗句
#         self.attempt_counter = 0
#         self.previous_attempts.clear()  # 清空尝试记录
#         self.correct_guesses.clear()  # 清空正确猜测记录
#         self.time_left = 15  # 重置时间
#         self.full_input.setPlaceholderText("请输入完整句子，这句有{}个字".format(len(self.poem)))

#         # 清空尝试的输入框和显示区域
#         for i in reversed(range(self.attempts_layout.count())): 
#             widget = self.attempts_layout.itemAt(i).widget()
#             if widget is not None:
#                 widget.deleteLater()
        
#         self.full_input.clear()  # 清空输入框
#         self.start_time = time.time()  # 重新开始计时
#         print(f"当前诗句: {self.poem}")  # 打印当前诗句以便调试
#         self.timer.start()  # 重新启动计时器
#         self.show()  # 显示游戏窗口

#     def store_user_record(self, user_input, correct_guesses, time_taken):
#         conn = sqlite3.connect('poetry_game.db')
#         cursor = conn.cursor()
#         cursor.execute('INSERT INTO user_records (user_id, user_input, correct_guesses, attempts, time_taken) VALUES (?, ?, ?, ?, ?)',
#                        (self.user_id, user_input, correct_guesses, self.attempt_counter, time_taken))
#         conn.commit()
#         conn.close()

#     def update_leaderboard(self, time_taken):
#         conn = sqlite3.connect('poetry_game.db')
#         cursor = conn.cursor()
#         cursor.execute('INSERT INTO leaderboard (user_id, poem_text, time_taken) VALUES (?, ?, ?)',
#                        (self.user_id, self.poem, time_taken))
#         conn.commit()
#         conn.close()

#     def view_records(self):
#         conn = sqlite3.connect('poetry_game.db')
#         cursor = conn.cursor()
#         cursor.execute('SELECT MIN(time_taken) FROM user_records WHERE user_id = ?', (self.user_id,))
#         fastest_time = cursor.fetchone()[0]
#         conn.close()
        
#         if fastest_time is not None:
#             QMessageBox.information(self, "最快答题记录", f"你的最快答题时间是: {fastest_time:.2f}秒")
#         else:
#             QMessageBox.information(self, "最快答题记录", "你还没有答题记录。")

#     def view_leaderboard(self):
#         conn = sqlite3.connect('poetry_game.db')
#         cursor = conn.cursor()
#         cursor.execute('''
#             SELECT u.username, l.time_taken
#             FROM leaderboard l
#             JOIN users u ON l.user_id = u.id
#             ORDER BY l.time_taken ASC
#             LIMIT 10
#         ''')
#         leaderboard = cursor.fetchall()
#         conn.close()

#         leaderboard_message = "排行榜:\n"
#         for rank, (username, time_taken) in enumerate(leaderboard, start=1):
#             leaderboard_message += f"{rank}. {username} - {time_taken:.2f}秒\n"

#         QMessageBox.information(self, "排行榜", leaderboard_message)

#     def animate_result(self, message):
#         result_box = QMessageBox(self)
#         result_box.setText(message)
#         result_box.setWindowTitle("提示")
        
#         # 动画效果
#         animation = QPropertyAnimation(result_box, b"geometry")
#         animation.setDuration(500)
#         animation.setStartValue(QRect(100, 100, 0, 0))
#         animation.setEndValue(QRect(100, 100, 300, 100))
#         animation.start()
        
#         result_box.exec_()  # 显示消息框

# if __name__ == "__main__":
#     create_database()  # 创建数据库和表
#     if not load_poems():
#         load_poems_from_file('./poem.txt')  # 从文件导入诗句

#     app = QApplication(sys.argv)
#     game = PoetryGame()
#     game.show()
#     sys.exit(app.exec_())

import sys
import random
import sqlite3
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QTimer
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity
from transformers import BertTokenizer, BertModel
import opencc
import time  # 导入时间模块

# 初始化 BERT
tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
model = BertModel.from_pretrained('bert-base-chinese')

def create_database():
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
            time_taken REAL,  -- 新增字段，记录答题时间
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
    conn = sqlite3.connect('poetry_game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, text FROM poems')
    poems = cursor.fetchall()
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

class PoetryGame(QWidget):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.poem = self.load_random_poem()
        self.initUI()

    def load_random_poem(self):
        poems = load_poems()
        return random.choice(poems) if poems else None

    def initUI(self):
        self.setWindowTitle("中文诗句填字游戏")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("用户名")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("登录", self)
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)

        self.register_button = QPushButton("注册", self)
        self.register_button.clicked.connect(self.register)
        layout.addWidget(self.register_button)

        self.setLayout(layout)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        conn = sqlite3.connect('poetry_game.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            self.current_user = user[0]  # 用户ID
            QMessageBox.information(self, "成功", "登录成功！")
            self.start_game()
        else:
            QMessageBox.warning(self, "错误", "用户名或密码错误！")

    def register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        conn = sqlite3.connect('poetry_game.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            QMessageBox.information(self, "成功", "注册成功！请登录。")
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "错误", "用户名已存在！")
        finally:
            conn.close()

    def start_game(self):
        self.game_window = GameWindow(self.current_user, self.load_random_poem())
        self.game_window.show()
        self.close()

class GameWindow(QWidget):
    def __init__(self, user_id, poem):
        super().__init__()
        self.user_id = user_id
        self.poem_id, self.poem_text = poem
        self.language = 'simplified'
        self.previous_attempts = []
        self.attempt_counter = 0  
        self.correct_guesses = set()  
        self.time_left = 15  # 设置初始时间为15秒
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.initUI()

        self.start_time = time.time()  # 开始计时
        # 打印当前诗句以便调试
        print(f"当前诗句: {self.poem_text}")

    def initUI(self):
        self.setWindowTitle("游戏窗口")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        self.timer_label = QLabel(f"剩余时间: {self.time_left}秒", self)
        layout.addWidget(self.timer_label)

        self.full_input = QLineEdit(self)
        self.full_input.setPlaceholderText("请输入完整句子，这句有{}个字".format(len(self.poem_text)))
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

        # 添加查看记录按钮
        self.view_records_button = QPushButton("查看最快答题记录", self)
        self.view_records_button.clicked.connect(self.view_records)
        layout.addWidget(self.view_records_button)

        # 添加查看排行榜按钮
        self.view_leaderboard_button = QPushButton("查看排行榜", self)
        self.view_leaderboard_button.clicked.connect(self.view_leaderboard)
        layout.addWidget(self.view_leaderboard_button)

        self.setLayout(layout)

        # 启动计时器
        self.timer.start(1000)  # 每秒更新

    def update_timer(self):
        self.time_left -= 1
        self.timer_label.setText(f"剩余时间: {self.time_left}秒")
        if self.time_left <= 0:
            self.timer.stop()
            self.show_results()  # 时间到时显示结果

    def switch_language(self):
        if self.language == 'simplified':
            self.language = 'traditional'
            self.setWindowTitle("中文詩句填字遊戲")
            self.submit_button.setText("提交")
            self.switch_language_button.setText("简体中文")
            self.full_input.setPlaceholderText("請輸入完整句子，這句有{}个字".format(len(self.poem_text)))
        else:
            self.language = 'simplified'
            self.setWindowTitle("中文诗句填字游戏")
            self.submit_button.setText("提交")
            self.switch_language_button.setText("繁体中文")
            self.full_input.setPlaceholderText("请输入完整句子，这句有{}个字".format(len(self.poem_text)))

    def is_valid_poem(self, user_input):
        """检查输入的诗句是否在诗词库中"""
        converter = opencc.OpenCC('t2s')  # 繁体转简体
        simplified_input = converter.convert(user_input)
        return any(poem[1] == simplified_input for poem in load_poems())

    def check_answer(self):
        user_input = self.full_input.text()
        self.attempt_counter += 1  
        converter = opencc.OpenCC('t2s')  # 繁体转简体
        user_input = converter.convert(user_input)

        # 检查输入的诗句是否有效
        if not self.is_valid_poem(user_input):
            similarity = calculate_similarity(user_input, self.poem_text)
            if similarity > 0.9:  # 设置一个阈值
                self.animate_result(f"你输入的句子与正确句子相似度为 {similarity:.2f}，请再尝试一下！")
                self.full_input.clear()
            else:
                QMessageBox.warning(self, "错误", "请输入诗词库中的有效诗句！")
                self.full_input.clear()
                return

        if self.attempt_counter > 10:
            self.show_results()
            return

        self.previous_attempts.append(user_input)

        attempt_container = QHBoxLayout()

        for i, char in enumerate(user_input):
            char_input = QLineEdit(self)
            char_input.setReadOnly(True)
            char_input.setFixedSize(40, 40)
            char_input.setAlignment(Qt.AlignCenter)

            if i < len(self.poem_text):  
                if char == self.poem_text[i]:
                    char_input.setStyleSheet("background-color: darkgreen;")
                    self.correct_guesses.add(char)  # 记录正确猜测
                elif char in self.poem_text:
                    char_input.setStyleSheet("background-color: lightgreen;")
                else:
                    char_input.setStyleSheet("background-color: lightgray;")
                char_input.setText(char)

            attempt_container.addWidget(char_input)

        self.attempts_layout.addLayout(attempt_container)

        if user_input == self.poem_text:
            self.show_results()
        else:
            self.animate_result("很遗憾，填字错误。请再试一次！")
            self.full_input.clear()

    def show_results(self):
        correct_chars = ''.join(self.correct_guesses)
        all_guesses = ''.join(self.previous_attempts)
        char_count = Counter(all_guesses)
        most_common = char_count.most_common(1)

        result_message = f"正确猜中的字：{correct_chars}\n"
        if most_common:
            result_message += f"重复最多的字：{most_common[0][0]} (出现次数: {most_common[0][1]})"

        # 计算答题时间
        time_taken = time.time() - self.start_time

        # 存储用户记录
        self.store_user_record(all_guesses, correct_chars, time_taken)

        # 更新排行榜
        self.update_leaderboard(time_taken)

        result_box = QMessageBox(self)
        result_box.setText(f"游戏结束\n正确答案是：{self.poem_text}\n{result_message}\n答题时间: {time_taken:.2f}秒")
        result_box.setWindowTitle("提示")

        # 添加“再来一局”按钮
        replay_button = result_box.addButton("再来一局", QMessageBox.ActionRole)
        exit_button = result_box.addButton("退出", QMessageBox.RejectRole)

        result_box.exec_()  # 显示消息框

        # 根据用户选择的按钮执行相应操作
        if result_box.clickedButton() == replay_button:
            self.replay_game()
        else:
            self.close()  # 退出游戏窗口

    def replay_game(self):
        self.poem_id, self.poem_text = random.choice(load_poems())  # 重新加载随机诗句
        self.attempt_counter = 0
        self.previous_attempts.clear()  # 清空尝试记录
        self.correct_guesses.clear()  # 清空正确猜测记录
        self.time_left = 15  # 重置时间
        self.full_input.setPlaceholderText("请输入完整句子，这句有{}个字".format(len(self.poem_text)))

        # 清空尝试的输入框和显示区域
        for i in reversed(range(self.attempts_layout.count())): 
            widget = self.attempts_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        
        self.full_input.clear()  # 清空输入框
        self.start_time = time.time()  # 重新开始计时
        print(f"当前诗句: {self.poem_text}")  # 打印当前诗句以便调试
        self.timer.start()  # 重新启动计时器
        self.show()  # 显示游戏窗口

    def store_user_record(self, user_input, correct_guesses, time_taken):
        conn = sqlite3.connect('poetry_game.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO user_records (user_id, user_input, correct_guesses, attempts, time_taken) VALUES (?, ?, ?, ?, ?)',
                       (self.user_id, user_input, correct_guesses, self.attempt_counter, time_taken))
        conn.commit()
        conn.close()

    def update_leaderboard(self, time_taken):
        conn = sqlite3.connect('poetry_game.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO leaderboard (user_id, poem_id, time_taken) VALUES (?, ?, ?)',
                       (self.user_id, self.poem_id, time_taken))
        conn.commit()
        conn.close()

    def view_records(self):
        conn = sqlite3.connect('poetry_game.db')
        cursor = conn.cursor()
        cursor.execute('SELECT MIN(time_taken) FROM user_records WHERE user_id = ?', (self.user_id,))
        fastest_time = cursor.fetchone()[0]
        conn.close()
        
        if fastest_time is not None:
            QMessageBox.information(self, "最快答题记录", f"你的最快答题时间是: {fastest_time:.2f}秒")
        else:
            QMessageBox.information(self, "最快答题记录", "你还没有答题记录。")

    def view_leaderboard(self):
        conn = sqlite3.connect('poetry_game.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.username, l.time_taken
            FROM leaderboard l
            JOIN users u ON l.user_id = u.id
            WHERE l.poem_id = ?
            ORDER BY l.time_taken ASC
            LIMIT 10
        ''', (self.poem_id,))
        leaderboard = cursor.fetchall()
        conn.close()

        leaderboard_message = "排行榜:\n"
        for rank, (username, time_taken) in enumerate(leaderboard, start=1):
            leaderboard_message += f"{rank}. {username} - {time_taken:.2f}秒\n"

        QMessageBox.information(self, "排行榜", leaderboard_message)

    def animate_result(self, message):
        result_box = QMessageBox(self)
        result_box.setText(message)
        result_box.setWindowTitle("提示")
        
        # 动画效果
        animation = QPropertyAnimation(result_box, b"geometry")
        animation.setDuration(500)
        animation.setStartValue(QRect(100, 100, 0, 0))
        animation.setEndValue(QRect(100, 100, 300, 100))
        animation.start()
        
        result_box.exec_()  # 显示消息框

if __name__ == "__main__":
    create_database()  # 创建数据库和表
    if not load_poems():
        load_poems_from_file('./poem.txt')  # 从文件导入诗句

    app = QApplication(sys.argv)
    game = PoetryGame()
    game.show()
    sys.exit(app.exec_())