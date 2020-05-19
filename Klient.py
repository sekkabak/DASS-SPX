from Client import Client
from KlientUI import Ui_MainWindow

import sys
from PyQt5 import QtWidgets


class Klient:
    client: Client
    ui: Ui_MainWindow

    def __init__(self):
        app = QtWidgets.QApplication(sys.argv)
        main_window = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(main_window)
        self.setup_ui()
        main_window.show()
        sys.exit(app.exec_())

    def setup_ui(self):
        self.ui.label_3.hide()
        self.hide_other_user_connection()
        self.ui.registerInServer.clicked.connect(self.click_register_button)
        self.ui.pushButton.clicked.connect(self.click_connect_to_user)

    def click_register_button(self):
        self.client = Client(self.ui.lineEdit_2.text())
        self.register_in_server()
        if self.client.is_registered:
            self.ui.lineEdit_2.setDisabled(True)
            self.ui.registerInServer.setDisabled(True)
            self.ui.label.setText("Zarejestrowany")
            self.show_other_user_connection()

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
        key = self.client.get_public_key_from_sever(self.ui.lineEdit.text())
        # TODO
        # self.append_text_to_console("Klucz to:")
        # self.append_text_to_console("e: " + str(key.e))
        # self.append_text_to_console("n: " + str(key.n))


if __name__ == "__main__":
    Klient()
