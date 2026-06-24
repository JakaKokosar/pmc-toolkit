def drop_empty($o):
  $o | with_entries(select(.value | if type == "array" then length > 0 else . != null end));

def section:
  drop_empty({
    source_id: .source_id,
    section_id: .section_id,
    title: .title,
    sections: [.sections[]? | section]
  });

{
  title: .article_info.title,
  sections: [.content.sections[]? | section]
}
