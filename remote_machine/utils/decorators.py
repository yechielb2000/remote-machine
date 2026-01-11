"""
Action requirement decorators.

These decorators declare runtime requirements for action methods
and delegate enforcement to RemoteMachine.

Rules:
- SSH is implicit and never checked here
- Extra protocols must be explicitly declared
- Root / sudo checks are declarative only
"""

from __future__ import annotations

from functools import wraps
from typing import Callable, Set


def requires_protocols(*protocols: str) -> Callable:
    """
    Declare that an action method requires specific protocols
    (e.g. 'scp', 'ftp').

    SSH is implicit and MUST NOT be declared.
    """
    required: Set[str] = set(protocols)

    def decorator(func: Callable) -> Callable:
        func.__required_protocols__ = required

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # self is expected to be an Action with access to RemoteMachine
            self._rm.ensure_protocols(required)
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


def requires_root(func: Callable) -> Callable:
    """
    Declare that an action method requires the remote user to be root (uid=0).
    """

    func.__requires_root__ = True

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self._rm.ensure_root()
        return func(self, *args, **kwargs)

    return wrapper


def requires_sudo(func: Callable) -> Callable:
    """
    Declare that an action method requires sudo privileges.
    """

    func.__requires_sudo__ = True

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self._rm.ensure_sudo()
        return func(self, *args, **kwargs)

    return wrapper
