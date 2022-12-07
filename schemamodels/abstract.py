from abc import ABC, abstractmethod
from typing import Callable


class BaseErrorHandler(ABC):

    @classmethod
    @abstractmethod
    def apply(cls, f: Callable) -> Callable:
        raise NotImplementedError()

    @classmethod
    def __subclasshook__(cls, klass):
        if cls is ErrorHandler:
            if "apply" in klass.__dict__:
                return True
        return NotImplementedError()


class BaseRenderer(ABC):

    @classmethod
    @abstractmethod
    def apply(cls, f: Callable) -> Callable:
        raise NotImplementedError()

    @classmethod
    def __subclasshook__(cls, klass):
        if cls is Renderer:
            if "apply" in klass.__dict__:
                return True
        return NotImplementedError()
