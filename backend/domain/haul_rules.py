import re

from core.records import need

RACKS = {"横抽盘架", "双列苗框"}
ROUTES = {"EAST-REEF", "WEST-GRAVEL"}


def rack_family(name):
    need(name in RACKS, "未知的苗盘架型")
    return name


def route_name(code):
    need(code in ROUTES, "未知的内部试车线路")
    return code


def cycle_name(code):
    need(re.fullmatch(r"(AM|PM)-[0-9]{2}", code), "班次编号需形如 AM-01 或 PM-02")
    return code
