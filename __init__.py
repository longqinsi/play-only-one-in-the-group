import types
from pathlib import Path
from typing import Optional, Union, Callable

import anki
import aqt
from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QWidget
from anki.sound import SoundOrVideoTag, AVTag, TTSTag
from aqt import gui_hooks
from aqt.browser.previewer import Previewer
from aqt.clayout import CardLayout
from aqt.main import MainWebView
from aqt.reviewer import Reviewer
from aqt.sound import RecordDialog

from .play_group import *

_REPLAY_AUDIO_STUB_METHOD_NAME = "_replay_audio_stub"
_PLAY_AUDIO_INTERNAL_METHOD_NAME = "_play_audio_internal"
_REPLAY_AUDIO_METHOD_NAME = 'replayAudio'
_PLAY_NEXT_AUDIO_METHOD_NAME = 'play_next_audio'
_PLAY_PREVIOUS_AUDIO_METHOD_NAME = 'play_previous_audio'
_css_text = (Path(__file__).parent / "play_only_one.css").read_text()
_js_text = (Path(__file__).parent / "play_only_one.js").read_text()


def filter_play_list(tags: list[AVTag], play_group_collection: PlayGroupCollection) -> None:
    """过滤播放列表
    :param tags: 待过滤播放列表
    :param play_group_collection: 用于过滤播放列表的播放组集合
    """
    play_indices = set(play_group_collection.get_play_indices())
    for idx in reversed(range(len(tags))):
        if idx not in play_indices:
            del tags[idx]


def _replay_audio(self: Reviewer) -> None:
    getattr(self, _PLAY_AUDIO_INTERNAL_METHOD_NAME)(FetchMode.CURRENT)
    _paint_current_av_tags(self.card, self.state)
    if self.state == 'answer' and self.card.replay_question_audio_on_answer_side():
        _paint_current_av_tags(self.card, "question")


def _play_next_audio(self: Reviewer) -> None:
    getattr(self, _PLAY_AUDIO_INTERNAL_METHOD_NAME)(FetchMode.NEXT)
    _paint_current_av_tags(self.card, self.state)
    if self.state == 'answer' and self.card.replay_question_audio_on_answer_side():
        _paint_current_av_tags(self.card, "question")


def _play_previous_audio(self: Reviewer) -> None:
    getattr(self, _PLAY_AUDIO_INTERNAL_METHOD_NAME)(FetchMode.PREVIOUS)
    _paint_current_av_tags(self.card, self.state)
    if self.state == 'answer' and self.card.replay_question_audio_on_answer_side():
        _paint_current_av_tags(self.card, "question")


def _set_play_audio_methods_for_reviewer(reviewer: Reviewer) -> None:
    setattr(reviewer, _REPLAY_AUDIO_METHOD_NAME, types.MethodType(_replay_audio, reviewer))
    setattr(reviewer, _PLAY_NEXT_AUDIO_METHOD_NAME, types.MethodType(_play_next_audio, reviewer))
    setattr(reviewer, _PLAY_PREVIOUS_AUDIO_METHOD_NAME, types.MethodType(_play_previous_audio, reviewer))


def on_av_player_will_play_tags(tags: list[anki.sound.AVTag], side: str, context: Any) -> None:
    card: Optional[Card] = None
    web: Optional[MainWebView] = None
    if isinstance(context, CardLayout):
        card = context.rendered_card
        web = context.preview_web
    elif isinstance(context, Reviewer):
        card = context.card
        web = context.web
    elif isinstance(context, Previewer):
        card = context.card()
    if not card:
        return
    play_group_collection = PlayGroupCollection.create(card, side)
    card_render_output = card.render_output()
    if tags is card_render_output.question_av_tags:
        card_render_output.question_av_tags = tags.copy()
    elif tags is card_render_output.answer_av_tags:
        card_render_output.answer_av_tags = tags.copy()
    if tags:
        play_indices = set(play_group_collection.get_play_indices())
        for idx in reversed(range(len(tags))):
            if idx not in play_indices:
                del tags[idx]
    if web:
        setattr(card, 'web', web)

    if isinstance(context, Reviewer):
        setattr(card, f'{side}_play_group_collection', play_group_collection)

        def play_audio_internal(self: Reviewer, fetch_mode: FetchMode) -> None:
            from aqt.sound import av_player
            if self.state not in ["question", "answer"]:
                return
            question_side: bool = self.state == "question"

            def get_filtered_av_tags(side_to_play: str) -> list[Union[SoundOrVideoTag, TTSTag]]:
                pgc: PlayGroupCollection = getattr(card, f'{side_to_play}_play_group_collection')
                filtered_play_indices = pgc.get_play_indices(fetch_mode)
                unfiltered_av_tags = self.card.question_av_tags() if side_to_play == 'question' \
                    else self.card.answer_av_tags()
                return [unfiltered_av_tags[i] for i in filtered_play_indices]

            if question_side:
                tags_to_replay = get_filtered_av_tags("question")
                av_player.play_tags(tags_to_replay)
            else:
                tags_to_replay = get_filtered_av_tags("answer")
                if self.card.replay_question_audio_on_answer_side():
                    tags_to_replay = get_filtered_av_tags("question") + tags_to_replay
                av_player.play_tags(tags_to_replay)

        setattr(context, _PLAY_AUDIO_INTERNAL_METHOD_NAME, types.MethodType(play_audio_internal, context))
        _set_play_audio_methods_for_reviewer(context)


