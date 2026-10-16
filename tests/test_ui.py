from unittest.mock import Mock

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QCheckBox, QDialog, QMessageBox, QPushButton

from vptauto.service import Manager
from vptauto.storage import JsonStore, StorageError
from vptauto.ui import LinkDialog, MainWindow, TaskDialog


def test_create_links_and_tasks_with_dialogs_then_select_independently(qt_app, tmp_path):
    manager = Manager(JsonStore(tmp_path / "settings.json"))
    window = MainWindow(manager)
    window.show()
    qt_app.processEvents()
    try:
        create = LinkDialog(manager, window)
        create.name_input.setText("Nhân vật chính")
        create.url_input.setText("https://example.com/main.swf?server=1&user=2")
        create.show()
        qt_app.processEvents()
        QTest.mouseClick(create.findChild(QPushButton, "primary"), Qt.MouseButton.LeftButton)
        assert create.result() == QDialog.DialogCode.Accepted
        first = create.saved_id

        other = LinkDialog(manager, window)
        other.name_input.setText("Nhân vật phụ")
        other.url_input.setText("https://example.com/second.swf")
        other.save()
        second = other.saved_id

        new_task = TaskDialog(manager, window)
        new_task.name_input.setText("Nhiệm vụ hằng ngày")
        new_task.description_input.setPlainText("Quy trình sẽ bổ sung sau.")
        new_task.save()
        task_id = manager.state.tasks[0].id
        window.refresh(first)
        qt_app.processEvents()
        checkbox = window.findChild(QCheckBox, f"task_{task_id}")
        assert checkbox is not None
        QTest.mouseClick(checkbox, Qt.MouseButton.LeftButton)
        qt_app.processEvents()
        assert manager.get_link(first).task_ids == []
        QTest.mouseClick(window.save_button, Qt.MouseButton.LeftButton)
        assert manager.get_link(first).task_ids == [task_id]
        assert manager.get_link(second).task_ids == []

        window.search.setText("phụ")
        qt_app.processEvents()
        assert window.link_list.count() == 1
        assert window.selected_id == second
        assert not window.findChild(QCheckBox, f"task_{task_id}").isChecked()

        window.search.clear()
        qt_app.processEvents()
        restored = MainWindow(Manager(manager.store))
        restored.show()
        restored.refresh(first)
        qt_app.processEvents()
        assert restored.findChild(QCheckBox, f"task_{task_id}").isChecked()
        assert restored.metric_values[0].text() == "2"
        assert restored.metric_values[2].text() == "1"
        restored.close()
    finally:
        window.close()
        qt_app.processEvents()


def test_bad_link_shows_inline_error_and_saves_nothing(qt_app, tmp_path):
    manager = Manager(JsonStore(tmp_path / "settings.json"))
    dialog = LinkDialog(manager)
    dialog.name_input.setText("Link lỗi")
    dialog.url_input.setText("not a url")
    dialog.save()
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert dialog.error.text()
    assert manager.state.links == []
    assert not manager.store.path.exists()
    dialog.close()


def test_save_failure_keeps_unsaved_fields_and_preserves_committed_settings(qt_app, tmp_path, monkeypatch):
    manager = Manager(JsonStore(tmp_path / "settings.json"))
    key = manager.save_link("Pháp sư", "https://example.com/game.swf")
    task = manager.add_task("Hằng ngày")
    window = MainWindow(manager)
    window.show()
    qt_app.processEvents()
    errors = Mock()
    monkeypatch.setattr(window, "show_error", errors)
    monkeypatch.setattr(manager.store, "save", Mock(side_effect=StorageError("disk full")))
    checkbox = window.findChild(QCheckBox, f"task_{task}")
    window.editor_url.setText("https://example.com/changed.swf")
    QTest.mouseClick(checkbox, Qt.MouseButton.LeftButton)
    errors.assert_not_called()
    QTest.mouseClick(window.save_button, Qt.MouseButton.LeftButton)
    assert checkbox.isChecked()
    assert window.editor_url.text() == "https://example.com/changed.swf"
    assert manager.get_link(key).task_ids == []
    assert manager.get_link(key).url == "https://example.com/game.swf"
    assert Manager(manager.store).get_link(key).url == "https://example.com/game.swf"
    assert key in window.drafts
    errors.assert_called_once()
    window.drafts.clear()
    window.close()


