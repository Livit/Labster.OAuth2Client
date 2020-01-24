"""
Cryptographic utilities.
Remember, don't roll out your own crypto, just connect the blocks together.
"""


def sign_rs256(data, key_path):
    """
    Sign the data using RSA with SHA256. Use X509 key in .pem format for signing.
    Use `EMSA-PKCS1-v1_5` signature scheme. `pem key` is the one enclosed
    between "-----BEGIN CERTIFICATE-----" and "-----END CERTIFICATE-----" markers.
    Use renowned `cryptography` lib.

    Notes:
        Currently recommended signature scheme is `EMSA-PSS`. Unfortunately, we
        cannot use it here, as it is not supported by Salesforce's authentication
        server (tested on January 24, 2020). `EMSA-PKCS1-v1_5` that we use is
        still considered secure though, see the reference.

    Reference:
        https://crypto.stackexchange.com/questions/34558/is-ssl-sign-safe-as-it-is-using-openssl-pkcs1-padding
        https://www.cryptoexamples.com/python_cryptography_string_signature_rsa.html

    Args:
        data (bytes): whatever you need signed
        key_path: path to a file containing the key

    Returns:
        str: signature
    """
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.backends import default_backend

    with open(key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(), password=None, backend=default_backend()
        )
    signature = private_key.sign(
        data=data,
        padding=padding.PKCS1v15(),
        algorithm=hashes.SHA256()
    )
    return signature
