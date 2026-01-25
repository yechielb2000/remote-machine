"""Path resolution utilities."""

from pathlib import PurePosixPath


class PathResolver:
    """Resolve filesystem paths against remote state cwd."""

    @staticmethod
    def resolve(path: str, cwd: str = "/") -> str:
        """Resolve a path against cwd.

        Args:
            path: Path to resolve (absolute or relative)
            cwd: Current working directory

        Returns:
            Absolute path
        """
        p = PurePosixPath(path)

        if p.is_absolute():
            return str(p)

        # Relative path - resolve against cwd
        base = PurePosixPath(cwd)
        resolved = base / p

        # Normalize path components (handle .. and . lexically)
        return PathResolver.normalize(str(resolved))

    @staticmethod
    def normalize(path: str) -> str:
        """Normalize a path.

        Args:
            path: Path to normalize

        Returns:
            Normalized path
        """
        p = PurePosixPath(path)
        parts = p.parts
        is_abs = path.startswith("/")
        stack: list[str] = []
        for part in parts:
            # Skip empty and current-dir markers
            if part in ("", "."):
                continue
            # Skip root token produced by PurePosixPath.parts
            if part == "/":
                continue
            if part == "..":
                if stack and stack[-1] != "..":
                    stack.pop()
                else:
                    if not is_abs:
                        stack.append("..")
                continue
            stack.append(part)

        if is_abs:
            return "/" + "/".join(stack)
        return "/".join(stack) or "."
