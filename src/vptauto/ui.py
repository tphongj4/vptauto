from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QDialog, QDialogButtonBox, QFileDialog, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QSizePolicy, QStackedWidget, QStyle, QStyleOptionButton,
    QTextEdit, QVBoxLayout, QWidget,
)

from . import __version__, launcher
from .models import GameLink
from .service import Manager
from .storage import StorageError


STYLESHEET = """
QWidget { font-family: 'Segoe UI', 'Noto Sans', sans-serif; font-size: 13px; color: #263047; }
QMainWindow, QDialog { background: #f5f6fa; }
QFrame#sidebar { background: #191c32; border: none; }
QFrame#sidebar QLabel { color: #959bb8; background: transparent; }
QFrame#sidebar QLabel#brand { color: #ffffff; font-size: 23px; font-weight: 700; }
QFrame#sidebar QLabel#brandSub { color: #b3b6d2; font-size: 11px; }
QLabel#eyebrow { color: #9196ab; font-size: 10px; font-weight: 700; letter-spacing: 2px; }
QPushButton { border: 1px solid #dfe2ed; border-radius: 8px; background: #ffffff;
    padding: 10px 15px; font-weight: 600; }
QPushButton:hover { background: #f0edff; border-color: #b8a5fa; }
QPushButton:pressed { background: #e4dcff; }
QPushButton:disabled { color: #9ca0b3; background: #f2f3f7; border-color: #e5e7ee; }
QPushButton#primary { color: #ffffff; background: #7154dc; border-color: #7154dc; }
QPushButton#primary:hover { background: #6243cf; }
QPushButton#danger { color: #bb5265; background: #fff; border-color: #efdce0; }
QPushButton#nav { text-align: left; background: transparent; color: #b3b7cf;
    border: none; padding: 13px 16px; margin: 3px 0; }
QPushButton#nav:hover { color: #fff; background: #242840; }
QPushButton#nav:checked { background: #363052; color: #d9ccff; }
QFrame#card { background: #ffffff; border: 1px solid #e7e9f2; border-radius: 12px; }
QFrame#notice { background: #f4f0ff; border: 1px solid #e7dffc; border-radius: 8px; }
QFrame#playerCard { background: #23273f; border: 1px solid #343951; border-radius: 9px; }
QLabel#title { font-size: 25px; font-weight: 700; color: #20263d; }
QLabel#sectionTitle { font-size: 17px; font-weight: 700; color: #252b43; }
QLabel#metric { font-size: 28px; font-weight: 700; color: #493884; }
QLabel#muted { color: #80869c; }
QLabel#badge { color: #7154dc; background: #efeafb; border-radius: 5px; padding: 4px 8px; font-size: 11px; }
QLabel#avatar { color: #7154dc; background: #efebfb; border-radius: 12px; font-size: 18px; font-weight: 700; }
QLabel#emptyIcon { font-size: 35px; color: #aa98d8; }
QLineEdit, QTextEdit { border: 1px solid #e0e3ed; border-radius: 7px; background: #fff;
    padding: 10px; selection-background-color: #7154dc; }
QLineEdit:focus, QTextEdit:focus { border-color: #967ce9; }
QLineEdit:read-only { background: #f8f9fc; color: #7a8097; }
QListWidget { background: transparent; border: none; outline: none; }
QListWidget::item { border: 1px solid transparent; border-radius: 9px; margin: 3px 0; }
QListWidget::item:selected { background: #f2eeff; border-color: #d4c6fb; }
QListWidget::item:hover:!selected { background: #f7f7fb; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }
QCheckBox { spacing: 10px; padding: 7px 0; }
QCheckBox::indicator { width: 17px; height: 17px; border: 1px solid #c7cbdc; border-radius: 4px; background: #fff; }
QCheckBox::indicator:checked { background: #7154dc; border-color: #7154dc; image: none; }
QCheckBox::indicator:checked:hover { background: #6243cf; }
QScrollBar:vertical { border: none; background: #f5f6fa; width: 7px; margin: 0; }
QScrollBar::handle:vertical { background: #d5d4e1; min-height: 24px; border-radius: 3px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QStatusBar { background: #ffffff; border-top: 1px solid #e8eaf2; color: #858ba0; font-size: 11px; }
QLabel#error { color: #b53d55; }
"""


