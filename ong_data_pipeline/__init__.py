"""ong_data_pipeline package.

Keep imports light at package import time to avoid importing heavy
dependencies (e.g. SQLAlchemy) when the package metadata is inspected.
Use explicit imports from submodules where needed.
"""

__all__ = [
    "extract",
    "transform",
    "load",
    "config",
]
