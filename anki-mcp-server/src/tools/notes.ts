import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { AnkiConnectError, invoke } from "../services/ankiConnect.js";
import {
  AddNoteInputSchema,
  AddNotesInputSchema,
  DeleteNotesInputSchema,
  FindNotesInputSchema,
  GetNotesInfoInputSchema,
  TagNotesInputSchema,
  UpdateNoteFieldsInputSchema,
} from "../schemas/notes.js";
import type { NoteInfo } from "../types.js";
import { CREATE, DESTRUCTIVE, IDEMPOTENT_WRITE, READ_ONLY, registerAnkiTool, withTruncation } from "./format.js";

// AnkiConnect returns {} in place of notes that don't exist, so bulk lookups
// must be partitioned before use.
function isFoundNote(note: Partial<NoteInfo>): note is NoteInfo {
  return note != null && note.noteId !== undefined && note.fields !== undefined;
}

async function partitionByExistence(
  noteIds: number[]
): Promise<{ found: NoteInfo[]; foundIds: number[]; missingIds: number[] }> {
  const notes = await invoke<Partial<NoteInfo>[]>("notesInfo", { notes: noteIds });
  const found: NoteInfo[] = [];
  const foundIds: number[] = [];
  const missingIds: number[] = [];
  notes.forEach((note, index) => {
    if (isFoundNote(note)) {
      found.push(note);
      foundIds.push(noteIds[index]);
    } else {
      missingIds.push(noteIds[index]);
    }
  });
  return { found, foundIds, missingIds };
}

function toNewNoteParam(note: {
  deck_name: string;
  model_name: string;
  fields: Record<string, string>;
  tags: string[];
}): object {
  return {
    deckName: note.deck_name,
    modelName: note.model_name,
    fields: note.fields,
    tags: note.tags,
  };
}

