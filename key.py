import os
import binascii

random_bytes = os.urandom(24)

secret_key = binascii.hexlify(random_bytes).decode('utf-8')

print(secret_key)