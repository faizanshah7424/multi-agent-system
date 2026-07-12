from enum import Enum
from pydantic import BaseModel


class NodeType(str, Enum):
    FILE = "file"
    CLASS = "class"
    METHOD = "method"
    FUNCTION = "function"


class Node(BaseModel):
    id: str
    type: NodeType
    name: str
