import { z } from "zod";

// Anki splits tags on whitespace, so a tag like "week 1" silently becomes two
// tags; reject spaces up front and steer toward :: hierarchy separators.
const TagSchema = z
  .string()
  .min(1)
  .regex(/^\S+$/, "Anki tags cannot contain spaces — use '::' separators instead (e.g. 'week::1')");

const NoteFieldsSchema = z
  .record(z.string())
  .refine((fields) => Object.keys(fields).length > 0, "fields must contain at least one field");

const NewNoteSchema = z.object({
  deck_name: z.string().min(1).describe("Target deck name, e.g. '<Course>'"),
  model_name: z.string().min(1).describe("Note type name, e.g. 'Basic' or 'Cloze'"),
  fields: NoteFieldsSchema.describe(
    "Field name -> HTML content, e.g. {\"Text\": \"The {{c1::hippocampus}} is critical for memory.\"}"
  ),
  tags: z
    .array(TagSchema)
    .default([])
    .describe("Tags to attach. No spaces within a tag — use '::' separators (e.g. 'week::1')"),
});

export const AddNoteInputSchema = NewNoteSchema.strict();
export type AddNoteInput = z.output<typeof AddNoteInputSchema>;

export const AddNotesInputSchema = z
  .object({
    notes: z
      .array(NewNoteSchema)
      .min(1)
      .max(500)
      .describe("Notes to create in one call (max 500)"),
  })
  .strict();
export type AddNotesInput = z.output<typeof AddNotesInputSchema>;

export const FindNotesInputSchema = z
  .object({
    query: z
      .string()
      .trim()
      .min(1)
      .describe("Anki search query, e.g. 'deck:<Course> tag:<tag>' or 'tag:fix-me'"),
  })
  .strict();
export type FindNotesInput = z.output<typeof FindNotesInputSchema>;

export const GetNotesInfoInputSchema = z
  .object({
    note_ids: z
      .array(z.number().int())
      .min(1)
      .max(500)
      .describe("Note IDs to fetch, typically from anki_find_notes"),
  })
  .strict();
export type GetNotesInfoInput = z.output<typeof GetNotesInfoInputSchema>;

export const UpdateNoteFieldsInputSchema = z
  .object({
    note_id: z.number().int().describe("Note ID to update, from anki_find_notes"),
    fields: NoteFieldsSchema.describe(
      "Field name -> new HTML content. Only the listed fields are changed. Field names must match the note's model exactly (case-sensitive)."
    ),
  })
  .strict();
export type UpdateNoteFieldsInput = z.output<typeof UpdateNoteFieldsInputSchema>;

export const DeleteNotesInputSchema = z
  .object({
    note_ids: z
      .array(z.number().int())
      .min(1)
      .max(500)
      .describe("Note IDs to permanently delete (max 500 per call)"),
  })
  .strict();
export type DeleteNotesInput = z.output<typeof DeleteNotesInputSchema>;

export const TagNotesInputSchema = z
  .object({
    note_ids: z.array(z.number().int()).min(1).max(500).describe("Note IDs to tag/untag"),
    tags: z
      .string()
      .trim()
      .min(1)
      .describe("Space-separated tags, e.g. 'fix-me week::3'"),
  })
  .strict();
export type TagNotesInput = z.output<typeof TagNotesInputSchema>;
