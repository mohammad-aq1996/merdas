from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
from config.settings import BASE_DIR


def load_private_key_from_file(file_path):
    with open(file_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,  # If your key is encrypted, provide the password here
            backend=default_backend()
        )
    return private_key

def decryption(encrypted_data: str) -> str:
    private_key = load_private_key_from_file(f"{BASE_DIR}/private.pem")
    decrypted_data = private_key.decrypt(
        base64.b64decode(encrypted_data),  # Ensure the data is in bytes
        padding.PKCS1v15()  # Use the same padding as in JSEncrypt
    )
    return decrypted_data.decode('utf-8')