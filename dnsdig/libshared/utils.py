import random
import string


def random_chars(length: int = 7) -> str:
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length)).lower()
