import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class DynamicFontSizeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.label = QLabel('창 크기에 따라 글꼴 크기가 변경됩니다.', self)
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.setWindowTitle('동적 폰트 크기 조정')
        self.setGeometry(100, 100, 800, 600)
        self.show()

    def resizeEvent(self, event):
        # 창의 높이에 비례하여 폰트 크기를 설정합니다.
        new_font_size = min(500, max(20, self.height() // 20))  # 최소 폰트 크기는 20, 최대 폰트 크기는 100으로 제한
        font = QFont('Arial', new_font_size)
        self.label.setFont(font)
        super().resizeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DynamicFontSizeApp()
    sys.exit(app.exec_())
