import { z } from "zod";

type FieldRefinement<TShape extends z.ZodRawShape> = {
  [TKey in keyof TShape]: {
    field: TKey;
    check: (val: z.infer<TShape[TKey]>) => boolean;
    message: string;
  };
}[keyof TShape];

export function refineField<TShape extends z.ZodRawShape>(
  schema: z.ZodObject<TShape>,
  refinements: FieldRefinement<TShape> | FieldRefinement<TShape>[],
) {
  const rules = Array.isArray(refinements) ? refinements : [refinements];
  return schema.superRefine((val, ctx) => {
    for (const { field, check, message } of rules) {
      const fieldVal = (val as Record<keyof TShape, unknown>)[field];
      if (!(check as (val: unknown) => boolean)(fieldVal)) {
        ctx.addIssue({ code: "custom", path: [field as string], message });
      }
    }
  });
}
