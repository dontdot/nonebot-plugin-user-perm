<div align="center">
    <a href="https://v2.nonebot.dev/store">
    <img src="https://raw.githubusercontent.com/fllesser/nonebot-plugin-template/refs/heads/resource/.docs/NoneBotPlugin.svg" width="310" alt="logo"></a>

## ✨ nonebot-plugin-user-perm ✨
[![LICENSE](https://img.shields.io/github/license/dontdot/nonebot-plugin-user-perm.svg)](./LICENSE)
[![pypi](https://img.shields.io/pypi/v/nonebot-plugin-user-perm.svg)](https://pypi.python.org/pypi/nonebot-plugin-user-perm)
[![python](https://img.shields.io/badge/python-3.10|3.11|3.12|3.13-blue.svg)](https://www.python.org)
[![uv](https://img.shields.io/badge/package%20manager-uv-black?style=flat-square&logo=uv)](https://github.com/astral-sh/uv)
<br/>
[![ruff](https://img.shields.io/badge/code%20style-ruff-black?style=flat-square&logo=ruff)](https://github.com/astral-sh/ruff)
[![pre-commit](https://results.pre-commit.ci/badge/github/dontdot/nonebot-plugin-user-perm/master.svg)](https://results.pre-commit.ci/latest/github/dontdot/nonebot-plugin-user-perm/master)

</div>

## 📖 介绍

设置群聊的某些普通用户使用插件的某个权限命令！

使用onebotv11适配器提供 `is_perm_user` 函数给其他插件使用在响应器中

注意：`is_perm_user`只接受群消息事件`GroupMessageEvent` 

> `is_perm_user` 将判断这条消息发送人是否是该群聊设置的特定普通用户 + super用户

默认数据格式：{'super': [ ], 'group': { } } 

> 例如：{'super': [12345], 'group': {'某个qq群号': [112233, 223344]}} \
> 每个[ ]里填入普通用户的qq号(int类型)


## 💿 安装

<details open>
<summary>【XXX】使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-user-perm --upgrade
使用 **pypi** 源安装

    nb plugin install nonebot-plugin-user-perm --upgrade -i "https://pypi.org/simple"
使用**清华源**安装

    nb plugin install nonebot-plugin-user-perm --upgrade -i "https://pypi.tuna.tsinghua.edu.cn/simple"


</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details open>
<summary>uv</summary>

    uv add nonebot-plugin-user-perm
安装仓库 master 分支

    uv add git+https://github.com/dontdot/nonebot-plugin-user-perm@master
</details>

<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-user-perm
安装仓库 master 分支

    pdm add git+https://github.com/dontdot/nonebot-plugin-user-perm@master
</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-user-perm
安装仓库 master 分支

    poetry add git+https://github.com/dontdot/nonebot-plugin-user-perm@master
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_user_perm"]

</details>

<details>
<summary>使用 nbr 安装(使用 uv 管理依赖可用)</summary>

[nbr](https://github.com/fllesser/nbr) 是一个基于 uv 的 nb-cli，可以方便地管理 nonebot2

    nbr plugin install nonebot-plugin-user-perm
使用 **pypi** 源安装

    nbr plugin install nonebot-plugin-user-perm -i "https://pypi.org/simple"
使用**清华源**安装

    nbr plugin install nonebot-plugin-user-perm -i "https://pypi.tuna.tsinghua.edu.cn/simple"

</details>


## ⚙️ 配置

使用`nonebot-plugin-localstore`持久化保存数据
可在 nonebot2 项目的`.env`文件中添加以下配置，使数据文件保存在bot项目下的`data`目录

> LOCALSTORE_USE_CWD=True



## 🎉 使用

提供以下4个方法：

|     方法     |    参数   |                说明                |
| :----------: | :-------: | :-------------------------------: |
|   add_user   |  user_id  |      在当前群聊增加一个权限用户     |
|   del_user   |  user_id  |      在当前群聊删除一个权限用户     |
| is_perm_user |     无    | 检查当前信息发送人是否是在权限用户中 |
|   get_users  |  group_id, mode | 获取该群聊的权限用户, mode默认为0，包含global用户，mode=1则排除global用户 |

示例：在其他插件上使用

```python
...
from nonebot import require
require("nonebot_plugin_user_perm")
from nonebot_plugin_user_perm import is_perm_user

weather = on_command("天气", permission=is_perm_user)` 
```

or 

```python
...
from nonebot import require
require("nonebot_plugin_user_perm")
from nonebot_plugin_user_perm import isPermUser

any_permission = SUPERUSER | GROUP_ADMIN | GROUP_OWNER | Permission(is_perm_user)
weather = on_command("天气", permission=any_permission)
```


### 🎨 效果图
如果有效果图的话