@pytest.mark.parametrize("button_text", ["Đăng nhập", "Chạy auto"])
@pytest.mark.parametrize("saved_tasks", [False, True])
def test_launch_buttons_use_saved_links_url_and_player(qt_app, tmp_path, monkeypatch, button_text, saved_tasks):
    manager = Manager(JsonStore(tmp_path / "settings.json"))
    first = manager.save_link("Chính", "https://example.com/first.swf")
    second = manager.save_link("Phụ", "https://example.com/second.swf?x=1&y=2")
    player = tmp_path / "flash.exe"
    player.write_bytes(b"test fixture")
    manager.set_player(str(player))
    if saved_tasks:
        task = manager.add_task("Hằng ngày")
        manager.assign_tasks(second, [task])
    window = MainWindow(manager)
    window.show()
    window.refresh(second)
    process = Mock()
    process.poll.return_value = None
    open_game = Mock(return_value=process)
    monkeypatch.setattr("vptauto.ui.launcher.open_game", open_game)
    monkeypatch.setattr(QMessageBox, "information", Mock())
    window.editor_url.setText("https://example.com/unsaved.swf")
    launch_button = next(widget for widget in window.findChildren(QPushButton) if widget.text() == button_text)
    QTest.mouseClick(launch_button, Qt.MouseButton.LeftButton)
    open_game.assert_called_once_with(str(player.resolve()), manager.get_link(second).url)
    assert manager.get_link(second).last_opened is not None
    assert manager.get_link(first).last_opened is None
    assert window.editor_url.text() == "https://example.com/unsaved.swf"
    assert second in window.drafts
    window.drafts.clear()
    window.close()


def test_save_button_commits_name_url_and_auto_settings_together(qt_app, tmp_path):
    manager = Manager(JsonStore(tmp_path / "settings.json"))
    key = manager.save_link("Tên cũ", "https://example.com/old.swf")
    other = manager.save_link("Link khác", "https://example.com/other.swf")
    daily = manager.add_task("Hằng ngày")
    window = MainWindow(manager)
    window.show()
    window.refresh(key)
    qt_app.processEvents()
    window.editor_name.setText("Tên mới")
    window.editor_url.setText("https://example.com/new.swf?x=1&y=2")
    QTest.mouseClick(window.task_checks[daily], Qt.MouseButton.LeftButton)
    assert Manager(manager.store).get_link(key).name == "Tên cũ"
    assert manager.get_link(key).task_ids == []
    QTest.mouseClick(window.save_button, Qt.MouseButton.LeftButton)
    restored = Manager(manager.store)
    assert restored.get_link(key).name == "Tên mới"
    assert restored.get_link(key).url == "https://example.com/new.swf?x=1&y=2"
    assert restored.get_link(key).task_ids == [daily]
    assert restored.get_link(other).task_ids == []
    assert key not in window.drafts
    assert window.draft_status.text() == "Đang hiển thị cấu hình đã lưu của link này."
    window.close()


def test_switching_links_preserves_separate_unsaved_drafts(qt_app, tmp_path):
    manager = Manager(JsonStore(tmp_path / "settings.json"))
    first = manager.save_link("Chính", "https://example.com/first.swf")
    second = manager.save_link("Phụ", "https://example.com/second.swf")
    task = manager.add_task("Hằng ngày")
    window = MainWindow(manager)
    window.show()
    qt_app.processEvents()
    window.editor_url.setText("https://example.com/changed-first.swf")
    window.task_checks[task].setChecked(True)
    QTest.mouseClick(window.link_list.viewport(), Qt.MouseButton.LeftButton,
                     pos=window.link_list.visualItemRect(window.link_list.item(1)).center())
    assert window.selected_id == second
    assert not window.task_checks[task].isChecked()
    window.editor_name.setText("Tên phụ mới")
    window.link_list.setCurrentRow(0)
    assert window.editor_url.text() == "https://example.com/changed-first.swf"
    assert window.task_checks[task].isChecked()
    window.edit_link()
    assert manager.get_link(first).task_ids == [task]
    assert manager.get_link(second).name == "Phụ"
    window.link_list.setCurrentRow(1)
    assert window.editor_name.text() == "Tên phụ mới"
    window.revert_draft()
    assert window.editor_name.text() == "Phụ"
    assert window.drafts == {}
    window.close()


def test_invalid_url_blocks_entire_edit_and_keeps_draft(qt_app, tmp_path, monkeypatch):
    manager = Manager(JsonStore(tmp_path / "settings.json"))
    key = manager.save_link("Tên cũ", "https://example.com/old.swf")
    task = manager.add_task("Hằng ngày")
    window = MainWindow(manager)
    errors = Mock()
    monkeypatch.setattr(window, "show_error", errors)
    window.editor_name.setText("Tên mới")
    window.editor_url.setText("invalid url")
    window.task_checks[task].setChecked(True)
    window.edit_link()
    errors.assert_called_once()
    restored = Manager(manager.store).get_link(key)
    assert (restored.name, restored.url, restored.task_ids) == ("Tên cũ", "https://example.com/old.swf", [])
    assert window.editor_url.text() == "invalid url"
    window.revert_draft()
    assert window.editor_name.text() == "Tên cũ"
    assert not window.task_checks[task].isChecked()
    assert window.drafts == {}
    window.close()


