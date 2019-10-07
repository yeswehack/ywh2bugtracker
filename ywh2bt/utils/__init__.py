
import getpass

def read_input(text, secret=False):
    print(text, flush=True, end="")
    if secret:
        return getpass.getpass(prompt='')
    return input()
