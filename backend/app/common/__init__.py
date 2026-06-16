"""Shared application primitives: model base, field factories, and HTTP error classes.

Import directly from the owning submodule (``from app.common.models import AppModel``,
``from app.common.api.errors import HTTP404``) — this package intentionally re-exports nothing
so importing ``app.common`` stays side-effect free during early model setup.
"""
