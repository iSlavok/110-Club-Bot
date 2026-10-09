import importlib
import pkgutil

from aiogram import Router
from aiogram.filters import Command

import bot.handlers
from app.telegram import ADMIN_COMMANDS


def _handler_routers() -> list[Router]:
    modules = [
        importlib.import_module(f"bot.handlers.{info.name}") for info in pkgutil.iter_modules(bot.handlers.__path__)
    ]
    return [module.router for module in modules if isinstance(getattr(module, "router", None), Router)]


def _handled_commands() -> set[str]:
    commands: set[str] = set()
    for router in _handler_routers():
        for handler in router.message.handlers:
            for filter_object in handler.filters or []:
                if isinstance(filter_object.callback, Command):
                    commands.update(c for c in filter_object.callback.commands if isinstance(c, str))
    return commands


def test_every_menu_command_has_a_handler() -> None:
    menu_commands = {command.command for command in ADMIN_COMMANDS}

    assert menu_commands <= _handled_commands()
