import pickle
import socket
import threading
import time

from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes
from Crypto.Cipher import DES, PKCS1_v1_5
from Crypto.Signature import pkcs1_15

from Codes import Codes


class Client:
    """
    | Kody które akceptuje serwer
    | 1 - pierwsze połączenie z serwerem czyli podanie swojej nazwy i klucza
    | 2 - poproszenie serwera o klucz innej osoby po wysłanej nazwie
    """
    server_socket = ('127.0.0.1', 44444)
    my_socket = ('127.0.0.1', 44445)
    sock = None
    receive_sock = None

    name: str
    key: RSA.RsaKey
    server_public_key: RSA.RsaKey

    is_registered = False

    consoleAppend: None

    def __init__(self, name: str):
        # TODO sprawdzić czy socket jest już używany
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receive_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receive_sock.bind(self.my_socket)

        # Generowanie klucza RSA
        self.key = RSA.generate(1024)

        # przypisanie nazwy
        self.name = name

        # nasłuchiwanie połączenie od innego użytkownika
        self._set_contact_listener()

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

    def get_public_key_from_sever(self, username: str):
        """
        Metoda pobierająca z serwera klucz publiczny danego użytkownika

        | Zwraca:
        | RSA.RsaKey - jeśli otrzymano klucz i jest on poprawny,
        | 1 - błąd(nieokreślony),
        | 2 - taki użytkownik nie istnieje
        | 3 - klucz jest błędny
        """
        self._socket_connect_to_server()

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

    # TODO dokończyć
    def connect_to_user(self, username: str):
        """
        Łączy sie z użytkownikiem po podanej nazwie użytkownika

        | Zwraca:
        | 1 - jeśli połączenie zostało ustanowione,
        | -1 - błąd(nieokreślony),
        """
        b_key: RSA.RsaKey = self.get_public_key_from_sever(username)
        if b_key is not RSA.RsaKey:
            return -1

        K = get_random_bytes(1024)
        K_key = RSA.generate(1024)
        T_A = int(time.time())
        L = 3600  # jedna godzina w sekundach

        cipher = DES.new(K, DES.MODE_OFB)
        a = cipher.iv + cipher.encrypt(T_A)

        b = pickle.dumps((L, self.name, K_key))
        h = SHA256.new(b)
        b_sign = pkcs1_15.new(self.key).sign(h)

        c = PKCS1_v1_5.new(b_key).encrypt(K)
        h = SHA256.new(c)
        c_sign = pkcs1_15.new(K_key).sign(h)

        pickle.dumps((a, b, b_sign, c, c_sign))

        return 1

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
        self._socket_connect_to_server()

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

    def _set_contact_listener(self):
        """
        Uruchamia metodę _listen co 5 sekund
        """
        threading.Timer(5.0, self._listen).start()

    def _listen(self):
        """
        Nasłuchuje w pętli połączeń od innych użytkowników
        """
        print('lul')
        self.receive_sock.listen()
        conn, addr = self.receive_sock.accept()
        with conn:
            print('Connected by', addr)
            # zrobić początek komunikacji
            code = conn.recv(4)
            # TODO zrobić odesłanie potwierdzenia
            self._receive_contact(conn.recv(1024))
            print('Connection closed', addr)
        self._set_contact_listener()

    def _receive_contact(self, data):
        """
        Po otrzymaniu kontaktu przez innego użytkownika sprawdzamy wysłane dane

        | Zwraca:
        | 0 - połączenie może zostać ustanowione
        | -1 - klucz użytkownika o podanej nazwie otrzymany od servera jest niepoprawny
        | -2 - znacznik czasu jest niepoprawny
        | -3 - przesłane dane są niepoprawne
        """
        a, b, b_sign, c, c_sign = pickle.loads(data)

        a_key: RSA.RsaKey = self.get_public_key_from_sever(b[1])
        if a_key is not RSA.RsaKey:
            return -1

        K = PKCS1_v1_5.new(self.key).decrypt(c)
        T_A = DES.new(K, DES.MODE_OFB).decrypt(a)

        if int(time.time()) > (T_A + b[0]):
            return -2

        try:
            pkcs1_15.new(a_key).verify(SHA256.new(b), b_sign)
            pkcs1_15.new(b[2]).verify(SHA256.new(c), c_sign)
        except (ValueError, TypeError):
            return -3

        return 0

    def _socket_connect_to_server(self):
        self.sock.connect(self.server_socket)

    def _socket_connect_to_client(self):
        self.sock.connect(self.my_socket)
