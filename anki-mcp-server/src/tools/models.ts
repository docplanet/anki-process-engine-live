import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { invoke } from "../services/ankiConnect.js";
import { GetModelFieldsInputSchema } from "../schemas/models.js";
import { READ_ONLY, registerAnkiTool, withTruncation } from "./format.js";

export function registerModelTools(server: McpServer): void {
  registerAnkiTool(
    server,
    "anki_list_models",
    {
      title: "List Anki Note Types",
      description: `List every note type (model) name in the collection, e.g. "Basic", "Cloze".

Returns: {"total": number, "count": number, "items": string[], "truncated"?: true}

Use when: discovering which note types are available before calling anki_get_model_fields or anki_add_note.`,
      annotations: READ_ONLY,
    },
    async () => {
      const models = await invoke<string[]>("modelNames");
      return withTruncation(models);
    }
  );

  registerAnkiTool(
    server,
    "anki_get_model_fields",
    {
      title: "Get Anki Note Type Fields",
      description: `List the field names for a given note type, in order.

Returns: {"fields": string[]}

Use when: you need the exact field names to pass to anki_add_note's "fields" object (e.g. Cloze uses "Text", Basic uses "Front"/"Back"). Field names are case-sensitive.`,
      schema: GetModelFieldsInputSchema,
      annotations: READ_ONLY,
    },
    async (params) => {
      const fields = await invoke<string[]>("modelFieldNames", { modelName: params.model_name });
      return { fields };
    }
  );
}
