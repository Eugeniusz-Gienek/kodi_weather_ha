from abc import abstractmethod


class _ValueWithUnit:
    unit: str

    def __init__(self, value: float):
        self.value = value

    @abstractmethod
    def si_value(self) -> float:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def from_si_value(value: float) -> '_ValueWithUnit':
        raise NotImplementedError
