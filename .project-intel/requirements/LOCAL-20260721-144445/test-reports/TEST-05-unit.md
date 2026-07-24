# LOCAL-20260721-144445 测试报告

- 测试类型：unit
- 阶段：verify
- 结果：passed
- 验收标准：AC-01,AC-02,AC-03,AC-04,AC-05,AC-06,AC-07,AC-08,AC-09,AC-10,AC-11,AC-12,AC-13,AC-14,AC-15
- 文件范围：.baseline/cli-snapshot.json, .baseline/fixtures/README.md, .baseline/fixtures/project-intel/.gitignore, .baseline/fixtures/project-intel/config.json, .baseline/fixtures/project-intel/graph/project-graph.json, .baseline/fixtures/project-intel/knowledge/backend.json, .baseline/fixtures/project-intel/knowledge/files.json, .baseline/fixtures/project-intel/knowledge/frontend.json, .baseline/fixtures/project-intel/manifest.json, .baseline/fixtures/project-intel/project-status.md, .baseline/fixtures/project-intel/standards/api.md, .baseline/fixtures/project-intel/standards/backend-api.md, .baseline/fixtures/project-intel/standards/backend-async.md, .baseline/fixtures/project-intel/standards/backend-config.md, .baseline/fixtures/project-intel/standards/backend-errors.md, .baseline/fixtures/project-intel/standards/backend-models.md, .baseline/fixtures/project-intel/standards/backend-remote-calls.md, .baseline/fixtures/project-intel/standards/backend-repository.md, .baseline/fixtures/project-intel/standards/backend-security.md, .baseline/fixtures/project-intel/standards/backend-services.md, .baseline/fixtures/project-intel/standards/backend-transactions.md, .baseline/fixtures/project-intel/standards/backend-utilities.md, .baseline/fixtures/project-intel/standards/backend.md, .baseline/fixtures/project-intel/standards/components.md, .baseline/fixtures/project-intel/standards/domain-flows.md, .baseline/fixtures/project-intel/standards/frontend.md, .baseline/fixtures/project-intel/standards/quality.md, .baseline/fixtures/project-intel/standards/reuse.md, .baseline/fixtures/project-intel/standards/router.md, .baseline/test-map.json, .github/workflows/validate.yml, .gitignore, .ua/.trash-1784630749/assemble-review.json, .ua/.trash-1784630749/assembled-graph.json, .ua/.trash-1784630749/batch-1-part-1.json, .ua/.trash-1784630749/batch-1-part-2.json, .ua/.trash-1784630749/batch-1-part-3.json, .ua/.trash-1784630749/batch-1-part-4.json, .ua/.trash-1784630749/batch-10.json, .ua/.trash-1784630749/batch-11.json, .ua/.trash-1784630749/batch-12.json, .ua/.trash-1784630749/batch-2.json, .ua/.trash-1784630749/batch-3-part-1.json, .ua/.trash-1784630749/batch-3-part-2.json, .ua/.trash-1784630749/batch-3-part-3.json, .ua/.trash-1784630749/batch-4.json, .ua/.trash-1784630749/batch-5.json, .ua/.trash-1784630749/batch-6.json, .ua/.trash-1784630749/batch-7.json, .ua/.trash-1784630749/batch-8.json, .ua/.trash-1784630749/batch-9.json, .ua/.trash-1784630749/batches.json, .ua/.trash-1784630749/fingerprint-input.json, .ua/.trash-1784630749/layers.json, .ua/.trash-1784630749/review.json, .ua/.trash-1784630749/tmp/arch-input.json, .ua/.trash-1784630749/tmp/build-tour-input.cjs, .ua/.trash-1784630749/tmp/gen_batch1.py, .ua/.trash-1784630749/tmp/ua-arch-analyze.cjs, .ua/.trash-1784630749/tmp/ua-arch-input.json, .ua/.trash-1784630749/tmp/ua-arch-results.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-1.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-10.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-11.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-12.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-2.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-3.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-4.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-5.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-6.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-7.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-8.json, .ua/.trash-1784630749/tmp/ua-file-analyzer-input-9.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-1.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-10.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-11.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-12.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-2.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-3.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-4.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-5.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-6.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-7.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-8.json, .ua/.trash-1784630749/tmp/ua-file-extract-results-9.json, .ua/.trash-1784630749/tmp/ua-import-map-input.json, .ua/.trash-1784630749/tmp/ua-import-map-output.json, .ua/.trash-1784630749/tmp/ua-inline-validate.cjs, .ua/.trash-1784630749/tmp/ua-scan-files.json, .ua/.trash-1784630749/tmp/ua-tour-analyze.cjs, .ua/.trash-1784630749/tmp/ua-tour-input.json, .ua/.trash-1784630749/tmp/ua-tour-results.json, .ua/.trash-1784630749/tour.json, .ua/.understandignore, .ua/config.json, .ua/fingerprints.json, .ua/intermediate/scan-result.json, .ua/knowledge-graph.json, .ua/meta.json, .understand-anything, .understand-anything/.trash-1784630749/assemble-review.json, .understand-anything/.trash-1784630749/assembled-graph.json, .understand-anything/.trash-1784630749/batch-1-part-1.json, .understand-anything/.trash-1784630749/batch-1-part-2.json, .understand-anything/.trash-1784630749/batch-1-part-3.json, .understand-anything/.trash-1784630749/batch-1-part-4.json, .understand-anything/.trash-1784630749/batch-10.json, .understand-anything/.trash-1784630749/batch-11.json, .understand-anything/.trash-1784630749/batch-12.json, .understand-anything/.trash-1784630749/batch-2.json, .understand-anything/.trash-1784630749/batch-3-part-1.json, .understand-anything/.trash-1784630749/batch-3-part-2.json, .understand-anything/.trash-1784630749/batch-3-part-3.json, .understand-anything/.trash-1784630749/batch-4.json, .understand-anything/.trash-1784630749/batch-5.json, .understand-anything/.trash-1784630749/batch-6.json, .understand-anything/.trash-1784630749/batch-7.json, .understand-anything/.trash-1784630749/batch-8.json, .understand-anything/.trash-1784630749/batch-9.json, .understand-anything/.trash-1784630749/batches.json, .understand-anything/.trash-1784630749/fingerprint-input.json, .understand-anything/.trash-1784630749/layers.json, .understand-anything/.trash-1784630749/review.json, .understand-anything/.trash-1784630749/tmp/arch-input.json, .understand-anything/.trash-1784630749/tmp/build-tour-input.cjs, .understand-anything/.trash-1784630749/tmp/gen_batch1.py, .understand-anything/.trash-1784630749/tmp/ua-arch-analyze.cjs, .understand-anything/.trash-1784630749/tmp/ua-arch-input.json, .understand-anything/.trash-1784630749/tmp/ua-arch-results.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-1.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-10.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-11.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-12.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-2.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-3.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-4.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-5.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-6.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-7.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-8.json, .understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-9.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-1.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-10.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-11.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-12.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-2.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-3.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-4.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-5.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-6.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-7.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-8.json, .understand-anything/.trash-1784630749/tmp/ua-file-extract-results-9.json, .understand-anything/.trash-1784630749/tmp/ua-import-map-input.json, .understand-anything/.trash-1784630749/tmp/ua-import-map-output.json, .understand-anything/.trash-1784630749/tmp/ua-inline-validate.cjs, .understand-anything/.trash-1784630749/tmp/ua-scan-files.json, .understand-anything/.trash-1784630749/tmp/ua-tour-analyze.cjs, .understand-anything/.trash-1784630749/tmp/ua-tour-input.json, .understand-anything/.trash-1784630749/tmp/ua-tour-results.json, .understand-anything/.trash-1784630749/tour.json, .understand-anything/.understandignore, .understand-anything/config.json, .understand-anything/fingerprints.json, .understand-anything/intermediate/scan-result.json, .understand-anything/knowledge-graph.json, .understand-anything/meta.json, AGENTS.md, CHANGELOG.md, CLAUDE.md, README.md, bin/project-intel.mjs, package-lock.json, package.json, plugins/project-intelligence/.claude-plugin/plugin.json, plugins/project-intelligence/.codex-plugin/plugin.json, plugins/project-intelligence/scripts/.npmignore, plugins/project-intelligence/scripts/project-intel, plugins/project-intelligence/scripts/project_intel.py, plugins/project-intelligence/scripts/project_intel_lib/__init__.py, plugins/project-intelligence/scripts/project_intel_lib/application.py, plugins/project-intelligence/scripts/project_intel_lib/cli.py, plugins/project-intelligence/scripts/project_intel_lib/core.py, plugins/project-intelligence/scripts/project_intel_lib/design_documents.py, plugins/project-intelligence/scripts/project_intel_lib/graph.py, plugins/project-intelligence/scripts/project_intel_lib/lifecycle.py, plugins/project-intelligence/scripts/project_intel_lib/quality.py, plugins/project-intelligence/scripts/project_intel_lib/requirement_documents.py, plugins/project-intelligence/scripts/project_intel_lib/requirements.py, plugins/project-intelligence/scripts/project_intel_lib/scanner/__init__.py, plugins/project-intelligence/scripts/project_intel_lib/scanner/backend.py, plugins/project-intelligence/scripts/project_intel_lib/scanner/frontend.py, plugins/project-intelligence/scripts/project_intel_lib/standards.py, plugins/project-intelligence/scripts/project_intel_lib/testing.py, plugins/project-intelligence/skills/project-design/SKILL.md, plugins/project-intelligence/skills/project-design/scripts/validate_design_doc.mjs, plugins/project-intelligence/skills/project-design/scripts/validate_design_doc.py, plugins/project-intelligence/tests/design_fixtures.py, plugins/project-intelligence/tests/test_document_truth_validation.py, plugins/project-intelligence/tests/test_project_design.py, plugins/project-intelligence/tests/test_project_intel.py, plugins/project-intelligence/tests/test_project_test.py, plugins/project-intelligence/tests/test_requirement_hardening.py, plugins/project-intelligence/tests/test_requirement_layout_v2.py, plugins/project-intelligence/tests/test_requirement_workflow.py, plugins/project-intelligence/tests/test_testing_security.py, scripts/bench.mjs, scripts/build-fixtures.mjs, scripts/check-dual-compat.mjs, scripts/check-package.mjs, scripts/check-release.mjs, scripts/gen-version.mjs, scripts/rollback-read.mjs, scripts/run-tests.mjs, scripts/run-unit-tests.mjs, scripts/scan-python-runtime-refs.mjs, scripts/smoke-pack.mjs, scripts/snapshot-cli.mjs, scripts/validate-test-map.mjs, scripts/validate_bundle.py, src/__tests__/backend.test.ts, src/__tests__/cli-contract.test.ts, src/__tests__/dispatcher.test.ts, src/__tests__/dual-impl.test.ts, src/__tests__/frontend-files-quality.test.ts, src/__tests__/graph-setup.test.ts, src/__tests__/helpers.ts, src/__tests__/install-hooks.test.ts, src/__tests__/json-envelope.test.ts, src/__tests__/lock-contender.ts, src/__tests__/lock.test.ts, src/__tests__/paths.test.ts, src/__tests__/process-io.test.ts, src/__tests__/project-facts.test.ts, src/__tests__/requirement-command.test.ts, src/__tests__/review-finish-graph.test.ts, src/__tests__/scope.test.ts, src/__tests__/smoke.test.ts, src/__tests__/state-machine.test.ts, src/__tests__/test-evidence.test.ts, src/app/dispatcher.ts, src/app/project-state.ts, src/cli.ts, src/cli/command-flags.ts, src/cli/json-envelope.ts, src/cli/parser.ts, src/commands/adapter-blocks.ts, src/commands/adapters.ts, src/commands/agent-install.ts, src/commands/agent-rules.ts, src/commands/check.ts, src/commands/doctor.ts, src/commands/finish.ts, src/commands/graph-tools.ts, src/commands/hooks.ts, src/commands/init.ts, src/commands/install.ts, src/commands/maintain.ts, src/commands/orchestration.ts, src/commands/query.ts, src/commands/requirement.ts, src/commands/review.ts, src/commands/test.ts, src/errors.ts, src/fs/atomic-write.ts, src/fs/lock.ts, src/fs/paths.ts, src/graph/actions.ts, src/graph/setup.ts, src/graph/sources.ts, src/index.ts, src/io/markdown.ts, src/io/output.ts, src/io/yaml.ts, src/process/exec-shell.ts, src/process/spawn.ts, src/requirements/documents.ts, src/requirements/layout.ts, src/requirements/scope.ts, src/requirements/state-machine.ts, src/rules/hard.ts, src/scanner/backend.ts, src/scanner/core.ts, src/scanner/files.ts, src/scanner/frontend.ts, src/scanner/quality.ts, src/standards/docs.ts, src/standards/domains.ts, src/standards/infer.ts, src/testing/dual-impl.ts, src/testing/render.ts, src/testing/sanitize.ts, src/version.ts, tsconfig.json

