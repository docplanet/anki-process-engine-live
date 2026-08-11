import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { invoke } from "../services/ankiConnect.js";
import { CreateDeckInputSchema } from "../schemas/decks.js";
import { IDEMPOTENT_WRITE, READ_ONLY, registerAnkiTool, withTruncation } from "./format.js";

export function registerDeckTools(server: McpServer): void {
  registerAnkiTool(
    server,
    "anki_list_decks",
    {
      title: "List Anki Decks",
      description: `List every deck in the collection with its deck ID.

Returns: {"total": number, "count": number, "items": [{"name": string, "id": number}], "truncated"?: true}

Use when: discovering available deck names before creating a note or scoping a search query.`,
      annotations: READ_ONLY,
    },
    async () => {
      const decks = await invoke<Record<string, number>>("deckNamesAndIds");
      return withTruncation(Object.entries(decks).map(([name, id]) => ({ name, id })));
    }
  );

  registerAnkiTool(
    server,
    "anki_create_deck",
    {
      title: "Create Anki Deck",
      description: `Create a new deck (or subdeck, using "::" separators). Creating a deck that already exists is a no-op and returns its existing ID.

Returns: {"deck_id": number}

Use when: setting up a new deck/subdeck before adding notes to it.`,
      schema: CreateDeckInputSchema,
      annotations: IDEMPOTENT_WRITE,
    },
    async (params) => {
      const deckId = await invoke<number>("createDeck", { deck: params.deck_name });
      return { deck_id: deckId };
    }
  );
}
