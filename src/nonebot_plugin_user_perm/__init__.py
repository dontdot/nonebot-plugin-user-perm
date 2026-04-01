import re
import json
from typing import ClassVar
from pathlib import Path

from nonebot import logger, require, get_driver
from pydantic import Field, BaseModel
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import GroupMessageEvent

require("nonebot_plugin_localstore")

import nonebot_plugin_localstore as store

__plugin_meta__ = PluginMetadata(
    name="user_perm",
    description="为其他nonebot插件提供q群普通用户权限管理",
    usage="给响应器的rule或者permission添加isPermUser来检查",
    type="library",  # library
    homepage="https://github.com/dontdot/nonebot-plugin-user-perm",
    supported_adapters={"~onebot.v11"}, # 仅 onebot
    extra={"author": "dontdot 55482264+dontdot@users.noreply.github.com"},
)

driver = get_driver()

data_dir = store.get_plugin_data_dir()

data_file_path: Path = data_dir / "user_perm.json"


class Users(BaseModel):
    users: list[int] = Field(default_factory=list)


class PermConfig(BaseModel):
    super: list[int] = Field(default_factory=list)
    group: dict[int, Users] = Field(default_factory=dict)


class PermStore:
    perm: ClassVar[dict] = {}

    @classmethod
    def _load(cls):
        data_file_path.parent.mkdir(parents=True, exist_ok=True)
        if not data_file_path.exists():
            cls._save(PermConfig().model_dump())
            return
        try:
            with open(data_file_path, encoding="utf-8") as f:
                data = json.load(f)
                if "group" in data:
                    data["group"] = {
                        int(k): cls._sw_value_int(v) for k, v in data["group"].items()
                    }
                cls.perm = data
                return
        except (json.JSONDecodeError, ValueError) as e:
            # 尝试修复读取的数据
            logger.error(f"读取数据文件出错：\n   {e}")
            cls._fix_data()

    @classmethod
    def _save(cls, data=None):
        data_file_path.parent.mkdir(parents=True, exist_ok=True)
        _data = data if data else cls.perm
        if "group" in _data:
            _data["group"] = {
                str(k): cls._sw_value_int(v) for k, v in _data["group"].items()
            }
        with open(data_file_path, "w", encoding="utf-8") as f:
            json.dump(_data, f, indent=4, ensure_ascii=True)

    @classmethod
    def _sw_value_int(cls, data: list):
        return [int(i) for i in data]

    @classmethod
    def _sw_value_str(cls, data: list):
        return [str(i) for i in data]

    @classmethod
    def _fix_data(cls):
        with open(data_file_path, encoding="utf-8") as f:
            err_data = f.read()
        fixed = re.sub(r"(\d+)(?=\s*:)", r'"\1"', err_data)
        logger.debug(f"err_data:{err_data}")
        logger.debug(f"fixed:{fixed}")
        try:
            fixed_data = json.loads(fixed)
            logger.debug(f"fixed_data:{fixed_data}")
            fixed_data["group"] = {
                int(k): cls._sw_value_int(v) for k, v in fixed_data["group"].items()
            }
            cls.perm = fixed_data
            cls._save()
            logger.info("Json格式已修复")
        except Exception as e:
            # 修复失败，使用默认
            logger.info(f"数据Json文件修复失败{e}，使用默认")
            cls.perm = PermConfig().model_dump()
            cls._save()

    @classmethod
    async def get_user_perm(cls, group_id) -> list[int]:
        _users = []
        _users.extend(cls.perm["group"].get(group_id, []))
        _users.extend(cls.perm.get("super", []))
        _users = list(set(_users))
        return _users


async def isPermUser(event: GroupMessageEvent) -> bool:
    user = event.user_id
    try:
        if user in (_premUser := await PermStore.get_user_perm(event.group_id)):
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"PermUser判断失败：\n{e}")
        return False


@driver.on_startup
async def _():
    PermStore._load()
    logger.info(f"额外用户权限已启动，具体如下：\n{PermStore.perm}")


__all__ = ["PermStore", "isPermUser"]
