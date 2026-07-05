


import os
from dotenv import load_dotenv

load_dotenv()

key_1 = os.getenv("GOOGLE_API_KEY_1")
key_2 = os.getenv("GOOGLE_API_KEY_2")


print(key_1)
print(key_2)
print(key_1 == key_2)