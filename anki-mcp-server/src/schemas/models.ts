import { z } from "zod";

export const GetModelFieldsInputSchema = z
  .object({
    model_name: z.string().min(1).describe("Note type name, e.g. 'Basic' or 'Cloze'"),
  })
  .strict();
export type GetModelFieldsInput = z.output<typeof GetModelFieldsInputSchema>;
