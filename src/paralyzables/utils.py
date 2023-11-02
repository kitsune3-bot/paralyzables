def is_ascii(string: str) -> bool:
    for char in string:
        if ord(char) >= 128:
            return False
    return True
