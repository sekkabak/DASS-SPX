from Client import Client
from KlientUI import Ui_MainWindow

import sys
from PyQt5 import QtWidgets, QtCore


class Klient:
    client: Client
    ui: Ui_MainWindow
    port: int
    checkThreadTimer: QtCore.QTimer

    def __init__(self, port: int = 44445):
        self.port = port

        app = QtWidgets.QApplication(sys.argv)
        main_window = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(main_window)
        self.timer = QtCore.QTimer()
        self.setup_ui()
        main_window.show()
        sys.exit(app.exec_())

    def setup_ui(self):
        self.ui.label_3.hide()
        self.hide_other_user_connection()
        self.ui.registerInServer.clicked.connect(self.click_register_button)
        self.ui.pushButton.clicked.connect(self.click_connect_to_user)

    def click_register_button(self):
        self.client = Client(self.ui.lineEdit_2.text(), self.port)
        self.print_client_messages()
        self.timer.timeout.connect(self.print_client_messages)
        self.timer.start(1000)
        self.register_in_server()
        if self.client.is_registered:
            self.ui.lineEdit_2.setDisabled(True)
            self.ui.registerInServer.setDisabled(True)
            self.ui.label.setText("Zarejestrowany")
            self.show_other_user_connection()

            # włączenie nasłuchiwanie połączenia od użytkownika
            self.client.read_the_socket()
            # self.checkThreadTimer = QtCore.QTimer()
            # self.checkThreadTimer.setInterval(1000)
            # self.checkThreadTimer.timeout.connect(self.client.read_the_socket)
            # self.checkThreadTimer.start()

    def append_text_to_console(self, message):
        self.ui.textEdit.setPlainText(self.ui.textEdit.toPlainText() + '\n' + message)

    def hide_other_user_connection(self):
        self.ui.label_2.hide()
        self.ui.lineEdit.hide()
        self.ui.pushButton.hide()

    def show_other_user_connection(self):
        self.ui.label_2.show()
        self.ui.lineEdit.show()
        self.ui.pushButton.show()

    def register_in_server(self):
        res = self.client.register_in_server()
        if res == 0:
            self.append_text_to_console("Rejestracja na serwerze powiodła się")
        elif res == 1:
            self.append_text_to_console("Rejestracja na serwerze NIE powiodła się")
        elif res == 2:
            self.append_text_to_console("Rejestracja na serwerze NIE powiodła się, taka nazwa użytkownika jest już "
                                        "zajęta")
        elif res == 3:
            self.append_text_to_console("Rejestracja na serwerze NIE powiodła się, błąd pobierania klucza serwera")

    def click_connect_to_user(self):
        self.client.connect_to_user(self.ui.lineEdit.text())
        if self.client.is_connected:
            self.append_text_to_console("Połączenie z użytkownikiem: " + self.ui.lineEdit.text() + " zostało "
                                                                                                   "ustanowione")
        else:
            self.append_text_to_console("Połączenie z użytkownikiem: " + self.ui.lineEdit.text() + " NIE zostało "
                                                                                                   "ustanowione")

    def print_client_messages(self):
        while not self.client.to_display.empty():
            self.append_text_to_console(self.client.to_display.get())


if __name__ == "__main__":
    Klient(44445)
