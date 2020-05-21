import pickle
import socket
import threading
import time
import queue

from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_v1_5, AES
from Crypto.Signature import pkcs1_15

from Codes import Codes


class Client:
    """
    | Kody które akceptuje serwer
    | 1 - pierwsze połączenie z serwerem czyli podanie swojej nazwy i klucza
    | 2 - poproszenie serwera o klucz innej osoby po wysłanej nazwie
    """
    server_socket = ('127.0.0.1', 44444)
    client1_socket = ('127.0.0.1', 44445)
    client2_socket = ('127.0.0.1', 44446)

    sock = None
    receive_sock = None

    name: str
    key: RSA.RsaKey
    server_public_key: RSA.RsaKey

    is_registered = False
    is_connected = False

    to_display = queue.Queue()

    def __init__(self, name: str, port: int = 44445):
        # TODO na sztywno
        self.client1_socket = ('127.0.0.1', port)
        if port == 44446:
            self.client2_socket = ('127.0.0.1', 44445)

        # Generowanie klucza RSA
        self.key = RSA.generate(1024)

        # przypisanie nazwy
        self.name = name

    def register_in_server(self):
        """
        Metoda obsługuje rejestrację na serwerze wyświetlając komunikaty
        """
        self._socket_connect_to_server()

        res = self._register_in_server()
        if res == 0:
            self.is_registered = True
        else:
            self.is_registered = False

        self.sock.close()
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

    def connect_to_user(self, username: str):
        """
        Łączy sie z użytkownikiem po podanej nazwie użytkownika

        | Zwraca:
        | 1 - jeśli połączenie zostało ustanowione,
        | -1 - błąd(nieokreślony),
        | -2 - użytkownik nie odrzucił połączenie
        """
        b_key: RSA.RsaKey = self.get_public_key_from_sever(username)
        if type(b_key) is not RSA.RsaKey:
            # TODO dodać kod o niepoprawnym kluczu
            return -1

        self._socket_connect_to_client()
        self.sock.send(Codes.connection_request)
        if self.sock.recv(4) != Codes.ok:
            return -2

        K = get_random_bytes(16)
        K_key = RSA.generate(1024)
        T_A = str(int(time.time()))
        L = 3600  # jedna godzina w sekundach

        cipher = AES.new(K, AES.MODE_EAX)
        nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(T_A.encode("utf-8"))
        a = (nonce, ciphertext, tag)

        b = pickle.dumps((L, self.name, K_key.export_key('DER')))
        h = SHA256.new(b)
        b_sign = pkcs1_15.new(self.key).sign(h)

        c = PKCS1_v1_5.new(b_key).encrypt(K)
        h = SHA256.new(c)
        c_sign = pkcs1_15.new(K_key).sign(h)

        data = pickle.dumps((a, b, b_sign, c, c_sign))

        self.sock.sendall(data)

        if self.sock.recv(4) != Codes.ok:
            return -1
        self.is_connected = True
        self.sock.close()

        return 1

    def read_the_socket(self):
        """
        Nasłuchuje w pętli połączeń od innych użytkowników
        """
        thread = threading.Thread(target=self._read_the_socket)
        thread.daemon = True
        thread.start()

    def _read_the_socket(self):
        """
        Metoda otwierana w wątku sprawdzająca czy spłyneło jakieś połączenie
        """
        self.to_display.put('Słucham ...')
        self.receive_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receive_sock.bind(self.client1_socket)
        self.receive_sock.listen(3)
        conn, addr = self.receive_sock.accept()
        with conn:
            self.to_display.put('Połączenie przychodzące z: ' + str(addr))

            if conn.recv(4) == Codes.connection_request:
                conn.send(Codes.ok)
                res = self._receive_contact(conn.recv(4096))
                self.to_display.put('Próba połączenia zakończona kodem: ' + str(res))
                if res == 0:
                    conn.send(Codes.ok)
                    self.is_connected = True
                    self.to_display.put("Połączenie zostało ustanowione")
                else:
                    conn.send(Codes.err)
                    self.is_connected = False
                    self.to_display.put("Połączenie NIE zostało ustanowione")

            self.to_display.put('Połączenie zamknięte z:' + str(addr))
        self.to_display.put('Już nie słucham')
        self.receive_sock.close()

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

        # wysyła kod 1 czyli kod do rejestracji
        self.sock.send(bytes([1]))
        # wysyła nazwę użytkownika
        self.sock.send(str.encode(self.name))
        # odpowiedz od serwera czy taka nazwa użytkownika jest jeszcze dostępna
        if self.sock.recv(4) == Codes.err:
            return 2

        # wysłanie klucza
        self.sock.send(self.key.publickey().exportKey('DER'))
        if self.sock.recv(4) == Codes.err:
            return 1

        # otrzymanie klucza publicznego serwera
        try:
            self.server_public_key = RSA.import_key(self.sock.recv(2048))
        except ValueError or IndexError or TypeError:
            return 3

        return 0

    def _verify_sign(self, sign, value) -> bool:
        """
        Zwraca True jeśli podpis jest zgodny z kluczem, w przeciwnym wypadku false
        """
        try:
            pkcs1_15.new(self.server_public_key).verify(SHA256.new(value), sign)
            return True
        except (ValueError, TypeError):
            return False

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
        b = pickle.loads(b)
        a_key: RSA.RsaKey = self.get_public_key_from_sever(b[1])
        if type(a_key) is not RSA.RsaKey:
            return -1

        K = PKCS1_v1_5.new(self.key).decrypt(c, None)
        cipher = AES.new(K, AES.MODE_EAX, nonce=a[0])
        plaintext = cipher.decrypt(a[1])
        try:
            cipher.verify(a[2])
            T_A = int(plaintext)
        except ValueError:
            return -3

        if int(time.time()) > (T_A + b[0]):
            return -2

        try:
            # TODO przerobić _verify_sign
            pkcs1_15.new(a_key).verify(SHA256.new(pickle.dumps(b)), b_sign)
            pkcs1_15.new(RSA.import_key(b[2])).verify(SHA256.new(c), c_sign)
        except (ValueError, TypeError):
            return -3

        return 0

    def _socket_connect_to_server(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.server_socket)

    def _socket_connect_to_client(self):
        # TODO tak na sztywno :(
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.client2_socket)
