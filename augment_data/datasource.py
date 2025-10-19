

from abc import abstractmethod
from typing import Any, Optional


class AddressAugmentationDatasource:
    """
    A class which provides additional information when provided an address.
    """
    @abstractmethod
    def query(self, address: str) -> Optional[Any]:
        """
        Get additional information based on the provided address. 
        The return value should be an instance of a dataclass.
        """
