// Exit-code contract (AC-03), mirrored from the Python CLI.
//   0   success
//   1   runtime failure / unsuccessful gate
//   2   usage error / gate failure (fail_usage, JsonArgumentParser.error)
//   124 timeout (run_shell)
//   127 external command not found (run FileNotFoundError)
export const EXIT_SUCCESS = 0;
export const EXIT_RUNTIME = 1;
export const EXIT_USAGE = 2;
export const EXIT_TIMEOUT = 124;
export const EXIT_NOT_FOUND = 127;

/** A usage/gate error that maps to exit code 2 (matches Python fail_usage). */
export class UsageError extends Error {
  readonly exitCode = EXIT_USAGE;
  constructor(message: string) {
    super(message);
    this.name = "UsageError";
  }
}

/** A runtime error that maps to exit code 1. */
export class RuntimeError extends Error {
  readonly exitCode = EXIT_RUNTIME;
  constructor(message: string) {
    super(message);
    this.name = "RuntimeError";
  }
}

/** A requirement-state-machine error (maps to usage/exit 2 like Python RequirementError). */
export class RequirementError extends UsageError {
  constructor(message: string) {
    super(message);
    this.name = "RequirementError";
  }
}
