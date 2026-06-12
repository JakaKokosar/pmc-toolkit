{
  references: "reference_ids",
  figures: "figure_ids",
  tables: "table_ids"
}[$xref] as $field
| if $field == null then
    error("xref must be references, figures, or tables")
  else
    [ .. | objects
      | select(.[$field]? | index($id))
      | {source_id, text, ($field): .[$field] }
    ]
  end
