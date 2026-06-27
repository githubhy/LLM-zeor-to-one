Add a new reference to the specified survey: $ARGUMENTS

Workflow:
1. Read the References section of the target survey (use section index for line range).
2. Add the bibliography entry with `<!-- bib:N -->` marker.
3. Add `<!-- cite:N -->` markers at all in-text citation points.
4. Run `link-references.py` on the file.
5. Verify no orphaned citations.
