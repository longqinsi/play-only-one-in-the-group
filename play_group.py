import random

from abc import ABC, abstractmethod


class PlayGroup(ABC):
    """播放组"""
    def __init__(self, items: list[int]):
        self.items = items

    @abstractmethod
    def get_items_to_play(self) -> list[int]:
        """获取待播放对象列表"""
        pass

    def __len__(self):
        return len(self.items)


class OnlyOneGroup(PlayGroup):
    """单项播放组，每次只播放一个对象"""

    def __init__(self, items: list[int], idx_first_to_play: int = -1):
        super().__init__(items)
        if len(items) > 0:
            if idx_first_to_play >= 0:
                self.idx_next_to_play = idx_first_to_play
            else:
                self.idx_next_to_play = random.randint(0, len(items) - 1)
        else:
            self.idx_next_to_play = -1

    def get_items_to_play(self) -> list[int]:
        result = self.items[self.idx_next_to_play]
        if self.idx_next_to_play >= len(self.items) - 1:
            self.idx_next_to_play = 0
        else:
            self.idx_next_to_play += 1
        return [result]


class PlayAllGroup(PlayGroup):
    """全部播放组，每次都播放全部对象"""

    def __init__(self, items: list[int]):
        super().__init__(items)

    def get_items_to_play(self) -> list[int]:
        return self.items


class PlayGroupManager:
    """播放组管理器"""
    def __init__(self, items: list[PlayGroup] = None):
        self.items = items if items else []

    def append(self, play_group: PlayGroup) -> None:
        self.items.append(play_group)

    def get_items_to_play(self) -> list[int]:
        result = []
        play_group: PlayGroup
        for play_group in self.items:
            result.extend(play_group.get_items_to_play())
        return result


question_play_groups: list[PlayGroup] = []
"""问题卡面的播放对象组列表"""

answer_play_groups: list[PlayGroup] = []
"""答案卡面的播放对象组列表"""
