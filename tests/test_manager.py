import json
from unittest.mock import Mock

import pytest

from vptauto import launcher
from vptauto.models import clean_url
from vptauto.service import Manager
from vptauto.storage import JsonStore, StorageError


def test_links_keep_separate_tasks_after_restart_and_edit(tmp_path):
    store = JsonStore(tmp_path / "settings.json")
    manager = Manager(store)
    first = manager.save_link("Pháp sư chính", "https://example.com/play.swf?a=1&b=2")
    second = manager.save_link("Nhân vật phụ", "https://example.com/play.swf?a=3&b=4")
    daily = manager.add_task("Nhiệm vụ hằng ngày", "Nhận rồi trả nhiệm vụ.")
    collect = manager.add_task("Thu thập vật phẩm")
    manager.assign_tasks(first, [daily])
    manager.assign_tasks(second, [collect])
    manager.save_link("Pháp sư chính đã sửa", "https://example.com/new.swf", first)

    restored = Manager(store)
    assert restored.get_link(first).name == "Pháp sư chính đã sửa"
    assert restored.get_link(first).task_ids == [daily]
    assert restored.get_link(second).task_ids == [collect]
    assert restored.get_link(second).url == "https://example.com/play.swf?a=3&b=4"

    restored.delete_task(daily)
    again = Manager(store)
    assert again.get_link(first).task_ids == []
    assert again.get_link(second).task_ids == [collect]
    again.delete_link(first)
    assert [link.id for link in Manager(store).state.links] == [second]


@pytest.mark.parametrize("url", ["", "file:///tmp/a.swf", "javascript:alert(1)", "https://", "https://example.com/a b", "https://example.com:99999/a"])
def test_reject_invalid_or_local_urls(url):
    with pytest.raises(ValueError):
        clean_url(url)


def test_failed_atomic_save_preserves_previous_file_and_memory(tmp_path, monkeypatch):
    store = JsonStore(tmp_path / "settings.json")
    manager = Manager(store)
    manager.save_link("Link cũ", "https://example.com/old.swf")
    original = store.path.read_bytes()
    monkeypatch.setattr("vptauto.storage.os.replace", Mock(side_effect=OSError("disk error")))
    with pytest.raises(StorageError):
        manager.save_link("Link mới", "https://example.com/new.swf")
    assert store.path.read_bytes() == original
    assert len(manager.state.links) == 1
    assert list(tmp_path.glob("*.tmp")) == []


@pytest.mark.parametrize("contents", ["not json", '{"schema_version": 999}', json.dumps({"schema_version": 1, "links": [{"id": "x", "name": "A", "url": "https://example.com", "task_ids": ["missing"]}]})])
def test_corrupt_or_future_data_is_never_overwritten(tmp_path, contents):
    path = tmp_path / "settings.json"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(StorageError):
        Manager(JsonStore(path))
    assert path.read_text(encoding="utf-8") == contents


def test_launcher_passes_url_as_one_argument_without_shell(tmp_path, monkeypatch):
    player = tmp_path / "Flash Player with spaces.exe"
    player.write_bytes(b"test fixture")
    url = "https://example.com/game.swf?user=abc&server=1&next=%22test%22"
    spawn = Mock()
    monkeypatch.setattr(launcher.sys, "platform", "win32")
    startup = Mock(dwFlags=0)
    monkeypatch.setattr(launcher.subprocess, "STARTUPINFO", Mock(return_value=startup), raising=False)
    monkeypatch.setattr(launcher.subprocess, "STARTF_USESHOWWINDOW", 1, raising=False)
    monkeypatch.setattr(launcher.subprocess, "Popen", spawn)
    launcher.open_game(str(player), url)
    assert spawn.call_args.args == ([str(player.resolve()), url],)
    assert spawn.call_args.kwargs["shell"] is False
    assert spawn.call_args.kwargs["cwd"] == str(tmp_path)
    assert spawn.call_args.kwargs["startupinfo"].wShowWindow == 4


def test_missing_flash_never_spawns_process(tmp_path, monkeypatch):
    spawn = Mock()
    monkeypatch.setattr(launcher.subprocess, "Popen", spawn)
    with pytest.raises(launcher.LaunchError):
        launcher.open_game(str(tmp_path / "missing.exe"), "https://example.com/game.swf")
    spawn.assert_not_called()


def test_invalid_task_assignment_does_not_change_saved_selection(tmp_path):
    manager = Manager(JsonStore(tmp_path / "settings.json"))
    key = manager.save_link("Pháp sư", "https://example.com/game.swf")
    task = manager.add_task("Hằng ngày")
    manager.assign_tasks(key, [task])
    with pytest.raises(ValueError):
        manager.assign_tasks(key, ["not-present"])
    with pytest.raises(ValueError):
        manager.assign_tasks(key, [task, task])
    assert Manager(manager.store).get_link(key).task_ids == [task]


def test_auto_plan_is_an_immutable_snapshot_of_committed_settings(tmp_path):
    manager = Manager(JsonStore(tmp_path / "settings.json"))
    key = manager.save_link("Pháp sư", "https://example.com/first.swf")
    daily = manager.add_task("Hằng ngày")
    manager.assign_tasks(key, [daily])
    plan = manager.auto_plan(key)
    manager.save_link("Tên khác", "https://example.com/second.swf", key, [])
    assert plan.link_name == "Pháp sư"
    assert plan.url == "https://example.com/first.swf"
    assert plan.task_ids == (daily,)
    assert plan.task_names == ("Hằng ngày",)


def test_combined_edit_rejects_missing_task_without_partial_update(tmp_path):
    manager = Manager(JsonStore(tmp_path / "settings.json"))
    key = manager.save_link("Tên cũ", "https://example.com/old.swf")
    before = manager.store.path.read_bytes()
    with pytest.raises(ValueError):
        manager.save_link("Tên mới", "https://example.com/new.swf", key, ["missing"])
    assert manager.store.path.read_bytes() == before
    assert manager.get_link(key).name == "Tên cũ"


def test_character_slot_is_saved_per_link_and_old_config_defaults_to_one(tmp_path):
    store = JsonStore(tmp_path / "settings.json")
    store.path.write_text(json.dumps({"schema_version": 1, "tasks": [], "links": [
        {"id": "old", "name": "Cũ", "url": "https://example.com/old.swf"}
    ]}), encoding="utf-8")
    manager = Manager(store)
    assert manager.get_link("old").character_slot == 1
    second = manager.save_link("Phụ", "https://example.com/new.swf", character_slot=2)
    manager.save_link("Cũ sửa", "https://example.com/old.swf", "old", character_slot=3)
    restored = Manager(store)
    assert restored.get_link("old").character_slot == 3
    assert restored.get_link(second).character_slot == 2


@pytest.mark.parametrize("slot", [0, 4, True, "2", 2.0])
def test_invalid_character_slot_does_not_change_config(tmp_path, slot):
    manager = Manager(JsonStore(tmp_path / "settings.json"))
    key = manager.save_link("Chính", "https://example.com/game.swf")
    before = manager.store.path.read_bytes()
    with pytest.raises(ValueError):
        manager.save_link("Đổi tên", "https://example.com/new.swf", key, character_slot=slot)
    assert manager.store.path.read_bytes() == before
