import pickle
import socket

from typing import List, Optional

from Crypto.PublicKey import RSA

from Codes import Codes
from User import User


class Server:
    """
    | Kody które akceptuje serwer
    | 1 - pierwsze połączenie z serwerem czyli podanie swojej nazwy i klucza
    | 2 - poproszenie serwera o klucz innej osoby po wysłanej nazwie
    """
    my_socket = ('127.0.0.1', 44444)
    sock = None

    key: RSA.RsaKey

    users: List[User] = []

    def start(self):
        """
        Główna metoda startująca serwer
        """
        # Generowanie klucza RSA
        self.key = RSA.generate(1024)

        print("Starting server")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(self.my_socket)
        self._listen()

    def _listen(self):
        """
        Nasłuchuje w pętli płączeń od klientów
        """
        while True:
            self.sock.listen()
            conn, addr = self.sock.accept()
            with conn:
                print('Połączenie przychodzące z: ', addr)

                code = conn.recv(1)
                if int.from_bytes(code, 'big') == 1:
                    self._add_user(conn)
                elif int.from_bytes(code, 'big') == 2:
                    self._send_public_key_by_name(conn)

                print('Połączenie zamknięte z:', addr)

    def _add_user(self, conn: socket):
        """
        Metoda serwera która rejestruje użytkownika i podpisuje jego klucz publiczny
        """
        # pobranie nazwy od uzytkownika
        name = conn.recv(1024)
        if not name or self._is_name_used(name):
            conn.send(Codes.err)
            return conn.close()
        else:
            conn.send(Codes.ok)

        # pobranie klucza od uzytkownika
        key = conn.recv(2048)
        if not key:
            conn.send(Codes.err)
            return conn.close()

        # tworzenie użytkownika
        new_user = User(name, RSA.import_key(key))
        # podpisywanie klucza użytkonika
        new_user.generate_signature(self.key)

        # dodaje użytkownika
        res = self._add_user_to_list(new_user)
        if res is False:
            conn.send(Codes.err)
            return conn.close()
        else:
            conn.send(Codes.ok)

        print('Dodaję użytkownika: ', name)
        # wysłanie klucza publicznego
        conn.send(self.key.publickey().exportKey('DER'))

        # koniec transmisji
        conn.close()

    def _send_public_key_by_name(self, conn: socket):
        """
        Metoda serwera która wysyła klucz publiczny użytkownika po podanej nazwie
        """
        # pobranie nazwy uzytkownika
        name = conn.recv(1024)
        if not name:
            conn.send(Codes.err)
            return conn.close()
        elif not self._is_name_used(name):
            conn.send(Codes.nul)
            return conn.close()
        else:
            conn.send(Codes.ok)

        # wyszukanie nazwy użytkownika na liście
        user = self._get_user_by_name(name)
        message = (user.key.publickey().export_key('DER'), user.sign)
        data = pickle.dumps(message)
        print('Wysyłam użytkownikowi klucza użytkownika: ', user.name)
        conn.send(data)
        conn.close()

    def _add_user_to_list(self, user: User) -> bool:
        """
        Dodaje użytkowika do listy jeśli jego nazwa wcześniej nie została zajęta

        | Zwraca:
        | True - dodał użytkownika
        | False - użytkownik o tej nazwie już istnieje
        """
        if self._is_name_used(user.name):
            return False

        self.users.append(user)
        return True

    def _is_name_used(self, name: str) -> bool:
        """
        | Zwraca True jeśli imie jest zajęte
        | Fale jeśli jest wolne
        """
        for x in self.users:
            if x.name == name:
                return True

        return False

    def _get_user_by_name(self, name: str) -> Optional[User]:
        """
        Zwraca uzytkownika z listy po jego nazwie

        | Zwraca:
        | User object jeśli istnieje
        | None jeśli nie istnieje
        """
        for user in self.users:
            if user.name == name:
                return user
        return None


Server().start()
