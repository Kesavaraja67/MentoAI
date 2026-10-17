"""
test_graph_queries.py — Integration tests for MentoAI's 15 FalkorDB queries (G1–G15).
"""
import pytest
from app.graph.schema import init_learner_graph, clear_learner_graph
from app.graph.client import get_graph
from app.graph.queries import (
    get_learner_snapshot,
    semantic_recall,
    find_bridge_paths,
    find_weak_prerequisites,
    get_style_outcomes,
    get_open_loops_ranked,
    get_saga_state,
    record_evidence,
    upsert_concept,
    record_decision,
    get_decision_trace,
    get_mind_view,
    find_duplicate_concepts,
    get_hubs_and_clusters,
    forget_learner_graph,
)

TEST_LEARNER_ID = "test_mira"
GRAPH_NAME = f"learner_{TEST_LEARNER_ID}"


@pytest.fixture(autouse=True)
def setup_teardown_graph():
    # Setup
    clear_learner_graph(TEST_LEARNER_ID)
    init_learner_graph(TEST_LEARNER_ID, "Mira", "en", "curious young learner")
    yield
    # Teardown
    clear_learner_graph(TEST_LEARNER_ID)


class TestMentoAIGraphQueries:
    def test_g1_learner_snapshot(self):
        snapshot = get_learner_snapshot(GRAPH_NAME, TEST_LEARNER_ID)
        assert snapshot is not None
        assert snapshot.learner.display_name == "Mira"
        assert snapshot.learner.language == "en"
        assert "curious" in snapshot.learner.register_text

    def test_g9_and_g2_concept_upsert_and_recall(self):
        # G9: Upsert concept
        upsert_concept(GRAPH_NAME, "octopus_biology", "Octopus Biology", "Octopuses have 3 hearts and blue blood", "marine_biology")
        upsert_concept(GRAPH_NAME, "blood_circulation", "Blood Circulation", "Circulation of oxygenated blood in organisms", "biology")

        # Connect them
        graph = get_graph(GRAPH_NAME)
        graph.query("""
        MATCH (c1:Concept {key: 'octopus_biology'}), (c2:Concept {key: 'blood_circulation'})
        MERGE (c1)-[:PREREQUISITE_OF]->(c2)
        """)

        # G2: Semantic Recall
        results = semantic_recall(GRAPH_NAME, "octopus", limit=5)
        assert len(results) >= 1
        assert results[0]["key"] == "octopus_biology"
        assert len(results[0]["context_neighbors"]) >= 1

    def test_g3_bridge_paths(self):
        graph = get_graph(GRAPH_NAME)
        # Create an interest loved by Mira
        graph.query("""
        MATCH (l:Learner {id: $lid})
        CREATE (i:Interest {name: 'Drawing Sea Creatures', summary: 'Loves drawing octopuses'})
        CREATE (l)-[:LOVES {strength: 0.9}]->(i)
        CREATE (c1:Concept {key: 'octopus_tentacles', name: 'Octopus Tentacles', summary: 'Has suction cups'})
        CREATE (c2:Concept {key: 'suction_physics', name: 'Suction Physics', summary: 'Pressure differential creates hold'})
        CREATE (i)-[:TOUCHES]->(c1)
        CREATE (c1)-[:ANALOGOUS_TO]->(c2)
        """, {"lid": TEST_LEARNER_ID})

        bridges = find_bridge_paths(GRAPH_NAME, TEST_LEARNER_ID, "suction_physics")
        assert len(bridges) >= 1
        assert bridges[0]["hops"] <= 3

    def test_g4_weak_prerequisites(self):
        graph = get_graph(GRAPH_NAME)
        graph.query("""
        MATCH (l:Learner {id: $lid})
        CREATE (root:Concept {key: 'buoyancy', name: 'Buoyancy', summary: 'Why things float'})
        CREATE (target:Concept {key: 'boat_design', name: 'Boat Design', summary: 'Designing hollow boats'})
        CREATE (root)-[:PREREQUISITE_OF]->(target)
        CREATE (l)-[:KNOWS {confidence: 0.35, depth: 0.2}]->(root)
        """, {"lid": TEST_LEARNER_ID})

        weak = find_weak_prerequisites(GRAPH_NAME, TEST_LEARNER_ID, "boat_design")
        assert len(weak) >= 1
        assert weak[0]["prerequisite_key"] == "buoyancy"
        assert weak[0]["confidence"] < 0.6

    def test_g5_style_outcomes(self):
        graph = get_graph(GRAPH_NAME)
        graph.query("""
        MATCH (m:TeachingMove {name: 'analogy'})
        CREATE (d:Decision {id: 'dec_1', agent: 'companion', kind: 'pedagogical', rationale: 'Use octopus analogy', ts: '2026-10-16T12:00:00Z', confidence: 1.0})
        CREATE (e:Evidence {id: 'ev_1', kind: 'applied', quote: 'Like an octopus suction cup!', verdict: 'demonstrated', strength: 0.9, ts: '2026-10-16T12:01:00Z'})
        CREATE (d)-[:USED]->(m)
        CREATE (m)-[:LED_TO {outcome: 'success'}]->(e)
        """)

        outcomes = get_style_outcomes(GRAPH_NAME)
        assert len(outcomes) >= 1
        assert outcomes[0]["move_name"] == "analogy"
        assert outcomes[0]["successes"] >= 1

    def test_g6_open_loops(self):
        graph = get_graph(GRAPH_NAME)
        graph.query("""
        CREATE (op:OpenLoop {id: 'loop_1', text: 'Why is octopus blood blue?', kind: 'curiosity', priority_note: 'high', status: 'open'})
        """)

        loops = get_open_loops_ranked(GRAPH_NAME)
        assert len(loops) == 1
        assert loops[0]["loop_id"] == "loop_1"
        assert loops[0]["priority_note"] == "high"

    def test_g7_saga_state(self):
        graph = get_graph(GRAPH_NAME)
        graph.query("""
        MATCH (l:Learner {id: $lid})
        CREATE (t:Tale {id: 'tale_1', title: 'Captain Biscuit', premise: 'Adventures of a dog pirate', status: 'active'})
        CREATE (ch:Chapter {id: 'ch_1', idx: 1, text: 'Biscuit found a sunken submarine', cliffhanger: 'What is inside the airlock?', ts: '2026-10-16T10:00:00Z'})
        CREATE (l)-[:ON_JOURNEY]->(t)
        CREATE (t)-[:HAS_CHAPTER]->(ch)
        """, {"lid": TEST_LEARNER_ID})

        saga = get_saga_state(GRAPH_NAME)
        assert saga is not None
        assert saga["title"] == "Captain Biscuit"
        assert saga["cliffhanger"] == "What is inside the airlock?"

    def test_g8_write_evidence(self):
        graph = get_graph(GRAPH_NAME)
        # Create Turn and Concept first
        graph.query("""
        CREATE (:Turn {id: 'turn_101', idx: 1, role: 'person', text: 'Things float if they are less dense than water!', ts: '2026-10-16T10:05:00Z'})
        CREATE (:Concept {key: 'density', name: 'Density', summary: 'Mass per unit volume'})
        """)

        res = record_evidence(
            graph_name=GRAPH_NAME,
            turn_id="turn_101",
            concept_key="density",
            learner_id=TEST_LEARNER_ID,
            evidence_id="ev_202",
            kind="explained",
            quote="Things float if they are less dense than water!",
            verdict="demonstrated",
            strength=0.85,
            ts="2026-10-16T10:05:05Z",
            new_depth=0.7,
            new_confidence=0.8,
            rationale="Correctly stated density rule of buoyancy",
        )
        assert res["evidence_id"] == "ev_202"
        assert res["confidence"] == 0.8

    def test_g10_and_g11_decision_recording_and_trace(self):
        graph = get_graph(GRAPH_NAME)
        graph.query("""
        CREATE (:Turn {id: 'turn_201', idx: 2, role: 'person', text: 'Tell me about Biscuit', ts: '2026-10-16T10:10:00Z'})
        CREATE (c:Concept {key: 'buoyancy', name: 'Buoyancy', summary: 'Floating'})
        CREATE (e:Evidence {id: 'ev_301', quote: 'Biscuit likes the pool', verdict: 'demonstrated', strength: 0.9, ts: '2026-10-16T10:09:00Z'})
        """)

        dec_id = record_decision(
            graph_name=GRAPH_NAME,
            decision_id="dec_999",
            agent="strategist",
            kind="bridge",
            rationale="Bridge from Biscuit floating in pool to buoyancy",
            confidence=0.95,
            ts="2026-10-16T10:10:05Z",
            turn_id="turn_201",
        )
        assert dec_id == "dec_999"

        # Connect chose and because
        graph.query("""
        MATCH (d:Decision {id: 'dec_999'})
        MATCH (c:Concept {key: 'buoyancy'})
        MATCH (e:Evidence {id: 'ev_301'})
        CREATE (d)-[:CHOSE]->(c)
        CREATE (d)-[:BECAUSE {note: 'Learner mentioned Biscuit in pool'}]->(e)
        """)

        trace = get_decision_trace(GRAPH_NAME, "dec_999")
        assert trace is not None
        assert trace.decision_id == "dec_999"
        assert trace.chose["name"] == "Buoyancy"
        assert len(trace.because) == 1
        assert trace.because[0]["note"] == "Learner mentioned Biscuit in pool"

    def test_g12_mind_view(self):
        graph = get_graph(GRAPH_NAME)
        graph.query("""
        MATCH (l:Learner {id: $lid})
        CREATE (c1:Concept {key: 'octopuses', name: 'Octopuses', domain: 'biology'})
        CREATE (c2:Concept {key: 'hearts', name: 'Hearts', domain: 'anatomy'})
        CREATE (c1)-[:TOUCHES {why: 'Has 3 hearts'}]->(c2)
        CREATE (l)-[:KNOWS {depth: 0.8, confidence: 0.9}]->(c1)
        """, {"lid": TEST_LEARNER_ID})

        mind = get_mind_view(GRAPH_NAME, limit=10)
        assert len(mind.nodes) >= 2
        assert len(mind.edges) >= 1

    def test_g13_duplicate_concepts(self):
        upsert_concept(GRAPH_NAME, "water_density", "Water Density", "Density of liquid water")
        upsert_concept(GRAPH_NAME, "water_density_alt", "Water Density", "Alternate density")

        dups = find_duplicate_concepts(GRAPH_NAME)
        assert len(dups) >= 1

    def test_g14_hubs_and_clusters(self):
        graph = get_graph(GRAPH_NAME)
        graph.query("""
        CREATE (hub:Concept {key: 'ocean', name: 'Ocean', domain: 'nature'})
        CREATE (c1:Concept {key: 'fish', name: 'Fish', domain: 'nature'})
        CREATE (c2:Concept {key: 'coral', name: 'Coral', domain: 'nature'})
        CREATE (hub)-[:PART_OF]->(c1)
        CREATE (hub)-[:PART_OF]->(c2)
        """)

        hubs = get_hubs_and_clusters(GRAPH_NAME)
        assert len(hubs) >= 1
        assert hubs[0]["key"] == "ocean"
        assert hubs[0]["degree"] == 2

    def test_g15_forget_learner(self):
        assert forget_learner_graph(GRAPH_NAME) is True
        snapshot = get_learner_snapshot(GRAPH_NAME, TEST_LEARNER_ID)
        assert snapshot is None