export function registerNoteTools(server: McpServer): void {
  registerAnkiTool(
    server,
    "anki_add_note",
    {
      title: "Add Anki Note",
      description: `Create a single new note in Anki.

Returns: {"note_id": number} on success.

Use when: adding one flashcard. For more than a couple of notes, use anki_add_notes (bulk) instead — one call for the whole batch.
Errors if: the first field is empty, the deck/model name doesn't exist (check with anki_list_decks / anki_list_models), or the note is a duplicate.`,
      schema: AddNoteInputSchema,
      annotations: CREATE,
    },
    async (params) => {
      const noteId = await invoke<number>("addNote", { note: toNewNoteParam(params) });
      return { note_id: noteId };
    }
  );

  registerAnkiTool(
    server,
    "anki_add_notes",
    {
      title: "Add Anki Notes (Bulk)",
      description: `Create up to 500 notes in a single call.

Returns: {"created_count": number, "note_ids": (number | null)[], "failed_indices": number[]} — note_ids is index-aligned with the input; null means that note failed (most commonly a duplicate, or a bad deck/model/field name).

Use when: importing a batch of generated cards. Check failed_indices afterward and report or retry those notes individually via anki_add_note to see the specific error.`,
      schema: AddNotesInputSchema,
      annotations: CREATE,
    },
    async (params) => {
      const noteIds = await invoke<(number | null)[]>("addNotes", {
        notes: params.notes.map(toNewNoteParam),
      });
      const failedIndices = noteIds
        .map((id, index) => (id === null ? index : -1))
        .filter((index) => index !== -1);
      return {
        created_count: noteIds.length - failedIndices.length,
        note_ids: noteIds,
        failed_indices: failedIndices,
      };
    }
  );

  registerAnkiTool(
    server,
    "anki_find_notes",
    {
      title: "Find Anki Notes",
      description: `Search for notes using Anki's search syntax and return matching note IDs.

Returns: {"total": number, "count": number, "items": number[], "truncated"?: true} — note IDs; feed into anki_get_notes_info for field/tag details.

Use when: locating notes by deck, tag, or field content before reading or editing them.`,
      schema: FindNotesInputSchema,
      annotations: READ_ONLY,
    },
    async (params) => {
      const noteIds = await invoke<number[]>("findNotes", { query: params.query });
      return withTruncation(noteIds);
    }
  );

  registerAnkiTool(
    server,
    "anki_get_notes_info",
    {
      title: "Get Anki Note Details",
      description: `Fetch full field content, tags, and note type for a list of note IDs.

Returns: {"total", "count", "items": [{"note_id", "model_name", "tags": string[], "fields": {fieldName: value}, "card_ids": number[]}], "missing_note_ids"?: number[], "truncated"?} — IDs that no longer exist (deleted since they were found) are listed in missing_note_ids instead of failing the call.

Use when: reading a note's current content/tags before editing, or auditing flagged cards.`,
      schema: GetNotesInfoInputSchema,
      annotations: READ_ONLY,
    },
    async (params) => {
      const { found, missingIds } = await partitionByExistence(params.note_ids);
      const items = found.map((note) => ({
        note_id: note.noteId,
        model_name: note.modelName,
        tags: note.tags,
        fields: Object.fromEntries(
          Object.entries(note.fields).map(([name, field]) => [name, field.value])
        ),
        card_ids: note.cards ?? [],
      }));
      return {
        ...withTruncation(items),
        ...(missingIds.length ? { missing_note_ids: missingIds } : {}),
      };
    }
  );

  registerAnkiTool(
    server,
    "anki_update_note_fields",
    {
      title: "Update Anki Note Fields",
      description: `Overwrite one or more field values on an existing note. Tags and note type are unaffected. Field names are validated against the note's model before writing, so a typo'd field name errors instead of silently changing nothing.

Returns: {"success": true, "updated_fields": string[]} on success.

Use when: fixing a flagged card's wording, cloze markup, or content.
Caution: close the note in Anki's Browse/editor window first — AnkiConnect cannot reliably update a note that's open in the editor and the change may be silently lost.
Don't use when: you need to change the note type (requires migrating notes instead).`,
      schema: UpdateNoteFieldsInputSchema,
      annotations: DESTRUCTIVE,
    },
    async (params) => {
      const [note] = await invoke<Partial<NoteInfo>[]>("notesInfo", { notes: [params.note_id] });
      if (!isFoundNote(note)) {
        throw new AnkiConnectError(
          `Note ${params.note_id} was not found — it may have been deleted. Re-run anki_find_notes to get current IDs.`
        );
      }
      const validFields = Object.keys(note.fields);
      const unknownFields = Object.keys(params.fields).filter(
        (name) => !validFields.includes(name)
      );
      if (unknownFields.length) {
        throw new AnkiConnectError(
          `Field(s) ${unknownFields.join(", ")} do not exist on note type "${note.modelName}" ` +
            `(field names are case-sensitive). Valid fields: ${validFields.join(", ")}.`
        );
      }
      await invoke<null>("updateNoteFields", {
        note: { id: params.note_id, fields: params.fields },
      });
      return { success: true, updated_fields: Object.keys(params.fields) };
    }
  );

  registerAnkiTool(
    server,
    "anki_delete_notes",
    {
      title: "Delete Anki Notes",
      description: `Permanently delete one or more notes (and all their cards). This cannot be undone from here.

Returns: {"deleted_count": number, "not_found_note_ids"?: number[]} — existence is checked before deleting, so deleted_count reflects notes that actually existed; stale IDs are reported in not_found_note_ids rather than counted.

Use when: removing duplicates or notes created by mistake.
Caution: destructive and irreversible via this tool — confirm the IDs with anki_get_notes_info first.`,
      schema: DeleteNotesInputSchema,
      annotations: DESTRUCTIVE,
    },
    async (params) => {
      const { foundIds, missingIds } = await partitionByExistence(params.note_ids);
      if (foundIds.length) {
        await invoke<null>("deleteNotes", { notes: foundIds });
      }
      return {
        deleted_count: foundIds.length,
        ...(missingIds.length ? { not_found_note_ids: missingIds } : {}),
      };
    }
  );

  registerAnkiTool(
    server,
    "anki_add_tags",
    {
      title: "Add Tags to Anki Notes",
      description: `Add one or more tags to a set of notes without touching existing tags.

Returns: {"tagged_count": number, "not_found_note_ids"?: number[]} — stale/nonexistent IDs are reported instead of silently skipped.

Use when: flagging notes for later review (e.g. tag "fix-me"), or applying week/subject tags in bulk.`,
      schema: TagNotesInputSchema,
      annotations: IDEMPOTENT_WRITE,
    },
    async (params) => {
      const { foundIds, missingIds } = await partitionByExistence(params.note_ids);
      if (foundIds.length) {
        await invoke<null>("addTags", { notes: foundIds, tags: params.tags });
      }
      return {
        tagged_count: foundIds.length,
        ...(missingIds.length ? { not_found_note_ids: missingIds } : {}),
      };
    }
  );

  registerAnkiTool(
    server,
    "anki_remove_tags",
    {
      title: "Remove Tags from Anki Notes",
      description: `Remove one or more tags from a set of notes.

Returns: {"untagged_count": number, "not_found_note_ids"?: number[]} — stale/nonexistent IDs are reported instead of silently skipped.

Use when: clearing a "fix-me" flag once a card has been corrected.`,
      schema: TagNotesInputSchema,
      annotations: IDEMPOTENT_WRITE,
    },
    async (params) => {
      const { foundIds, missingIds } = await partitionByExistence(params.note_ids);
      if (foundIds.length) {
        await invoke<null>("removeTags", { notes: foundIds, tags: params.tags });
      }
      return {
        untagged_count: foundIds.length,
        ...(missingIds.length ? { not_found_note_ids: missingIds } : {}),
      };
    }
  );
}
