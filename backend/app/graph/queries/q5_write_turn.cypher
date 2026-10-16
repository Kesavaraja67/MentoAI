-- Q5: write_turn
-- Record one Turn node in the session graph and link it.
-- Also increments turn_count on the Session node.
--
-- Run in the SESSION graph (session_<id>).
-- Parameters: $session_id, $n, $problem_id, $skill_id, $op, $a, $b,
--             $answer, $given, $correct, $misconception_id, $hint_level,
--             $hint_style, $ts
--
-- Creates (:Turn) and two edges:
--   (:Session)-[:HAS_TURN]->(:Turn)
--   Previous Turn (if any) -[:NEXT]->(:Turn)

-- Create the Turn node
MATCH (sess:Session {id: $session_id})
CREATE (t:Turn {
    n:              $n,
    problem_id:     $problem_id,
    skill_id:       $skill_id,
    op:             $op,
    a:              $a,
    b:              $b,
    answer:         $answer,
    given:          $given,
    correct:        $correct,
    misconception_id: $misconception_id,
    hint_level:     $hint_level,
    hint_style:     $hint_style,
    ts:             $ts
})
CREATE (sess)-[:HAS_TURN]->(t)
SET sess.turn_count = sess.turn_count + 1

-- Link previous turn if one exists
WITH t, sess, $n AS n
OPTIONAL MATCH (sess)-[:HAS_TURN]->(prev:Turn {n: n - 1})
FOREACH (_ IN CASE WHEN prev IS NOT NULL THEN [1] ELSE [] END |
    CREATE (prev)-[:NEXT]->(t)
)

RETURN t.n AS turn_n
