"""
personas.py — Synthetic demo personas and graph memory seeder for MentoAI.

Provides 3 pre-built personas with multi-day FalkorDB learning history:
1. Mira (octopuses, dog Biscuit, buoyancy / displacement)
2. Arjun (cricket statistics, probability misconceptions, fairness)
3. Lakshmi (adult returning learner, baking, fractions / parts of whole)
"""
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException

from app.graph.client import get_graph
from app.graph.schema import ensure_indices_and_moves
from app.graph.embeddings import get_embedding

router = APIRouter(prefix="/api/personas", tags=["personas"])

PERSONAS = {
    "mira": {
        "id": "mira",
        "name": "Mira (Curious 7yo)",
        "summary": "Loves octopuses, drawing, and swimming with her dog Biscuit. Shaky on why things float.",
        "topics": ["buoyancy", "marine_biology", "water_displacement"],
        "register": "playful 7yo, uses simple physical analogies, concrete examples",
    },
    "arjun": {
        "id": "arjun",
        "name": "Arjun (High Schooler)",
        "summary": "Passionate about cricket statistics and sports analytics. Holds gambler's fallacy misconception.",
        "topics": ["probability", "cricket_analytics", "fairness"],
        "register": "inquisitive teenager, comfortable with algebraic symbols and sports data",
    },
    "lakshmi": {
        "id": "lakshmi",
        "name": "Lakshmi (Adult Learner)",
        "summary": "Passionate baker returning to math. Wants to master fractions and proportions without rushing.",
        "topics": ["fractions", "proportions", "baking_chemistry"],
        "register": "thoughtful adult, visual reasoning, appreciates gentle pacing",
    },
}


@router.get("")
def list_personas() -> List[Dict[str, Any]]:
    return list(PERSONAS.values())


@router.post("/{persona_id}/restore")
def restore_persona(persona_id: str) -> Dict[str, Any]:
    if persona_id not in PERSONAS:
        raise HTTPException(status_code=404, detail="Persona not found")

    p = PERSONAS[persona_id]
    graph_name = f"learner_{persona_id}"

    # Initialize graph schema
    ensure_indices_and_moves(graph_name)
    graph = get_graph(graph_name)

    # Clean existing data for this persona
    try:
        graph.delete()
    except Exception:
        pass

    ensure_indices_and_moves(graph_name)
    graph = get_graph(graph_name)

    # 1. Seed Learner
    graph.query(
        """
        CREATE (l:Learner {
            id: $lid,
            display_name: $name,
            language: 'en',
            register_text: $register,
            register_conf: 0.9,
            voice_pref: 'natural',
            created_at: timestamp()
        })
        """,
        {"lid": persona_id, "name": p["name"], "register": p["register"]},
    )

    # 2. Seed Persona-specific rich multi-day history
    if persona_id == "mira":
        _seed_mira_history(graph)
    elif persona_id == "arjun":
        _seed_arjun_history(graph)
    elif persona_id == "lakshmi":
        _seed_lakshmi_history(graph)

    return {
        "status": "restored",
        "persona_id": persona_id,
        "name": p["name"],
        "graph_name": graph_name,
        "message": f"Successfully restored 3 days of memory history for {p['name']}.",
    }


