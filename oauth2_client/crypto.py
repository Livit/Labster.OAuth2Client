"""
Cryptographic utilities.
Remeber, don't roll out your own crypto, just connect the blocks together.
"""


def sign_rs256(data, keyfile):
    """
    Sign the data using RSA with SHA256. This uses a renowned `cryptography` lib.

    Args:
        data (bytes): whatever you need signed
        keyfile: path to a file containing the signing X509 key

    Returns:
        str: signature
    """
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.backends import default_backend

    with open(keyfile, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(), password=None, backend=default_backend()
        )
    signature = private_key.sign(
        data=data,
        padding=padding.PKCS1v15(),
        algorithm=hashes.SHA256()
    )
    return signature
