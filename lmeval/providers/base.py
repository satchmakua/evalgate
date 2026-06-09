"""Provider interface. A provider knows how to turn messages into a Completion."""

from abc import ABC, abstractmethod

from ..types import Completion


class Provider(ABC):
    name = "base"

    @abstractmethod
    def complete(self, model, messages, options=None) -> Completion:
        ...

    def available(self) -> bool:
        """Whether this provider is usable right now (server up / key present)."""
        return True
