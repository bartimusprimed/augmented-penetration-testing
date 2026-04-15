"""Unit tests for Phase 0 and Phase 1 features.

Phase 0: module fact system (consumes/produces), Target.facts
Phase 1: Chain DAG model, topological sort, prerequisite validation
"""
import sys
import pathlib

# Ensure src/ is on the path so imports work without installing the package.
SRC_DIR = pathlib.Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

import pytest
from models.target import Target, create_target
from models.chain import Chain
from models.chain_node import ChainNode
from models.module_metadata import FactKey


# ---------------------------------------------------------------------------
# Phase 0 — facts system
# ---------------------------------------------------------------------------

class TestTargetFacts:
    def test_new_target_has_empty_facts(self):
        t = create_target("10.0.0.1")
        assert isinstance(t.facts, set)
        assert len(t.facts) == 0

    def test_set_fact_adds_key(self):
        t = create_target("10.0.0.2")
        t.set_fact("host_alive")
        assert t.has_fact("host_alive")

    def test_has_fact_false_for_missing_key(self):
        t = create_target("10.0.0.3")
        assert not t.has_fact("open_ports")

    def test_set_fact_syncs_is_alive(self):
        t = create_target("10.0.0.4")
        assert not t.is_alive
        t.set_fact(FactKey.HOST_ALIVE)
        assert t.is_alive

    def test_multiple_facts(self):
        t = create_target("10.0.0.5")
        t.set_fact("host_alive")
        t.set_fact("c2_session")
        assert t.has_fact("host_alive")
        assert t.has_fact("c2_session")
        assert not t.has_fact("credentials")

    def test_fact_key_constants_are_strings(self):
        assert isinstance(FactKey.HOST_ALIVE, str)
        assert isinstance(FactKey.C2_SESSION, str)
        assert isinstance(FactKey.OPEN_PORTS, str)


class TestAPTModuleFactDeclarations:
    def test_base_module_defaults_empty(self):
        # Import and instantiate a concrete module to check defaults
        from modules.reconnaissance.arpping import arpping
        mod = arpping()
        assert isinstance(mod.consumes, list)
        assert isinstance(mod.produces, list)

    def test_arpping_produces_host_alive(self):
        from modules.reconnaissance.arpping import arpping
        mod = arpping()
        assert "host_alive" in mod.produces
        assert mod.consumes == []

    def test_beacon_produces_c2_session(self):
        from modules.command_and_control.beacon import beacon
        mod = beacon()
        assert "c2_session" in mod.produces
        assert mod.consumes == []


# ---------------------------------------------------------------------------
# Phase 1 — Chain DAG model
# ---------------------------------------------------------------------------

class TestChainNode:
    def test_node_has_unique_id(self):
        n1 = ChainNode(module_key="arpping")
        n2 = ChainNode(module_key="arpping")
        assert n1.node_id != n2.node_id

    def test_node_default_status_pending(self):
        n = ChainNode(module_key="beacon")
        assert n.status == "pending"

    def test_node_default_position(self):
        n = ChainNode(module_key="beacon")
        assert n.position == (0.0, 0.0)


