# SPDX-License-Identifier: GPL-3.0-or-later
"""Conservative, deterministic selection for room lighting controls."""
import re

from app.core.models import DeviceInfo

_CHANNEL = re.compile(r"\.s\d+$")


def room_light_devices(devices: list[DeviceInfo], home: str, room: str,
                       *, online_only: bool = True) -> list[DeviceInfo]:
    if not home or home in ("全部", "未知") or not room or room in ("全屋", "场景", "未知"):
        return []
    # A parent panel's first channel may alias a named virtual device.
    parents = {_CHANNEL.sub("", d.did) for d in devices if _CHANNEL.search(d.did)}
    targets = {}
    for dev in devices:
        if dev.home_name != home or dev.room_name != room:
            continue
        if online_only and not dev.online:
            continue
        parts = dev.model.lower().split(".")
        kind = parts[1] if len(parts) >= 3 else ""
        if kind == "switch":
            if dev.did in parents:
                continue
            label = dev.name.lower()
            if not any(word in label for word in ("灯", "照明", "light", "lamp")):
                continue
        elif kind != "light":
            continue
        targets.setdefault(dev.did, dev)
    # Keep source order within each group, but restore relay power first.
    return sorted(targets.values(), key=lambda d: ".switch." not in d.model.lower())
