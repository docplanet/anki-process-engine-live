import { z } from "zod";

export const FindCardsInputSchema = z
  .object({
    query: z
      .string()
      .trim()
      .min(1)
      .describe("Anki search query, e.g. 'deck:<Course>' or 'deck:<Course> is:due'"),
  })
  .strict();
export type FindCardsInput = z.output<typeof FindCardsInputSchema>;

export const GetCardsInfoInputSchema = z
  .object({
    card_ids: z
      .array(z.number().int())
      .min(1)
      .max(500)
      .describe("Card IDs to fetch, typically from anki_find_cards"),
    sort_by: z
      .enum(["none", "lapses_desc", "ease_asc"])
      .default("none")
      .describe(
        "'lapses_desc' surfaces the most-failed cards first; 'ease_asc' surfaces the hardest " +
          "(lowest ease factor) reviewed cards first, with never-reviewed cards (ease 0) last; " +
          "'none' preserves input order"
      ),
  })
  .strict();
export type GetCardsInfoInput = z.output<typeof GetCardsInfoInputSchema>;

export const GetCardReviewsInputSchema = z
  .object({
    card_ids: z
      .array(z.number().int())
      .min(1)
      .max(200)
      .describe("Card IDs to fetch review history for"),
    max_reviews_per_card: z
      .number()
      .int()
      .min(1)
      .max(1000)
      .default(50)
      .describe("Most recent reviews to return per card (default 50)"),
  })
  .strict();
export type GetCardReviewsInput = z.output<typeof GetCardReviewsInputSchema>;
