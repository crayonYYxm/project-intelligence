#!/usr/bin/env node

// Canonical entry point for the Project Intelligence CLI (Node.js runtime).
// Phase 4: flipped to the TypeScript/Node core as the sole production path.
// The legacy Python CLI is no longer part of the repository or npm package.

import("../dist/cli.js").catch((err) => {
  console.error(`Unable to load Node CLI: ${err.message}`);
  process.exit(1);
});
