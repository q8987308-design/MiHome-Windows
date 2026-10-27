"""Room scope, power-channel safety, and partial failures; no network calls."""
import unittest
from app.core.models import DeviceInfo


def device(did, name, model="test.light.v1", home="新家", room="主卧", online=True):
    return DeviceInfo(did, name, model, home, room, online)


class RoomLightsTest(unittest.TestCase):
    def test_filter_is_room_and_home_scoped_and_excludes_non_lights(self):
        from app.core.room_lights import room_light_devices
        devices = [
            device("lamp", "主灯"), device("relay.s3", "射灯", "test.switch.v1"),
            device("plug", "灯光插座", "test.plug.v1"),
            device("hub", "网关", "test.gateway.v1"),
            device("ac", "空调", "test.aircondition.v1"),
            device("unknown", "床头柜左", "test.switch.v1"),
            device("other", "主灯", home="另一家庭"),
            device("room", "主灯", room="客厅"),
            device("offline", "离线灯", online=False),
        ]
        self.assertEqual([d.did for d in room_light_devices(devices, "新家", "主卧")],
                         ["relay.s3", "lamp"])
        self.assertEqual([d.did for d in room_light_devices(devices, "新家", "主卧", online_only=False)],
                         ["relay.s3", "lamp", "offline"])

    def test_no_aggregate_scope_or_ambiguous_switch_parent(self):
        from app.core.room_lights import room_light_devices
        devices = [device("p", "主灯总开关", "test.switch.v1"),
                   device("p.s2", "主灯", "test.switch.v1"),
                   device("p.s3", "射灯", "test.switch.v1"),
                   device("p.s2", "重复灯", "test.switch.v1")]
        self.assertEqual([d.did for d in room_light_devices(devices, "新家", "主卧")],
                         ["p.s2", "p.s3"])
        self.assertEqual(room_light_devices(devices, "全部", "主卧"), [])
        self.assertEqual(room_light_devices(devices, "新家", "全屋"), [])
        self.assertEqual(room_light_devices(devices, "新家", "场景"), [])

    def test_unresolved_home_or_room_must_never_enable_bulk_writes(self):
        from app.core.room_lights import room_light_devices
        unknown = [device("a", "灯", home="未知", room="未知"),
                   device("b", "灯", home="未知", room="未知")]
        self.assertEqual(room_light_devices(unknown, "未知", "未知"), [])
        self.assertEqual(room_light_devices([device("c", "灯", room="未知")],
                                           "新家", "未知"), [])


if __name__ == "__main__":
    unittest.main()
