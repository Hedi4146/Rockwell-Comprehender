"""rockwell_comprehender — comprensión de proyectos Rockwell Studio 5000.

API pública v0.1:
    load_project(filepath) -> Project
    L5XParseError, UnsupportedFormatError (excepciones tipadas)

Shapes y demás exportados desde model:
    Project, Identity, Module, Task, Program,
    Routine, AOIDetail, UDTDetail, Parameter, Member, Tag,
    SearchHit, Observation
"""

from .loader import load_project
from .model import (
    AOIDetail,
    Identity,
    L5XParseError,
    Member,
    Module,
    Observation,
    Parameter,
    Program,
    Project,
    Routine,
    SearchHit,
    Tag,
    Task,
    UDTDetail,
    UnsupportedFormatError,
)

__version__ = "0.1.0"

__all__ = [
    "load_project",
    "L5XParseError",
    "UnsupportedFormatError",
    "Project",
    "Identity",
    "Module",
    "Task",
    "Program",
    "Routine",
    "AOIDetail",
    "UDTDetail",
    "Parameter",
    "Member",
    "Tag",
    "SearchHit",
    "Observation",
    "__version__",
]