def _seed_mira_history(graph):
    # Mira: Octopuses, dog Biscuit, swimming, buoyancy, water displacement
    emb_oct = get_embedding("Octopus Biology: Cephalopods with 3 hearts and blue copper-based blood")
    emb_buoy = get_embedding("Buoyancy: The upward force exerted by a fluid that opposes the weight of an immersed object")
    emb_disp = get_embedding("Water Displacement: The volume of fluid moved out of the way when an object enters water")

    graph.query(
        """
        MATCH (l:Learner {id: 'mira'})
        CREATE (c_oct:Concept {
            key: 'octopus_biology',
            name: 'Octopus Biology',
            summary: 'Cephalopods with 3 hearts and blue blood',
            domain: 'biology',
            embedding: $emb_oct,
            created_at: timestamp()
        })
        CREATE (c_buoy:Concept {
            key: 'buoyancy',
            name: 'Buoyancy',
            summary: 'Upward force exerted by fluids on objects',
            domain: 'physics',
            embedding: $emb_buoy,
            created_at: timestamp()
        })
        CREATE (c_disp:Concept {
            key: 'water_displacement',
            name: 'Water Displacement',
            summary: 'Volume of water pushed aside by an object',
            domain: 'physics',
            embedding: $emb_disp,
            created_at: timestamp()
        })
        CREATE (c_disp)-[:PREREQUISITE_OF {why: 'Displacement causes the buoyant force', conf: 0.95}]->(c_buoy)
        CREATE (c_oct)-[:TOUCHES]->(c_buoy)

        CREATE (i_draw:Interest {name: 'Drawing', summary: 'Loves drawing sea creatures and dogs'})
        CREATE (i_swim:Interest {name: 'Swimming', summary: 'Loves swimming in the pool'})
        CREATE (l)-[:LOVES {strength: 0.95}]->(i_draw)
        CREATE (l)-[:LOVES {strength: 0.9}]->(i_swim)
        CREATE (i_swim)-[:TOUCHES]->(c_buoy)

        CREATE (e_biscuit:Entity {id: 'ent_biscuit', name: 'Biscuit', kind: 'pet', facts: ['Golden retriever', 'Loves swimming']})
        CREATE (l)-[:MENTIONED {times: 4, last_ts: timestamp()}]->(e_biscuit)

        CREATE (l)-[:KNOWS {depth: 0.85, confidence: 0.9, rationale: 'Explained 3 hearts clearly on Day 1'}]->(c_oct)
        CREATE (l)-[:KNOWS {depth: 0.35, confidence: 0.5, rationale: 'Understands swimming but confused why heavy boats float'}]->(c_buoy)

        CREATE (cur:Curiosity {id: 'cur_1', text: 'Why do octopuses have 3 hearts?', intensity: 0.9, status: 'explored'})
        CREATE (cur2:Curiosity {id: 'cur_2', text: 'Why does Biscuit float in the pool but a toy metal spoon sinks?', intensity: 0.95, status: 'open'})
        CREATE (l)-[:WONDERS]->(cur)
        CREATE (l)-[:WONDERS]->(cur2)

        CREATE (misc:Misconception {id: 'misc_1', statement: 'Heavy objects always sink regardless of shape', status: 'active'})
        CREATE (l)-[:HOLDS]->(misc)
        CREATE (misc)-[:ABOUT]->(c_buoy)

        CREATE (conv1:Conversation {id: 'conv_day1', title: 'Creatures of the Deep', started_at: timestamp() - 172800000, ended_at: timestamp() - 171800000, summary: 'Explored octopus hearts and swimming.'})
        CREATE (l)-[:HAD]->(conv1)
        CREATE (d1:Digest {id: 'dig_1', text: 'Mira lit up when learning about octopus anatomy. She connected their soft bodies to floating in water.', topics: ['Octopuses', 'Hearts'], strengths: ['Vivid imagination', 'Recall'], shaky_areas: ['Heavy vs light concepts'], offline_activities: ['Test floating plastic vs metal toys in bathtub'], ts: timestamp() - 171800000})
        CREATE (d1)-[:SUMMARISES]->(conv1)
        CREATE (l)-[:HAS_DIGEST]->(d1)
        """,
        {"emb_oct": emb_oct, "emb_buoy": emb_buoy, "emb_disp": emb_disp},
    )


