"""Controlled login-layout fixtures, based on the positions in the supplied UI."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPen


def rectangles(kind):
    if kind == "login":
        return [(586, 622, 146, 28), (612, 675, 96, 24)]
    if kind == "channels":
        return [(550, round(287 + i * 42.5), 214, 28) for i in range(8)]
    return [(410 + 174 * i, 548, 164, 76) for i in range(3)] + [(442, 674, 102, 28), (818, 674, 70, 28)]


def scene(kind, scale=1.0, offset=(0, 0), background=True, gradient=False):
    width, height = round(1310 * scale + offset[0] * 2), round(850 * scale + offset[1] * 2)
    image = QImage(width, height, QImage.Format.Format_RGB32)
    image.fill(QColor("#101010"))
    painter = QPainter(image)
    painter.translate(*offset)
    painter.scale(scale, scale)
    if kind != "login" and background:
        painter.fillRect(QRectF(90, 70, 1125, 715), QColor("#8beaf4"))
    painter.setPen(QPen(QColor("#32a4b8"), 3))
    painter.setBrush(QColor("#087780"))
    if kind == "characters":
        painter.drawRect(QRectF(400, 505, 532, 132))
    else:
        painter.drawRect(QRectF(326, 184, 658, 336))

    def control(rect, text, color="#00cbd7"):
        painter.setPen(QPen(QColor("#06515c"), 3))
        if gradient and color == "#00cbd7":
            fill = QLinearGradient(rect[0], rect[1], rect[0], rect[1] + rect[3])
            for stop, shade in ((0, "#28475b"), (.5, "#46697c"), (.7, "#00e8ce"), (.85, "#00d8c2"), (1, "#075b68")):
                fill.setColorAt(stop, QColor(shade))
            painter.setBrush(fill)
        else:
            painter.setBrush(QColor(color))
        painter.drawRoundedRect(QRectF(*rect), 4, 4)
        painter.setPen(QColor("#ffeb61"))
        painter.drawText(QRectF(*rect), Qt.AlignmentFlag.AlignCenter, text)

    if kind in ("login", "channels", "force_loading", "login_notice"):
        control(rectangles("login")[0], "Bat dau")
        control(rectangles("login")[1], "Bat buoc")
    if kind == "channels":
        for i, rect in enumerate(rectangles(kind)):
            control(rect, str(i + 1), "#eeb332" if i == 1 else "#3ac587" if i == 7 else "#00cbd7")
    if kind == "characters":
        for i, rect in enumerate(rectangles(kind)[:3]):
            control(rect, "", color="#35b9c8")
            painter.fillRect(QRectF(rect[0] + 9, rect[1] + 8, 50, 58), QColor("#603784"))
            painter.setPen(QColor("white"))
            painter.drawText(QRectF(rect[0] + 65, rect[1] + 10, 92, 50), f"NV {i + 1}\nLV 130")
        control(rectangles(kind)[3], "Vao game")
        control(rectangles(kind)[4], "Quay lai")
        control((804, 471, 128, 28), "Tao lai pass")
    if kind == "force_loading":
        # Server kick/progress dialog overlays the welcome screen while the
        # original Force button remains visible, as in the user's screenshot.
        painter.setPen(QPen(QColor("#32c4d8"), 3))
        painter.setBrush(QColor("#155b68"))
        painter.drawRoundedRect(QRectF(470, 350, 370, 146), 8, 8)
        painter.setPen(QColor("white"))
        painter.drawText(QRectF(485, 390, 340, 50), Qt.AlignmentFlag.AlignCenter, "Waiting for the old session...")
        painter.fillRect(QRectF(525, 447, 260, 10), QColor("#eeeeee"))
        painter.fillRect(QRectF(525, 447, 120, 10), QColor("#32b6f1"))
    if kind == "login_notice":
        painter.setPen(QPen(QColor("#32c4d8"), 3))
        painter.setBrush(QColor("#002d2d"))
        painter.drawRoundedRect(QRectF(480, 400, 352, 80), 8, 8)
        painter.setPen(QColor("white"))
        painter.drawText(QRectF(495, 409, 325, 25), Qt.AlignmentFlag.AlignCenter, "Lien ket qua han, vui long dang nhap lai sau")
        control((618, 442, 78, 24), "Co")
    painter.end()
    return image