class TestChainDAG:
    def _make_chain(self) -> Chain:
        return Chain(name="test")

    def test_add_node(self):
        c = self._make_chain()
        node = c.add_node("arpping")
        assert node.node_id in c.nodes
        assert c.nodes[node.node_id].module_key == "arpping"

    def test_remove_node(self):
        c = self._make_chain()
        node = c.add_node("arpping")
        c.remove_node(node.node_id)
        assert node.node_id not in c.nodes

    def test_add_edge(self):
        c = self._make_chain()
        n1 = c.add_node("arpping")
        n2 = c.add_node("beacon")
        c.add_edge(n1.node_id, n2.node_id)
        assert (n1.node_id, n2.node_id) in c.edges

    def test_remove_edge(self):
        c = self._make_chain()
        n1 = c.add_node("arpping")
        n2 = c.add_node("beacon")
        c.add_edge(n1.node_id, n2.node_id)
        c.remove_edge(n1.node_id, n2.node_id)
        assert (n1.node_id, n2.node_id) not in c.edges

    def test_remove_node_cleans_edges(self):
        c = self._make_chain()
        n1 = c.add_node("arpping")
        n2 = c.add_node("beacon")
        c.add_edge(n1.node_id, n2.node_id)
        c.remove_node(n1.node_id)
        assert not any(s == n1.node_id or d == n1.node_id for s, d in c.edges)

    def test_topo_order_respects_edges(self):
        c = self._make_chain()
        n1 = c.add_node("arpping")
        n2 = c.add_node("beacon")
        c.add_edge(n1.node_id, n2.node_id)
        order = c._topo_order()
        assert order.index(n1.node_id) < order.index(n2.node_id)

    def test_topo_order_three_nodes_linear(self):
        c = self._make_chain()
        n1 = c.add_node("a")
        n2 = c.add_node("b")
        n3 = c.add_node("c")
        c.add_edge(n1.node_id, n2.node_id)
        c.add_edge(n2.node_id, n3.node_id)
        order = c._topo_order()
        assert order.index(n1.node_id) < order.index(n2.node_id) < order.index(n3.node_id)

    def test_topo_order_handles_cycle_gracefully(self):
        c = self._make_chain()
        n1 = c.add_node("a")
        n2 = c.add_node("b")
        c.add_edge(n1.node_id, n2.node_id)
        c.add_edge(n2.node_id, n1.node_id)
        # Should not raise; all nodes appear in the result
        order = c._topo_order()
        assert set(order) == {n1.node_id, n2.node_id}

    def test_module_keys_property_backward_compat(self):
        c = self._make_chain()
        c.add_node("arpping")
        c.add_node("beacon")
        keys = c.module_keys
        assert "arpping" in keys
        assert "beacon" in keys

    def test_clear_removes_all(self):
        c = self._make_chain()
        c.add_node("arpping")
        c.add_node("beacon")
        c.clear()
        assert c.nodes == {}
        assert c.edges == []

    def test_legacy_add_module(self):
        c = self._make_chain()
        c.add_module("arpping")
        assert any(n.module_key == "arpping" for n in c.nodes.values())

    def test_legacy_remove_module(self):
        c = self._make_chain()
        c.add_module("arpping")
        c.remove_module("arpping")
        assert not any(n.module_key == "arpping" for n in c.nodes.values())


class TestChainPrerequisiteValidation:
    """Validate that the DAG prerequisite checker produces correct warnings."""

    class _FakeModule:
        def __init__(self, name, consumes, produces):
            self.name = name
            self.consumes = consumes
            self.produces = produces

    class _FakeLoader:
        def __init__(self, classes):
            self.classes = classes

    def test_no_warnings_when_upstream_satisfies(self):
        arp = self._FakeModule("ARP Ping", [], ["host_alive"])
        bea = self._FakeModule("Beacon", ["host_alive"], ["c2_session"])
        loader = self._FakeLoader({"arpping": arp, "beacon": bea})

        c = Chain(name="valid")
        n1 = c.add_node("arpping")
        n2 = c.add_node("beacon")
        c.add_edge(n1.node_id, n2.node_id)

        warnings = c.validate_prerequisites(loader)
        assert warnings == []

    def test_warning_when_upstream_missing(self):
        bea = self._FakeModule("Beacon", ["host_alive"], ["c2_session"])
        loader = self._FakeLoader({"beacon": bea})

        c = Chain(name="broken")
        c.add_node("beacon")

        warnings = c.validate_prerequisites(loader)
        assert len(warnings) == 1
        assert "host_alive" in warnings[0]

    def test_no_warning_for_module_without_consumes(self):
        arp = self._FakeModule("ARP Ping", [], ["host_alive"])
        loader = self._FakeLoader({"arpping": arp})

        c = Chain(name="ok")
        c.add_node("arpping")

        warnings = c.validate_prerequisites(loader)
        assert warnings == []

    def test_warning_partial_satisfaction(self):
        m1 = self._FakeModule("M1", [], ["host_alive"])
        m2 = self._FakeModule("M2", ["host_alive", "credentials"], ["c2_session"])
        loader = self._FakeLoader({"m1": m1, "m2": m2})

        c = Chain(name="partial")
        n1 = c.add_node("m1")
        n2 = c.add_node("m2")
        c.add_edge(n1.node_id, n2.node_id)

        warnings = c.validate_prerequisites(loader)
        # "credentials" is not produced by any upstream node
        assert any("credentials" in w for w in warnings)
        # "host_alive" IS satisfied, so no warning for it
        assert not any("host_alive" in w for w in warnings)
