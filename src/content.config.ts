import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const insights = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/insights' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    date: z.string(),
    original: z.string().optional(),
  }),
});

const practices = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/practices' }),
  schema: z.object({
    title: z.string(),
    tagline: z.string(),
    order: z.number().default(99),
  }),
});

export const collections = { insights, practices };
