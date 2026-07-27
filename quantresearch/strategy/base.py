from abc import ABC
from abc import abstractmethod


class BaseStrategy(ABC):

    @abstractmethod
    def generate(self, prices):
        pass