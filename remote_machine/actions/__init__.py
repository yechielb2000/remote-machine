"""Actions package."""

from remote_machine.actions.fs import FSAction
from remote_machine.actions.ps import PSAction
from remote_machine.actions.net import NETAction
from remote_machine.actions.env import ENVAction
from remote_machine.actions.sys import SYSAction
from remote_machine.actions.service import ServiceAction
from remote_machine.actions.device import DeviceAction
from remote_machine.actions.docker import DockerAction
from remote_machine.actions.git import GitAction
from remote_machine.actions.firewall import FirewallAction
from remote_machine.actions.cron import CronAction
from remote_machine.actions.python import PythonAction
from remote_machine.actions.onie import ONIEAction
from remote_machine.actions.proxy import ProxyAction

__all__ = [
    "FSAction",
    "PSAction",
    "NETAction",
    "ENVAction",
    "SYSAction",
    "ServiceAction",
    "DeviceAction",
    "DockerAction",
    "GitAction",
    "FirewallAction",
    "CronAction",
    "PythonAction",
    "ONIEAction",
    "ProxyAction",
]
