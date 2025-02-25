import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QHBoxLayout
from PyQt5.QtCore import Qt

with open('./poem.txt', 'r', encoding='utf-8') as f:
    poems = f.readlines()
    poem = random.choice(poems).strip() 

class PoetryGame(QWidget):
    def __init__(self):
        super().__init__()

        self.previous_attempts = []
        self.attempt_counter = 0  
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

        self.setLayout(layout)

    def check_answer(self):
        user_input = self.full_input.text()
        self.attempt_counter += 1  

        if self.attempt_counter > 10:
            QMessageBox.information(self, "答案", f"超过次数限制，正确答案是：{poem}")
            self.close()  
            return

        self.previous_attempts.append(user_input)

        attempt_container = QHBoxLayout()

        for i, char in enumerate(user_input):
            char_input = QLineEdit(self)
            char_input.setReadOnly(True)
            char_input.setFixedSize(40, 40)
            char_input.setAlignment(Qt.AlignCenter)

            if i < len(poem):  
                if char == poem[i]:
                    char_input.setStyleSheet("background-color: darkgreen;")
                elif char in poem:
                    char_input.setStyleSheet("background-color: lightgreen;")
                else:
                    char_input.setStyleSheet("background-color: lightgray;")
                char_input.setText(char)
            else:
                char_input.setText(char) 

            attempt_container.addWidget(char_input)

        self.attempts_layout.addLayout(attempt_container)

        if user_input == poem:
            QMessageBox.information(self, "结果", "恭喜你，填字正确！")
        else:
            QMessageBox.warning(self, "结果", "很遗憾，填字错误。请再试一次！")

        self.full_input.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = PoetryGame()
    game.show()
    sys.exit(app.exec_())
