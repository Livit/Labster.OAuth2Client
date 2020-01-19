"""
Tests for crypto utils.
"""
import os

from oauth2_client.crypto import sign_rs256
from test_case import StandaloneAppTestCase

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_KEY = os.path.join(CURR_DIR, 'resources', 'test.key')


class TestCrypto(StandaloneAppTestCase):
    """
    Tests for crypto utils.
    """

    def test_sign_rs256(self):
        """
        Current implementation is happily accepted by Salesforce's authentication
        server. Make sure it doesn't change unintentionally.
        """
        input_data = "Hello world!".encode()
        signature_expected = b'k\xb1F\x05\xf7\xbd,\xbf\x8cq\xf7@\xf6\x16\xa0m\x0eR[\xe4\x81\x89j' \
                             b'\xe0\r\x83x\x84\xa5l\x92qP/\xf6\x95\x96\xf1\xfbG\xa0\xde\xb8,\x01' \
                             b'\x9a\xa4i\x00\x9b\x9b\xa4\xdb^\xc6`/j\xcf\xb8$\x8e\x8c\xdd^\xa2p' \
                             b'\x8cXb\xbeinX\xf5\xeeb\x13\x9b9\x1a\xf7\xde\x1ek\xec\xf6\xde1Y' \
                             b'\xdf)\xc4\xd3\xd6\xfe\x1bj\x94\xc0\x16\x88\xe0\x92/8\x18\xfc\x84!' \
                             b'\xc4\x08m$V\x9b\xd7\xb5\xacZ\xa4A\xd7c\xb0\xd7\xa0\xaa'
        signature_actual = sign_rs256(input_data, TEST_KEY)
        self.assertEqual(signature_actual, signature_expected)