def on_state_shortcuts_will_change(state: str, shortcuts: list[tuple[str, Callable]]) -> None:
    if state != "review":
        return
    are_play_audio_methods_set_for_reviewer = False
    reviewer: Optional[Reviewer] = None
    for idx, (key, method) in enumerate(shortcuts):
        if str(key).lower() in ['r', 'f5']:
            reviewer = getattr(method, '__self__')
            if isinstance(reviewer, Reviewer):
                if not are_play_audio_methods_set_for_reviewer:
                    _set_play_audio_methods_for_reviewer(reviewer)
                    are_play_audio_methods_set_for_reviewer = True
                shortcuts[idx] = key, reviewer.replayAudio
        elif str(key).lower() == 'v':
            reviewer = getattr(method, '__self__')
            if isinstance(reviewer, Reviewer):
                reviewer.onRecordVoice = types.MethodType(_on_record_voice, reviewer)
                shortcuts[idx] = key, reviewer.onRecordVoice
        elif str(key).lower() == 'shift+v':
            reviewer = getattr(method, '__self__')
            if isinstance(reviewer, Reviewer):
                shortcuts[idx] = key, reviewer.onReplayRecorded

    if reviewer:
        shortcuts.append(('Ctrl+R', reviewer.replayAudio))
        shortcuts.append(('n', getattr(reviewer, _PLAY_NEXT_AUDIO_METHOD_NAME)))
        shortcuts.append(('p', getattr(reviewer, _PLAY_PREVIOUS_AUDIO_METHOD_NAME)))
        shortcuts.append(('j', reviewer.replayAudio))
        shortcuts.append(('k', reviewer.on_pause_audio))
        shortcuts.append(('l', reviewer.on_seek_backward))
        shortcuts.append((';', reviewer.on_seek_forward))
        shortcuts.append(('ö', reviewer.on_seek_forward))
        shortcuts.append(('g', reviewer.onReplayRecorded))
        # noinspection PyProtectedMember
        setattr(reviewer, '_contextMenu_orig', reviewer._contextMenu)
        reviewer._contextMenu = types.MethodType(_context_menu, reviewer)


def _context_menu(self: Reviewer) -> list[Any]:
    opts: list[Any] = self._contextMenu_orig()
    for opt in opts:
        if isinstance(opt, list) and len(opt) == 3:
            if opt[1] == "Shift+V":
                opt[1] = "V"
            elif opt[1] == "V":
                opt[1] = "G"
    return opts


def _on_record_voice(self: Reviewer) -> None:
    def after_record(path: str) -> None:
        self._recordedAudio = path
        self.onReplayRecorded()

    _record_audio(self.mw, self.mw, False, after_record)


def _record_audio(
    parent: QWidget, mw: aqt.main.AnkiQt, encode: bool, on_done: Callable[[str], None]
) -> None:
    def after_record(path: str) -> None:
        if not encode:
            on_done(path)
        else:
            aqt.sound.encode_mp3(mw, path, on_done)

    try:
        _diag = CustomRecordDialog(parent, mw, after_record)
    except Exception as e:
        err_str = str(e)
        aqt.sound.showWarning(aqt.sound.markdown(aqt.sound.tr.qt_misc_unable_to_record(error=err_str)))


def on_card_will_show(text: str, _card: Card, _kind: str) -> str:
    return f"<style>{_css_text}</style>" + text + f"<script>{_js_text}</script>"


def on_reviewer_did_show_answer(card: Card) -> None:
    _paint_current_av_tags(card, "answer")
    if card.replay_question_audio_on_answer_side():
        _paint_current_av_tags(card, "question")


def on_reviewer_did_show_question(card: Card) -> None:
    _paint_current_av_tags(card, "question")


def _paint_current_av_tags(card: Card, side: str) -> None:
    pgc: PlayGroupCollection = getattr(card, f'{side}_play_group_collection')
    play_indices: list[int] = pgc.get_play_indices()
    play_indices_str = ','.join([str(i) for i in play_indices])
    web: MainWebView = getattr(card, 'web')
    web.eval(f"""
if (typeof paint_current_av_tags === "function") {{ 
    paint_current_av_tags([{play_indices_str}], '{side}');
}}
""")


def on_webview_did_receive_js_message(handled: tuple[bool, Any], message: str, context: Any) -> tuple[bool, Any]:
    if not isinstance(context, Reviewer):
        return handled
    if not message.startswith("play:"):
        return handled
    split_result = message.split(':')
    if len(split_result) != 3:
        return handled
    play, side_first_letter, idx_str = split_result
    if not side_first_letter or side_first_letter not in ['q', 'a']:
        return handled
    idx: int
    try:
        idx = int(idx_str)
    except (ValueError, TypeError):
        return handled
    side = "question" if side_first_letter == 'q' else "answer"
    pgc: PlayGroupCollection = getattr(context.card, f'{side}_play_group_collection')
    if pgc.set_current_index(idx):
        _paint_current_av_tags(context.card, side)
    return handled


class CustomRecordDialog(RecordDialog):
    def __init__(
        self,
        parent: QWidget,
        mw: aqt.main.AnkiQt,
        on_success: Callable[[str], None]
    ):
        RecordDialog.__init__(self, parent, mw, on_success)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key.Key_Space:
            self.accept()
            event.accept()
        elif event.key() == QtCore.Qt.Key.Key_Q:
            self.reject()
            event.accept()
        else:
            super().keyPressEvent(event)


gui_hooks.av_player_will_play_tags.append(on_av_player_will_play_tags)
gui_hooks.state_shortcuts_will_change.append(on_state_shortcuts_will_change)
gui_hooks.card_will_show.append(on_card_will_show)
gui_hooks.reviewer_did_show_answer.append(on_reviewer_did_show_answer)
gui_hooks.reviewer_did_show_question.append(on_reviewer_did_show_question)
gui_hooks.webview_did_receive_js_message.append(on_webview_did_receive_js_message)