def app_icon() -> QIcon:
    pixmap = QPixmap(128, 128)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#7154dc"))
    painter.drawRoundedRect(0, 0, 128, 128, 28, 28)
    painter.setPen(QColor("white"))
    font = painter.font()
    font.setPixelSize(76)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "V")
    painter.end()
    return QIcon(pixmap)


def label(text: str, style: str | None = None, wrap: bool = False) -> QLabel:
    widget = QLabel(text)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    if style:
        widget.setObjectName(style)
    widget.setWordWrap(wrap)
    return widget


def button(text: str, callback, style: str | None = None) -> QPushButton:
    widget = QPushButton(text)
    if style:
        widget.setObjectName(style)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    widget.clicked.connect(callback)
    return widget


def card() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(22, 20, 22, 20)
    layout.setSpacing(12)
    return frame, layout


def empty_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            widget = item.widget()
            widget.hide()
            widget.setParent(None)
            widget.deleteLater()
        elif item.layout():
            empty_layout(item.layout())


class TaskCheckBox(QCheckBox):
    def hitButton(self, position) -> bool:
        # Make the entire row clickable, including the space after short names.
        return self.rect().contains(position)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self.isChecked():
            option = QStyleOptionButton()
            self.initStyleOption(option)
            rect = self.style().subElementRect(QStyle.SubElement.SE_CheckBoxIndicator, option, self)
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            pen = QPen(QColor("white"), 2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(rect.left() + 4, rect.top() + 9, rect.left() + 7, rect.top() + 12)
            painter.drawLine(rect.left() + 7, rect.top() + 12, rect.left() + 13, rect.top() + 5)
            painter.end()


@dataclass
class LinkDraft:
    name: str
    url: str
    task_ids: list[str]

    @classmethod
    def from_link(cls, link: GameLink) -> LinkDraft:
        return cls(link.name, link.url, list(link.task_ids))

    def matches(self, link: GameLink) -> bool:
        return self.name == link.name and self.url == link.url and set(self.task_ids) == set(link.task_ids)


class LinkDialog(QDialog):
    def __init__(self, manager: Manager, parent=None, link: GameLink | None = None):
        super().__init__(parent)
        self.setWindowTitle("Sửa link game" if link else "Tạo link game")
        self.setMinimumWidth(520)
        self.manager, self.link = manager, link
        self.saved_id = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 24)
        layout.setSpacing(14)
        layout.addWidget(label(self.windowTitle(), "sectionTitle"))
        layout.addWidget(label("Đặt tên để phân biệt các nhân vật hoặc máy chủ.", "muted", True))
        layout.addWidget(label("Tên link"))
        self.name_input = QLineEdit(link.name if link else "")
        self.name_input.setObjectName("linkName")
        self.name_input.setMaxLength(80)
        self.name_input.setPlaceholderText("Ví dụ: Nhân vật chính · Máy chủ 1")
        layout.addWidget(self.name_input)
        layout.addWidget(label("Link mở game"))
        self.url_input = QLineEdit(link.url if link else "")
        self.url_input.setObjectName("linkUrl")
        self.url_input.setMaxLength(8192)
        self.url_input.setPlaceholderText("https://…")
        layout.addWidget(self.url_input)
        layout.addWidget(label(
            "Dán link mở game bạn đang dùng trong Flash Player. Nút này tạo mục lưu link; "
            "không tạo đường dẫn đăng nhập từ tài khoản.", "muted", True
        ))
        self.error = label("", "error", True)
        layout.addWidget(self.error)
        actions = QDialogButtonBox()
        cancel = actions.addButton("Hủy", QDialogButtonBox.ButtonRole.RejectRole)
        save = actions.addButton("Lưu thay đổi" if link else "Tạo & lưu link", QDialogButtonBox.ButtonRole.AcceptRole)
        save.setObjectName("primary")
        save.setDefault(True)
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.save)
        layout.addWidget(actions)

    def save(self) -> None:
        try:
            self.saved_id = self.manager.save_link(
                self.name_input.text(), self.url_input.text(), self.link.id if self.link else None
            )
        except (ValueError, StorageError) as error:
            self.error.setText(str(error))
            return
        self.accept()


