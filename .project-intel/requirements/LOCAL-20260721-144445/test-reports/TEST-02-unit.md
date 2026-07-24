# LOCAL-20260721-144445 测试报告

- 测试类型：unit
- 阶段：verify
- 结果：passed
- 验收标准：AC-01,AC-02,AC-03,AC-04,AC-05,AC-06,AC-07,AC-08,AC-09,AC-10,AC-11,AC-12,AC-13,AC-14,AC-15
- 文件范围：.baseline/cli-snapshot.json, .baseline/fixtures/README.md, .baseline/fixtures/project-intel/.gitignore, .baseline/fixtures/project-intel/config.json, .baseline/fixtures/project-intel/graph/project-graph.json, .baseline/fixtures/project-intel/knowledge/backend.json, .baseline/fixtures/project-intel/knowledge/files.json, .baseline/fixtures/project-intel/knowledge/frontend.json, .baseline/fixtures/project-intel/manifest.json, .baseline/fixtures/project-intel/project-status.md, .baseline/fixtures/project-intel/standards/api.md, .baseline/fixtures/project-intel/standards/backend-api.md, .baseline/fixtures/project-intel/standards/backend-async.md, .baseline/fixtures/project-intel/standards/backend-config.md, .baseline/fixtures/project-intel/standards/backend-errors.md, .baseline/fixtures/project-intel/standards/backend-models.md, .baseline/fixtures/project-intel/standards/backend-remote-calls.md, .baseline/fixtures/project-intel/standards/backend-repository.md, .baseline/fixtures/project-intel/standards/backend-security.md, .baseline/fixtures/project-intel/standards/backend-services.md, .baseline/fixtures/project-intel/standards/backend-transactions.md, .baseline/fixtures/project-intel/standards/backend-utilities.md, .baseline/fixtures/project-intel/standards/backend.md, .baseline/fixtures/project-intel/standards/components.md, .baseline/fixtures/project-intel/standards/domain-flows.md, .baseline/fixtures/project-intel/standards/frontend.md, .baseline/fixtures/project-intel/standards/quality.md, .baseline/fixtures/project-intel/standards/reuse.md, .baseline/fixtures/project-intel/standards/router.md, .baseline/test-map.json, .github/workflows/validate.yml, .gitignore, .ua/.trash-1784630749/assemble-review.json, .ua/.trash-1784630749/assembled-graph.json, .ua/.trash-1784630749/batch-1-part-1.json, .ua/.trash-1784630749/batch-1-part-2.json, .ua/.trash-1784630749/batch-1-part-3.json, .ua/.trash-1784630749/batch-1-part-4.json, .ua/.trash-1784630749/batch-10.json, .ua/.trash-1784630749/batch-11.json, .ua/.trash-1784630749/batch-12.json, .ua/.trash-1784630749/batch-2.json, .ua/.trash-1784630749/batch-3-part-1.json, .ua/.trash-1784630749/batch-3-part-2.json, .ua/.trash-1784630749/batch-3-part-3.json, .ua/.trash-1784630749/batch-4.json, .ua/.trash-1784630749/batch-5.json, .ua/.trash-1784630749/batch-6.json, .ua/.trash-1784630749/batch-7.json, .ua/.trash-1784630749/batch-8.json, .ua/.trash-1784630749/batch-9.json, .ua/.trash-1784630749/batches.json, .ua/.trash-1784630749/fingerprint-input.json, .ua/.trash-1784630749/layers.json, .ua/.trash-1784630749/review.json, .ua/.trash-1784630749/tmp/arch-input.json, .ua/.trash-1784630749/tmp/build-tour-input.cjs, .ua/.trash-1784630749/tmp/gen_batch1.py, .ua/.trash-1784630749/tmp/ua-arch-analyze.cjs, .ua/.trash-1784630749/tmp/ua-arch-input.json, .ua/.trash-1784630749/tmp/ua-arch-results.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-1.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-10.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-11.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-12.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-2.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-3.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-4.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-5.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-6.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-7.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-8.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-9.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-1.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-10.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-11.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-12.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-2.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-3.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-4.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-5.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-6.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-7.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-8.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-9.json, .ua/.trash-1784630749/tmp/ua-import-map-input.json, .ua/.trash-1784630749/tmp/ua-import-map-output.json, .ua/.trash-1784630749/tmp/ua-inline-validate.cjs, .ua/.trash-1784630749/tmp/ua-scan-files.json, .ua/.trash-1784630749/tmp/ua-tour-analyze.cjs, .ua/.trash-1784630749/tmp/ua-tour-input.json, .ua/.trash-1784630749/tmp/ua-tour-results.json, .ua/.trash-1784630749/tour.json, .ua/.understandignore, .ua/config.json, .ua/fingerprints.json, .ua/intermediate/scan-result.json, .ua/knowledge-graph.json, .ua/meta.json, .understand-anything, .understand-anything/.trash-1784630749/assemble-review.json, .understand-anything/.trash-1784630749/assembled-graph.json, .understand-anything/.trash-1784630749/batch-1-part-1.json, .understand-anything/.trash-1784630749/batch-1-part-2.json, .understand-anything/.trash-1784630749/batch-1-part-3.json, .understand-anything/.trash-1784630749/batch-1-part-4.json, .understand-anything/.trash-1784630749/batch-10.json, .understand-anything/.trash-1784630749/batch-11.json, .understand-anything/.trash-1784630749/batch-12.json, .understand-anything/.trash-1784630749/batch-2.json, .understand-anything/.trash-1784630749/batch-3-part-1.json, .understand-anything/.trash-1784630749/batch-3-part-2.json, .understand-anything/.trash-1784630749/batch-3-part-3.json, .understand-anything/.trash-1784630749/batch-4.json, .understand-anything/.trash-1784630749/batch-5.json, .understand-anything/.trash-1784630749/batch-6.json, .understand-anything/.trash-1784630749/batch-7.json, .understand-anything/.trash-1784630749/batch-8.json, .understand-anything/.trash-1784630749/batch-9.json, .understand-anything/.trash-1784630749/batches.json, .understand-anything/.trash-1784630749/fingerprint-input.json, .understand-anything/.trash-1784630749/layers.json, .understand-anything/.trash-1784630749/review.json, .understand-anything/.trash-1784630749/tmp/arch-input.json, .understand-anything/.trash-1784630749/tmp/build-tour-input.cjs, .understand-anything/.trash-1784630749/tmp/gen_batch1.py, .understand-anything/.trash-1784630749/tmp/ua-arch-analyze.cjs, .understand-anything/.trash-1784630749/tmp/ua-arch-input.json, .understand-anything/.trash-1784630749/tmp/ua-arch-results.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-1.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-10.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-11.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-12.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-2.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-3.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-4.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-5.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-6.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-7.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-8.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-9.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-1.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-10.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-11.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-12.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-2.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-3.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-4.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-5.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-6.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-7.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-8.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-9.json, .understand-anything/.trash-1784630749/tmp/ua-import-map-input.json, .understand-anything/.trash-1784630749/tmp/ua-import-map-output.json, .understand-anything/.trash-1784630749/tmp/ua-inline-validate.cjs, .understand-anything/.trash-1784630749/tmp/ua-scan-files.json, .understand-anything/.trash-1784630749/tmp/ua-tour-analyze.cjs, .understand-anything/.trash-1784630749/tmp/ua-tour-input.json, .understand-anything/.trash-1784630749/tmp/ua-tour-results.json, .understand-anything/.trash-1784630749/tour.json, .understand-anything/.understandignore, .understand-anything/config.json, .understand-anything/diff-overlay.json, .understand-anything/fingerprints.json, .understand-anything/intermediate/scan-result.json, .understand-anything/knowledge-graph.json, .understand-anything/meta.json, .zcode/plans/plan-sess_33c80225-17a6-4398-b649-79cba6fba992.md, AGENTS.md, CHANGELOG.md, CLAUDE.md, README.md, bin/project-intel.mjs, package-lock.json, package.json, plugins/project-intelligence/.claude-plugin/plugin.json, plugins/project-intelligence/.codex-plugin/plugin.json, plugins/project-intelligence/scripts/.npmignore, plugins/project-intelligence/scripts/project-intel, plugins/project-intelligence/scripts/project_intel.py, plugins/project-intelligence/scripts/project_intel_lib/__init__.py, plugins/project-intelligence/scripts/project_intel_lib/application.py, plugins/project-intelligence/scripts/project_intel_lib/cli.py, plugins/project-intelligence/scripts/project_intel_lib/core.py, plugins/project-intelligence/scripts/project_intel_lib/design_documents.py, plugins/project-intelligence/scripts/project_intel_lib/graph.py, plugins/project-intelligence/scripts/project_intel_lib/lifecycle.py, plugins/project-intelligence/scripts/project_intel_lib/quality.py, plugins/project-intelligence/scripts/project_intel_lib/requirement_documents.py, plugins/project-intelligence/scripts/project_intel_lib/requirements.py, plugins/project-intelligence/scripts/project_intel_lib/scanner/__init__.py, plugins/project-intelligence/scripts/project_intel_lib/scanner/backend.py, plugins/project-intelligence/scripts/project_intel_lib/scanner/frontend.py, plugins/project-intelligence/scripts/project_intel_lib/standards.py, plugins/project-intelligence/scripts/project_intel_lib/testing.py, plugins/project-intelligence/skills/project-design/SKILL.md, plugins/project-intelligence/skills/project-design/scripts/validate_design_doc.mjs, plugins/project-intelligence/skills/project-design/scripts/validate_design_doc.py, plugins/project-intelligence/tests/design_fixtures.py, plugins/project-intelligence/tests/test_document_truth_validation.py, plugins/project-intelligence/tests/test_project_design.py, plugins/project-intelligence/tests/test_project_intel.py, plugins/project-intelligence/tests/test_project_test.py, plugins/project-intelligence/tests/test_requirement_hardening.py, plugins/project-intelligence/tests/test_requirement_layout_v2.py, plugins/project-intelligence/tests/test_requirement_workflow.py, plugins/project-intelligence/tests/test_testing_security.py, scripts/bench.mjs, scripts/build-fixtures.mjs, scripts/check-dual-compat.mjs, scripts/check-package.mjs, scripts/check-release.mjs, scripts/gen-version.mjs, scripts/rollback-read.mjs, scripts/run-tests.mjs, scripts/run-unit-tests.mjs, scripts/scan-python-runtime-refs.mjs, scripts/smoke-pack.mjs, scripts/snapshot-cli.mjs, scripts/validate-test-map.mjs, scripts/validate_bundle.py, src/__tests__/backend.test.ts, src/__tests__/cli-contract.test.ts, src/__tests__/dispatcher.test.ts, src/__tests__/dual-impl.test.ts, src/__tests__/frontend-files-quality.test.ts, src/__tests__/graph-setup.test.ts, src/__tests__/helpers.ts, src/__tests__/install-hooks.test.ts, src/__tests__/json-envelope.test.ts, src/__tests__/lock-contender.ts, src/__tests__/lock.test.ts, src/__tests__/paths.test.ts, src/__tests__/process-io.test.ts, src/__tests__/project-facts.test.ts, src/__tests__/requirement-command.test.ts, src/__tests__/review-finish-graph.test.ts, src/__tests__/scope.test.ts, src/__tests__/smoke.test.ts, src/__tests__/state-machine.test.ts, src/__tests__/test-evidence.test.ts, src/app/dispatcher.ts, src/app/project-state.ts, src/cli.ts, src/cli/command-flags.ts, src/cli/json-envelope.ts, src/cli/parser.ts, src/commands/adapter-blocks.ts, src/commands/adapters.ts, src/commands/agent-install.ts, src/commands/agent-rules.ts, src/commands/check.ts, src/commands/doctor.ts, src/commands/finish.ts, src/commands/graph-tools.ts, src/commands/hooks.ts, src/commands/init.ts, src/commands/install.ts, src/commands/maintain.ts, src/commands/orchestration.ts, src/commands/query.ts, src/commands/requirement.ts, src/commands/review.ts, src/commands/test.ts, src/errors.ts, src/fs/atomic-write.ts, src/fs/lock.ts, src/fs/paths.ts, src/graph/actions.ts, src/graph/setup.ts, src/graph/sources.ts, src/index.ts, src/io/markdown.ts, src/io/output.ts, src/io/yaml.ts, src/process/exec-shell.ts, src/process/spawn.ts, src/requirements/documents.ts, src/requirements/layout.ts, src/requirements/scope.ts, src/requirements/state-machine.ts, src/rules/hard.ts, src/scanner/backend.ts, src/scanner/core.ts, src/scanner/files.ts, src/scanner/frontend.ts, src/scanner/quality.ts, src/standards/docs.ts, src/standards/domains.ts, src/standards/infer.ts, src/testing/dual-impl.ts, src/testing/render.ts, src/testing/sanitize.ts, src/version.ts, tsconfig.json