def _seed_arjun_history(graph):
    emb_prob = get_embedding("Probability: Measure of the likelihood that an event will occur")
    emb_avg = get_embedding("Batting and Bowling Averages: Statistical mean calculations in cricket")

    graph.query(
        """
        MATCH (l:Learner {id: 'arjun'})
        CREATE (c_prob:Concept {key: 'independent_events', name: 'Independent Events', summary: 'Events where previous outcomes do not affect future probability', domain: 'math', embedding: $emb_prob, created_at: timestamp()})
        CREATE (c_avg:Concept {key: 'weighted_averages', name: 'Weighted Averages', summary: 'Means where some values contribute more than others', domain: 'math', embedding: $emb_avg, created_at: timestamp()})
        CREATE (c_prob)-[:TOUCHES]->(c_avg)

        CREATE (i_cricket:Interest {name: 'Cricket Analytics', summary: 'Obsessed with IPL statistics and bowler economy rates'})
        CREATE (l)-[:LOVES {strength: 0.95}]->(i_cricket)
        CREATE (i_cricket)-[:TOUCHES]->(c_avg)

        CREATE (misc:Misconception {id: 'misc_arjun', statement: 'Gamblers Fallacy: believing a bowler who bowled 3 dots is due to concede a boundary', status: 'active'})
        CREATE (l)-[:HOLDS]->(misc)
        CREATE (misc)-[:ABOUT]->(c_prob)

        CREATE (conv:Conversation {id: 'conv_arjun_1', title: 'Cricket Probabilities', started_at: timestamp() - 86400000, ended_at: timestamp() - 85000000, summary: 'Calculated bowling averages and debated streak momentum.'})
        CREATE (l)-[:HAD]->(conv)
        CREATE (d:Digest {id: 'dig_arjun', text: 'Arjun demonstrated strong algebraic mastery when calculating bowling averages. Guided him on independent coin tosses vs sports momentum.', topics: ['Cricket Stats', 'Probability'], strengths: ['Rapid mental arithmetic', 'Analytical curiosity'], shaky_areas: ['Independent probability vs hot-hand intuition'], offline_activities: ['Track coin toss streaks vs cricket delivery outcomes'], ts: timestamp() - 85000000})
        CREATE (d)-[:SUMMARISES]->(conv)
        CREATE (l)-[:HAS_DIGEST]->(d)
        """,
        {"emb_prob": emb_prob, "emb_avg": emb_avg},
    )


def _seed_lakshmi_history(graph):
    emb_frac = get_embedding("Fractions: Numerical quantities that represent parts of a whole or proportions")
    emb_ratio = get_embedding("Ratios and Proportions: Relationship between two or more quantities")

    graph.query(
        """
        MATCH (l:Learner {id: 'lakshmi'})
        CREATE (c_frac:Concept {key: 'fractions_parts_of_whole', name: 'Fractions as Parts of a Whole', summary: 'Understanding numerator and denominator as pieces of a shared unit', domain: 'math', embedding: $emb_frac, created_at: timestamp()})
        CREATE (c_ratio:Concept {key: 'baking_ratios', name: 'Baking Proportions', summary: 'Baker percentages and proportional ingredient scaling', domain: 'math', embedding: $emb_ratio, created_at: timestamp()})
        CREATE (c_frac)-[:PREREQUISITE_OF {why: 'Proportions require understanding unit fractions', conf: 0.9}]->(c_ratio)

        CREATE (i_bake:Interest {name: 'Sourdough Baking', summary: 'Passionate about sourdough bread and pastry chemistry'})
        CREATE (l)-[:LOVES {strength: 0.98}]->(i_bake)
        CREATE (i_bake)-[:TOUCHES]->(c_ratio)

        CREATE (l)-[:KNOWS {depth: 0.6, confidence: 0.75, rationale: 'Understands halving and doubling cake recipes with ease'}]->(c_ratio)

        CREATE (conv:Conversation {id: 'conv_lakshmi_1', title: 'Scaling Sourdough Recipes', started_at: timestamp() - 86400000, ended_at: timestamp() - 85400000, summary: 'Explored scaling 70% hydration dough using unit fractions.'})
        CREATE (l)-[:HAD]->(conv)
        CREATE (d:Digest {id: 'dig_lakshmi', text: 'Lakshmi made brilliant progress connecting hydration percentages in sourdough to fractions. She responded wonderfully to visual slice diagrams.', topics: ['Fractions', 'Scaling Ratios'], strengths: ['Sensory and culinary intuition', 'Patience'], shaky_areas: ['Fraction division abstractions'], offline_activities: ['Slice a round focaccia bread into 8 equal parts and group them'], ts: timestamp() - 85400000})
        CREATE (d)-[:SUMMARISES]->(conv)
        CREATE (l)-[:HAS_DIGEST]->(d)
        """,
        {"emb_frac": emb_frac, "emb_ratio": emb_ratio},
    )
