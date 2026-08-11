#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { registerDeckTools } from "./tools/decks.js";
import { registerModelTools } from "./tools/models.js";
import { registerNoteTools } from "./tools/notes.js";
import { registerStatsTools } from "./tools/stats.js";

const server = new McpServer({
  name: "anki-mcp-server",
  version: "1.1.0",
});

registerNoteTools(server);
registerDeckTools(server);
registerModelTools(server);
registerStatsTools(server);

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("anki-mcp-server running via stdio");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
