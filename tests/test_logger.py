import logging
import sys


def test_import_does_not_configure_root_logger_handlers():
    """Importing frankfurter must not add handlers to the root logger."""
    root = logging.getLogger()
    handlers_before = list(root.handlers)

    # Force a clean reimport
    for mod in list(sys.modules.keys()):
        if mod.startswith("frankfurter"):
            del sys.modules[mod]

    import frankfurter  # noqa: F401

    assert root.handlers == handlers_before, (
        f"Import added handlers to root logger: {root.handlers}"
    )


def test_import_does_not_change_root_logger_level():
    """Importing frankfurter must not change the root logger's level."""
    root = logging.getLogger()
    level_before = root.level

    for mod in list(sys.modules.keys()):
        if mod.startswith("frankfurter"):
            del sys.modules[mod]

    import frankfurter  # noqa: F401

    assert root.level == level_before, (
        f"Import changed root logger level from {level_before} to {root.level}"
    )


def test_library_logger_has_null_handler():
    """The frankfurter logger must have a NullHandler so it is silent by default."""
    for mod in list(sys.modules.keys()):
        if mod.startswith("frankfurter"):
            del sys.modules[mod]

    import frankfurter  # noqa: F401

    logger = logging.getLogger("frankfurter")
    assert any(isinstance(h, logging.NullHandler) for h in logger.handlers), (
        "frankfurter logger must have a NullHandler"
    )
