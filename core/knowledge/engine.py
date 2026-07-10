from typing import Dict, Any

class InMemoryGraphEngine:
    """
    In-memory mock graph engine storing nodes and edges mapping.
    """
    def __init__(self):
        self.nodes: Dict[str, Any] = {}
        self.edges = []

    def add_node(self, node_id: str, data: Dict[str, Any]) -> None:
        self.nodes[node_id] = data
