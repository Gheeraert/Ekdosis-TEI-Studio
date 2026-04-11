from __future__ import annotations

from ets.domain import Play


def validate_play_structure(play: Play) -> None:
    if not play.acts:
        raise ValueError("Play has no act.")

    for act in play.acts:
        if not act.scenes:
            raise ValueError("Act has no scene.")
        for scene in act.scenes:
            if not scene.speeches:
                raise ValueError("Scene has no speeches.")
            for speech in scene.speeches:
                if not speech.verses:
                    raise ValueError("Speech has no verses.")