class TaskDialog(QDialog):
    def __init__(self, manager: Manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Thêm loại nhiệm vụ")
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 24)
        layout.setSpacing(12)
        layout.addWidget(label("Thêm loại nhiệm vụ", "sectionTitle"))
        layout.addWidget(label("Tên nhiệm vụ"))
        self.name_input = QLineEdit()
        self.name_input.setObjectName("taskName")
        self.name_input.setMaxLength(80)
        self.name_input.setPlaceholderText("Ví dụ: Nhiệm vụ hằng ngày")
        layout.addWidget(self.name_input)
        layout.addWidget(label("Ghi chú quy trình (không bắt buộc)"))
        self.description_input = QTextEdit()
        self.description_input.setObjectName("taskDescription")
        self.description_input.setAcceptRichText(False)
        self.description_input.setMaximumHeight(110)
        layout.addWidget(self.description_input)
        layout.addWidget(label(
            "Loại nhiệm vụ được dùng để lưu lựa chọn cho từng link. "
            "Bộ thực thi auto sẽ được bổ sung ở phiên bản sau.", "muted", True
        ))
        self.error = label("", "error", True)
        layout.addWidget(self.error)
        actions = QDialogButtonBox()
        cancel = actions.addButton("Hủy", QDialogButtonBox.ButtonRole.RejectRole)
        save = actions.addButton("Thêm nhiệm vụ", QDialogButtonBox.ButtonRole.AcceptRole)
        save.setObjectName("primary")
        save.setDefault(True)
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.save)
        layout.addWidget(actions)

    def save(self) -> None:
        try:
            self.manager.add_task(self.name_input.text(), self.description_input.toPlainText())
        except (ValueError, StorageError) as error:
            self.error.setText(str(error))
            return
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self, manager: Manager):
        super().__init__()
        self.manager = manager
        self.selected_id: str | None = None
        self.drafts: dict[str, LinkDraft] = {}
        self.setWindowTitle("VPT Auto Manager · Vua Pháp Thuật")
        self.setWindowIcon(app_icon())
        self.resize(1280, 820)
        self.setMinimumSize(1080, 700)
        self.setStyleSheet(STYLESHEET)
        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(208)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(20, 30, 20, 22)
        side.setSpacing(5)
        side.addWidget(label("VPT AUTO", "brand"))
        side.addWidget(label("VUA PHÁP THUẬT", "brandSub"))
        side.addSpacing(36)
        side.addWidget(label("KHÔNG GIAN LÀM VIỆC", "eyebrow"))
        side.addSpacing(12)
        self.nav_buttons = []
        for index, text in enumerate(("▦   Liên kết game", "☷   Loại nhiệm vụ", "⚙   Cài đặt")):
            nav = button(text, lambda checked=False, page=index: self.navigate(page), "nav")
            nav.setCheckable(True)
            self.nav_buttons.append(nav)
            side.addWidget(nav)
        side.addStretch()
        player_card = QFrame()
        player_card.setObjectName("playerCard")
        player_layout = QVBoxLayout(player_card)
        player_layout.setContentsMargins(13, 15, 13, 15)
        player_layout.addWidget(label("FLASH PLAYER", "eyebrow"))
        self.player_status = label("", wrap=True)
        player_layout.addWidget(self.player_status)
        side.addWidget(player_card)
        side.addSpacing(15)
        side.addWidget(label(f"Phiên bản {__version__}  /  Windows", "brandSub"))
        outer.addWidget(sidebar)

        content = QWidget()
        area = QVBoxLayout(content)
        area.setContentsMargins(28, 28, 28, 22)
        area.setSpacing(22)
        header = QHBoxLayout()
        heading = QVBoxLayout()
        heading.setSpacing(4)
        heading.addWidget(label("Trạm điều khiển của bạn", "title"))
        heading.addWidget(label("Quản lý link game và chuẩn bị nhiệm vụ cho từng nhân vật.", "muted"))
        header.addLayout(heading)
        header.addStretch()
        header.addWidget(label("VPT MANAGER", "badge"))
        area.addLayout(header)
        self.pages = QStackedWidget()
        self.pages.addWidget(self.build_links_page())
        self.pages.addWidget(self.build_tasks_page())
        self.pages.addWidget(self.build_settings_page())
        area.addWidget(self.pages, 1)
        outer.addWidget(content, 1)
        self.statusBar().showMessage("Cấu hình được lưu trên máy tính này. Chọn một link để bắt đầu.")
        self.refresh()
        self.navigate(0)

    def navigate(self, page: int) -> None:
        self.pages.setCurrentIndex(page)
        for index, nav in enumerate(self.nav_buttons):
            nav.setChecked(index == page)

    def build_links_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        metrics = QHBoxLayout()
        metrics.setSpacing(14)
        self.metric_values = []
        for title in ("Link đã lưu", "Loại nhiệm vụ", "Link đã chọn nhiệm vụ"):
            frame, inner = card()
            inner.setContentsMargins(18, 13, 18, 13)
            value = label("0", "metric")
            self.metric_values.append(value)
            inner.addWidget(value)
            inner.addWidget(label(title, "muted"))
            metrics.addWidget(frame, 1)
        layout.addLayout(metrics)
        toolbar = QHBoxLayout()
        toolbar.addWidget(label("Liên kết game", "sectionTitle"))
        toolbar.addStretch()
        self.search = QLineEdit()
        self.search.setObjectName("searchLinks")
        self.search.setPlaceholderText("Tìm tên link…")
        self.search.setMaximumWidth(220)
        self.search.textChanged.connect(self.refresh_links)
        toolbar.addWidget(self.search)
        create = button("+  Tạo link", self.create_link, "primary")
        create.setAccessibleName("Tạo link game")
        toolbar.addWidget(create)
        layout.addLayout(toolbar)
        panels = QHBoxLayout()
        panels.setSpacing(16)
        list_frame, list_layout = card()
        list_layout.setContentsMargins(12, 15, 12, 14)
        list_layout.addWidget(label("DANH SÁCH ĐÃ LƯU", "eyebrow"))
        self.link_list = QListWidget()
        self.link_list.setObjectName("linkList")
        self.link_list.setSpacing(3)
        self.link_list.currentItemChanged.connect(self.select_link)
        list_layout.addWidget(self.link_list, 1)
        self.list_empty = label("Chưa có link nào.\nBấm Tạo link để lưu link đầu tiên.", "muted", True)
        self.list_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        list_layout.addWidget(self.list_empty, 1)
        list_layout.addWidget(label("Mỗi link có lựa chọn nhiệm vụ riêng.", "muted", True))
        panels.addWidget(list_frame, 4)
        detail_frame, self.detail = card()
        detail_frame.setMinimumWidth(380)
        panels.addWidget(detail_frame, 5)
        layout.addLayout(panels, 1)
        return page

    def build_tasks_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        toolbar = QHBoxLayout()
        toolbar.addWidget(label("Các loại nhiệm vụ", "sectionTitle"))
        toolbar.addStretch()
        toolbar.addWidget(button("+  Thêm loại nhiệm vụ", self.add_task, "primary"))
        layout.addLayout(toolbar)
        layout.addWidget(label(
            "Tạo danh sách chức năng dự kiến, sau đó chọn riêng cho từng link ở trang Liên kết game.",
            "muted", True
        ))
        frame, inner = card()
        self.task_list = QListWidget()
        self.task_list.setObjectName("taskList")
        inner.addWidget(self.task_list, 1)
        self.tasks_empty = label("Chưa có loại nhiệm vụ.\nThêm nhiệm vụ đầu tiên để có thể chọn cho từng link.", "muted", True)
        self.tasks_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(self.tasks_empty, 1)
        self.remove_task_button = button("Xóa loại nhiệm vụ đã chọn", self.delete_task, "danger")
        self.task_list.currentItemChanged.connect(
            lambda current, previous: self.remove_task_button.setEnabled(current is not None)
        )
        inner.addWidget(self.remove_task_button, 0, Qt.AlignmentFlag.AlignRight)
        layout.addWidget(frame, 1)
        layout.addWidget(label(
            "Phiên bản này quản lý tên, ghi chú và lựa chọn nhiệm vụ. Chưa thực hiện thao tác auto trong game.",
            "muted", True
        ))
        return page

    def build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        layout.addWidget(label("Cài đặt ứng dụng", "sectionTitle"))
        frame, inner = card()
        inner.addWidget(label("Flash Player", "sectionTitle"))
        inner.addWidget(label(
            "Chọn flashplayer25sa.exe trên máy Windows của bạn. Tất cả link dùng chung trình phát này.",
            "muted", True
        ))
        row = QHBoxLayout()
        self.player_path = QLineEdit()
        self.player_path.setReadOnly(True)
        self.player_path.setPlaceholderText("Chưa chọn Flash Player")
        row.addWidget(self.player_path, 1)
        row.addWidget(button("Chọn tệp .exe", self.choose_player, "primary"))
        inner.addLayout(row)
        self.player_hint = label("", "muted", True)
        inner.addWidget(self.player_hint)
        layout.addWidget(frame)
        frame, inner = card()
        inner.addWidget(label("Dữ liệu của bạn", "sectionTitle"))
        inner.addWidget(label("Link và cài đặt auto được lưu khi bấm Sửa, tại:", "muted"))
        path = label(str(self.manager.store.path), wrap=True)
        path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        inner.addWidget(path)
        inner.addWidget(label(
            "Gỡ cài đặt hoặc cập nhật ứng dụng không xóa tệp cấu hình này. "
            "Ứng dụng không yêu cầu tài khoản game và không gửi link đến máy chủ khác.", "muted", True
        ))
        layout.addWidget(frame)
        layout.addStretch()
        return page

    def refresh(self, selected_id: str | None = None) -> None:
        links = {link.id: link for link in self.manager.state.links}
        valid_tasks = {task.id for task in self.manager.state.tasks}
        for key, draft in list(self.drafts.items()):
            draft.task_ids = [task_id for task_id in draft.task_ids if task_id in valid_tasks]
            if key not in links or draft.matches(links[key]):
                self.drafts.pop(key)
        if selected_id is not None:
            self.selected_id = selected_id
        self.refresh_metrics()
        self.refresh_links()
        self.refresh_tasks()
        player = self.manager.state.flash_player_path
        self.player_path.setText(player)
        self.player_path.setToolTip(player)
        exists = bool(player) and Path(player).is_file()
        self.player_status.setText("●  Đã chọn trình phát" if exists else "○  Chưa chọn trình phát" if not player else "○  Không tìm thấy tệp")
        self.player_hint.setText(
            "Đã lưu đường dẫn. Việc mở game cần được thực hiện trên Windows."
            if exists else "Vào Chọn tệp .exe trước khi mở link game."
        )

    def refresh_metrics(self) -> None:
        state = self.manager.state
        for widget, count in zip(self.metric_values, (len(state.links), len(state.tasks), sum(bool(link.task_ids) for link in state.links))):
            widget.setText(str(count))

    def refresh_links(self, *_args) -> None:
        self.link_list.blockSignals(True)
        self.link_list.clear()
        search = self.search.text().casefold().strip()
        visible = [link for link in self.manager.state.links if search in link.name.casefold()]
        current = None
        for link in visible:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, link.id)
            item.setSizeHint(QSize(220, 99))
            self.link_list.addItem(item)
            self.link_list.setItemWidget(item, self.link_row(link))
            if link.id == self.selected_id:
                current = item
        if current is None and self.link_list.count():
            current = self.link_list.item(0)
        self.link_list.setCurrentItem(current)
        self.link_list.blockSignals(False)
        self.list_empty.setVisible(not visible)
        self.link_list.setVisible(bool(visible))
        self.list_empty.setText(
            "Không tìm thấy tên link phù hợp." if search else
            "Chưa có link nào.\nBấm Tạo link để lưu link đầu tiên."
        )
        self.select_link(current)

    def link_row(self, link: GameLink) -> QWidget:
        row = QWidget()
        row.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 10, 8, 10)
        avatar = label(link.name[0].upper(), "avatar")
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedSize(42, 42)
        layout.addWidget(avatar)
        texts = QVBoxLayout()
        texts.setSpacing(4)
        title = label(link.name)
        title.setToolTip(link.name)
        title.setStyleSheet("font-weight: 600;")
        title.setMinimumWidth(0)
        title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        texts.addWidget(title)
        domain = label(urlsplit(link.url).hostname or "Link game", "muted")
        domain.setMinimumWidth(0)
        domain.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        texts.addWidget(domain)
        texts.addWidget(label(
            "● Có thay đổi chưa lưu" if link.id in self.drafts else f"{len(link.task_ids)} nhiệm vụ đã lưu",
            "muted",
        ))
        layout.addLayout(texts, 1)
        return row

    def select_link(self, current, _previous=None) -> None:
        self.selected_id = current.data(Qt.ItemDataRole.UserRole) if current else None
        empty_layout(self.detail)
        if self.selected_id is None:
            self.detail.addStretch()
            icon = label("◇", "emptyIcon")
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.detail.addWidget(icon)
            text = label("Chọn một link để cấu hình", "sectionTitle", True)
            text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.detail.addWidget(text)
            text = label("Lưu link mở game, chọn nhiệm vụ\nvà mở bằng Flash Player tại đây.", "muted", True)
            text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.detail.addWidget(text)
            self.detail.addStretch()
            return
        link = self.manager.get_link(self.selected_id)
        draft = self.drafts.get(link.id) or LinkDraft.from_link(link)
        self.detail.addWidget(label("CẤU HÌNH LINK", "eyebrow"))
        self.editor_name = QLineEdit(draft.name)
        self.editor_name.setObjectName("selectedName")
        self.editor_name.setAccessibleName("Tên link")
        self.editor_name.setPlaceholderText("Tên link")
        self.editor_name.setMaxLength(80)
        self.detail.addWidget(self.editor_name)
        url_row = QHBoxLayout()
        self.editor_url = QLineEdit(draft.url)
        self.editor_url.setObjectName("selectedUrl")
        self.editor_url.setAccessibleName("Link đăng nhập game")
        self.editor_url.setPlaceholderText("https://…")
        self.editor_url.setMaxLength(8192)
        self.editor_url.setCursorPosition(0)
        url_row.addWidget(self.editor_url, 1)
        url_row.addWidget(button("Sao chép", self.copy_link))
        self.detail.addLayout(url_row)
        actions = QHBoxLayout()
        login = button("Đăng nhập", self.open_selected, "primary")
        login.setToolTip("Mở link đã lưu bằng Flash Player.")
        actions.addWidget(login, 1)
        self.save_button = button("Sửa", self.edit_link)
        self.save_button.setToolTip("Lưu tên, link và toàn bộ lựa chọn auto của link này.")
        actions.addWidget(self.save_button)
        actions.addWidget(button("Xóa", self.delete_link, "danger"))
        auto = button("Chạy auto", self.run_auto)
        auto.setToolTip("Mở Flash Player bằng link đã lưu, rồi dùng cấu hình auto đã lưu.")
        actions.addWidget(auto, 1)
        self.detail.addLayout(actions)
        self.draft_status = label("", "muted", True)
        self.detail.addWidget(self.draft_status)
        heading = QHBoxLayout()
        heading.addWidget(label("Cài đặt auto", "sectionTitle"))
        heading.addStretch()
        self.revert_button = button("Hoàn tác", self.revert_draft)
        heading.addWidget(self.revert_button)
        heading.addWidget(button("+ Thêm", self.add_task))
        self.detail.addLayout(heading)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)
        tasks_layout.setContentsMargins(0, 0, 8, 0)
        tasks_layout.setSpacing(2)
        if not self.manager.state.tasks:
            tasks_layout.addWidget(label("Chưa có loại nhiệm vụ. Bấm + Thêm để tạo danh sách chức năng.", "muted", True))
        self.task_checks = {}
        for task in self.manager.state.tasks:
            checkbox = TaskCheckBox(task.name.replace("&", "&&"))
            checkbox.setObjectName(f"task_{task.id}")
            checkbox.setChecked(task.id in draft.task_ids)
            self.task_checks[task.id] = checkbox
            checkbox.toggled.connect(self.update_draft)
            tasks_layout.addWidget(checkbox)
            if task.description:
                description = label(task.description, "muted", True)
                description.setContentsMargins(28, 0, 0, 10)
                tasks_layout.addWidget(description)
        tasks_layout.addStretch()
        scroll.setWidget(tasks_widget)
        self.detail.addWidget(scroll, 1)
        self.editor_name.textChanged.connect(self.update_draft)
        self.editor_url.textChanged.connect(self.update_draft)
        self.update_draft_status()
        notice = QFrame()
        notice.setObjectName("notice")
        notice_layout = QVBoxLayout(notice)
        notice_layout.setContentsMargins(13, 10, 13, 10)
        notice_layout.addWidget(label("Phần thực thi auto sẽ bổ sung sau.", wrap=True))
        self.detail.addWidget(notice)

    def update_link_row(self, key: str) -> None:
        for index in range(self.link_list.count()):
            item = self.link_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == key:
                self.link_list.setItemWidget(item, self.link_row(self.manager.get_link(key)))
                break

    def update_draft(self, *_args) -> None:
        if self.selected_id is None:
            return
        draft = LinkDraft(
            self.editor_name.text(), self.editor_url.text(),
            [key for key, checkbox in self.task_checks.items() if checkbox.isChecked()],
        )
        if draft.matches(self.manager.get_link(self.selected_id)):
            self.drafts.pop(self.selected_id, None)
        else:
            self.drafts[self.selected_id] = draft
        self.update_draft_status()
        self.update_link_row(self.selected_id)

    def update_draft_status(self) -> None:
        dirty = self.selected_id in self.drafts
        self.draft_status.setText(
            "Có thay đổi chưa lưu. Bấm Sửa để lưu link và cài đặt auto."
            if dirty else "Đang hiển thị cấu hình đã lưu của link này."
        )
        self.revert_button.setEnabled(dirty)

    def revert_draft(self) -> None:
        if self.selected_id:
            self.drafts.pop(self.selected_id, None)
            self.update_link_row(self.selected_id)
            self.select_link(self.link_list.currentItem())
            self.statusBar().showMessage("Đã khôi phục link và cài đặt auto về bản đã lưu.", 6000)

    def refresh_tasks(self) -> None:
        self.task_list.clear()
        for task in self.manager.state.tasks:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, task.id)
            item.setSizeHint(QSize(400, 98 if task.description else 76))
            self.task_list.addItem(item)
            row = QWidget()
            row.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            inner = QVBoxLayout(row)
            inner.setContentsMargins(14, 9, 14, 9)
            inner.addWidget(label(task.name, "sectionTitle"))
            if task.description:
                summary = task.description.replace("\n", " ")
                inner.addWidget(label(summary[:100] + ("…" if len(summary) > 100 else ""), "muted", True))
            inner.addWidget(label("Chưa tích hợp bộ thực thi auto", "muted"))
            self.task_list.setItemWidget(item, row)
        empty = not self.manager.state.tasks
        self.tasks_empty.setVisible(empty)
        self.task_list.setVisible(not empty)
        self.remove_task_button.setEnabled(False)

    def create_link(self) -> None:
        dialog = LinkDialog(self.manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.search.clear()
            self.refresh(dialog.saved_id)
            self.statusBar().showMessage("Đã tạo và lưu link mới.", 6000)

    def edit_link(self) -> None:
        if not self.selected_id:
            return
        key = self.selected_id
        draft = self.drafts.get(key)
        if draft is None:
            self.statusBar().showMessage("Không có thay đổi cần lưu.", 4000)
            return
        try:
            self.manager.save_link(draft.name, draft.url, key, draft.task_ids)
        except (ValueError, StorageError) as error:
            self.show_error(error)
            return
        self.drafts.pop(key, None)
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self.refresh(key)
        self.statusBar().showMessage("Đã lưu tên, link và toàn bộ cài đặt auto của link này.", 6000)

    def delete_link(self) -> None:
        if not self.selected_id:
            return
        answer = QMessageBox.question(
            self, "Xóa link", "Xóa link đã chọn và lựa chọn nhiệm vụ của link này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            try:
                self.manager.delete_link(self.selected_id)
                self.selected_id = None
                self.refresh()
                self.statusBar().showMessage("Đã xóa link.", 6000)
            except StorageError as error:
                self.show_error(error)

    def copy_link(self) -> None:
        if self.selected_id:
            QApplication.clipboard().setText(self.editor_url.text())
            self.statusBar().showMessage("Đã sao chép link đang hiển thị.", 4000)

    def add_task(self) -> None:
        dialog = TaskDialog(self.manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()
            self.statusBar().showMessage("Đã thêm loại nhiệm vụ. Bạn có thể chọn riêng cho từng link.", 6000)

    def delete_task(self) -> None:
        item = self.task_list.currentItem()
        if item is None:
            return
        answer = QMessageBox.question(
            self, "Xóa loại nhiệm vụ",
            "Xóa loại nhiệm vụ này khỏi danh sách và khỏi tất cả các link đã chọn?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            try:
                self.manager.delete_task(item.data(Qt.ItemDataRole.UserRole))
                self.refresh()
                self.statusBar().showMessage("Đã xóa loại nhiệm vụ và cập nhật các link liên quan.", 6000)
            except StorageError as error:
                self.show_error(error)

    def choose_player(self) -> None:
        value, _filter = QFileDialog.getOpenFileName(
            self, "Chọn Flash Player", "", "Chương trình Windows (*.exe)"
        )
        if not value:
            return
        try:
            self.manager.set_player(value)
            self.refresh()
            self.statusBar().showMessage("Đã lưu đường dẫn Flash Player.", 6000)
        except (ValueError, StorageError) as error:
            self.show_error(error)

    def open_selected(self) -> bool:
        if self.selected_id is None:
            return False
        link = self.manager.get_link(self.selected_id)
        try:
            process = launcher.open_game(self.manager.state.flash_player_path, link.url)
        except (ValueError, launcher.LaunchError) as error:
            self.show_error(error)
            if not self.manager.state.flash_player_path:
                self.navigate(2)
            return False
        try:
            self.manager.mark_opened(link.id)
            self.refresh()
        except StorageError:
            self.show_error("Đã gửi lệnh mở game nhưng không lưu được lịch sử mở.")
        self.statusBar().showMessage("Đã gửi link đến Flash Player. Kiểm tra cửa sổ game để xem kết quả.", 8000)
        QTimer.singleShot(1000, lambda: self.check_launch(process))
        return True

    def run_auto(self) -> None:
        if self.selected_id is None:
            return
        key = self.selected_id
        if not self.open_selected():
            return
        try:
            plan = self.manager.auto_plan(key)
        except ValueError:
            text = (
                "Đã gửi link đã lưu đến Flash Player.\n\n"
                "Link này chưa có nhiệm vụ đã lưu. Chọn nhiệm vụ và bấm Sửa để lưu cài đặt auto.\n"
                "Bộ thực thi nhiệm vụ auto sẽ được bổ sung sau."
            )
        else:
            names = "\n".join(f"• {name}" for name in plan.task_names)
            text = (
                f"Đã gửi link đã lưu đến Flash Player.\n\nCấu hình đã lưu của {plan.link_name}:\n{names}\n\n"
                "Các nhiệm vụ này chưa có bộ thực thi auto. Chưa có thao tác nào được chạy trong game."
            )
        if key in self.drafts:
            text += "\nCác thay đổi chưa bấm Sửa không được áp dụng."
        QMessageBox.information(self, "Chạy auto theo cài đặt đã lưu", text)

    def closeEvent(self, event) -> None:
        if self.drafts:
            answer = QMessageBox.question(
                self, "Có thay đổi chưa lưu",
                f"Có {len(self.drafts)} link đang chỉnh sửa chưa lưu. Đóng ứng dụng và bỏ các thay đổi này?\n"
                "Để lưu, hãy quay lại và bấm Sửa cho từng link cần lưu.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        event.accept()

    def check_launch(self, process) -> None:
        if process.poll() not in (None, 0):
            self.show_error("Flash Player đã thoát với lỗi. Hãy kiểm tra tệp trình phát và thử mở link trực tiếp.")

    def show_error(self, error) -> None:
        QMessageBox.warning(self, "Không thực hiện được", str(error))
