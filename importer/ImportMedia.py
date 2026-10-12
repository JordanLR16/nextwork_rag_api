from abc import ABC, abstractmethod

class ImportMedia(ABC):

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        pass

    @abstractmethod
    def import_media(self, url: str):
        pass