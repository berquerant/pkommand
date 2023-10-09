"""Simple functional containers."""
from dataclasses import dataclass
from typing import Any, Callable, Generic, Optional, TypeVar

from .exceptions import ContainerException

T = TypeVar("T")
U = TypeVar("U")


@dataclass
class Opt(Generic[T]):
    """Optional."""

    value: Optional[T]

    @property
    def is_some(self) -> bool:
        """Return true if it's some."""
        return self.value is not None

    def and_then(self, f: Callable[[T], Optional[U]]) -> "Opt[U]":
        """Call `f` if it's some."""
        if self.is_some:
            return Opt(value=f(self.get()))
        return self.none()

    def then(self, f: Callable[[T], None]):
        """Call `f` if it's some."""
        if self.is_some:
            f(self.get())

    def get(self) -> T:
        """Unwrap this."""
        if self.value is not None:
            return self.value
        raise ContainerException("try to get from none")

    def get_or(self, other: T) -> T:
        """Return this if it's some else `other`."""
        if self.value is not None:
            return self.value
        return other

    def flatten(self) -> "Opt":
        """Unwrap `Opt` if it's value is also `Opt`."""
        if self.is_some and isinstance(self.value, Opt):
            return self.value
        return self

    def __eq__(self, other) -> bool:
        """Return true if this == other."""
        if not isinstance(other, Opt):
            return False
        match (self.is_some, other.is_some):
            case (False, False):
                return True
            case (True, True):
                return self.get() == other.get()
            case _:
                return False

    def __bool__(self) -> bool:
        """Return true if it's some."""
        return self.is_some

    def __str__(self) -> str:
        """Return string expression."""
        if self.is_some:
            return f"Opt({self.value})"
        return "none"

    @staticmethod
    def some(value: T) -> "Opt[T]":
        """Return a new some value."""
        return Opt(value=value)

    @staticmethod
    def none() -> "Opt":
        """Return a new none value."""
        return Opt(value=None)

    @staticmethod
    def new(value: Optional[T]) -> "Opt[T]":
        """Return a new `Opt`."""
        return Opt(value=value)


def get_attribute(obj: Any, name: str) -> Opt:
    """
    Wrap `getattr()`.

    if obj has name attr then some, else none.
    Note: obj has name attr and the value is None then none.
    """
    if hasattr(obj, name):
        return Opt.new(getattr(obj, name))
    return Opt.none()
