from PyQt5.QtWidgets import QWidget, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt
import random
import sys
sys.path.append('..')  # 添加上级目录到路径，以便导入其他模块
from database import verify_user, register_user, load_poems
from ui.game_window import GameWindow
from utils import get_random_poem

class PoetryGame(QWidget):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.poems = load_poems()
        self.initUI()

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
        
        user = verify_user(username, password)
        
        if user:
            self.current_user = user[0]  # 用户ID
            QMessageBox.information(self, "成功", "登录成功！")
            self.start_game()
        else:
            QMessageBox.warning(self, "错误", "用户名或密码错误！")

    def register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if register_user(username, password):
            QMessageBox.information(self, "成功", "注册成功！请登录。")
        else:
            QMessageBox.warning(self, "错误", "用户名已存在！")

    def start_game(self):
        poem = get_random_poem(self.poems)
        self.game_window = GameWindow(self.current_user, poem)
        self.game_window.show()
        self.close()