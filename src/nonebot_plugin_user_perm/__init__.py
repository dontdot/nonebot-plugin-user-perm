import re
import json
from typing import ClassVar
from pathlib import Path

from nonebot import logger, require, get_driver, on_notice
from pydantic import Field, BaseModel
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, GroupIncreaseNoticeEvent, GroupDecreaseNoticeEvent

require("nonebot_plugin_localstore")

import nonebot_plugin_localstore as store

__plugin_meta__ = PluginMetadata(
    name="user_perm",
    description="为其他nonebot插件提供q群普通用户权限管理",
    usage="给响应器的rule或者permission添加isPermUser来检查",
    type="library",  # library
    homepage="https://github.com/dontdot/nonebot-plugin-user-perm",
    supported_adapters={"~onebot.v11"},  # 仅 onebot
    extra={"author": "dontdot 55482264+dontdot@users.noreply.github.com"},
)

driver = get_driver()

data_dir = store.get_plugin_data_dir()

data_file_path: Path = data_dir / "perm_users.json"


class Users(BaseModel):
    users: list[int] = Field(default_factory=list)


class PermConfig(BaseModel):
    super: list[int] = Field(default_factory=list)
    group: dict[int, Users] = Field(default_factory=dict)


class PermStore:
    _perm: ClassVar[dict] = {}

    @classmethod
    def _load(cls):
        data_file_path.parent.mkdir(parents=True, exist_ok=True)
        if not data_file_path.exists():
            _default_data = PermConfig().model_dump()
            cls._perm = _default_data
            cls._save(_default_data)
            return
        try:
            with open(data_file_path, encoding="utf-8") as f:
                data = json.load(f)
                if "group" in data:
                    data["group"] = {
                        int(k): cls._sw_value_int(v) for k, v in data["group"].items()
                    }
                cls._perm = data
                return
        except (json.JSONDecodeError, ValueError) as e:
            # 尝试修复读取的数据
            logger.error(f"读取数据文件出错：\n   {e}")
            cls._fix_data()

    @classmethod
    def _save(cls, data=None):
        data_file_path.parent.mkdir(parents=True, exist_ok=True)
        _data = data if data else cls._perm
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
            cls._perm = fixed_data
            cls._save()
            logger.info("Json格式已修复")
        except Exception as e:
            # 修复失败，使用默认
            logger.info(f"数据Json文件修复失败{e}，使用默认")
            cls._perm = PermConfig().model_dump()
            cls._save()


async def get_users(group_id, mode: int = 0) -> list[int]:
    """
    ; group_id: 群号
    ; mode: 0-包含global用户，1-排除global用户
    """
    try:
        _users = []
        _users.extend(PermStore._perm["group"].get(group_id, []))
        if mode == 0:
            _users.extend(PermStore._perm.get("super", []))
        _users = list(set(_users))

        # 排除不在群聊里的账号
        _group_mem_cache = set(await get_group_mem_cache(group_id))
        _users = [uid for uid in _users if uid in _group_mem_cache]

        # 记录被排除的用户
        excluded = set(_users) - set([uid for uid in _users if uid in _group_mem_cache])
        if excluded:
            logger.info(f"排除不在群聊的用户: {excluded}")
            
        return _users
    
    except Exception as e:
        logger.error(f"获取群'{group_id}'的权限用户出错，\n {e}")
        return []


async def is_perm_user(event: GroupMessageEvent) -> bool:
    try:
        user = event.user_id
        if user in (_premUser := await get_users(event.group_id)):
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"PermUser判断失败： \n {e}")
        return False


async def add_user(user_id, event: GroupMessageEvent) -> bool:
    try:
        user_id = int(user_id)
        user_set = set(await get_users(event.group_id))
        user_set.add(user_id)
        _users = list(user_set)
        PermStore._perm["group"][event.group_id] = _users
        logger.info(f"<success> 群'{event.group_id}'，用户'{user_id}'已添加")
        PermStore._save()
        return True
    except Exception as e:
        logger.error(f"群'{event.group_id}'用户添加失败：\n{e}")
        return False


async def del_user(user_id, event: GroupMessageEvent) -> bool:
    try:
        user_id = int(user_id)
        user_set = set(await get_users(event.group_id))
        user_set.discard(user_id)
        _users = list(user_set)
        PermStore._perm["group"][event.group_id] = _users
        logger.info(f"<success> 群'{event.group_id}'，用户'{user_id}'已移除")
        PermStore._save()
        return True
    except Exception as e:
        logger.error(f"群'{event.group_id}'用户移除失败： \n {e}")
        return False


class GroupMemberCache:
    _groups_cache: dict[int, list[int]] = {}

    @classmethod
    def update(cls, group_id: int, members: list[int]):
        """更新缓存"""
        cls._groups_cache[group_id] = members
    
    @classmethod
    def get(cls, group_id: int) -> list[int]:
        """获取缓存"""
        return cls._groups_cache.get(group_id, [])


group_notice = on_notice(priority=1)


@group_notice.handle()
async def updata_group_mem_cache(bot: Bot, event: GroupIncreaseNoticeEvent | GroupDecreaseNoticeEvent | None):
    if isinstance(event, GroupIncreaseNoticeEvent|GroupDecreaseNoticeEvent):
        logger.info(f"检测到群聊<{event.group_id}>成员增加，更新群聊成员列表缓存")
        groups_id = [event.group_id]
    elif event is None:
        groups_id = [gid for gid in PermStore._perm["group"].keys()]

    for group_id in groups_id:
        _users = [id["user_id"] for id in (await bot.get_group_member_list(group_id=group_id))]
        GroupMemberCache.update(group_id, _users)
        logger.success(f"更新群聊成员列表缓存 > \n<{group_id}>\n{_users}")


async def get_group_mem_cache(group_id) -> list:
    return GroupMemberCache.get(group_id)


@driver.on_startup
async def _():
    PermStore._load()
    logger.info(f"额外用户权限已启动，具体如下： \n {PermStore._perm}")


async def startup(bot):
    """插件启动时清理已入群用户"""
    try:
        # global driver
        # bots = driver.bots
        # if bots:
        #     bot = next(iter(bots.values()))
        await updata_group_mem_cache(bot, event=None)
    except Exception as e:
        logger.error(f"群聊成员缓存获取失败: {e}")


driver.on_bot_connect(startup)


__all__ = ["add_user", "del_user", "get_users", "get_group_mem_cache", "is_perm_user"]
