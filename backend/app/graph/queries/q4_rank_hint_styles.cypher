-- Q4: rank_hint_styles
-- Return HintStyle nodes ranked by: score DESC, tries ASC, order ASC.
-- The Planner picks rank 1 for hint level 1, rank 2 for level 2,
-- rank 1 again for level 3 (spec section 7.4).
--
-- Run in the SESSION graph (session_<id>).
-- No parameters.
--
-- Returns: id, order, score, tries — ordered best first.

MATCH (h:HintStyle)
RETURN
    h.id    AS id,
    h.order AS order,
    h.score AS score,
    h.tries AS tries
ORDER BY h.score DESC, h.tries ASC, h.order ASC
