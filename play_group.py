import random
import re

from abc import ABC, abstractmethod
from typing import Any

from anki.cards import Card
from bs4 import Tag, BeautifulSoup


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
        self._next_idx = random.randint(0, len(items) - 1)

    def get_play_indices(self) -> list[int]:
        """randomly fetches an item from the group"""
        result = [self.items[self._next_idx]]
        if len(self.items) > 1:
            self._next_idx = self._next_idx + 1 if self._next_idx < len(self.items) - 1 else 0
        return result


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
        if not self.items:
            return []
        result = []
        play_group: PlayGroup
        for play_group in self.items:
            result.extend(play_group.get_play_indices())
        return result

    @classmethod
    def create(cls, card: Card, side: str):
        card_html = card.question() if side == 'question' else card.answer()
        q_a = side[0]
        anki_play_tag_name = f'anki-play-{q_a}'

        def contains_anki_play_tag(ele: Any) -> bool:
            if not isinstance(ele, Tag):
                return False
            if ele.name != 'only-one':
                return False
            if not ele.find(anki_play_tag_name):
                return False
            return True

        rexp = re.compile(fr'\[anki:play:{q_a}:([0-9]+)]')
        card_html = rexp.sub(rf'<{anki_play_tag_name}>\1</{anki_play_tag_name}>', card_html)
        soup = BeautifulSoup(card_html, 'html.parser')
        play_group_list: list[PlayGroup] = []
        anki_play_tag_total = len(re.findall(rf'<{anki_play_tag_name}>\d+</{anki_play_tag_name}>', card_html))
        if not anki_play_tag_total:
            return PlayGroupCollection([])
        only_one_tags = soup.findAll(contains_anki_play_tag)
        if not only_one_tags:
            play_all_group = PlayAllGroup(list(range(anki_play_tag_total)))
            play_group_list.append(play_all_group)
        else:
            for i in range(len(only_one_tags)):
                only_one_tag: Tag = only_one_tags[i]
                only_one_group_items: list[int] = [int(tag.string) for tag in only_one_tag.findAll(anki_play_tag_name)]
                if i == 0:
                    if only_one_group_items[0] > 0:
                        play_all_group = PlayAllGroup(list(range(only_one_group_items[0])))
                        play_group_list.append(play_all_group)
                elif play_group_list[-1].items[-1] < only_one_group_items[0] - 1:
                    play_all_group = PlayAllGroup(
                        list(range(play_group_list[-1].items[-1] + 1, only_one_group_items[0])))
                    play_group_list.append(play_all_group)
                only_one_group = OnlyOneGroup(only_one_group_items)
                play_group_list.append(only_one_group)
            if play_group_list[-1].items[-1] < anki_play_tag_total - 1:
                play_all_group = PlayAllGroup(list(range(play_group_list[-1].items[-1] + 1, anki_play_tag_total)))
                play_group_list.append(play_all_group)
        play_group_collection = PlayGroupCollection(play_group_list)
        return play_group_collection