## 执行结果

### npm test

- exitCode: 0
- executedCount: 249

```text
Skill behavior scenario contracts verified: 27 scenarios, 17 skills
▶ maskCommentsAndStrings
  ✔ masks line and block comments and string contents (0.471041ms)
✔ maskCommentsAndStrings (1.160958ms)
▶ scanBackendFile
  ✔ extracts a Spring controller endpoint and methods (.java) (2.588792ms)
  ✔ extracts Python def/class and Flask routes (.py) (1.858875ms)
  ✔ classifies a service by name and extracts transaction signals (0.190917ms)
  ✔ extracts config keys from yaml (0.644ms)
  ✔ classifies repository files and extracts SQL ops from xml mapper (0.339375ms)
  ✔ extracts permission signals (0.13175ms)
  ✔ extracts error code signals (0.09225ms)
  ✔ requires bound framework imports and keeps Django class views (0.157417ms)
  ✔ labels malformed Python without accepting route facts (0.084042ms)
  ✔ applies configured backend entrypoint rules (0.146542ms)
✔ scanBackendFile (6.482292ms)
▶ BACKEND_SUFFIXES
  ✔ includes java, kt, py, go, ts, js (0.044833ms)
✔ BACKEND_SUFFIXES (0.079166ms)
▶ cli snapshot contract (AC-02)
  ✔ loads a well-formed snapshot (0.528792ms)
  ✔ captured every top-level command's help (0.686916ms)
  ✔ pins the JSON envelope shape on every probe (0.29975ms)
  ✔ the version command exits 0 and prints a semver (0.239ms)
  ✔ usage errors exit non-zero with a non-ok envelope (0.131625ms)
✔ cli snapshot contract (AC-02) (2.583167ms)
▶ live Node CLI contract (AC-02/AC-10)
  ✔ dist/cli.js exists and is runnable (0.46975ms)
  ✔ version command exits 0 and prints a semver (118.126958ms)
  ✔ --version flag exits 0 and prints a semver (119.749333ms)
  ✔ every baseline command's --help is byte-for-byte compatible (1525.634666ms)
  ✔ top-level --help is byte-for-byte compatible (67.599625ms)
  ✔ top-level --help output contains all baseline commands (74.1795ms)
  ✔ subcommand --help output contains usage line and key flags (316.760875ms)
  ✔ unknown command exits 2 (108.676916ms)
  ✔ unknown flag exits 2 (93.658167ms)
  ✔ version --json produces a valid envelope with version field (71.664292ms)
  ✔ doctor --json produces a valid envelope with runtime=node (76.287792ms)
  ✔ usage error --json produces ok=false envelope (74.301167ms)
✔ live Node CLI contract (AC-02/AC-10) (2649.080375ms)
0.6.1-test
{
  "ok": true,
  "command": "version",
  "status": "ok",
  "exitCode": 0,
  "error": null,
  "result": {
    "version": "0.6.1-test"
  },
  "output": ""
}
{
  "echoed": [
    "hi"
  ]
}
{
  "ok": true,
  "command": "echo",
  "status": "ok",
  "exitCode": 0,
  "error": null,
  "result": {
    "echoed": [
      "hi"
    ]
  },
  "output": ""
}
usage: project-intel [-h] [--project PROJECT] [--version]
                     {boom,echo,fail} ...

项目智能 CLI

positional arguments:
  {boom,echo,fail}
    boom             runtime error
    echo             echo a message
    fail             always fails

options:
  -h, --help            show this help message and exit
  --project PROJECT     项目根目录，默认为当前目录。
  --version             打印版本号
无法识别的命令：nope
{
  "ok": false,
  "command": "nope",
  "status": "failed",
  "exitCode": 2,
  "error": {
    "code": "USAGE_ERROR",
    "message": "无法识别的命令：nope"
  },
  "result": {
    "error": "无法识别的命令：nope"
  },
  "output": ""
}
boom
kaboom
{
  "ok": false,
  "command": "unknown",
  "status": "failed",
  "exitCode": 2,
  "error": {
    "code": "USAGE_ERROR",
    "message": "缺少子命令"
  },
  "result": {
    "error": "缺少子命令"
  },
  "output": ""
}
usage: project-intel echo [-h] [--msg MSG]

options:
  -h, --help            show this help message and exit
  --msg MSG              参数值
{
  "ok": true,
  "command": "echo",
  "status": "ok",
  "exitCode": 0,
  "error": null,
  "result": {
    "help": true
  },
  "output": ""
}
无法识别的参数：--definitely-invalid
{
  "ok": false,
  "command": "echo",
  "status": "failed",
  "exitCode": 2,
  "error": {
    "code": "USAGE_ERROR",
    "message": "无法识别的参数：--definitely-invalid"
  },
  "result": {
    "error": "无法识别的参数：--definitely-invalid"
  },
  "output": ""
}
{
  "echoed": [
    "--msg",
    "--definitely-invalid"
  ]
}
无法识别的参数：--nope
▶ dispatch
  ✔ prints --version alone (1.798625ms)
  ✔ prints --version envelope in json mode (0.437209ms)
  ✔ runs a registered command (text mode) (0.282791ms)
  ✔ runs a registered command (json mode) with envelope (0.09575ms)
  ✔ rejects unknown command with exit 2 (text) (0.343875ms)
  ✔ rejects unknown command with exit 2 (json envelope) (1.94975ms)
  ✔ surfaces usage errors as exit 2 (0.126375ms)
  ✔ surfaces runtime errors as exit 1 (1.156584ms)
  ✔ rejects missing subcommand (json exit 2) (0.092833ms)
  ✔ subcommand --help is intercepted and exits 0 (text) (0.269083ms)
  ✔ subcommand -h is intercepted and exits 0 (json) (0.226791ms)
  ✔ rejects unknown long flag with exit 2 (text) (0.129042ms)
  ✔ rejects unknown long flag with exit 2 (json envelope) (0.117292ms)
  ✔ accepts known value flag and its value (not mistaken for a flag) (0.086084ms)
  ✔ rejects unknown flag even after a valid value flag (0.112875ms)
✔ dispatch (10.046666ms)
▶ normalizeForCompare
  ✔ masks ISO-8601 timestamps (1.350917ms)
  ✔ masks 40-char git hashes (0.0755ms)
  ✔ masks epoch-second/milli integers (0.053125ms)
  ✔ masks absolute repo roots (POSIX) (0.05175ms)
  ✔ normalizes Windows backslashes and masks sample root (0.058042ms)
  ✔ collapses mtime integers regardless of value (0.066208ms)
  ✔ applies longest-root-first masking so nested roots win (0.058542ms)
✔ normalizeForCompare (2.802542ms)
▶ compareJsonOutputs
  ✔ returns null for equal normalized values (0.1315ms)
  ✔ reports the first differing path (0.0525ms)
  ✔ reports missing keys with direction (0.108917ms)
  ✔ reports array length mismatches (0.0535ms)
✔ compareJsonOutputs (0.471959ms)
▶ frontend scanner
  ✔ extracts vue component props/emits (2.664333ms)
  ✔ extracts react props from interface (1.142417ms)
  ✔ extracts hooks by use* filename (0.843542ms)
  ✔ extracts routes and redundancy candidates (1.393625ms)
  ✔ extractVueProps from defineProps object form (0.174542ms)
  ✔ extractEmits filters to valid names (0.058125ms)
  ✔ extractApiEndpoints from request/fetch calls (0.176125ms)
✔ frontend scanner (7.338416ms)
▶ files scanner
  ✔ discoverFiles walks and categorizes (2.142ms)
  ✔ discoverFiles excludes node_modules/.git (0.3775ms)
  ✔ uses stable code-point ordering across operating systems (0.266791ms)
  ✔ categorize and simpleMatch basics (0.134458ms)
✔ files scanner (3.034459ms)
▶ incremental scan cache
  ✔ reuses unchanged frontend facts without reading the file again (0.210333ms)
  ✔ uses nanosecond-compatible file signatures and invalidates changed entries (0.277625ms)
✔ incremental scan cache (0.534167ms)
▶ quality scanner
  ✔ packageFrameworks detects Vue+TypeScript from deps (0.083ms)
  ✔ detectPackage reads package.json scripts and frameworks (3.37075ms)
  ✔ packageManager detects npm/pnpm/yarn by lockfile (0.50675ms)
  ✔ detectQualityCommands: Python project STILL recognizes pytest/ruff/mypy (P1.3) (0.605625ms)
  ✔ detectQualityCommands: JS project infers eslint/tsc from config presence (0.492875ms)
✔ quality scanner (5.180375ms)
FixtureGraph 已安装，开始运行分析："/opt/homebrew/Cellar/node/26.3.0/bin/node" -e "process.stdout.write('graph-ok')"
FixtureGraph 开始执行，超时上限 900 秒。
GitNexus：仓库内 runner 需要显式使用 --allow-repo-runner。
▶ graph command authorization
  ✔ preserves and detects Windows absolute paths on POSIX (1.196333ms)
  ✔ allows repository-contained absolute paths and rejects outside paths (0.155042ms)
  ✔ requires explicit permission for repo runners and environment commands (0.280708ms)
✔ graph command authorization (2.276041ms)
▶ graph setup execution
  ✔ executes an authorized installed analyzer and captures evidence (102.596417ms)
  ✔ records a skipped result instead of executing an unauthorized runner (0.546167ms)
✔ graph setup execution (103.30775ms)
▶ adapter block management
  ✔ rejects paths outside the allowed set (1.2585ms)
  ✔ replaceSingleManagedBlock creates then updates (0.33675ms)
  ✔ upsert then remove a managed block (1.616209ms)
✔ adapter block management (4.946292ms)
▶ adapters command family
  ✔ apply writes codex + claude blocks; status reports current (2.193459ms)
  ✔ preview is dry-run (no files written) (0.653208ms)
  ✔ remove clears blocks (0.581458ms)
  ✔ status --check returns non-zero when not current (0.310584ms)
  ✔ adapterTargets both returns 3 targets (codex, claude, claude-nested) (0.907666ms)
✔ adapters command family (4.985041ms)
▶ top-level install command
  ✔ creates .claude/ and applies adapters; --hooks writes templates (1.925459ms)
✔ top-level install command (2.021833ms)
▶ agent install command
  ✔ agentInstallCommands builds codex+claude for all (0.107458ms)
  ✔ --dry-run classifies present when cli exists, missing otherwise (0.318291ms)
  ✔ rejects invalid target (0.09925ms)
✔ agent install command (0.577958ms)
▶ git hooks (AC-07: no python3)
  ✔ hook body calls project-intel (Node CLI), never python3 (0.082833ms)
  ✔ writeHookTemplates writes 3 hooks + README under .project-intel/hooks (0.482ms)
✔ git hooks (AC-07: no python3) (0.595625ms)
▶ sanitizeErrorText
  ✔ redacts authorization bearer tokens (1.198583ms)
  ✔ redacts cookies (0.0955ms)
  ✔ redacts password/secret/token/api_key (0.05375ms)
  ✔ redacts aws credentials (0.043875ms)
  ✔ redacts URL userinfo (0.035667ms)
  ✔ leaves benign text intact (1.287708ms)
✔ sanitizeErrorText (3.807833ms)
▶ extractGlobalJson
  ✔ strips --json and reports mode (1.335333ms)
  ✔ preserves argv when --json absent (0.127708ms)
✔ extractGlobalJson (1.624125ms)
▶ jsonEnvelope
  ✔ shapes a success envelope (0.160625ms)
  ✔ classifies exit 2 as USAGE_ERROR with sanitized in-place error (0.089375ms)
  ✔ classifies non-2 failure as COMMAND_FAILED with default message (0.050708ms)
  ✔ trims the output field (0.033709ms)
✔ jsonEnvelope (0.528459ms)
▶ parseGlobal / splitArgv
  ✔ parses --project value (0.857042ms)
  ✔ parses --project= form (0.097583ms)
  ✔ parses --json (0.174042ms)
  ✔ rejects unknown long option before subcommand with exit-2 UsageError (0.159583ms)
  ✔ splitArgv separates global, command, and rest (0.130958ms)
  ✔ splitArgv returns null when no subcommand (0.055875ms)
✔ parseGlobal / splitArgv (1.647584ms)
▶ withLock (in-process)
  ✔ blocks same-process re-entrant acquire (no deadlock) (62.656125ms)
  ✔ releases the lockfile after the critical section (0.409792ms)
✔ withLock (in-process) (63.6725ms)
▶ withLock (multi-process contention)
  ✔ grants exclusive access across child processes (920.349917ms)
✔ withLock (multi-process contention) (920.429791ms)
▶ paths
  ✔ toPosix converts separators (0.428833ms)
  ✔ normalizeBusinessPath strips leading ./ and normalizes (0.067709ms)
  ✔ isAbsolutePathLike detects posix, windows drive, unc (0.070833ms)
  ✔ resolveInside rejects traversal outside root (0.318666ms)
  ✔ expandUser leaves non-home paths alone (0.100791ms)
✔ paths (1.644625ms)
▶ atomic-write
  ✔ writes text with a trailing newline, UTF-8 preserved (6.6385ms)
  ✔ writes JSON without ascii escaping and creates parent dirs (6.483667ms)
  ✔ preserves existing file mode (8.762625ms)
  ✔ loadJson returns default on missing/corrupt (0.351792ms)
  ✔ loadJsonStrict raises on corrupt/non-object (1.486375ms)
✔ atomic-write (24.200917ms)
中文测试
{
  "name": "中文"
}
err 中文
▶ subprocess.spawn (argv)
  ✔ runs a successful command and captures output (70.978125ms)
  ✔ returns 127 when the binary is missing (2.404792ms)
  ✔ returns a non-zero code on argv usage error (18.816708ms)
✔ subprocess.spawn (argv) (93.044292ms)
▶ subprocess.which / commandExists
  ✔ finds node on PATH (0.615875ms)
  ✔ returns null for a missing command (1.253666ms)
✔ subprocess.which / commandExists (2.04675ms)
▶ subprocess.runShell (shell form)
  ✔ supports pipes and redirects (7.183ms)
  ✔ supports environment variable expansion (9.266375ms)
  ✔ returns 0 for a true compound command (5.939ms)
  ✔ surfaces non-zero exit of a failed command (4.717959ms)
✔ subprocess.runShell (shell form) (27.36575ms)
▶ output (UTF-8)
  ✔ print writes a UTF-8 line including Chinese (0.899625ms)
  ✔ printJson renders without ASCII escaping (0.155083ms)
  ✔ printError writes to stderr (0.089292ms)
✔ output (UTF-8) (1.27275ms)
▶ io.yaml
  ✔ parses flat key: value (1.458541ms)
  ✔ strips quoted values (0.128083ms)
  ✔ coerces scalars (0.180042ms)
✔ io.yaml (1.875542ms)
▶ io.markdown
  ✔ parses ATX headings with level and text (0.285834ms)
  ✔ normalizeHeading collapses whitespace (0.060459ms)
  ✔ hasMeaningfulContent rejects blank/placeholder (0.217083ms)
✔ io.markdown (0.652125ms)
已初始化 .project-intel，索引了 4 个文本文件。
{
  "dryRun": true,
  "manifest": {
    "schemaVersion": 2,
    "toolVersion": "0.7.0",
    "projectRoot": ".",
    "generatedAt": "2026-07-24T08:36:02.042Z",
    "git": {
      "commit": null,
      "branch": null,
      "dirty": null
    },
    "frameworks": [],
    "packageName": "demo",
    "packages": [
      {
        "path": ".",
        "name": "demo",
        "frameworks": []
      }
    ],
    "fileCount": 4,
    "suffixCounts": {
      ".py": 2,
      ".json": 1,
      ".vue": 1
    },
    "graphSources": [
      {
        "name": "GitNexus",
        "path": ".gitnexus",
        "role": "符号调用、影响、变更风险",
        "status": "missing",
        "reason": "未找到索引目录"
      },
      {
        "name": "Understand-Anything",
        "path": ".understand-anything/knowledge-graph.json",
        "role": "架构、模块、领域流、入职",
        "status": "missing",
        "reason": "未找到知识图谱"
      }
    ],
    "tooling": {
      "node": "present",
      "gitnexus": "installable",
      "understandAnything": "agent-installed",
      "recommendedActions": 1
    },
    "notes": [
      "可用时优先使用 GitNexus 和 Understand-Anything 作为图谱来源。"
    ]
  },
  "config": {
    "schemaVersion": 2,
    "scan": {
      "include": [
        "**/*"
      ],
      "exclude": [
        ".cache",
        ".claude",
        ".git",
        ".idea",
        ".next",
        ".nuxt",
        ".project-intel",
        ".project-intel/cache",
        ".project-intel/local",
        ".project-intel/tmp",
        ".turbo",
        ".vscode",
        "build",
        "coverage",
        "dist",
        "node_modules",
        "target"
      ],
      "excludeHidden": true
    },
    "quality": {
      "commands": []
    },
    "backend": {
      "entrypointRules": [
        {
          "type": "annotation",
          "pattern": "@RestController|@Controller|@RequestMapping|@GetMapping|@PostMapping|@MessageListener|@Scheduled"
        },
        {
          "type": "call",
          "pattern": "router\\.(get|post|put|delete|use)|app\\.(get|post|put|delete|use)"
        },
        {
          "type": "path",
          "pattern": "**/{controller,handler,endpoint,facade,adapter}/**/*"
        }
      ]
    },
    "rules": {
      "hard": [],
      "preferred": [],
      "inferred": [],
      "candidate": []
    }
  },
  "graph": {
    "schemaVersion": 2,
    "generatedAt": "2026-07-24T08:36:02.077Z",
    "sources": [
      {
        "name": "GitNexus",
        "path": ".gitnexus",
        "role": "符号调用、影响、变更风险",
        "status": "missing",
        "reason": "未找到索引目录"
      },
      {
        "name": "Understand-Anything",
        "path": ".understand-anything/knowledge-graph.json",
        "role": "架构、模块、领域流、入职",
        "status": "missing",
        "reason": "未找到知识图谱"
      }
    ],
    "summary": {
      "components": 1,
      "hooks": 0,
      "apis": 0,
      "services": 1,
      "candidateEntrypoints": 0
    },
    "gitnexusSummary": {
      "name": "GitNexus",
      "path": ".gitnexus",
      "role": "符号调用、影响、变更风险",
      "status": "missing",
      "reason": "未找到索引目录"
    },
    "understandSummary": {
      "status": "missing",
      "reason": "未找到知识图谱",
      "nodes": 0,
      "edges": 0,
      "domains": [],
      "keyModules": [],
      "topPathPrefixes": []
    },
    "projectDomains": [
      {
        "name": "backend",
        "count": 2,
        "paths": [
          "backend/OrderService.py",
          "backend/OrderDTO.py"
        ],
        "source": "project-derived"
      }
    ]
  },
  "wouldWrite": [
    ".project-intel/manifest.json",
    ".project-intel/config.json",
    ".project-intel/knowledge/*.json",
    ".project-intel/graph/project-graph.json",
    ".project-intel/standards/*.md",
    ".project-intel/project-status.md",
    ".project-intel/requirements/<requirement-id>/*.md"
  ],
  "adapterWritesRequireExplicitFlag": true,
  "wouldRunGraph": false
}
已初始化 .project-intel，索引了 4 个文本文件。
已刷新 .project-intel，索引了 4 个文本文件。
已初始化 .project-intel，索引了 4 个文本文件。
已初始化 .project-intel，索引了 4 个文本文件。
已初始化 .project-intel，索引了 4 个文本文件。
▶ init command
  ✔ writes the .project-intel layout (manifest/config/knowledge/status) (205.140458ms)
  ✔ --dry-run does not write files (42.217292ms)
  ✔ refresh re-writes without tooling (673.671541ms)
  ✔ strict + no-graph is a usage error (12.237375ms)
  ✔ ensureProjectIntelGitignore writes local-only rules (11.718166ms)
✔ init command (946.130417ms)
▶ doctor command
  ✔ reports node runtime, not python (25.688875ms)
  ✔ detects initialized state after init (311.296041ms)
✔ doctor command (337.106875ms)
▶ check command
  ✔ passes with no hard rules configured (334.915167ms)
  ✔ --dry-run does not write status (426.282334ms)
✔ check command (761.384666ms)
▶ standards inference
  ✔ infers PascalCase naming from >=3 pascal components (0.457625ms)
  ✔ infers backend Service suffix from >=2 services (0.094125ms)
  ✔ infers ui-pattern from redundancy candidates (0.043458ms)
  ✔ ports backend API, layering and operational inference categories (0.121625ms)
✔ standards inference (0.829875ms)
▶ project domain candidates
  ✔ aggregates repeated non-generic parent segments in stable order (1.529916ms)
✔ project domain candidates (1.650125ms)
▶ standards documents
  ✔ renders detailed frontend and backend facts instead of count-only placeholders (2.952792ms)
✔ standards documents (3.035833ms)
▶ hard rules engine
  ✔ returns no violations with the empty default set (0.068166ms)
  ✔ surfaces a registered rule violation (0.191709ms)
✔ hard rules engine (0.337708ms)
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ requirement command dispatcher
  ✔ status returns state for a created requirement (40.62125ms)
  ✔ intake persists document actions and later selection blocks generation (46.268667ms)
  ✔ acceptance set persists AC-01..AC-02 (54.704375ms)
  ✔ query reads v2 and legacy by-id archives and supports --file (42.105083ms)
  ✔ test-contract set requires --kind and --report-action (53.820041ms)
  ✔ test-contract register validates and normalizes a structured report path (99.258125ms)
  ✔ ready -> begin through the dispatcher (839.997459ms)
  ✔ reopen after close (68.879209ms)
  ✔ generate enforces lifecycle order and creates a requirement scaffold (40.079667ms)
  ✔ generate refuses implicit overwrite and --replace really rebuilds the scaffold (95.045625ms)
  ✔ rejects missing --requirement-id (3.439417ms)
  ✔ add persists artifact registration into the manifest (539.493541ms)
  ✔ rejects arbitrary delivery-document content (234.22825ms)
  ✔ design registration rejects missing source evidence paths (351.924334ms)
  ✔ design registration ignores symbols that exist only in comments or strings (183.671083ms)
  ✔ add registers a structured test report as current requirement evidence (425.491875ms)
  ✔ diagnose records a Bug root cause (ticketKind=bug) (54.062125ms)
  ✔ diagnose rejects missing source evidence paths (37.389833ms)
  ✔ diagnose rejects symbols that only appear in comments or strings (32.191417ms)
  ✔ diagnose rejects non-bug requirements (26.540959ms)
  ✔ defer adds a readiness blocker for design (37.967167ms)
  ✔ resolve-finding marks a review finding resolved (30.892125ms)
  ✔ resolve-finding rejects unknown finding IDs (29.343958ms)
✔ requirement command dispatcher (3369.467875ms)
▶ requirement layout
  ✔ artifactFilename maps known types (0.04895
```
