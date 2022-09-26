import types
from typing import Optional, Union, Callable

import anki
from anki.sound import SoundOrVideoTag, AVTag, TTSTag
from aqt import gui_hooks
from aqt.browser.previewer import Previewer
from aqt.clayout import CardLayout
from aqt.reviewer import Reviewer

from .play_group import *


_REPLAY_AUDIO_STUB_METHOD_NAME = "_replay_audio_stub"


def filter_play_list(tags: list[AVTag], play_group_collection: PlayGroupCollection) -> None:
    """过滤播放列表"""
    play_indices = set(play_group_collection.get_play_indices())
    for idx in reversed(range(len(tags))):
        if idx not in play_indices:
            del tags[idx]


def on_av_player_will_play_tags(tags: list[anki.sound.AVTag], side: str, context: Any) -> None:
    card: Optional[Card] = None
    if isinstance(context, CardLayout):
        card = context.rendered_card
    elif isinstance(context, Reviewer):
        card = context.card
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
        filter_play_list(tags, play_group_collection)
    if isinstance(context, Reviewer):
        setattr(context, f'{side}_play_group_collection', play_group_collection)

        def replay_audio(self: Reviewer) -> None:
            from aqt.sound import av_player
            if self.state not in ["question", "answer"]:
                return
            question_side: bool = self.state == "question"

            def get_filtered_av_tags(side_to_play: str) -> list[Union[SoundOrVideoTag, TTSTag]]:
                pgc: PlayGroupCollection = getattr(context, f'{side_to_play}_play_group_collection')
                filtered_play_indices = pgc.get_play_indices()
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

        context.replayAudio = types.MethodType(replay_audio, context)
        setattr(context, _REPLAY_AUDIO_STUB_METHOD_NAME, context.replayAudio)


def replay_audio_stub(self) -> None:
    getattr(self, _REPLAY_AUDIO_STUB_METHOD_NAME)()


def on_state_shortcuts_will_change(state: str, shortcuts: list[tuple[str, Callable]]) -> None:
    if state != "review":
        return
    is_reviewer_replay_audio_replaced = False
    reviewer: Optional[Reviewer] = None
    for idx, (key, method) in enumerate(shortcuts):
        if str(key).lower() in ['r', 'f5']:
            reviewer = getattr(method, '__self__')
            if isinstance(reviewer, Reviewer):
                if not is_reviewer_replay_audio_replaced:
                    reviewer.replayAudio = types.MethodType(replay_audio_stub, reviewer)
                    is_reviewer_replay_audio_replaced = True
                shortcuts[idx] = key, reviewer.replayAudio
    if reviewer:
        shortcuts.append(('Ctrl+R', reviewer.replayAudio))


def on_card_will_show(text: str, _card: Card, _kind: str) -> str:
    text += """
<script>
(() => {
    for (let only_one of document.getElementsByTagName('only-one')) {
        if(only_one.getElementsByClassName('replay-button soundLink').length > 1){
            only_one.style.display = 'block';
            only_one.style.border = '1px solid black';
            only_one.style.margin = '10px';
        }
    }
})();
</script>
"""
    return text


gui_hooks.av_player_will_play_tags.append(on_av_player_will_play_tags)
gui_hooks.state_shortcuts_will_change.append(on_state_shortcuts_will_change)
gui_hooks.card_will_show.append(on_card_will_show)