def test_auto_uses_saved_task_selection_instead_of_unsaved_draft(qt_app, tmp_path, monkeypatch):
    manager = Manager(JsonStore(tmp_path / "settings.json"))
    key = manager.save_link("Chính", "https://example.com/game.swf")
    saved = manager.add_task("Nhiệm vụ đã lưu")
    new = manager.add_task("Nhiệm vụ chưa lưu")
    manager.assign_tasks(key, [saved])
    process = Mock()
    process.poll.return_value = None
    open_game = Mock(return_value=process)
    monkeypatch.setattr("vptauto.ui.launcher.open_game", open_game)
    window = MainWindow(manager)
    window.editor_name.setText("Tên chưa lưu")
    window.task_checks[saved].setChecked(False)
    window.task_checks[new].setChecked(True)
    info = Mock()
    monkeypatch.setattr(QMessageBox, "information", info)
    window.run_auto()
    text = info.call_args.args[2]
    assert "Nhiệm vụ đã lưu" in text
    assert "Nhiệm vụ chưa lưu" not in text
    assert "Tên chưa lưu" not in text
    assert "chưa có bộ thực thi auto" in text
    assert "chưa bấm Sửa không được áp dụng" in text
    window.revert_draft()
    window.close()


def test_auto_opens_flash_even_without_a_saved_task_selection(qt_app, tmp_path, monkeypatch):
    manager = Manager(JsonStore(tmp_path / "settings.json"))
    key = manager.save_link("Chính", "https://example.com/game.swf")
    task = manager.add_task("Hằng ngày")
    window = MainWindow(manager)
    window.task_checks[task].setChecked(True)
    errors = Mock()
    process = Mock()
    process.poll.return_value = None
    open_game = Mock(return_value=process)
    info = Mock()
    monkeypatch.setattr(window, "show_error", errors)
    monkeypatch.setattr("vptauto.ui.launcher.open_game", open_game)
    monkeypatch.setattr(QMessageBox, "information", info)
    window.run_auto()
    open_game.assert_called_once_with("", "https://example.com/game.swf")
    errors.assert_not_called()
    assert "chưa có nhiệm vụ đã lưu" in info.call_args.args[2]
    assert manager.get_link(key).last_opened is not None
    assert manager.get_link(key).task_ids == []
    assert window.task_checks[task].isChecked()
    window.revert_draft()
    window.close()


@pytest.mark.parametrize("button_text", ["Đăng nhập", "Chạy auto"])
@pytest.mark.parametrize("player_state", ["not_configured", "file_removed"])
def test_launch_failures_do_not_update_history_or_prepare_auto(qt_app, tmp_path, monkeypatch, button_text, player_state):
    manager = Manager(JsonStore(tmp_path / "settings.json"))
    key = manager.save_link("Chính", "https://example.com/game.swf")
    if player_state == "file_removed":
        player = tmp_path / "flash.exe"
        player.write_bytes(b"test fixture")
        manager.set_player(str(player))
        player.unlink()
    window = MainWindow(manager)
    window.show()
    qt_app.processEvents()
    errors, info, plan = Mock(), Mock(), Mock()
    spawn = Mock()
    monkeypatch.setattr(window, "show_error", errors)
    monkeypatch.setattr(QMessageBox, "information", info)
    monkeypatch.setattr(manager, "auto_plan", plan)
    monkeypatch.setattr("vptauto.launcher.subprocess.Popen", spawn)
    launch_button = next(widget for widget in window.findChildren(QPushButton) if widget.text() == button_text)
    QTest.mouseClick(launch_button, Qt.MouseButton.LeftButton)
    errors.assert_called_once()
    info.assert_not_called()
    plan.assert_not_called()
    spawn.assert_not_called()
    assert manager.get_link(key).last_opened is None
    if player_state == "not_configured":
        assert window.pages.currentIndex() == 2
    window.close()


def test_close_requires_explicit_discard_of_unsaved_changes(qt_app, tmp_path, monkeypatch):
    manager = Manager(JsonStore(tmp_path / "settings.json"))
    key = manager.save_link("Tên cũ", "https://example.com/game.swf")
    window = MainWindow(manager)
    window.show()
    qt_app.processEvents()
    window.editor_name.setText("Tên chưa lưu")
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No)
    assert not window.close()
    assert window.isVisible()
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    assert window.close()
    assert Manager(manager.store).get_link(key).name == "Tên cũ"


def test_cancel_deletion_preserves_links_and_confirm_only_removes_selected(qt_app, tmp_path, monkeypatch):
    manager = Manager(JsonStore(tmp_path / "settings.json"))
    first = manager.save_link("Chính", "https://example.com/first.swf")
    second = manager.save_link("Phụ", "https://example.com/second.swf")
    window = MainWindow(manager)
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No)
    window.delete_link()
    assert len(manager.state.links) == 2
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    window.delete_link()
    assert [link.id for link in Manager(manager.store).state.links] == [second]
    window.close()
