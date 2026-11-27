import { existsSync } from 'node:fs';
import { loadEnvFile } from 'node:process';
import { z } from 'zod';

// Local runs read a .env file; in CI the variables come from the workflow.
// A variable already set in the shell wins over the file, so a one-off
// `BASE_URL=... npm test` still works with a .env in place.
const envFile = new URL('../../.env', import.meta.url);
if (existsSync(envFile)) {
  loadEnvFile(envFile);
}

// Every variable the suite reads, documented in .env.example
const envSchema = z.object({
  BASE_URL: z.url({ protocol: /^https?$/ }),
  CI: z.stringbool().default(false),
});

const parsed = envSchema.safeParse(process.env);

// Fail fast: a missing variable stops the run before any test starts, with a
// message naming the variable, instead of the same confusing failure in every test
if (!parsed.success) {
  throw new Error(
    `Invalid environment configuration (see .env.example):\n${z.prettifyError(parsed.error)}`,
  );
}

export const env = parsed.data;
