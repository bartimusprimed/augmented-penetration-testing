import flet as ft
from typing import Callable, cast
from dataclasses import dataclass, field
from models.chain_node import ChainNode


@ft.observable
@dataclass
class Chain:
    """Attack-chain model as a directed acyclic graph (DAG).

    Nodes are keyed by node_id.  Edges are directed pairs
    (from_node_id, to_node_id) meaning "from must complete before to".

    The ``module_keys`` property is kept for backward compatibility with any
    code that iterates the chain as an ordered list; it returns a topological
    order of module keys (cycles are silently omitted from the tail).
    """
    name: str = "New Chain"
    nodes: dict = field(default_factory=dict)
    edges: list = field(default_factory=list)
    is_running: bool = False
    current_step: int = 0
    target_count: int = 0
    on_change: Callable[[], None] | None = field(default=None, repr=False, compare=False)

    # ------------------------------------------------------------------
    # Backward-compat property
    # ------------------------------------------------------------------

    @property
    def module_keys(self) -> list[str]:
        """Return module keys in topological order (best-effort)."""
        order = self._topo_order()
        return [self.nodes[nid].module_key for nid in order if nid in self.nodes]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def trigger_update(self):
        cast(ft.Observable, self).notify()
        if self.on_change is not None:
            self.on_change()

    def _topo_order(self) -> list[str]:
        """Return node_ids in topological order via Kahn's algorithm.

        If the graph has a cycle the remaining nodes are appended in
        arbitrary order so execution can still proceed.
        """
        from collections import deque

        in_degree: dict[str, int] = {nid: 0 for nid in self.nodes}
        successors: dict[str, list[str]] = {nid: [] for nid in self.nodes}
        for src, dst in self.edges:
            if src in in_degree and dst in in_degree:
                in_degree[dst] += 1
                successors[src].append(dst)

        queue: deque[str] = deque(nid for nid, deg in in_degree.items() if deg == 0)
        order: list[str] = []
        while queue:
            nid = queue.popleft()
            order.append(nid)
            for succ in successors.get(nid, []):
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    queue.append(succ)

        remaining = [nid for nid in self.nodes if nid not in order]
        return order + remaining

    def _provides_for_predecessors(self, node_id: str, module_loader) -> set[str]:
        """Collect all variables provided by transitive predecessors of node_id."""
        predecessors: set[str] = set()
        stack = [node_id]
        while stack:
            current = stack.pop()
            for src, dst in self.edges:
                if dst == current and src not in predecessors:
                    predecessors.add(src)
                    stack.append(src)
        variables: set[str] = set()
        for nid in predecessors:
            node = self.nodes.get(nid)
            if node:
                mod = module_loader.classes.get(node.module_key)
                if mod:
                    variables.update(mod.produces_variables)
        return variables

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def add_node(self, module_key: str, position: tuple[float, float] = (0.0, 0.0)) -> ChainNode:
        """Add a new node for the given module_key and return it."""
        node = ChainNode(module_key=module_key, position=position)
        self.nodes[node.node_id] = node
        self.trigger_update()
        return node

    def remove_node(self, node_id: str):
        """Remove a node and all edges that reference it."""
        self.nodes.pop(node_id, None)
        self.edges = [(s, d) for s, d in self.edges if s != node_id and d != node_id]
        self.trigger_update()

    def add_edge(self, from_node_id: str, to_node_id: str):
        """Add a directed edge (from_node_id → to_node_id)."""
        if from_node_id not in self.nodes or to_node_id not in self.nodes:
            return
        pair = (from_node_id, to_node_id)
        if pair not in self.edges:
            self.edges.append(pair)
            self.trigger_update()

    def remove_edge(self, from_node_id: str, to_node_id: str):
        pair = (from_node_id, to_node_id)
        if pair in self.edges:
            self.edges.remove(pair)
            self.trigger_update()

    def update_node_position(self, node_id: str, x: float, y: float):
        node = self.nodes.get(node_id)
        if node:
            node.position = (x, y)
            self.trigger_update()

    def validate_prerequisites(self, module_loader) -> list[str]:
        """Return warning strings for unmet variable prerequisites.

        A warning is raised when a node requires variables that no upstream
        node declares as produced.
        """
        warnings: list[str] = []
        for node_id, node in self.nodes.items():
            mod = module_loader.classes.get(node.module_key)
            if not mod or not mod.consumes_variables:
                continue
            upstream_variables = self._provides_for_predecessors(node_id, module_loader)
            for var_name in mod.consumes_variables:
                if var_name not in upstream_variables:
                    warnings.append(
                        f"'{mod.name}' requires variable '{var_name}' but no upstream "
                        f"module provides it."
                    )
        return warnings

    def clear(self):
        self.nodes = {}
        self.edges = []
        self.trigger_update()

    # ------------------------------------------------------------------
    # Legacy list-style helpers used by simple chain manipulation flows.
    # ------------------------------------------------------------------

    def add_module(self, key: str):
        """Append a module as a new isolated node (legacy list-style API)."""
        if key not in [n.module_key for n in self.nodes.values()]:
            self.add_node(key)

    def remove_module(self, key: str):
        """Remove the first node with matching module_key."""
        target_id = next(
            (nid for nid, n in self.nodes.items() if n.module_key == key), None
        )
        if target_id:
            self.remove_node(target_id)

    def move_up(self, key: str):
        """Shift a node earlier in topological order (legacy list-style API)."""
        order = self._topo_order()
        keys = [self.nodes[nid].module_key for nid in order]
        if key not in keys:
            return
        idx = keys.index(key)
        if idx > 0:
            self.edges = [
                (s, d) for s, d in self.edges
                if not (s == order[idx] or d == order[idx])
            ]
            self.trigger_update()

    def move_down(self, key: str):
        """Shift a node later in topological order (legacy list-style API)."""
        order = self._topo_order()
        keys = [self.nodes[nid].module_key for nid in order]
        if key not in keys:
            return
        idx = keys.index(key)
        if idx < len(order) - 1:
            self.edges = [
                (s, d) for s, d in self.edges
                if not (s == order[idx] or d == order[idx])
            ]
            self.trigger_update()

