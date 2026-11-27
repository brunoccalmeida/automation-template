import { test, expect } from '@playwright/test';

// The tracer bullet of the template's decision
// (https://github.com/brunoccalmeida/automation-template/blob/main/docs/adr/0003-stack-agnostic-core-defines-contracts.md):
// the system under test answers. Replace it
// with the project's first real API test once there is one.
test('the system under test answers', { tag: '@smoke' }, async ({ request }) => {
  await expect(await request.get('/')).toBeOK();
});
