import pickle
import socket

from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

from Codes import Codes


class Client:
    """
    | Kody które akceptuje serwer
    | 1 - pierwsze połączenie z serwerem czyli podanie swojej nazwy i klucza
    | 2 - poproszenie serwera o klucz innej osoby po wysłanej nazwie
    """
    HOST = '127.0.0.1'
    PORT = 44444
    sock = None

    name: str
    key: RSA.RsaKey
    server_public_key: RSA.RsaKey

    is_registered = False

    consoleAppend: None

    def __init__(self, name: str):
        # Generowanie klucza RSA
        self.key = RSA.generate(1024)

        # przypisanie nazwy
        self.name = name

    def register_in_server(self):
        """
        Metoda obsługuje rejestrację na serwerze wyświetlając komunikaty
        """
        res = self._register_in_server()
        if res == 0:
            self.is_registered = True
        else:
            self.is_registered = False
        return res

    def communicate_to_user_with_name(self):
        key = self.get_public_key_from_sever()

    def get_public_key_from_sever(self, username):
        """
        Metoda pobierająca z serwera klucz publiczny danego użytkownika

        | Zwraca:
        | RSA.RsaKey - jeśli otrzymano klucz i jest on poprawny,
        | 1 - błąd(nieokreślony),
        | 2 - taki użytkownik nie istnieje
        | 3 - klucz jest błędny
        """
        self._socket_connect()

        self.sock.send(bytes([2]))
        # wysyła nazwę użytkownika oraz obsługuje odpowiedź
        self.sock.send(str.encode(username))
        res = self.sock.recv(4)
        if res == Codes.err:
            self.sock.close()
            return 1
        elif res == Codes.nul:
            self.sock.close()
            return 2

        # pobranie klucza oraz jego podpisu

        data = self.sock.recv(4096)
        key, sign = pickle.loads(data)

        # sprawdzenie poprawności klucza
        if not self._verify_sign(sign, key):
            self.sock.close()
            return 3

        self.sock.close()
        return RSA.import_key(key)

    def _register_in_server(self) -> int:
        """
        Metoda wykonująca rejestracje klienta na serwerze
        podjac mu swoja nazwe oraz klucz

        | Zwraca:
        | 0 - jeśli został zarejestrowany,
        | 1 - błąd(nieokreślony),
        | 2 - taka nazwa jest już zajęta
        | 3 - błąd otrzymywania klucza publicznego serwera
        """
        self._socket_connect()

        # wysyła kod 1 czyli kod do rejestracji
        self.sock.send(bytes([1]))
        # wysyła nazwę użytkownika
        self.sock.send(str.encode(self.name))
        # odpowiedz od serwera czy taka nazwa użytkownika jest jeszcze dostępna
        if self.sock.recv(4) == Codes.err:
            self.sock.close()
            return 2

        # wysłanie klucza
        self.sock.send(self.key.publickey().exportKey('DER'))
        if self.sock.recv(4) == Codes.err:
            self.sock.close()
            return 1

        # otrzymanie klucza publicznego serwera
        try:
            self.server_public_key = RSA.import_key(self.sock.recv(2048))
        except:
            self.sock.close()
            return 3

        # zamknięcie połączenia
        self.sock.close()

        return 0

    def _verify_sign(self, sign, value) -> bool:
        """
        Zwraca True jeśli podpis jest zgodny z klucze, w przeciwnym wypadku false
        """
        try:
            pkcs1_15.new(self.server_public_key).verify(SHA256.new(value), sign)
            return True
        except (ValueError, TypeError):
            return False

    def _socket_connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.HOST, self.PORT))
