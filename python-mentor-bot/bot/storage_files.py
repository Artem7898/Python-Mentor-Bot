"""File preparation for private SQLite databases."""

import os
import stat
from pathlib import Path

_SIDECARS = ("-journal", "-wal", "-shm")


def prepare_database_files(path: Path) -> None:
    """Create a private database file and tighten existing SQLite sidecars on POSIX."""
    if path == Path(":memory:"):
        return

    directory = path.parent
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    names = (path, *(path.with_name(path.name + suffix) for suffix in _SIDECARS))
    if directory.is_symlink() or any(candidate.is_symlink() for candidate in names):
        raise PermissionError("The database path must not use a symbolic link.")
    if os.name != "posix":
        # Parent ACLs, rather than chmod, govern filesystem privacy on Windows.
        return

    parent = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        owner = os.geteuid()
        info = os.fstat(parent)
        if info.st_uid != owner or info.st_mode & 0o022:
            raise PermissionError("Use an owned SQLite directory without shared write access.")

        for index, candidate in enumerate(names):
            _prepare_file(parent, candidate.name, owner, create=index == 0)
    finally:
        os.close(parent)


def _prepare_file(directory: int, name: str, owner: int, *, create: bool) -> None:
    flags = os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        metadata = os.stat(name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        if not create:
            return
        try:
            descriptor = os.open(name, flags | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=directory)
        except FileExistsError:
            metadata = os.stat(name, dir_fd=directory, follow_symlinks=False)
        else:
            try:
                os.fchmod(descriptor, 0o600)
            finally:
                os.close(descriptor)
            return

    _check_private_file(metadata, owner)
    if stat.S_IMODE(metadata.st_mode) == 0o600:
        # Closing an extra descriptor on this inode could release SQLite's POSIX locks.
        return
    try:
        descriptor = os.open(name, flags, dir_fd=directory)
    except FileNotFoundError:
        if not create:  # A SQLite worker can remove a transient sidecar.
            return
        raise
    try:
        _check_private_file(os.fstat(descriptor), owner)
        os.fchmod(descriptor, 0o600)
    finally:
        os.close(descriptor)


def _check_private_file(metadata: os.stat_result, owner: int) -> None:
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != owner or metadata.st_nlink != 1:
        raise PermissionError("Use regular SQLite files owned by the service account.")
