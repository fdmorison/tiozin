from environs import Env

from .registry import Registry


class EnvSecretRegister(Registry):

    def __init__(self):
        super().__init__()
        self.env = Env()
        self.env.read_env()

    def get_secret(self, key: str) -> str:
        return self.env.str(key)
