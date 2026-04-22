#!/usr/bin/env node
/**
 * PostToolUse hook for tenets architecture monitoring.
 * Fires after Edit/Write tool calls to remind Claude about architecture rules.
 */

const LAYER_RULES = {
  domain: 'Domain layer: no external deps, entities have identity equality, VOs are immutable, aggregates enforce invariants.',
  application: 'Application layer: use cases orchestrate only — no business logic. Depend on ports, never adapters.',
  adapters: 'Adapter layer: implement port interfaces, handle external complexity, no domain logic.',
  infrastructure: 'Infrastructure layer: implement port interfaces, keep tech-specific models here.',
};

let input = '';
process.stdin.setEncoding('utf-8');
process.stdin.on('data', (chunk) => { input += chunk; });
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    const filePath = data.tool_input?.file_path || data.tool_input?.path || '';

    for (const [layer, reminder] of Object.entries(LAYER_RULES)) {
      if (filePath.includes(`/${layer}/`) || filePath.includes(`/${layer}s/`)) {
        process.stdout.write(`[tenets] Editing ${layer} layer. ${reminder}`);
        process.exit(0);
        return;
      }
    }
  } catch {
    // Silently ignore parse errors
  }
  process.exit(0);
});
