import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

KEY = b"TgRUDNSaa0sMPllMTKwEBA=="
def encrypt_message(message):
    iv = get_random_bytes(16)  # Generate a secure IV
    cipher = AES.new(KEY, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(message.encode(), AES.block_size))
    return base64.b64encode(iv + ciphertext).decode()  # Store IV with encrypted text


def decrypt_message(encrypted_message):
    data = base64.b64decode(encrypted_message)  # Decode from base64
    iv, ciphertext = data[:16], data[16:]  # Extract IV and ciphertext
    cipher = AES.new(KEY, AES.MODE_CBC, iv)
    decrypted = unpad(
                cipher.decrypt(ciphertext), AES.block_size
            )  # Unpad and decode
    encrypted_message = decrypted.decode()
        
    return decrypted.decode()
