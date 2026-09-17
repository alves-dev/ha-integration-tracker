"""Provider contracts for Integration Tracker."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import ProviderItem


class ProviderError(Exception):
    """Base provider failure."""


class ProviderUnavailableError(ProviderError):
    """Raised when a provider cannot return a trustworthy snapshot."""


class IntegrationProvider(ABC):
    """Source-neutral provider interface."""

    source: str

    @abstractmethod
    async def async_discover(self) -> list[ProviderItem]:
        """Return a complete snapshot of currently installed items."""
