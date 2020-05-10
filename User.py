from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256


class User:
    name: str
    key: RSA.RsaKey
    sign = None

    def __init__(self, name, key: RSA.RsaKey):
        self.name = name
        self.key = key

    def generate_signature(self, server_key: RSA.RsaKey):
        """
        Metoda podpisująca klucz użytkownika
        """
        h = SHA256.new(self.key.publickey().export_key('DER'))
        self.sign = pkcs1_15.new(server_key).sign(h)
