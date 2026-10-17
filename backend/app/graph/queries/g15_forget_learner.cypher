// G15: forget_learner
// One-click privacy wipe: deletes all nodes and relationships in the learner graph.

MATCH (n)
DETACH DELETE n;
