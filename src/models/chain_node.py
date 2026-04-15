import uuid
from dataclasses import dataclass, field


@dataclass
class ChainNode:
    """A single node in an attack-chain DAG.

    Attributes
    ----------
    node_id:
        Unique identifier for this node within the chain.
    module_key:
        The key used to look up the module in ModuleLoader.classes.
    position:
        (x, y) canvas position in pixels for the drag-drop UI.
    status:
        Execution state: "pending", "running", "success", "failed", "skipped".
    """
    module_key: str = ""
    node_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    position: tuple[float, float] = (0.0, 0.0)
    status: str = "pending"
