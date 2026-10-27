"""Room controls integration: fake queue and service, never real devices."""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from tests._isolate import isolate
isolate()
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from tests.room_lights_test import device


class Queue:
    def __init__(self):
        self.tasks = []

    def submit(self, fn, on_success=None, on_error=None, **kwargs):
        self.tasks.append((fn, on_success, on_error))

    def drain(self):
        while self.tasks:
            fn, success, failure = self.tasks.pop(0)
            try:
                result = fn()
            except Exception as exc:
                failure(exc)
            else:
                success(result)


class RoomLightsUITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.toast = patch("app.ui.main_window.Toast.info").start()
        self.win = MainWindow()
        self.win._jobs.shutdown(wait=1)
        self.win._web_jobs.shutdown(wait=1)
        self.queue = Queue()
        self.win._jobs = self.queue
        self.writes = []

        def write(did, state):
            self.writes.append((did, state))
            if did == "fail":
                raise RuntimeError("设备无响应")

        self.win._service = SimpleNamespace(set_power_state=write,
            spec_has_published_functions=lambda _: True)
        self.win._update_tray_devices = lambda: None
        self.win._board = None
        self.win._all_devices = [device("ok", "主灯"), device("fail", "射灯"),
            device("offline", "离线灯", online=False),
            device("other", "客厅灯", room="客厅"),
            device("plug", "空调插座", "test.plug.v1")]
        self.win._current_home = "新家"
        self.win._current_room = "主卧"
        self.win._known_power = {"ok": True, "fail": True}

    def tearDown(self):
        self.win.hide()
        self.win.deleteLater()
        self.app.processEvents()
        patch.stopall()

    def test_buttons_are_only_available_for_a_specific_room_and_home(self):
        self.assertTrue(hasattr(self.win, "_room_lights_on_btn"), "Missing room light controls")
        self.win._update_count_label()
        self.assertTrue(self.win._room_lights_on_btn.isEnabled())
        self.assertIn("2", self.win._room_lights_label.text())
        self.win._current_room = "全屋"
        self.win._update_count_label()
        self.assertTrue(self.win._room_lights_bar.isHidden())
        self.win._current_room = "主卧"
        self.win._current_home = "全部"
        self.win._update_count_label()
        self.assertFalse(self.win._room_lights_on_btn.isEnabled())
        self.win._current_room = "场景"
        self.win._update_count_label()
        self.assertTrue(self.win._room_lights_bar.isHidden())

    def test_partial_failure_repeat_clicks_and_room_switch_do_not_change_targets(self):
        self.assertTrue(hasattr(self.win, "_on_room_lights_power"), "Missing batch control")
        self.win._on_room_lights_power(False)
        self.assertEqual(len(self.queue.tasks), 2)
        self.assertFalse(self.win._room_lights_on_btn.isEnabled())
        snapshot = {"ok": 0, "fail": 0}
        self.win._on_room_lights_power(True)
        self.assertEqual(len(self.queue.tasks), 2, "Duplicate batch was queued")
        self.win._current_room = "客厅"
        self.queue.drain()
        self.assertEqual(self.writes, [("ok", False), ("fail", False)])
        self.assertFalse(self.win._known_power["ok"])
        self.assertTrue(self.win._known_power["fail"], "Failed write changed displayed state")
        self.win._maybe_localize_names = lambda: None
        self.win._apply_power_states({"ok": True}, snapshot)
        self.assertFalse(self.win._known_power["ok"], "Old poll overwrote batch result")
        self.assertFalse(self.win._room_light_pending)
        self.assertIn("成功 1", self.toast.call_args.args[1])
        self.assertIn("失败 1", self.toast.call_args.args[1])
        self.assertIn("离线 1", self.toast.call_args.args[1])


if __name__ == "__main__":
    unittest.main()
