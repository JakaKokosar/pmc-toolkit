# Find body paragraphs that cite a given reference, figure, or table id, each
# tagged with its enclosing section so the citation is locatable even when the
# paragraph itself has no source_id (common — see the parsed schema in SKILL.md).
# Args: --arg xref references|figures|tables   --arg id <ID>
# Output: array of { section_id, section_title, text, <xref array> }.
{ references: "reference_ids", figures: "figure_ids", tables: "table_ids" }[$xref] as $field
| if $field == null then error("xref must be references, figures, or tables") else . end
| def walk($sid; $stitle):
    ( .paragraphs[]?
      | select(.[$field]? | index($id))
      | { section_id: $sid, section_title: $stitle, text, ($field): .[$field] } ),
    ( .sections[]? | walk(.source_id; .title) );
  [ .content | walk(null; null) ]
