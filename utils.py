import os
import hashlib

username_pattern = r'[A-Za-z0-9_-]{4,10}'
password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[.-_@$!%*?&])[A-Za-z\d.-_@$!%*?&]{8,}$'
email_pattern = r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
name_pattern = r'[A-Za-z0-9 ]{5,30}'

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    salted_password = salt + password.encode('utf-8')
    hashed_password = hashlib.sha256(salted_password).hexdigest()
    return salt.hex() + hashed_password

def verify_password(stored_hash: str, password: str) -> bool:
    salt = bytes.fromhex(stored_hash[:32])
    salted_password = salt + password.encode('utf-8')
    hashed_password = hashlib.sha256(salted_password).hexdigest()
    return stored_hash[32:] == hashed_password