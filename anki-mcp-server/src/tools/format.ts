import type { McpServer, ToolCallback } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { CHARACTER_LIMIT } from "../constants.js";
import { handleAnkiError } from "../services/ankiConnect.js";

// Emitted (pretty-printed) size is what counts against CHARACTER_LIMIT — this
// is the single choke point every tool response flows through, so nothing can
// bypass the cap. Truncated-mid-JSON output is a last resort; list tools
// should shape their payload with withTruncation() first so output stays
// valid JSON.
function jsonResult(output: unknown): CallToolResult {
  const text = JSON.stringify(output, null, 2);
  if (text.length > CHARACTER_LIMIT) {
    // Never emit a half-object. Slicing pretty-printed JSON lands mid-token, so the caller
    // gets a parse error with nothing explaining it. A whole, valid envelope says what
    // happened; list tools should have shaped their payload with withTruncation() first.
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              error: "response_too_large",
              characters: text.length,
              limit: CHARACTER_LIMIT,
              message:
                "Response exceeded the character limit and was withheld rather than cut mid-JSON. Narrow the query or request fewer items.",
            },
            null,
            2
          ),
        },
      ],
    };
  }
  return { content: [{ type: "text", text }] };
}

function errorResult(message: string): CallToolResult {
  return { isError: true, content: [{ type: "text", text: message }] };
}

export interface TruncatedList<T> {
  total: number;
  count: number;
  items: T[];
  truncated?: true;
  truncation_message?: string;
}

export function withTruncation<T>(items: T[]): TruncatedList<T> {
  const measure = (obj: unknown): number => JSON.stringify(obj, null, 2).length;
  const full: TruncatedList<T> = { total: items.length, count: items.length, items };
  if (measure(full) <= CHARACTER_LIMIT) {
    return full;
  }

  const wrap = (kept: T[]): TruncatedList<T> => ({
    total: items.length,
    count: kept.length,
    items: kept,
    truncated: true,
    truncation_message: `Response truncated from ${items.length} to ${kept.length} items. Narrow your query to see the rest.`,
  });

  let kept = items;
  while (kept.length > 1 && measure(wrap(kept)) > CHARACTER_LIMIT) {
    kept = kept.slice(0, Math.ceil(kept.length / 2));
  }
  // a single item can still exceed the limit; jsonResult's hard cap catches it
  return wrap(kept);
}

export const READ_ONLY = {
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: true,
} as const;

export const CREATE = {
  readOnlyHint: false,
  destructiveHint: false,
  idempotentHint: false,
  openWorldHint: true,
} as const;

export const IDEMPOTENT_WRITE = {
  readOnlyHint: false,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: true,
} as const;

export const DESTRUCTIVE = {
  readOnlyHint: false,
  destructiveHint: true,
  idempotentHint: true,
  openWorldHint: true,
} as const;

type ToolAnnotations =
  | typeof READ_ONLY
  | typeof CREATE
  | typeof IDEMPOTENT_WRITE
  | typeof DESTRUCTIVE;

/**
 * Registers a tool with the shared Anki behavior applied once:
 * - passes the full ZodObject to the SDK (a raw .shape would lose .strict(),
 *   silently stripping unknown keys), and re-parses in the wrapper as a
 *   typed belt-and-braces check
 * - wraps the handler so any AnkiConnectError/ZodError becomes a clean
 *   isError result, and every payload flows through the size-capped
 *   jsonResult
 */
export function registerAnkiTool<Shape extends z.ZodRawShape>(
  server: McpServer,
  name: string,
  config: {
    title: string;
    description: string;
    schema?: z.ZodObject<Shape>;
    annotations: ToolAnnotations;
  },
  handler: (params: z.output<z.ZodObject<Shape>>) => Promise<unknown>
): void {
  const wrapped = async (params: unknown): Promise<CallToolResult> => {
    try {
      const parsed = config.schema
        ? config.schema.parse(params)
        : ({} as z.output<z.ZodObject<Shape>>);
      return jsonResult(await handler(parsed));
    } catch (error) {
      return errorResult(handleAnkiError(error));
    }
  };

  if (config.schema) {
    server.registerTool(
      name,
      {
        title: config.title,
        description: config.description,
        // the full ZodObject (not .shape) so the SDK validates with .strict()
        // intact and unknown keys are rejected, not silently stripped
        inputSchema: config.schema,
        annotations: config.annotations,
      },
      // safe: wrapped accepts unknown and re-parses with the strict schema
      wrapped as ToolCallback<z.ZodObject<Shape>>
    );
  } else {
    server.registerTool(
      name,
      {
        title: config.title,
        description: config.description,
        annotations: config.annotations,
      },
      wrapped as ToolCallback
    );
  }
}
