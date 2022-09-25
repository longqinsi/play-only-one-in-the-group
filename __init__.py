import sys
import re
from re import Match

from typing import Any, Optional

from aqt.browser.previewer import Previewer
from aqt.clayout import CardLayout
from bs4 import BeautifulSoup

import anki
from aqt import gui_hooks
from aqt.reviewer import Reviewer
from aqt.sound import av_player
from aqt.webview import AnkiWebView
from anki.cards import Card
from bs4.element import Tag
from .play_group import *
from anki.sound import SoundOrVideoTag


def get_idx_to_play_attr_name(status: str) -> str:
    if status != 'question' and status != 'answer':
        raise ValueError(f"status '{status}' is not 'question' or 'answer'")
    return f'{status}_idx_to_play'


def on_webview_did_receive_js_message(handled: tuple[bool, Any], pycmd: str, context: Any) -> tuple[bool, Any]:
    if not pycmd or not pycmd.__contains__(':') or pycmd.endswith(':'):
        return handled

    command, para_str = pycmd.split(":", 1)
    if command == 'play':
        if not isinstance(context, Reviewer):
            # not reviewer, pass on message
            return handled
        status_first_letter, idx_str = para_str.split(":", 1)
        idx = int(idx_str)
        status = "question" if status_first_letter == 'q' else "answer"
        card = context.card
        idx_to_play: list[int] = getattr(card, get_idx_to_play_attr_name(status))
        if idx_to_play:
            new_idx = idx_to_play.index(idx)
            av_tags = card.question_av_tags() if status_first_letter == "q" else card.answer_av_tags()
            av_player.play_tags([av_tags[new_idx]])
            return True, None
        return handled
    else:
        return handled


def get_play_group_manager(card: Card, side: str) -> PlayGroupManager:
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
    play_group_manager = PlayGroupManager(play_group_list)
    return play_group_manager


def on_av_player_will_play_tags(tags: list[anki.sound.AVTag], side: str, context: Any) -> None:
    card: Optional[Card] = None
    if side not in ['question', 'answer']:
        return
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
    play_group_manager = get_play_group_manager(card, side)
    idx_to_play = sorted(play_group_manager.get_items_to_play())
    setattr(card, get_idx_to_play_attr_name(side), idx_to_play)
    if len(idx_to_play) == len(tags):
        return
    new_tags = [tags[idx] for idx in idx_to_play]
    tags.clear()
    tags.extend(new_tags)
    pass


def on_card_will_show(text: str, card: Card, kind: str) -> str:
    question_idx_to_play_attr_name = get_idx_to_play_attr_name("question")
    answer_idx_to_play_attr_name = get_idx_to_play_attr_name("answer")
    filters: list[str] = []
    question_idx_to_play: list[int]
    if hasattr(card, question_idx_to_play_attr_name):
        question_idx_to_play = getattr(card, question_idx_to_play_attr_name)
        filters.extend([f'play:q:{i}' for i in question_idx_to_play])
    else:
        question_idx_to_play = list(range(len(card.question_av_tags())))

    answer_idx_to_play: list[int]
    if hasattr(card, answer_idx_to_play_attr_name):
        answer_idx_to_play = getattr(card, answer_idx_to_play_attr_name)
        filters.extend([f'play:a:{i}' for i in answer_idx_to_play])
    else:
        answer_idx_to_play = list(range(len(card.answer_av_tags())))

    if not filters:
        return text

    rexp = re.compile(r"""<a class="replay-button soundLink" href=# onclick="pycmd\('play:([qa]):(\d+)'\);""" \
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
        idx_to_play = question_idx_to_play if q_a == 'q' else answer_idx_to_play
        new_str: str
        if idx not in idx_to_play:
            new_str = orig_str[:2] + " style='display: none;'" + orig_str[2:]
        else:
            new_idx = idx_to_play.index(idx)
            new_str = f"""<a class="replay-button soundLink" href=# onclick="pycmd('play:{q_a}:{new_idx}'); """ \
                      + 'return false;">'
        text = text[:match.start(0)] + new_str + text[match.end(0):]
    return text


gui_hooks.av_player_will_play_tags.append(on_av_player_will_play_tags)
gui_hooks.card_will_show.append(on_card_will_show)
