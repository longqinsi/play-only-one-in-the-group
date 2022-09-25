import re
from re import Match
from typing import Optional, Any

import anki
from anki.cards import Card
from anki.sound import SoundOrVideoTag
from aqt import gui_hooks
from aqt.browser.previewer import Previewer
from aqt.clayout import CardLayout
from aqt.reviewer import Reviewer
from bs4 import BeautifulSoup
from bs4.element import Tag

from .play_group import *


def get_play_indices_attr_name(status: str) -> str:
    if status != 'question' and status != 'answer':
        raise ValueError(f"status '{status}' is not 'question' or 'answer'")
    return f'{status}_play_indices'


def get_play_indices(card: Card, side: str) -> list[int]:
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
        return []
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
                play_all_group = PlayAllGroup(list(range(play_group_list[-1].items[-1] + 1, only_one_group_items[0])))
                play_group_list.append(play_all_group)
            only_one_group = OnlyOneGroup(only_one_group_items)
            play_group_list.append(only_one_group)
        if play_group_list[-1].items[-1] < anki_play_tag_total - 1:
            play_all_group = PlayAllGroup(list(range(play_group_list[-1].items[-1] + 1, anki_play_tag_total)))
            play_group_list.append(play_all_group)
    play_group_collection = PlayGroupCollection(play_group_list)
    return play_group_collection.get_play_indices()


def get_play_list(tags: list[anki.sound.AVTag], side: str, card: Card) -> list[int]:
    if side not in ['question', 'answer']:
        raise ValueError(f"{side} is invalid for side, which must be either 'question' nor 'answer'.")
    play_indices = sorted(get_play_indices(card, side))
    if len(play_indices) == len(tags):
        return play_indices
    new_tags = [tags[idx] for idx in play_indices]
    tags.clear()
    tags.extend(new_tags)
    setattr(card, get_play_indices_attr_name(side), play_indices)
    return play_indices


def on_av_player_will_play_tags(tags: list[anki.sound.AVTag], side: str, context: Any) -> None:
    card: Optional[Card] = None
    if not tags:
        return
    if isinstance(context, CardLayout):
        card = context.rendered_card
    elif isinstance(context, Reviewer):
        card = context.card
    elif isinstance(context, Previewer):
        card = context.card()
    if not card:
        return
    get_play_list(tags, side, card)


def on_card_will_show(text: str, card: Card, _kind: str) -> str:
    question_play_indices_attr_name = get_play_indices_attr_name("question")
    answer_play_indices_attr_name = get_play_indices_attr_name("answer")
    question_play_indices: list[int]
    if hasattr(card, question_play_indices_attr_name):
        question_play_indices = getattr(card, question_play_indices_attr_name)
    else:
        question_play_indices = get_play_list(card.question_av_tags(), 'question', card)

    answer_play_indices: list[int]
    if hasattr(card, answer_play_indices_attr_name):
        answer_play_indices = getattr(card, answer_play_indices_attr_name)
    else:
        answer_play_indices = get_play_list(card.answer_av_tags(), "answer", card)

    if not question_play_indices and not answer_play_indices:
        return text

    rexp = re.compile(r"""<a class="replay-button soundLink" href=# onclick="pycmd\('play:([qa]):(\d+)'\);"""
                      + """ return false;">""")
    matches: list[Match] = []
    pos = 0
    while pos < len(text):
        match = rexp.search(text, pos)
        if match:
            matches.append(match)
            pos = match.end(0)
        else:
            break
    for match in reversed(matches):
        orig_str: str = match[0]
        q_a: str = match[1]
        idx = int(match[2])
        play_indices = question_play_indices if q_a == 'q' else answer_play_indices
        new_str: str
        if idx not in play_indices:
            new_str = orig_str[:2] + " style='display: none;'" + orig_str[2:]
        else:
            new_idx = play_indices.index(idx)
            new_str = f"""<a class="replay-button soundLink" href=# onclick="pycmd('play:{q_a}:{new_idx}'); """ \
                      + 'return false;">'
        text = text[:match.start(0)] + new_str + text[match.end(0):]
    return text


gui_hooks.av_player_will_play_tags.append(on_av_player_will_play_tags)
gui_hooks.card_will_show.append(on_card_will_show)
