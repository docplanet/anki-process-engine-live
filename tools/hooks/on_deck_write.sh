#!/bin/sh
# PostToolUse hook, wired in .claude/settings.json: after every Write or Edit, if the file
# written was a deck.json, run tools/check_deck.py on it and feed the report back into the
# conversation. The writer never has to remember the check — the harness runs it.
#
# Exit 2 is the PostToolUse channel whose stderr reaches the model, so the report goes there
# even when the deck is clean — the deck-wide counts (facets, slide coverage) are the point,
# not only the failures. Media is skipped here because a deck is often written before its
# images are staged; the full run — media and --transcript both — is step 1 of the run-sheet
# in the anki-cards skill.
path=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' 2>/dev/null) || exit 0
[ "$(basename "$path")" = "deck.json" ] || exit 0
repo=$(cd "$(dirname "$0")/../.." && pwd)
{
  echo "deck-write hook > python3 tools/check_deck.py --no-media '$path'"
  echo "(structural check only; the media + --transcript run is still owed — see the run-sheet)"
  python3 "$repo/tools/check_deck.py" --no-media "$path"
} >&2
exit 2
