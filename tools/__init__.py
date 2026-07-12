from typing import Dict, List, Type

from tools.base import BaseTool
from tools.file_reader import FileReaderTool
from tools.file_writer import FileWriterTool
from tools.dir_scanner import DirScannerTool
from tools.python_executor import PythonExecutorTool
from tools.web_search import WebSearchTool
from tools.memory_tool import MemoryRecallTool, MemoryStoreTool

# List of all tool classes available in the system
ALL_TOOL_CLASSES: List[Type[BaseTool]] = [
    FileReaderTool,
    FileWriterTool,
    DirScannerTool,
    PythonExecutorTool,
    WebSearchTool,
    MemoryRecallTool,
    MemoryStoreTool,
]


def get_tool_instances() -> List[BaseTool]:
    """
    Instantiate and return a list of all tools.
    """
    return [tool_cls() for tool_cls in ALL_TOOL_CLASSES]


def get_tool_map() -> Dict[str, BaseTool]:
    """
    Returns a dictionary mapping tool names to their instantiated classes.
    """
    return {tool.name: tool for tool in get_tool_instances()}
