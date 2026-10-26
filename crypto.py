"""Hash master passwords and encrypt each saved login."""
import json
import os

from argon2 import PasswordHasher
from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

password_hasher = PasswordHasher()


def derive_key(password, salt):
    # This salt is separate from the one inside the login password hash.
    return hash_secret_raw(password.encode(), salt, time_cost=3,
                           memory_cost=65536, parallelism=4,
                           hash_len=32, type=Type.ID)


def encrypt_item(key, user_id, fields):
    nonce = os.urandom(12)
    data = json.dumps(fields).encode()
    encrypted = AESGCM(key).encrypt(nonce, data, str(user_id).encode())
    return nonce, encrypted


def decrypt_item(key, user_id, row):
    data = AESGCM(key).decrypt(row['nonce'], row['encrypted_data'],
                               str(user_id).encode())
    return json.loads(data)
