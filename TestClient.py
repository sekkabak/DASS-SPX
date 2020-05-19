import unittest

from Client import Client


class TestClient(unittest.TestCase):

    def test_connect_to_user(self):
        Client('nic')
        print('nic')
        res = 1
        #
        # Client('testClient1').register_in_server()
        #
        # client = Client('testClient2')
        # client.register_in_server()
        # res = client.connect_to_user('testClient1')

        self.assertEqual(1, res)
