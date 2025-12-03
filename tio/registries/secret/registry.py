from abc import abstractmethod

from ..registry import Registry


class SecretRegister(Registry):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def get_secret(self, key: str) -> str:
        pass
