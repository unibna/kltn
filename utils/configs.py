from dataclasses import dataclass
from typing import (
    List,
    Dict
)

@dataclass
class FolderOutMetadata:
    filepath: str = None
    no_file: int = 0


@dataclass
class SplitedPercent:
    train: float = 0
    valid: float = 0
    test: float = 0

    def get_percents(self) -> Dict[str, float]:
        return {"train": self.train,"valid": self.valid,"test": self.test,}

    def verify(self) -> bool:
        if (self.train + self.valid + self.test) > 100:
            return False
        elif (self.train + self.valid + self.test) <= 0:
            return False

        return True

families = [i for i in range(1,10)]
folder_out_list = {
    "train-bytes": FolderOutMetadata(),
    "valid-bytes": FolderOutMetadata(),
    "test-bytes": FolderOutMetadata(),
    "train-img": FolderOutMetadata(),
    "valid-img": FolderOutMetadata(),
    "test-img": FolderOutMetadata(),
}