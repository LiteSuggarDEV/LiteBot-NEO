import random
import string


def generate_captcha(length: int, format: int):
    match format:
        case 0:
            captcha = ""
            for _ in range(length):
                captcha += str(random.randint(0, 9))
            return captcha
        case 1:
            captcha = ""
            for _ in range(length):
                if random.randint(0, 1) == 1:
                    captcha += random.choice(string.ascii_letters)
                else:
                    captcha += str(random.randint(0, 9))
            return captcha
        case 2:
            captcha = ""
            for _ in range(length):
                captcha += random.choice(string.ascii_letters)
            return captcha
        case _:
            captcha = "-1"
    return captcha
