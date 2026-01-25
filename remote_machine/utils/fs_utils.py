from remote_machine.models.filesystem_types import PermissionBits, Permissions


def parse_permissions(perms: str) -> Permissions:
    if len(perms) < 10:
        raise ValueError(f"Invalid permission string: {perms}")

    type_map = {
        "-": "file",
        "d": "dir",
        "l": "symlink",
        "c": "char_device",
        "b": "block_device",
        "s": "socket",
        "p": "fifo",
    }

    def bits(chunk: str) -> PermissionBits:
        return PermissionBits(
            read=chunk[0] == "r",
            write=chunk[1] == "w",
            execute=chunk[2] in ("x", "s", "t"),  # handles suid/sticky
        )

    return Permissions(
        entry_type=type_map.get(perms[0], "unknown"),
        owner=bits(perms[1:4]),
        group=bits(perms[4:7]),
        others=bits(perms[7:10]),
        raw=perms,
    )
