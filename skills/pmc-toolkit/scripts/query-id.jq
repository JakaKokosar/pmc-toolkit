# Returns the first object whose source_id == $id. source_id is the article's
# native JATS element id (e.g. "btpr70073-sec-0001", "btpr70073-fig-0001"), unique
# within the document, so the first recursive-descent match is the intended one.
# Pass ids taken from prior output (content-outline.jq or xref arrays), not guesses.
..
| objects
| select(.source_id? == $id)