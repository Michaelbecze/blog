import { defineCollection, z } from 'astro:content';

const posts = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    date: z.date(),
    description: z.string().optional(),
    tags: z.array(z.string()).default([]),
    hasMermaid: z.boolean().optional(),
  }),
});

export const collections = { posts };
