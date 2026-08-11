import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SYNC_TIMEOUT_MS } from "../constants.js";
import { invoke } from "../services/ankiConnect.js";
import {
  FindCardsInputSchema,
  GetCardReviewsInputSchema,
  GetCardsInfoInputSchema,
} from "../schemas/stats.js";
import type { CardInfo, CardReview } from "../types.js";
import { IDEMPOTENT_WRITE, READ_ONLY, registerAnkiTool, withTruncation } from "./format.js";

// revlog intervals are positive = days, negative = seconds (learning steps);
// normalize both to days so consumers get one unit
function intervalToDays(ivl: number): number {
  return ivl >= 0 ? ivl : Math.round((-ivl / 86400) * 10000) / 10000;
}

export function registerStatsTools(server: McpServer): void {
  registerAnkiTool(
    server,
    "anki_find_cards",
    {
      title: "Find Anki Cards",
      description: `Search for cards (not notes) using Anki's search syntax and return matching card IDs.

Returns: {"total", "count", "items": number[], "truncated"?} — card IDs; feed into anki_get_cards_info or anki_get_card_reviews.

Use when: you need per-card data (lapses, ease, review history) rather than note field content — one note can have multiple cards. Tip: add "-is:new" to the query to exclude never-studied cards when hunting for failing ones.`,
      schema: FindCardsInputSchema,
      annotations: READ_ONLY,
    },
    async (params) => {
      const cardIds = await invoke<number[]>("findCards", { query: params.query });
      return withTruncation(cardIds);
    }
  );

  registerAnkiTool(
    server,
    "anki_get_cards_info",
    {
      title: "Get Anki Card Performance Info",
      description: `Fetch per-card scheduling and performance data: lapses, ease factor, interval, and deck/model.

Returns: {"total", "count", "items": [{"card_id", "note_id", "deck_name", "model_name", "lapses", "ease_factor", "interval_days", "reps", "queue", "card_type", "due"}], "missing_card_ids"?: number[], "truncated"?}

Field semantics:
- "lapses": times the card was failed after being learned — the primary "which cards keep failing" signal (sort_by="lapses_desc").
- "ease_factor": Anki's ease ×1000 (2500 = default 250%); lower = harder. 0 means the card has NEVER been reviewed — it is not a difficulty signal. sort_by="ease_asc" places these never-reviewed cards last.
- "due" is Anki's internal encoding and varies by queue: for new cards it's a queue position, for review cards a day number relative to collection creation, for learning cards a raw epoch timestamp. Do NOT compare due across cards in different queues; use "queue" (0=new, 1=learning, 2=review, -1=suspended, -2/-3=buried) to interpret it, or query anki_find_cards with "is:due"/"prop:due<=N" instead.
- Card IDs that no longer exist are reported in missing_card_ids rather than failing the call.`,
      schema: GetCardsInfoInputSchema,
      annotations: READ_ONLY,
    },
    async (params) => {
      const cards = await invoke<Partial<CardInfo>[]>("cardsInfo", { cards: params.card_ids });
      const items: {
        card_id: number;
        note_id: number;
        deck_name: string;
        model_name: string;
        lapses: number;
        ease_factor: number;
        interval_days: number;
        reps: number;
        queue: number;
        card_type: number;
        due: number;
      }[] = [];
      const missingIds: number[] = [];
      cards.forEach((card, index) => {
        // AnkiConnect returns {} for card IDs that don't exist
        if (card == null || card.cardId === undefined) {
          missingIds.push(params.card_ids[index]);
          return;
        }
        items.push({
          card_id: card.cardId,
          note_id: card.note ?? 0,
          deck_name: card.deckName ?? "",
          model_name: card.modelName ?? "",
          lapses: card.lapses ?? 0,
          ease_factor: card.factor ?? 0,
          interval_days: card.interval ?? 0,
          reps: card.reps ?? 0,
          queue: card.queue ?? 0,
          card_type: card.type ?? 0,
          due: card.due ?? 0,
        });
      });
      if (params.sort_by === "lapses_desc") {
        items.sort((a, b) => b.lapses - a.lapses);
      } else if (params.sort_by === "ease_asc") {
        // ease 0 = never reviewed, not "hardest" — sort those last
        items.sort((a, b) => (a.ease_factor || Infinity) - (b.ease_factor || Infinity));
      }
      return {
        ...withTruncation(items),
        ...(missingIds.length ? { missing_card_ids: missingIds } : {}),
      };
    }
  );

  registerAnkiTool(
    server,
    "anki_get_card_reviews",
    {
      title: "Get Anki Card Review History",
      description: `Fetch the most recent reviews for a set of cards: each time the card was shown and what button was pressed.

Returns: {"total", "count", "items": [{"card_id": number, "total_reviews": number, "reviews": [{"reviewed_at_ms", "ease" (1=Again,2=Hard,3=Good,4=Easy), "new_interval_days", "previous_interval_days", "ease_factor", "review_duration_ms", "review_type" (0=learn,1=review,2=relearn,3=cram)}]}], "truncated"?} — one item per requested card ID. total_reviews of 0 means no reviews on record (a new card, or an unknown ID). Sub-day learning-step intervals appear as fractional days (e.g. a 10-minute step is ~0.007).

Use when: diagnosing *why* a specific card keeps lapsing (e.g. repeated "Again" shortly after "Good" suggests ambiguous wording). For a quick failing-cards ranking across a whole deck, use anki_get_cards_info with sort_by="lapses_desc" instead — it's much cheaper.`,
      schema: GetCardReviewsInputSchema,
      annotations: READ_ONLY,
    },
    async (params) => {
      // getReviewsOfCards documents string card IDs, unlike other actions
      const reviews = await invoke<Record<string, CardReview[]>>("getReviewsOfCards", {
        cards: params.card_ids.map(String),
      });
      return withTruncation(
        params.card_ids.map((cardId) => {
          const entries = reviews[String(cardId)] ?? [];
          return {
            card_id: cardId,
            total_reviews: entries.length,
            reviews: entries.slice(-params.max_reviews_per_card).map((review) => ({
              reviewed_at_ms: review.id,
              ease: review.ease,
              new_interval_days: intervalToDays(review.ivl),
              previous_interval_days: intervalToDays(review.lastIvl),
              ease_factor: review.factor,
              review_duration_ms: review.time,
              review_type: review.type,
            })),
          };
        })
      );
    }
  );

  registerAnkiTool(
    server,
    "anki_get_review_counts",
    {
      title: "Get Anki Daily Review Counts",
      description: `Get the number of reviews performed per day, across the whole collection.

Returns: {"total", "count", "items": [{"date": "YYYY-MM-DD", "review_count": number}], "truncated"?} — review_count is total review events (a card reviewed 5 times counts 5, not unique cards), and days with zero reviews are OMITTED entirely, so gaps in the date sequence mean skipped days.

Use when: checking overall review volume/consistency trends, not per-card failure data (use anki_get_cards_info for that).`,
      annotations: READ_ONLY,
    },
    async () => {
      const rows = await invoke<[string, number][]>("getNumCardsReviewedByDay");
      return withTruncation(rows.map(([date, count]) => ({ date, review_count: count })));
    }
  );

  registerAnkiTool(
    server,
    "anki_sync",
    {
      title: "Sync Anki with AnkiWeb",
      description: `Run an AnkiWeb sync from the running Anki instance (same as clicking the sync button).

Returns: {"success": true} after the sync completes. This BLOCKS until the sync finishes — it can take a while for large collections (up to a 5-minute timeout).

Use when: you want changes made via this MCP server to propagate to AnkiWeb / other devices right away.`,
      annotations: IDEMPOTENT_WRITE,
    },
    async () => {
      await invoke<null>("sync", undefined, { timeoutMs: SYNC_TIMEOUT_MS });
      return { success: true };
    }
  );
}
