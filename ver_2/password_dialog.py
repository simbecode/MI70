
# password_dialog.py

import sys
from PyQt5 import QtWidgets
import hashlib

class PasswordDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("비밀번호 입력")
        # 비밀번호를 일반 텍스트로 저장
        self.correct_password_hash = "1234"
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()

        label = QtWidgets.QLabel("비밀번호를 입력하세요:")
        layout.addWidget(label)

        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addWidget(self.password_edit)

        button_layout = QtWidgets.QHBoxLayout()
        ok_button = QtWidgets.QPushButton("확인")
        ok_button.clicked.connect(self.check_password)
        cancel_button = QtWidgets.QPushButton("취소")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def check_password(self):
        entered_password = self.password_edit.text()
        if entered_password == self.correct_password_hash:
            # QtWidgets.QMessageBox.information(self, "인증 성공", "올바른 비밀번호입니다.")
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(self, "인증 실패", "비밀번호가 틀렸습니다.")
            self.password_edit.clear()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    dialog = PasswordDialog()
    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        print("인증 성공")
    else:
        print("인증 실패")
    sys.exit()

# '''