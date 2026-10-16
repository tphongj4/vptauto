from random import Random

import pytest
from PySide6.QtGui import QColor, QImage, QPainter

from login_images import scene
from vptauto.login_flow import LoginError, LoginFlow
from vptauto.login_vision import observe


@pytest.mark.parametrize("kind", ["login", "channels", "characters"])
@pytest.mark.parametrize("scale,offset", [(1, (0, 0)), (.65, (23, 17)), (1.5, (40, 35))])
def test_visual_layout_recognition_with_scale_and_letterboxing(qt_app, kind, scale, offset):
    result = observe(scene(kind, scale, offset))
    assert result.kind == kind
    if kind == "channels":
        assert len(result.channels) == 8
        assert result.channels[0][1] < result.channels[-1][1]
    elif kind == "characters":
        assert len(result.characters) == 3
        assert result.characters[0][0] < result.characters[1][0] < result.characters[2][0]
        assert result.enter[1] > result.characters[0][1]
    else:
        expected = (round(660 * scale + offset[0]), round(687 * scale + offset[1]))
        assert max(abs(a - b) for a, b in zip(result.force, expected)) < 5 * scale


def test_blank_screen_never_produces_click_targets():
    image = QImage(1310, 850, QImage.Format.Format_RGB32)
    image.fill(QColor("black"))
    assert observe(image).kind == "unknown"


@pytest.mark.parametrize("kind", ["login", "channels", "characters"])
@pytest.mark.parametrize("scale", [.65, 1, 1.5])
def test_gradient_buttons_with_thin_cyan_strips_are_recognized(qt_app, kind, scale):
    frame = scene(kind, scale=scale, gradient=True)
    result = observe(frame)
    assert result.kind == kind


def test_background_fragments_do_not_override_lower_center_login_controls(qt_app):
    image = scene("login", gradient=True)
    painter = QPainter(image)
    painter.fillRect(545, 505, 150, 20, QColor("#00cbd7"))
    painter.fillRect(570, 558, 100, 20, QColor("#00cbd7"))
    painter.end()
    result = observe(image)
    assert result.kind == "login" and result.force[1] > 675


@pytest.mark.parametrize("slot", [1, 2, 3])
@pytest.mark.parametrize("channel", [1, 8])
def test_login_sequence_selects_saved_character_and_channel_boundaries(qt_app, slot, channel):
    class Fixed:
        def randint(self, first, last):
            assert (first, last) == (1, 8)
            return channel
    flow = LoginFlow(slot, 0, Fixed())
    now = 0
    sequence = [("login", "force"), ("channels", "channel")]
    if slot != 1:
        sequence.append(("characters", "character"))
    sequence.append(("characters", "enter"))
    for kind, action_name in sequence:
        observation = observe(scene(kind))
        click = None
        for _ in range(4):
            now += .4
            click = flow.next_click(observation, now)
            if click:
                break
        assert click is not None and click.name == action_name
        if action_name == "channel":
            assert click.point == observation.channels[channel - 1]
        if action_name == "character":
            assert click.point == observation.characters[slot - 1]
        flow.performed(click, now)
    assert flow.state == "done"
    assert flow.slot == slot and flow.channel == channel


def test_default_character_enters_without_clicking_any_card(qt_app):
    from vptauto.login_vision import Observation
    flow = LoginFlow(1, 0)
    frame = Observation("characters", enter=(490, 690))
    assert flow.next_click(frame, .4) is None
    assert flow.next_click(frame, .8) is None
    click = flow.next_click(frame, 1.2)
    assert click.name == "enter" and click.point == frame.enter
    flow.performed(click, 1.2)
    assert flow.state == "done"


def test_default_card_changed_color_or_other_slots_empty_still_finds_enter(qt_app):
    from login_images import rectangles
    image = scene("characters")
    painter = QPainter(image)
    # First selected card no longer matches cyan; third slot is empty.
    for index in (0, 2):
        painter.fillRect(*rectangles("characters")[index], QColor("#403a51"))
    painter.end()
    result = observe(image)
    assert result.kind == "characters" and result.enter is not None
    assert result.characters == ()  # Never invent a missing card's position.
    default = LoginFlow(1, 0)
    other = LoginFlow(2, 0)
    for i in range(1, 4):
        click = default.next_click(result, i * .4)
        assert other.next_click(result, i * .4) is None
    assert click.name == "enter"


def test_random_channel_is_chosen_once_even_if_click_cannot_be_sent(qt_app):
    class Counted(Random):
        calls = 0
        def randint(self, a, b):
            self.calls += 1
            return super().randint(a, b)
    rng = Counted(30)
    flow = LoginFlow(1, 0, rng)
    frame = observe(scene("channels"))
    for i in range(10):
        flow.next_click(frame, i * .4)
    assert rng.calls == 1 and 1 <= flow.channel <= 8
    assert flow.state == "channel"  # No input confirmation, no state advancement.


def test_unknown_or_transient_screens_never_advance_flow(qt_app):
    flow = LoginFlow(1, 0)
    from vptauto.login_vision import Observation
    known = observe(scene("login"))
    assert flow.next_click(known, .4) is None
    assert flow.next_click(Observation(), .8) is None
    assert flow.next_click(known, 1.2) is None
    assert flow.next_click(known, 1.6) is None
    assert flow.next_click(known, 2.0).name == "force"
    with pytest.raises(LoginError):
        flow.next_click(Observation(), 46)
