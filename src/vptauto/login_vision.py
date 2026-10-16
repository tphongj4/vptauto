"""Recognize the three illustrated login layouts from cyan control geometry.

Coordinates come from the current client image, not desktop screen positions.
No images or game links are sent to a remote service.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from PySide6.QtGui import QImage

Point = tuple[int, int]


@dataclass(frozen=True)
class Box:
    x: int
    y: int
    w: int
    h: int

    @property
    def center(self) -> Point:
        return self.x + self.w // 2, self.y + self.h // 2


@dataclass(frozen=True)
class Observation:
    kind: str = "unknown"
    force: Point | None = None
    channels: tuple[Point, ...] = ()
    characters: tuple[Point, ...] = ()
    enter: Point | None = None


def cyan_boxes(image: QImage) -> list[Box]:
    """Run-length connected components on a small cyan mask (including text holes)."""
    if image.isNull():
        return []
    image = image.convertToFormat(QImage.Format.Format_RGBA8888)
    width, height = image.width(), image.height()
    step = max(2, (width + 899) // 900, (height + 599) // 600)
    pixels, stride = image.constBits(), image.bytesPerLine()
    nodes: list[list[int]] = []  # parent, minx, miny, maxx, maxy, area
    previous: list[tuple[int, int, int]] = []

    def root(index: int) -> int:
        while nodes[index][0] != index:
            nodes[index][0] = nodes[nodes[index][0]][0]
            index = nodes[index][0]
        return index

    for row, y in enumerate(range(0, height, step)):
        segments, start = [], None
        columns = (width + step - 1) // step
        for column in range(columns + 1):
            active = False
            if column < columns:
                offset = y * stride + column * step * 4
                r, g, b = pixels[offset], pixels[offset + 1], pixels[offset + 2]
                active = r <= 130 and g >= 125 and b >= 125 and g - r >= 35 and b - r >= 35
            if active and start is None:
                start = column
            elif not active and start is not None:
                segments.append((start, column - 1))
                start = None
        current, cursor = [], 0
        for left, right in segments:
            while cursor < len(previous) and previous[cursor][1] < left - 1:
                cursor += 1
            touching, index = set(), cursor
            while index < len(previous) and previous[index][0] <= right + 1:
                touching.add(root(previous[index][2]))
                index += 1
            if not touching:
                label = len(nodes)
                nodes.append([label, left, row, right, row, right - left + 1])
            else:
                label = min(touching)
                target = nodes[label]
                for other in touching - {label}:
                    entry = nodes[other]
                    target[1], target[2] = min(target[1], entry[1]), min(target[2], entry[2])
                    target[3], target[4] = max(target[3], entry[3]), max(target[4], entry[4])
                    target[5] += entry[5]
                    entry[0] = label
                target[1], target[3], target[4] = min(target[1], left), max(target[3], right), row
                target[5] += right - left + 1
            current.append((left, right, label))
        previous = current
    boxes = []
    for index, entry in enumerate(nodes):
        if root(index) == index and entry[5] >= 12:
            _, left, top, right, bottom, _ = entry
            boxes.append(Box(left * step, top * step, min(width, (right + 1) * step) - left * step,
                             min(height, (bottom + 1) * step) - top * step))
    return boxes


def classify_boxes(boxes: list[Box], width: int, height: int) -> Observation:
    # A gradient may leave only a thin bright strip in the cyan mask. Its
    # height is not the button height; compare widths and spacing instead.
    buttons = [b for b in boxes if 2 <= b.h <= height * .075 and
               width * .035 <= b.w <= width * .4 and 2 <= b.w / b.h <= 60]
    # The eight-row channel dialog has six cyan regular rows; orange/green
    # special rows are inferred only after the aligned stack is established.
    for seed in buttons:
        group = sorted((b for b in buttons if abs(b.center[0] - seed.center[0]) < seed.w * .08
                        and .78 <= b.w / seed.w <= 1.25 and .65 <= b.h / seed.h <= 1.5),
                       key=lambda b: b.y)
        if len(group) < 5:
            continue
        gaps = [b.center[1] - a.center[1] for a, b in zip(group, group[1:])]
        # Text can split a thin strip and remove one row from the mask. The
        # lower half of gaps estimates adjacent rows rather than a two-row gap.
        spacing = median(sorted(gaps)[:max(1, (len(gaps) + 1) // 2)])
        if not .12 <= spacing / median(b.w for b in group) <= .32:
            continue
        top, center = group[0].center[1], round(median(b.center[0] for b in group))
        rows = {round((b.center[1] - top) / spacing) for b in group
                if abs((b.center[1] - top) / spacing - round((b.center[1] - top) / spacing)) < .18}
        if len(rows & set(range(8))) >= 5 and 0 in rows and 6 in rows and top + 7 * spacing < height:
            return Observation("channels", channels=tuple((center, round(top + i * spacing)) for i in range(8)))
    # Character cards sit side by side; enter/back buttons must also be present.
    cards = [b for b in boxes if width * .06 <= b.w <= width * .25
             and height * .04 <= b.h <= height * .15 and 1.2 <= b.w / b.h <= 3.8]
    for seed in cards:
        row = sorted((b for b in cards if abs(b.center[1] - seed.center[1]) <= seed.h * .25
                      and .6 <= b.w / seed.w <= 1.65 and .65 <= b.h / seed.h <= 1.5),
                     key=lambda b: b.x)
        for start in range(len(row) - 2):
            three = row[start:start + 3]
            if not all(.8 <= (b.center[0] - a.center[0]) / median(c.w for c in three) <= 2.3
                       for a, b in zip(three, three[1:])):
                continue
            bottom, card_height = max(b.y + b.h for b in three), median(b.h for b in three)
            below = [b for b in buttons if .2 * card_height < b.center[1] - bottom < 2.2 * card_height]
            enters = [b for b in below if abs(b.center[0] - three[0].center[0]) < three[0].w * .95
                      and 2.8 <= b.w / b.h <= 6.5]
            for enter in enters:
                backs = [b for b in below if b is not enter
                         and abs(b.center[0] - three[2].center[0]) < three[2].w
                         and abs(b.center[1] - enter.center[1]) < max(b.h, enter.h) * .6]
                if backs:
                    return Observation("characters", characters=tuple(b.center for b in three), enter=enter.center)
    # Slot 1 is the default and needs only Enter. Its selected card can change
    # color, or other slots can be empty. Validate the remaining card(s), the
    # separated Enter/Back pair, and the reset-password button above the right
    # side; do not invent click positions for slots we cannot see.
    for enter in buttons:
        if not (height * .6 < enter.center[1] < height * .94 and 2.8 <= enter.w / enter.h <= 6.5):
            continue
        backs = [b for b in buttons if .45 <= b.w / enter.w <= .9
                 and abs(b.center[1] - enter.center[1]) < enter.h * .6
                 and 2.5 <= (b.center[0] - enter.center[0]) / enter.w <= 5]
        for back in backs:
            above = [b for b in cards if .8 <= (enter.center[1] - b.center[1]) / b.h <= 2.8
                     and enter.center[0] - b.w < b.center[0] < back.center[0] + b.w * .5]
            resets = [b for b in buttons if abs(b.center[0] - back.center[0]) < enter.w
                      and 4 <= (enter.center[1] - b.center[1]) / enter.h <= 11]
            if above and resets:
                return Observation("characters", enter=enter.center)
    # Start is the wider button above the smaller mandatory-login button.
    for small in buttons:
        if not width * .35 < small.center[0] < width * .65 or not height * .55 < small.center[1] < height * .94:
            continue
        for big in buttons:
            if (1.2 <= big.w / small.w <= 2.1 and abs(big.center[0] - small.center[0]) < small.w * .12
                    and .35 <= (small.center[1] - big.center[1]) / small.w <= .85):
                return Observation("login", force=small.center)
    return Observation()


def observe(image: QImage) -> Observation:
    return classify_boxes(cyan_boxes(image), image.width(), image.height())