## 执行结果

### npm test

- exitCode: 0
- executedCount: 249

```text
Skill behavior scenario contracts verified: 27 scenarios, 17 skills
▶ maskCommentsAndStrings
  ✔ masks line and block comments and string contents (0.425625ms)
✔ maskCommentsAndStrings (0.935333ms)
▶ scanBackendFile
  ✔ extracts a Spring controller endpoint and methods (.java) (4.696584ms)
  ✔ extracts Python def/class and Flask routes (.py) (2.537709ms)
  ✔ classifies a service by name and extracts transaction signals (0.436334ms)
  ✔ extracts config keys from yaml (0.4485ms)
  ✔ classifies repository files and extracts SQL ops from xml mapper (0.545625ms)
  ✔ extracts permission signals (2.093709ms)
  ✔ extracts error code signals (0.109791ms)
  ✔ requires bound framework imports and keeps Django class views (0.166292ms)
  ✔ labels malformed Python without accepting route facts (0.082084ms)
  ✔ applies configured backend entrypoint rules (0.1485ms)
✔ scanBackendFile (11.611416ms)
▶ BACKEND_SUFFIXES
  ✔ includes java, kt, py, go, ts, js (0.046667ms)
✔ BACKEND_SUFFIXES (0.080291ms)
▶ cli snapshot contract (AC-02)
  ✔ loads a well-formed snapshot (1.922792ms)
  ✔ captured every top-level command's help (0.693042ms)
  ✔ pins the JSON envelope shape on every probe (0.178791ms)
  ✔ the version command exits 0 and prints a semver (0.73ms)
  ✔ usage errors exit non-zero with a non-ok envelope (0.332625ms)
✔ cli snapshot contract (AC-02) (4.978458ms)
▶ live Node CLI contract (AC-02/AC-10)
  ✔ dist/cli.js exists and is runnable (0.165125ms)
  ✔ version command exits 0 and prints a semver (119.006167ms)
  ✔ --version flag exits 0 and prints a semver (115.353083ms)
  ✔ every baseline command's --help is byte-for-byte compatible (1575.196208ms)
  ✔ top-level --help is byte-for-byte compatible (69.688459ms)
  ✔ top-level --help output contains all baseline commands (67.259208ms)
  ✔ subcommand --help output contains usage line and key flags (203.120583ms)
  ✔ unknown command exits 2 (86.583125ms)
  ✔ unknown flag exits 2 (79.302959ms)
  ✔ version --json produces a valid envelope with version field (66.408833ms)
  ✔ doctor --json produces a valid envelope with runtime=node (71.841167ms)
  ✔ usage error --json produces ok=false envelope (65.071667ms)
✔ live Node CLI contract (AC-02/AC-10) (2519.555834ms)
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
无法识别的命令：nope
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
  ✔ prints --version alone (1.280792ms)
  ✔ prints --version envelope in json mode (0.332875ms)
  ✔ runs a registered command (text mode) (1.114167ms)
  ✔ runs a registered command (json mode) with envelope (0.15ms)
  ✔ rejects unknown command with exit 2 (text) (0.453375ms)
  ✔ rejects unknown command with exit 2 (json envelope) (0.448834ms)
  ✔ surfaces usage errors as exit 2 (0.117083ms)
  ✔ surfaces runtime errors as exit 1 (0.080959ms)
  ✔ rejects missing subcommand (json exit 2) (1.016417ms)
  ✔ subcommand --help is intercepted and exits 0 (text) (0.535333ms)
  ✔ subcommand -h is intercepted and exits 0 (json) (0.190375ms)
  ✔ rejects unknown long flag with exit 2 (text) (0.122042ms)
  ✔ rejects unknown long flag with exit 2 (json envelope) (0.304458ms)
  ✔ accepts known value flag and its value (not mistaken for a flag) (0.069834ms)
  ✔ rejects unknown flag even after a valid value flag (0.056ms)
✔ dispatch (10.619375ms)
▶ normalizeForCompare
  ✔ masks ISO-8601 timestamps (1.150625ms)
  ✔ masks 40-char git hashes (0.088416ms)
  ✔ masks epoch-second/milli integers (0.055375ms)
  ✔ masks absolute repo roots (POSIX) (0.0505ms)
  ✔ normalizes Windows backslashes and masks sample root (0.054459ms)
  ✔ collapses mtime integers regardless of value (0.093625ms)
  ✔ applies longest-root-first masking so nested roots win (0.072666ms)
✔ normalizeForCompare (2.467333ms)
▶ compareJsonOutputs
  ✔ returns null for equal normalized values (0.141625ms)
  ✔ reports the first differing path (0.056125ms)
  ✔ reports missing keys with direction (0.1575ms)
  ✔ reports array length mismatches (0.052542ms)
✔ compareJsonOutputs (0.534041ms)
▶ frontend scanner
  ✔ extracts vue component props/emits (2.808292ms)
  ✔ extracts react props from interface (0.45775ms)
  ✔ extracts hooks by use* filename (0.59025ms)
  ✔ extracts routes and redundancy candidates (0.506917ms)
  ✔ extractVueProps from defineProps object form (0.150375ms)
  ✔ extractEmits filters to valid names (0.055917ms)
  ✔ extractApiEndpoints from request/fetch calls (0.171709ms)
✔ frontend scanner (5.872541ms)
▶ files scanner
  ✔ discoverFiles walks and categorizes (3.877958ms)
  ✔ discoverFiles excludes node_modules/.git (0.714542ms)
  ✔ uses stable code-point ordering across operating systems (0.319667ms)
  ✔ categorize and simpleMatch basics (0.1455ms)
✔ files scanner (5.224ms)
▶ incremental scan cache
  ✔ reuses unchanged frontend facts without reading the file again (0.319583ms)
  ✔ uses nanosecond-compatible file signatures and invalidates changed entries (0.539375ms)
✔ incremental scan cache (0.956167ms)
▶ quality scanner
  ✔ packageFrameworks detects Vue+TypeScript from deps (0.33325ms)
  ✔ detectPackage reads package.json scripts and frameworks (1.896167ms)
  ✔ packageManager detects npm/pnpm/yarn by lockfile (0.477625ms)
  ✔ detectQualityCommands: Python project STILL recognizes pytest/ruff/mypy (P1.3) (1.209834ms)
  ✔ detectQualityCommands: JS project infers eslint/tsc from config presence (0.608291ms)
✔ quality scanner (4.7495ms)
FixtureGraph 已安装，开始运行分析："/opt/homebrew/Cellar/node/26.3.0/bin/node" -e "process.stdout.write('graph-ok')"
FixtureGraph 开始执行，超时上限 900 秒。
GitNexus：仓库内 runner 需要显式使用 --allow-repo-runner。
▶ graph command authorization
  ✔ preserves and detects Windows absolute paths on POSIX (2.460542ms)
  ✔ allows repository-contained absolute paths and rejects outside paths (0.379209ms)
  ✔ requires explicit permission for repo runners and environment commands (0.463291ms)
✔ graph command authorization (5.448917ms)
▶ graph setup execution
  ✔ executes an authorized installed analyzer and captures evidence (80.954042ms)
  ✔ records a skipped result instead of executing an unauthorized runner (0.475791ms)
✔ graph setup execution (81.571417ms)
▶ adapter block management
  ✔ rejects paths outside the allowed set (0.878459ms)
  ✔ replaceSingleManagedBlock creates then updates (0.422584ms)
  ✔ upsert then remove a managed block (1.408542ms)
✔ adapter block management (4.051375ms)
▶ adapters command family
  ✔ apply writes codex + claude blocks; status reports current (1.78075ms)
  ✔ preview is dry-run (no files written) (0.193834ms)
  ✔ remove clears blocks (0.932333ms)
  ✔ status --check returns non-zero when not current (1.386125ms)
  ✔ adapterTargets both returns 3 targets (codex, claude, claude-nested) (1.248167ms)
✔ adapters command family (5.883166ms)
▶ top-level install command
  ✔ creates .claude/ and applies adapters; --hooks writes templates (2.221666ms)
✔ top-level install command (2.377125ms)
▶ agent install command
  ✔ agentInstallCommands builds codex+claude for all (0.203792ms)
  ✔ --dry-run classifies present when cli exists, missing otherwise (0.713667ms)
  ✔ rejects invalid target (0.328292ms)
✔ agent install command (1.460459ms)
▶ git hooks (AC-07: no python3)
  ✔ hook body calls project-intel (Node CLI), never python3 (0.189834ms)
  ✔ writeHookTemplates writes 3 hooks + README under .project-intel/hooks (1.141917ms)
✔ git hooks (AC-07: no python3) (1.438209ms)
▶ sanitizeErrorText
  ✔ redacts authorization bearer tokens (0.880833ms)
  ✔ redacts cookies (0.08725ms)
  ✔ redacts password/secret/token/api_key (0.050125ms)
  ✔ redacts aws credentials (0.037791ms)
  ✔ redacts URL userinfo (0.092917ms)
  ✔ leaves benign text intact (0.341917ms)
✔ sanitizeErrorText (3.056667ms)
▶ extractGlobalJson
  ✔ strips --json and reports mode (0.601917ms)
  ✔ preserves argv when --json absent (0.053583ms)
✔ extractGlobalJson (0.732542ms)
▶ jsonEnvelope
  ✔ shapes a success envelope (0.109417ms)
  ✔ classifies exit 2 as USAGE_ERROR with sanitized in-place error (0.213458ms)
  ✔ classifies non-2 failure as COMMAND_FAILED with default message (0.096708ms)
  ✔ trims the output field (0.06025ms)
✔ jsonEnvelope (1.530042ms)
▶ parseGlobal / splitArgv
  ✔ parses --project value (0.175ms)
  ✔ parses --project= form (0.065875ms)
  ✔ parses --json (0.110333ms)
  ✔ rejects unknown long option before subcommand with exit-2 UsageError (0.22725ms)
  ✔ splitArgv separates global, command, and rest (0.203708ms)
  ✔ splitArgv returns null when no subcommand (0.070625ms)
✔ parseGlobal / splitArgv (1.015291ms)
▶ withLock (in-process)
  ✔ blocks same-process re-entrant acquire (no deadlock) (64.9805ms)
  ✔ releases the lockfile after the critical section (0.487459ms)
✔ withLock (in-process) (66.252417ms)
▶ withLock (multi-process contention)
  ✔ grants exclusive access across child processes (930.261084ms)
✔ withLock (multi-process contention) (930.41675ms)
▶ paths
  ✔ toPosix converts separators (0.39225ms)
  ✔ normalizeBusinessPath strips leading ./ and normalizes (0.080416ms)
  ✔ isAbsolutePathLike detects posix, windows drive, unc (0.06775ms)
  ✔ resolveInside rejects traversal outside root (0.30975ms)
  ✔ expandUser leaves non-home paths alone (0.047458ms)
✔ paths (1.482125ms)
▶ atomic-write
  ✔ writes text with a trailing newline, UTF-8 preserved (7.902584ms)
  ✔ writes JSON without ascii escaping and creates parent dirs (5.730333ms)
  ✔ preserves existing file mode (9.619459ms)
  ✔ loadJson returns default on missing/corrupt (0.69825ms)
  ✔ loadJsonStrict raises on corrupt/non-object (0.726916ms)
✔ atomic-write (24.951541ms)
中文测试
{
  "name": "中文"
}
err 中文
▶ subprocess.spawn (argv)
  ✔ runs a successful command and captures output (91.204167ms)
  ✔ returns 127 when the binary is missing (2.465958ms)
  ✔ returns a non-zero code on argv usage error (22.85875ms)
✔ subprocess.spawn (argv) (117.53975ms)
▶ subprocess.which / commandExists
  ✔ finds node on PATH (1.133042ms)
  ✔ returns null for a missing command (0.471667ms)
✔ subprocess.which / commandExists (1.708084ms)
▶ subprocess.runShell (shell form)
  ✔ supports pipes and redirects (7.580041ms)
  ✔ supports environment variable expansion (8.227459ms)
  ✔ returns 0 for a true compound command (5.780666ms)
  ✔ surfaces non-zero exit of a failed command (4.1825ms)
✔ subprocess.runShell (shell form) (26.030041ms)
▶ output (UTF-8)
  ✔ print writes a UTF-8 line including Chinese (0.377291ms)
  ✔ printJson renders without ASCII escaping (0.113875ms)
  ✔ printError writes to stderr (0.158166ms)
✔ output (UTF-8) (0.746958ms)
▶ io.yaml
  ✔ parses flat key: value (0.680041ms)
  ✔ strips quoted values (0.0495ms)
  ✔ coerces scalars (0.086334ms)
✔ io.yaml (0.85825ms)
▶ io.markdown
  ✔ parses ATX headings with level and text (0.113416ms)
  ✔ normalizeHeading collapses whitespace (0.02025ms)
  ✔ hasMeaningfulContent rejects blank/placeholder (0.093167ms)
✔ io.markdown (0.257584ms)
已初始化 .project-intel，索引了 4 个文本文件。
{
  "dryRun": true,
  "manifest": {
    "schemaVersion": 2,
    "toolVersion": "0.7.0",
    "projectRoot": ".",
    "generatedAt": "2026-07-24T08:44:53.570Z",
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
    "generatedAt": "2026-07-24T08:44:53.608Z",
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
  ✔ writes the .project-intel layout (manifest/config/knowledge/status) (215.925916ms)
  ✔ --dry-run does not write files (43.743375ms)
  ✔ refresh re-writes without tooling (600.41175ms)
  ✔ strict + no-graph is a usage error (7.771667ms)
  ✔ ensureProjectIntelGitignore writes local-only rules (6.907792ms)
✔ init command (875.626666ms)
▶ doctor command
  ✔ reports node runtime, not python (35.635583ms)
  ✔ detects initialized state after init (340.411292ms)
✔ doctor command (376.161083ms)
▶ check command
  ✔ passes with no hard rules configured (329.6885ms)
  ✔ --dry-run does not write status (399.440875ms)
✔ check command (729.242833ms)
▶ standards inference
  ✔ infers PascalCase naming from >=3 pascal components (0.354917ms)
  ✔ infers backend Service suffix from >=2 services (0.220875ms)
  ✔ infers ui-pattern from redundancy candidates (0.123208ms)
  ✔ ports backend API, layering and operational inference categories (0.146583ms)
✔ standards inference (0.975083ms)
▶ project domain candidates
  ✔ aggregates repeated non-generic parent segments in stable order (0.832833ms)
✔ project domain candidates (0.910916ms)
▶ standards documents
  ✔ renders detailed frontend and backend facts instead of count-only placeholders (1.054333ms)
✔ standards documents (1.102959ms)
▶ hard rules engine
  ✔ returns no violations with the empty default set (0.057125ms)
  ✔ surfaces a registered rule violation (0.060167ms)
✔ hard rules engine (0.155166ms)
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ requirement command dispatcher
  ✔ status returns state for a created requirement (46.576625ms)
  ✔ intake persists document actions and later selection blocks generation (54.343625ms)
  ✔ acceptance set persists AC-01..AC-02 (43.85625ms)
  ✔ query reads v2 and legacy by-id archives and supports --file (45.112125ms)
  ✔ test-contract set requires --kind and --report-action (50.67075ms)
  ✔ test-contract register validates and normalizes a structured report path (93.322792ms)
  ✔ ready -> begin through the dispatcher (803.773292ms)
  ✔ reopen after close (59.0925ms)
  ✔ generate enforces lifecycle order and creates a requirement scaffold (58.869542ms)
  ✔ generate refuses implicit overwrite and --replace really rebuilds the scaffold (96.869333ms)
  ✔ rejects missing --requirement-id (3.993125ms)
  ✔ add persists artifact registration into the manifest (503.997917ms)
  ✔ rejects arbitrary delivery-document content (187.590958ms)
  ✔ design registration rejects missing source evidence paths (373.124666ms)
  ✔ design registration ignores symbols that exist only in comments or strings (154.067ms)
  ✔ add registers a structured test report as current requirement evidence (438.139083ms)
  ✔ diagnose records a Bug root cause (ticketKind=bug) (57.838916ms)
  ✔ diagnose rejects missing source evidence paths (47.187ms)
  ✔ diagnose rejects symbols that only appear in comments or strings (27.03175ms)
  ✔ diagnose rejects non-bug requirements (45.708167ms)
  ✔ defer adds a readiness blocker for design (24.04625ms)
  ✔ resolve-finding marks a review finding resolved (26.864666ms)
  ✔ resolve-finding rejects unknown finding IDs (29.158917ms)
✔ requirement command dispatcher (3273.083666ms)
▶ requirement layout
  ✔ artifactFilename maps known types (0.048ms)
  ✔ ARTI
```
