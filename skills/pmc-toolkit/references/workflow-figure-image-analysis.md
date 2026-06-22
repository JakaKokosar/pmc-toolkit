# Workflow: Figure And Image Analysis

Use this workflow for figure captions, figure-linked claims, panel interpretation, graphics files, and visual inspection requests.

## Caption And Text Evidence

1. Resolve to `<PMCID.N>`.
2. Fetch and parse XML.
3. List figures:
   `uvx pmc-toolkit parse <PMCID.N> | jq -c '.figures[] | {source_id, label, caption, graphics}'`
4. Retrieve the selected figure by ID:
   `uvx pmc-toolkit parse <PMCID.N> | jq -c --arg id "<FIGURE_ID>" -f <SKILL_DIR>/scripts/query-id.jq`
5. Retrieve paragraphs that cite the figure:
   `uvx pmc-toolkit parse <PMCID.N> | jq -c --arg xref figures --arg id "<FIGURE_ID>" -f <SKILL_DIR>/scripts/reverse-lookup-xref.jq`

Use caption plus linked paragraphs for text-grounded figure answers.

## Visual Inspection

Fetch image files only when the user asks about the visual itself, a panel, an image feature, or when caption/text evidence is insufficient.

1. Run `files <PMCID.N>` to inspect available image/media object keys.
2. Match figure `graphics[]` values to object-key suffixes when possible.
3. Fetch only likely image extensions:
   `uvx pmc-toolkit fetch <PMCID.N> --ext jpg,png,tif,tiff,gif`
4. Use the returned `local_path` for visual inspection with the available image-viewing tool.

## Output Rules

- Cite figure `label` and selected `<PMCID.N>`.
- Include caption evidence and linked paragraph evidence when used.
- Distinguish what is visible in the image from what the caption or article text states.
- If the graphics file cannot be matched or fetched, answer from caption/text evidence and report the visual gap.
