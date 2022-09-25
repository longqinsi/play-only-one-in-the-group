import random

from abc import ABC, abstractmethod


class PlayGroup(ABC):
    def __init__(self, items: list[int]):
        if not items:
            raise ValueError("items can't be empty.")
        self.items = items

    @abstractmethod
    def get_play_indices(self) -> list[int]:
        """get the items to play from the group"""
        pass

    def __len__(self):
        return len(self.items)


class OnlyOneGroup(PlayGroup):
    """Only One Group, randomly plays an item in the group"""

    def __init__(self, items: list[int]):
        super().__init__(items)

    def get_play_indices(self) -> list[int]:
        """randomly fetches an item from the group"""
        idx = random.randint(0, len(self.items) - 1)
        return [self.items[idx]]


class PlayAllGroup(PlayGroup):
    """Play All Group, plays all the items in the group."""

    def __init__(self, items: list[int]):
        super().__init__(items)

    def get_play_indices(self) -> list[int]:
        return self.items


class PlayGroupCollection:
    def __init__(self, items: list[PlayGroup] = None):
        self.items = items if items else []

    def append(self, play_group: PlayGroup) -> None:
        self.items.append(play_group)

    def get_play_indices(self) -> list[int]:
        result = []
        play_group: PlayGroup
        for play_group in self.items:
            result.extend(play_group.get_play_indices())
        return result
