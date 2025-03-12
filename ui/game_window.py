from PyQt5.QtWidgets import QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QTimer
import time
import sys
sys.path.append('..')  # 添加上级目录到路径，以便导入其他模块
from collections import Counter
import random
from database import (
    load_poems, store_user_record, update_leaderboard, 
    get_user_fastest_time, get_poem_leaderboard
)
from nlp_model import BertSimilarityModel
from utils import convert_to_simplified, convert_to_traditional, get_random_poem

class GameWindow(QWidget):
    def __init__(self, user_id, poem):
        super().__init__()
        self.user_id = user_id
        self.poem_id, self.poem_text = poem
        self.language = 'simplified'
        self.previous_attempts = []
        self.attempt_counter = 0  
        self.correct_guesses = set()  
        self.time_left = 60  # 设置初始时间为15秒
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.bert_model = BertSimilarityModel()
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
        simplified_input = convert_to_simplified(user_input)
        return any(poem[1] == simplified_input for poem in load_poems())

    def check_answer(self):
        user_input = self.full_input.text()
        self.attempt_counter += 1  
        user_input = convert_to_simplified(user_input)

        # 检查输入的诗句是否有效
        if not self.is_valid_poem(user_input):
            similarity = self.bert_model.calculate_similarity(user_input, self.poem_text)
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
        store_user_record(self.user_id, all_guesses, correct_chars, self.attempt_counter, time_taken)

        # 更新排行榜
        update_leaderboard(self.user_id, self.poem_id, time_taken)

        result_box = QMessageBox(self)
        result_box.setText(f"游戏结束\n正确答案是：{self.poem_text}\n{result_message}\n答题时间: {time_taken:.2f}秒")
        result_box.setWindowTitle("提示")

        # 添加"再来一局"按钮
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
        self.time_left = 60  # 重置时间
        self.full_input.setPlaceholderText("请输入完整句子，这句有{}个字".format(len(self.poem_text)))

        # 清空尝试的输入框和显示区域
        for i in reversed(range(self.attempts_layout.count())): 
            layout_item = self.attempts_layout.itemAt(i)
            if layout_item:
                if layout_item.layout():  # 如果是布局
                    layout = layout_item.layout()
                    for j in reversed(range(layout.count())):
                        widget = layout.itemAt(j).widget()
                        if widget:
                            widget.deleteLater()
                    # 删除空布局
                    # Note: 在PyQt中直接删除布局比较复杂
        
        self.full_input.clear()  # 清空输入框
        self.start_time = time.time()  # 重新开始计时
        print(f"当前诗句: {self.poem_text}")  # 打印当前诗句以便调试
        self.timer.start(1000)  # 重新启动计时器

    def view_records(self):
        """查看用户的最快答题记录"""
        fastest_time = get_user_fastest_time(self.user_id)
        
        if fastest_time is not None:
            QMessageBox.information(self, "最快答题记录", f"你的最快答题时间是: {fastest_time:.2f}秒")
        else:
            QMessageBox.information(self, "最快答题记录", "你还没有答题记录。")

    def view_leaderboard(self):
        """查看当前诗句的排行榜"""
        leaderboard = get_poem_leaderboard(self.poem_id)

        leaderboard_message = "排行榜:\n"
        for rank, (username, time_taken) in enumerate(leaderboard, start=1):
            leaderboard_message += f"{rank}. {username} - {time_taken:.2f}秒\n"

        if not leaderboard:
            leaderboard_message = "暂无排行数据"

        QMessageBox.information(self, "排行榜", leaderboard_message)

    def animate_result(self, message):
        """显示带动画效果的结果信息"""
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