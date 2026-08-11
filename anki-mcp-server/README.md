# anki-mcp-server

A local MCP server that wraps [AnkiConnect](https://foosoft.net/projects/anki-connect/) so an MCP-capable client can manage Anki notes/decks and read review-performance stats (lapses, ease, review history).

## Prerequisites

1. Anki desktop must be running.
2. Install the AnkiConnect add-on: Tools → Add-ons → Get Add-ons… → code `2055492159` → restart Anki.

## Setup

```bash
npm install
npm run build
```

## Configuration

Optional environment variables:

- `ANKI_CONNECT_URL` (default `http://127.0.0.1:8765`)
- `ANKI_CONNECT_API_KEY` (only needed if you've set an API key in AnkiConnect's config)
- `ANKI_CONNECT_TIMEOUT_MS` (default `30000`; `anki_sync` uses a fixed 5-minute timeout)

## Tools

| Tool | AnkiConnect action | Notes |
|---|---|---|
| `anki_add_note` | `addNote` | single note; rejects tags containing spaces |
| `anki_add_notes` | `addNotes` | bulk (max 500); reports per-note failures |
| `anki_find_notes` | `findNotes` | |
| `anki_get_notes_info` | `notesInfo` | stale IDs reported in `missing_note_ids`, never crash the batch |
| `anki_update_note_fields` | `notesInfo` + `updateNoteFields` | validates field names against the model first — typos error instead of silently no-oping |
| `anki_delete_notes` | `notesInfo` + `deleteNotes` | max 500; `deleted_count` reflects notes that actually existed |
| `anki_add_tags` / `anki_remove_tags` | `notesInfo` + `addTags`/`removeTags` | stale IDs reported, not silently skipped |
| `anki_list_decks` | `deckNamesAndIds` | |
| `anki_create_deck` | `createDeck` | |
| `anki_list_models` | `modelNames` | |
| `anki_get_model_fields` | `modelFieldNames` | |
| `anki_find_cards` | `findCards` | |
| `anki_get_cards_info` | `cardsInfo` | lapses/ease/interval per card; `sort_by: "lapses_desc"` surfaces most-failed cards; ease 0 (never reviewed) sorts last in `ease_asc`; exposes `queue`/`card_type` to interpret `due` |
| `anki_get_card_reviews` | `getReviewsOfCards` | most recent N reviews per card (default 50); learning-step intervals normalized to fractional days |
| `anki_get_review_counts` | `getNumCardsReviewedByDay` | review events per day (not unique cards); zero-review days omitted |
| `anki_sync` | `sync` | blocks until the sync completes |

All inputs are validated strictly (unknown/misspelled parameter names are rejected, not stripped), and every response is capped at 25,000 characters — list tools truncate at the item level with a `truncated` flag.

## Use it from an MCP client

`dist/` is not committed, so build it first — `npm install && npm run build`. Then register the
server with your client, using an **absolute** path:

```json
{
  "mcpServers": {
    "anki": {
      "command": "node",
      "args": ["/absolute/path/to/anki-mcp-server/dist/index.js"]
    }
  }
}
```

Claude Code can do the same in one line:

```bash
claude mcp add anki -- node "$(pwd)/dist/index.js"
```

Invoke it through `node` rather than pointing at the file directly. It carries a shebang and a
`bin` entry, but `tsc` does not set the execute bit — `npm run build` adds it via `postbuild`, and
`node <path>` works either way.

Anki must be running with AnkiConnect installed, and the `Custom Cloze` note type must exist —
see [`../anki/README.md`](../anki/README.md).

## Manual testing

```bash
npx @modelcontextprotocol/inspector node dist/index.js
```
