// Project Intelligence — TypeScript core entry.
//
// Root of the Node.js/TypeScript implementation being migrated from the Python
// core (see docs/node-typescript-migration-requirement.md). During the migration
// (phases 2-3) the public bin/project-intel.mjs still dispatches to Python; this
// TS core is exercised through the independent dev entry and unit tests until
// phase 4.1 flips the bin.
export { VERSION } from "./version.js";
