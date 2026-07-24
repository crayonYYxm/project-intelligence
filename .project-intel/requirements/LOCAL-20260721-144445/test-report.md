# Project Intelligence Node.js/TypeScript 运行时迁移 · 测试报告

- 需求号：`LOCAL-20260721-144445`
- 当前状态：最近一次执行失败

## 测试计划

- AC-01：计划验证，尚未执行。
- AC-02：计划验证，尚未执行。
- AC-03：计划验证，尚未执行。
- AC-04：计划验证，尚未执行。
- AC-05：计划验证，尚未执行。
- AC-06：计划验证，尚未执行。
- AC-07：计划验证，尚未执行。
- AC-08：计划验证，尚未执行。
- AC-09：计划验证，尚未执行。
- AC-10：计划验证，尚未执行。
- AC-11：计划验证，尚未执行。
- AC-12：计划验证，尚未执行。
- AC-13：计划验证，尚未执行。
- AC-14：计划验证，尚未执行。
- AC-15：计划验证，尚未执行。

## 执行记录

尚未执行。只有写入实际命令、结果和验收标准映射后，本文档才可作为完成证据。

### 2026-07-23T01:32:17.814898+00:00 · verify / service

- 结果：failed
- 已执行测试数：0
- 验收标准：AC-02, AC-04, AC-10
- 覆盖范围：`.baseline/cli-snapshot.json`, `.baseline/test-map.json`, `scripts/build-fixtures.mjs`, `scripts/snapshot-cli.mjs`, `scripts/validate-test-map.mjs`
- Git 提交：`5f3ad66c9355153e765351291f5c8d8e3620ce22`
- 代码快照：`f38dd69c74ae2c7a8fcf5508e63bd2fda9f56756ae8f3fe44c4796e5bf20c0a2`
- 命令：`node scripts/snapshot-cli.mjs --check && node scripts/build-fixtures.mjs --validate && node scripts/validate-test-map.mjs && git -C .baseline/worktree rev-parse HEAD`

```text
Snapshot OK (21 commands, version 0.6.1).
Fixture OK.
test-map: 23 mappings (done=0, planned=0, pending=23, skipped=0); baseline classes=23, node test files=0
test-map OK.
ad3f346a78fbbc29689e16e1c9002f7037381841
```

### 2026-07-23T01:59:05.350086+00:00 · verify / service

- 结果：failed
- 已执行测试数：0
- 验收标准：AC-02, AC-10, AC-12
- 覆盖范围：`package.json`, `scripts/gen-version.mjs`, `scripts/run-unit-tests.mjs`, `src/__tests__/cli-contract.test.ts`, `src/__tests__/dual-impl.test.ts`, `src/__tests__/smoke.test.ts`, `src/index.ts`, `src/testing/dual-impl.ts`, `src/version.ts`, `tsconfig.json`
- Git 提交：`5f3ad66c9355153e765351291f5c8d8e3620ce22`
- 代码快照：`b0c954853b61c15db11e7cad3e8c6333d62c17c162f26fbd5a94842dc8ca8844`
- 命令：`npm run typecheck && npm run test:unit && npm run check-release && node scripts/validate-test-map.mjs`

```text
npm notice run project-intelligence@0.6.1 typecheck
npm notice run tsc --noEmit -p tsconfig.json
▶ cli snapshot contract (AC-02)
  ✔ loads a well-formed snapshot (0.666333ms)
  ✔ captured every top-level command's help (0.678833ms)
  ✔ pins the JSON envelope shape on every probe (0.140875ms)
  ✔ the version command exits 0 and prints a semver (0.16525ms)
  ✔ usage errors exit non-zero with a non-ok envelope (0.092042ms)
✔ cli snapshot contract (AC-02) (2.61425ms)
▶ normalizeForCompare
  ✔ masks ISO-8601 timestamps (1.117625ms)
  ✔ masks 40-char git hashes (0.1755ms)
  ✔ masks epoch-second/milli integers (0.116708ms)
  ✔ masks absolute repo roots (POSIX) (0.13975ms)
  ✔ normalizes Windows backslashes and masks sample root (0.110833ms)
  ✔ collapses mtime integers regardless of value (0.146708ms)
  ✔ applies longest-root-first masking so nested roots win (0.142167ms)
✔ normalizeForCompare (2.952208ms)
▶ compareJsonOutputs
  ✔ returns null for equal normalized values (0.242208ms)
  ✔ reports the first differing path (0.078958ms)
  ✔ reports missing keys with direction (0.11925ms)
  ✔ reports array length mismatches (0.04525ms)
✔ compareJsonOutputs (0.630625ms)
▶ dual-impl path resolvers
  ✔ baselineCliPath resolves when worktree exists (0.107875ms)
  ✔ nodeCliPath is null until the Node CLI is built (expected during phase 1) (0.048916ms)
✔ dual-impl path resolvers (0.201083ms)
▶ typescript harness
  ✔ runs a TypeScript assertion (0.383333ms)
  ✔ can import a source module (1.340875ms)
✔ typescript harness (2.277458ms)
ℹ tests 20
ℹ suites 5
ℹ pass 20
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 114.312916
npm notice run project-intelligence@0.6.1 test:unit
npm notice run node scripts/run-unit-tests.mjs
Release metadata is consistent: 0.6.1
npm package contents and installed launcher verified: 55 files
npm notice run project-intelligence@0.6.1 check-release
npm notice run node scripts/check-release.mjs && node scripts/check-package.mjs
npm warn Unknown env config "global-ignore-file". This will stop working in the next major version of npm. See `npm help npmrc` for supported config options.
npm warn Unknown env config "global-ignore-file". This will stop working in the next major version of npm. See `npm help npmrc` for supported config options.
test-map: 23 mappings (done=0, planned=1, pending=22, skipped=0); baseline classes=23, node test files=3
test-map OK.
```

### 2026-07-23T02:44:34.382708+00:00 · verify / service

- 结果：failed
- 已执行测试数：0
- 验收标准：AC-03, AC-08, AC-13
- 覆盖范围：`src/app/dispatcher.ts`, `src/cli.ts`, `src/cli/json-envelope.ts`, `src/cli/parser.ts`, `src/errors.ts`, `src/fs/atomic-write.ts`, `src/fs/lock.ts`, `src/fs/paths.ts`, `src/index.ts`, `src/io/markdown.ts`, `src/io/output.ts`, `src/io/yaml.ts`, `src/process/exec-shell.ts`, `src/process/spawn.ts`
- Git 提交：`5f3ad66c9355153e765351291f5c8d8e3620ce22`
- 代码快照：`75390371b797a8dd5215ba2b841cc175d01cd421e7a485bcf5c38453560dacf2`
- 命令：`npm run typecheck && npm run build && npm run test:unit && npm run check-release`

```text
npm notice run project-intelligence@0.6.1 typecheck
npm notice run tsc --noEmit -p tsconfig.json
Version synced to 0.6.1 across package.json, src/version.ts, dist/version.js, both plugin.json, and application.py.
npm notice run project-intelligence@0.6.1 build
npm notice run node scripts/gen-version.mjs && tsc -p tsconfig.json
66ms)
✔ compareJsonOutputs (0.615458ms)
▶ dual-impl path resolvers
  ✔ baselineCliPath resolves when worktree exists (0.282833ms)
  ✔ nodeCliPath is null until the Node CLI is built (expected during phase 1) (0.083ms)
✔ dual-impl path resolvers (0.415083ms)
▶ sanitizeErrorText
  ✔ redacts authorization bearer tokens (1.34325ms)
  ✔ redacts cookies (0.215125ms)
  ✔ redacts password/secret/token/api_key (0.129959ms)
  ✔ redacts aws credentials (0.096084ms)
  ✔ redacts URL userinfo (0.089708ms)
  ✔ leaves benign text intact (0.422458ms)
✔ sanitizeErrorText (3.697459ms)
▶ extractGlobalJson
  ✔ strips --json and reports mode (0.659542ms)
  ✔ preserves argv when --json absent (0.059416ms)
✔ extractGlobalJson (0.876666ms)
▶ jsonEnvelope
  ✔ shapes a success envelope (0.308834ms)
  ✔ classifies exit 2 as USAGE_ERROR with sanitized in-place error (0.175458ms)
  ✔ classifies non-2 failure as COMMAND_FAILED with default message (0.093458ms)
  ✔ trims the output field (0.055625ms)
✔ jsonEnvelope (0.820875ms)
▶ parseGlobal / splitArgv
  ✔ parses --project value (0.172917ms)
  ✔ parses --project= form (0.180708ms)
  ✔ parses --json (0.057833ms)
  ✔ rejects unknown long option before subcommand with exit-2 UsageError (0.083333ms)
  ✔ splitArgv separates global, command, and rest (0.368625ms)
  ✔ splitArgv returns null when no subcommand (0.068416ms)
✔ parseGlobal / splitArgv (1.111708ms)
▶ withLock (in-process)
  ✔ blocks same-process re-entrant acquire (no deadlock) (62.074791ms)
  ✔ releases the lockfile after the critical section (0.341125ms)
✔ withLock (in-process) (63.068875ms)
▶ withLock (multi-process contention)
  ✔ grants exclusive access across child processes (665.552708ms)
✔ withLock (multi-process contention) (665.625042ms)
▶ paths
  ✔ toPosix converts separators (0.899125ms)
  ✔ normalizeBusinessPath strips leading ./ and normalizes (0.397833ms)
  ✔ isAbsolutePathLike detects posix, windows drive, unc (0.191625ms)
  ✔ resolveInside rejects traversal outside root (0.514208ms)
  ✔ expandUser leaves non-home paths alone (0.208916ms)
✔ paths (3.426167ms)
▶ atomic-write
  ✔ writes text with a trailing newline, UTF-8 preserved (8.646ms)
  ✔ writes JSON without ascii escaping and creates parent dirs (5.030792ms)
  ✔ preserves existing file mode (9.3885ms)
  ✔ loadJson returns default on missing/corrupt (0.377166ms)
  ✔ loadJsonStrict raises on corrupt/non-object (0.367625ms)
✔ atomic-write (24.069333ms)
中文测试
{
  "name": "中文"
}
err 中文
▶ subprocess.spawn (argv)
  ✔ runs a successful command and captures output (56.827917ms)
  ✔ returns 127 when the binary is missing (0.974291ms)
  ✔ returns a non-zero code on argv usage error (15.520208ms)
✔ subprocess.spawn (argv) (74.23775ms)
▶ subprocess.which / commandExists
  ✔ finds node on PATH (0.294666ms)
  ✔ returns null for a missing command (0.183375ms)
✔ subprocess.which / commandExists (0.8905ms)
▶ subprocess.runShell (shell form)
  ✔ supports pipes and redirects (5.361375ms)
  ✔ supports environment variable expansion (5.9405ms)
  ✔ returns 0 for a true compound command (2.862167ms)
  ✔ surfaces non-zero exit of a failed command (3.443958ms)
✔ subprocess.runShell (shell form) (17.816625ms)
▶ output (UTF-8)
  ✔ print writes a UTF-8 line including Chinese (0.224292ms)
  ✔ printJson renders without ASCII escaping (0.091667ms)
  ✔ printError writes to stderr (0.055542ms)
✔ output (UTF-8) (0.44725ms)
▶ io.yaml
  ✔ parses flat key: value (0.768875ms)
  ✔ strips quoted values (0.061542ms)
  ✔ coerces scalars (0.092042ms)
✔ io.yaml (0.972834ms)
▶ io.markdown
  ✔ parses ATX headings with level and text (0.110708ms)
  ✔ normalizeHeading collapses whitespace (0.02325ms)
  ✔ hasMeaningfulContent rejects blank/placeholder (0.102166ms)
✔ io.markdown (0.271417ms)
▶ typescript harness
  ✔ runs a TypeScript assertion (1.019291ms)
  ✔ can import a source module (2.25625ms)
✔ typescript harness (4.085917ms)
ℹ tests 78
ℹ suites 20
ℹ pass 78
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 904.941542
npm notice run project-intelligence@0.6.1 test:unit
npm notice run node scripts/run-unit-tests.mjs
Release metadata is consistent: 0.6.1
npm package contents and installed launcher verified: 83 files
npm notice run project-intelligence@0.6.1 check-release
npm notice run node scripts/check-release.mjs && node scripts/check-package.mjs
npm warn Unknown env config "global-ignore-file". This will stop working in the next major version of npm. See `npm help npmrc` for supported config options.
npm warn Unknown env config "global-ignore-file". This will stop working in the next major version of npm. See `npm help npmrc` for supported config options.
```

### 2026-07-23T03:17:58.652644+00:00 · verify / service

- 结果：failed
- 已执行测试数：0
- 验收标准：AC-06, AC-14
- 覆盖范围：`src/__tests__/backend.test.ts`, `src/__tests__/frontend-files-quality.test.ts`, `src/scanner/backend.ts`, `src/scanner/core.ts`, `src/scanner/files.ts`, `src/scanner/frontend.ts`, `src/scanner/quality.ts`
- Git 提交：`5f3ad66c9355153e765351291f5c8d8e3620ce22`
- 代码快照：`a763063b4e766336f96518298a244522ca154277656a977fa9708065fb86f1e6`
- 命令：`npm run typecheck && npm run build && npm run test:unit && node scripts/validate-test-map.mjs`

```text
npm notice run project-intelligence@0.6.1 typecheck
npm notice run tsc --noEmit -p tsconfig.json
Version synced to 0.6.1 across package.json, src/version.ts, dist/version.js, both plugin.json, and application.py.
npm notice run project-intelligence@0.6.1 build
npm notice run node scripts/gen-version.mjs && tsc -p tsconfig.json
packageManager detects npm/pnpm/yarn by lockfile (0.21375ms)
  ✔ detectQualityCommands: Python project STILL recognizes pytest/ruff/mypy (P1.3) (0.5975ms)
  ✔ detectQualityCommands: JS project infers eslint/tsc from config presence (0.52525ms)
✔ quality scanner (5.118291ms)
▶ sanitizeErrorText
  ✔ redacts authorization bearer tokens (1.841541ms)
  ✔ redacts cookies (0.141541ms)
  ✔ redacts password/secret/token/api_key (0.098959ms)
  ✔ redacts aws credentials (0.080958ms)
  ✔ redacts URL userinfo (0.07175ms)
  ✔ leaves benign text intact (0.637291ms)
✔ sanitizeErrorText (4.217916ms)
▶ extractGlobalJson
  ✔ strips --json and reports mode (1.221375ms)
  ✔ preserves argv when --json absent (1.5855ms)
✔ extractGlobalJson (3.003041ms)
▶ jsonEnvelope
  ✔ shapes a success envelope (0.23325ms)
  ✔ classifies exit 2 as USAGE_ERROR with sanitized in-place error (0.181667ms)
  ✔ classifies non-2 failure as COMMAND_FAILED with default message (0.119459ms)
  ✔ trims the output field (0.069459ms)
✔ jsonEnvelope (0.8345ms)
▶ parseGlobal / splitArgv
  ✔ parses --project value (0.905ms)
  ✔ parses --project= form (0.096125ms)
  ✔ parses --json (0.062417ms)
  ✔ rejects unknown long option before subcommand with exit-2 UsageError (0.199125ms)
  ✔ splitArgv separates global, command, and rest (0.200625ms)
  ✔ splitArgv returns null when no subcommand (0.162792ms)
✔ parseGlobal / splitArgv (1.830291ms)
▶ withLock (in-process)
  ✔ blocks same-process re-entrant acquire (no deadlock) (61.364542ms)
  ✔ releases the lockfile after the critical section (0.310875ms)
✔ withLock (in-process) (62.246875ms)
▶ withLock (multi-process contention)
  ✔ grants exclusive access across child processes (638.343125ms)
✔ withLock (multi-process contention) (638.410667ms)
▶ paths
  ✔ toPosix converts separators (0.798167ms)
  ✔ normalizeBusinessPath strips leading ./ and normalizes (0.130708ms)
  ✔ isAbsolutePathLike detects posix, windows drive, unc (1.850375ms)
  ✔ resolveInside rejects traversal outside root (0.686ms)
  ✔ expandUser leaves non-home paths alone (0.113541ms)
✔ paths (4.801167ms)
▶ atomic-write
  ✔ writes text with a trailing newline, UTF-8 preserved (6.819625ms)
  ✔ writes JSON without ascii escaping and creates parent dirs (5.121333ms)
  ✔ preserves existing file mode (9.661667ms)
  ✔ loadJson returns default on missing/corrupt (0.799042ms)
  ✔ loadJsonStrict raises on corrupt/non-object (0.703ms)
✔ atomic-write (23.385625ms)
中文测试
{
  "name": "中文"
}
err 中文
▶ subprocess.spawn (argv)
  ✔ runs a successful command and captures output (56.043834ms)
  ✔ returns 127 when the binary is missing (1.137041ms)
  ✔ returns a non-zero code on argv usage error (14.726291ms)
✔ subprocess.spawn (argv) (72.490667ms)
▶ subprocess.which / commandExists
  ✔ finds node on PATH (0.320084ms)
  ✔ returns null for a missing command (0.189333ms)
✔ subprocess.which / commandExists (0.584542ms)
▶ subprocess.runShell (shell form)
  ✔ supports pipes and redirects (5.112375ms)
  ✔ supports environment variable expansion (6.136ms)
  ✔ returns 0 for a true compound command (2.868458ms)
  ✔ surfaces non-zero exit of a failed command (2.586125ms)
✔ subprocess.runShell (shell form) (16.850208ms)
▶ output (UTF-8)
  ✔ print writes a UTF-8 line including Chinese (0.19ms)
  ✔ printJson renders without ASCII escaping (0.068958ms)
  ✔ printError writes to stderr (0.036375ms)
✔ output (UTF-8) (0.349ms)
▶ io.yaml
  ✔ parses flat key: value (0.728208ms)
  ✔ strips quoted values (0.066459ms)
  ✔ coerces scalars (0.086125ms)
✔ io.yaml (0.927666ms)
▶ io.markdown
  ✔ parses ATX headings with level and text (0.10675ms)
  ✔ normalizeHeading collapses whitespace (0.083ms)
  ✔ hasMeaningfulContent rejects blank/placeholder (0.121042ms)
✔ io.markdown (0.371166ms)
▶ typescript harness
  ✔ runs a TypeScript assertion (0.354417ms)
  ✔ can import a source module (1.0825ms)
✔ typescript harness (1.96325ms)
ℹ tests 102
ℹ suites 26
ℹ pass 102
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 842.70475
npm notice run project-intelligence@0.6.1 test:unit
npm notice run node scripts/run-unit-tests.mjs
test-map: 23 mappings (done=0, planned=1, pending=22, skipped=0); baseline classes=23, node test files=10
test-map OK.
```

### 2026-07-23T03:42:27.887107+00:00 · verify / service

- 结果：failed
- 已执行测试数：0
- 验收标准：AC-01, AC-03, AC-06
- 覆盖范围：`src/__tests__/project-facts.test.ts`, `src/app/project-state.ts`, `src/commands/check.ts`, `src/commands/doctor.ts`, `src/commands/init.ts`, `src/rules/hard.ts`, `src/standards/infer.ts`
- Git 提交：`5f3ad66c9355153e765351291f5c8d8e3620ce22`
- 代码快照：`0e39fd16ed2c749e8198b2b941315e7ad86cd3a9063fb63e3ca0032885e90b77`
- 命令：`npm run typecheck && npm run build && npm run test:unit`

```text
npm notice run project-intelligence@0.6.1 typecheck
npm notice run tsc --noEmit -p tsconfig.json
Version synced to 0.6.1 across package.json, src/version.ts, dist/version.js, both plugin.json, and application.py.
npm notice run project-intelligence@0.6.1 build
npm notice run node scripts/gen-version.mjs && tsc -p tsconfig.json
054ms)
✔ parseGlobal / splitArgv (0.735208ms)
▶ withLock (in-process)
  ✔ blocks same-process re-entrant acquire (no deadlock) (61.0825ms)
  ✔ releases the lockfile after the critical section (0.281833ms)
✔ withLock (in-process) (62.172208ms)
▶ withLock (multi-process contention)
  ✔ grants exclusive access across child processes (621.899167ms)
✔ withLock (multi-process contention) (621.960125ms)
▶ paths
  ✔ toPosix converts separators (0.384792ms)
  ✔ normalizeBusinessPath strips leading ./ and normalizes (0.06875ms)
  ✔ isAbsolutePathLike detects posix, windows drive, unc (0.07025ms)
  ✔ resolveInside rejects traversal outside root (0.321125ms)
  ✔ expandUser leaves non-home paths alone (0.047833ms)
✔ paths (1.454917ms)
▶ atomic-write
  ✔ writes text with a trailing newline, UTF-8 preserved (12.561334ms)
  ✔ writes JSON without ascii escaping and creates parent dirs (4.364ms)
  ✔ preserves existing file mode (10.522375ms)
  ✔ loadJson returns default on missing/corrupt (0.328084ms)
  ✔ loadJsonStrict raises on corrupt/non-object (0.307208ms)
✔ atomic-write (28.24025ms)
中文测试
{
  "name": "中文"
}
err 中文
▶ subprocess.spawn (argv)
  ✔ runs a successful command and captures output (52.372917ms)
  ✔ returns 127 when the binary is missing (1.2645ms)
  ✔ returns a non-zero code on argv usage error (14.099417ms)
✔ subprocess.spawn (argv) (68.63175ms)
▶ subprocess.which / commandExists
  ✔ finds node on PATH (0.275042ms)
  ✔ returns null for a missing command (0.198667ms)
✔ subprocess.which / commandExists (0.546917ms)
▶ subprocess.runShell (shell form)
  ✔ supports pipes and redirects (4.448917ms)
  ✔ supports environment variable expansion (5.898416ms)
  ✔ returns 0 for a true compound command (3.399ms)
  ✔ surfaces non-zero exit of a failed command (2.428209ms)
✔ subprocess.runShell (shell form) (16.336875ms)
▶ output (UTF-8)
  ✔ print writes a UTF-8 line including Chinese (0.278209ms)
  ✔ printJson renders without ASCII escaping (0.068375ms)
  ✔ printError writes to stderr (0.037458ms)
✔ output (UTF-8) (0.465083ms)
▶ io.yaml
  ✔ parses flat key: value (0.677709ms)
  ✔ strips quoted values (0.046917ms)
  ✔ coerces scalars (0.073125ms)
✔ io.yaml (0.832875ms)
▶ io.markdown
  ✔ parses ATX headings with level and text (0.100667ms)
  ✔ normalizeHeading collapses whitespace (0.025084ms)
  ✔ hasMeaningfulContent rejects blank/placeholder (0.092417ms)
✔ io.markdown (0.247541ms)
已初始化 .project-intel，索引了 4 个文本文件。
init --dry-run 预览：
- 文件数：4
- 框架：未识别
- 前端组件：1
- 后端 API：0
- 标准推断：0 条
已初始化 .project-intel，索引了 4 个文本文件。
已刷新 .project-intel，索引了 13 个文本文件。
已初始化 .project-intel，索引了 4 个文本文件。
已初始化 .project-intel，索引了 4 个文本文件。
已初始化 .project-intel，索引了 4 个文本文件。
▶ init command
  ✔ writes the .project-intel layout (manifest/config/knowledge/status) (75.197875ms)
  ✔ --dry-run does not write files (28.600792ms)
  ✔ refresh re-writes without tooling (117.778625ms)
  ✔ strict + no-graph is a usage error (0.198792ms)
  ✔ ensureProjectIntelGitignore writes local-only rules (0.1905ms)
✔ init command (222.558166ms)
▶ doctor command
  ✔ reports node runtime, not python (0.68225ms)
  ✔ detects initialized state after init (59.921708ms)
✔ doctor command (60.710875ms)
▶ check command
  ✔ passes with no hard rules configured (90.725208ms)
  ✔ --dry-run does not write status (91.858709ms)
✔ check command (182.688584ms)
▶ standards inference
  ✔ infers PascalCase naming from >=3 pascal components (0.249875ms)
  ✔ infers backend Service suffix from >=3 services (0.089917ms)
  ✔ infers ui-pattern from redundancy candidates (0.043417ms)
✔ standards inference (0.435875ms)
▶ hard rules engine
  ✔ returns no violations with the empty default set (0.539625ms)
  ✔ surfaces a registered rule violation (0.083042ms)
✔ hard rules engine (0.656792ms)
▶ typescript harness
  ✔ runs a TypeScript assertion (0.346125ms)
  ✔ can import a source module (0.841459ms)
✔ typescript harness (1.687958ms)
ℹ tests 116
ℹ suites 31
ℹ pass 116
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 813.865958
npm notice run project-intelligence@0.6.1 test:unit
npm notice run node scripts/run-unit-tests.mjs
```

### 2026-07-23T04:00:49.796309+00:00 · verify / service

- 结果：failed
- 已执行测试数：0
- 验收标准：AC-07, AC-14
- 覆盖范围：`src/__tests__/install-hooks.test.ts`, `src/commands/adapter-blocks.ts`, `src/commands/adapters.ts`, `src/commands/agent-install.ts`, `src/commands/agent-rules.ts`, `src/commands/hooks.ts`, `src/commands/install.ts`
- Git 提交：`5f3ad66c9355153e765351291f5c8d8e3620ce22`
- 代码快照：`5a156e8aa5c37dcbee0083af26232cd56b3818393cc3472fc8c4290e38f3b2ba`
- 命令：`npm run typecheck && npm run build && npm run test:unit`

```text
npm notice run project-intelligence@0.6.1 typecheck
npm notice run tsc --noEmit -p tsconfig.json
Version synced to 0.6.1 across package.json, src/version.ts, dist/version.js, both plugin.json, and application.py.
npm notice run project-intelligence@0.6.1 build
npm notice run node scripts/gen-version.mjs && tsc -p tsconfig.json
0.02725ms)
✔ parseGlobal / splitArgv (0.342ms)
▶ withLock (in-process)
  ✔ blocks same-process re-entrant acquire (no deadlock) (61.352667ms)
  ✔ releases the lockfile after the critical section (0.338ms)
✔ withLock (in-process) (62.576ms)
▶ withLock (multi-process contention)
  ✔ grants exclusive access across child processes (624.662917ms)
✔ withLock (multi-process contention) (624.728917ms)
▶ paths
  ✔ toPosix converts separators (0.371583ms)
  ✔ normalizeBusinessPath strips leading ./ and normalizes (0.060791ms)
  ✔ isAbsolutePathLike detects posix, windows drive, unc (0.064834ms)
  ✔ resolveInside rejects traversal outside root (0.294834ms)
  ✔ expandUser leaves non-home paths alone (0.046125ms)
✔ paths (1.393834ms)
▶ atomic-write
  ✔ writes text with a trailing newline, UTF-8 preserved (6.762542ms)
  ✔ writes JSON without ascii escaping and creates parent dirs (5.517833ms)
  ✔ preserves existing file mode (8.541042ms)
  ✔ loadJson returns default on missing/corrupt (0.595125ms)
  ✔ loadJsonStrict raises on corrupt/non-object (0.775917ms)
✔ atomic-write (22.445125ms)
中文测试
{
  "name": "中文"
}
err 中文
▶ subprocess.spawn (argv)
  ✔ runs a successful command and captures output (44.385416ms)
  ✔ returns 127 when the binary is missing (1.155458ms)
  ✔ returns a non-zero code on argv usage error (14.294583ms)
✔ subprocess.spawn (argv) (60.377125ms)
▶ subprocess.which / commandExists
  ✔ finds node on PATH (0.271292ms)
  ✔ returns null for a missing command (0.172083ms)
✔ subprocess.which / commandExists (0.510334ms)
▶ subprocess.runShell (shell form)
  ✔ supports pipes and redirects (4.328792ms)
  ✔ supports environment variable expansion (4.85025ms)
  ✔ returns 0 for a true compound command (2.498584ms)
  ✔ surfaces non-zero exit of a failed command (2.528375ms)
✔ subprocess.runShell (shell form) (14.608208ms)
▶ output (UTF-8)
  ✔ print writes a UTF-8 line including Chinese (0.202791ms)
  ✔ printJson renders without ASCII escaping (0.06275ms)
  ✔ printError writes to stderr (0.034834ms)
✔ output (UTF-8) (0.354792ms)
▶ io.yaml
  ✔ parses flat key: value (0.642625ms)
  ✔ strips quoted values (0.048ms)
  ✔ coerces scalars (0.068583ms)
✔ io.yaml (0.794ms)
▶ io.markdown
  ✔ parses ATX headings with level and text (0.094458ms)
  ✔ normalizeHeading collapses whitespace (0.025375ms)
  ✔ hasMeaningfulContent rejects blank/placeholder (0.098209ms)
✔ io.markdown (0.247708ms)
已初始化 .project-intel，索引了 4 个文本文件。
init --dry-run 预览：
- 文件数：4
- 框架：未识别
- 前端组件：1
- 后端 API：0
- 标准推断：0 条
已初始化 .project-intel，索引了 4 个文本文件。
已刷新 .project-intel，索引了 13 个文本文件。
已初始化 .project-intel，索引了 4 个文本文件。
已初始化 .project-intel，索引了 4 个文本文件。
已初始化 .project-intel，索引了 4 个文本文件。
▶ init command
  ✔ writes the .project-intel layout (manifest/config/knowledge/status) (70.0585ms)
  ✔ --dry-run does not write files (29.165041ms)
  ✔ refresh re-writes without tooling (118.103709ms)
  ✔ strict + no-graph is a usage error (0.181542ms)
  ✔ ensureProjectIntelGitignore writes local-only rules (0.179541ms)
✔ init command (218.279833ms)
▶ doctor command
  ✔ reports node runtime, not python (0.727209ms)
  ✔ detects initialized state after init (61.929917ms)
✔ doctor command (62.754458ms)
▶ check command
  ✔ passes with no hard rules configured (89.868542ms)
  ✔ --dry-run does not write status (85.868458ms)
✔ check command (175.843125ms)
▶ standards inference
  ✔ infers PascalCase naming from >=3 pascal components (0.238667ms)
  ✔ infers backend Service suffix from >=3 services (0.092167ms)
  ✔ infers ui-pattern from redundancy candidates (0.044834ms)
✔ standards inference (0.428084ms)
▶ hard rules engine
  ✔ returns no violations with the empty default set (0.523459ms)
  ✔ surfaces a registered rule violation (0.078625ms)
✔ hard rules engine (0.633917ms)
▶ typescript harness
  ✔ runs a TypeScript assertion (0.342167ms)
  ✔ can import a source module (0.826208ms)
✔ typescript harness (1.660209ms)
ℹ tests 130
ℹ suites 36
ℹ pass 130
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 799.167542
npm notice run project-intelligence@0.6.1 test:unit
npm notice run node scripts/run-unit-tests.mjs
```

### 2026-07-23T04:20:30.209902+00:00 · verify / service

- 结果：failed
- 已执行测试数：0
- 验收标准：AC-05, AC-13
- 覆盖范围：`src/__tests__/requirement-command.test.ts`, `src/__tests__/state-machine.test.ts`, `src/commands/requirement.ts`, `src/requirements/layout.ts`, `src/requirements/state-machine.ts`
- Git 提交：`5f3ad66c9355153e765351291f5c8d8e3620ce22`
- 代码快照：`4a57742f7ef8354bb728ecb149be6d7052a9e478500c8a807b19b7645a4bb815`
- 命令：`npm run typecheck && npm run build && npm run test:unit`

```text
npm notice run project-intelligence@0.6.1 typecheck
npm notice run tsc --noEmit -p tsconfig.json
Version synced to 0.6.1 across package.json, src/version.ts, dist/version.js, both plugin.json, and application.py.
npm notice run project-intelligence@0.6.1 build
npm notice run node scripts/gen-version.mjs && tsc -p tsconfig.json
ommand (2.686667ms)
  ✔ surfaces non-zero exit of a failed command (2.544834ms)
✔ subprocess.runShell (shell form) (16.294583ms)
▶ output (UTF-8)
  ✔ print writes a UTF-8 line including Chinese (0.197458ms)
  ✔ printJson renders without ASCII escaping (0.062709ms)
  ✔ printError writes to stderr (0.034875ms)
✔ output (UTF-8) (0.34825ms)
▶ io.yaml
  ✔ parses flat key: value (0.674ms)
  ✔ strips quoted values (0.050917ms)
  ✔ coerces scalars (0.074833ms)
✔ io.yaml (0.835792ms)
▶ io.markdown
  ✔ parses ATX headings with level and text (0.101417ms)
  ✔ normalizeHeading collapses whitespace (0.025958ms)
  ✔ hasMeaningfulContent rejects blank/placeholder (0.097542ms)
✔ io.markdown (0.256875ms)
已初始化 .project-intel，索引了 4 个文本文件。
init --dry-run 预览：
- 文件数：4
- 框架：未识别
- 前端组件：1
- 后端 API：0
- 标准推断：0 条
已初始化 .project-intel，索引了 4 个文本文件。
已刷新 .project-intel，索引了 13 个文本文件。
已初始化 .project-intel，索引了 4 个文本文件。
已初始化 .project-intel，索引了 4 个文本文件。
已初始化 .project-intel，索引了 4 个文本文件。
▶ init command
  ✔ writes the .project-intel layout (manifest/config/knowledge/status) (116.108417ms)
  ✔ --dry-run does not write files (31.59225ms)
  ✔ refresh re-writes without tooling (138.665292ms)
  ✔ strict + no-graph is a usage error (0.194875ms)
  ✔ ensureProjectIntelGitignore writes local-only rules (0.180958ms)
✔ init command (287.393458ms)
▶ doctor command
  ✔ reports node runtime, not python (0.717292ms)
  ✔ detects initialized state after init (62.788917ms)
✔ doctor command (63.610042ms)
▶ check command
  ✔ passes with no hard rules configured (92.812666ms)
  ✔ --dry-run does not write status (87.138375ms)
✔ check command (180.057917ms)
▶ standards inference
  ✔ infers PascalCase naming from >=3 pascal components (0.245334ms)
  ✔ infers backend Service suffix from >=3 services (0.087542ms)
  ✔ infers ui-pattern from redundancy candidates (0.040791ms)
✔ standards inference (0.4305ms)
▶ hard rules engine
  ✔ returns no violations with the empty default set (0.530125ms)
  ✔ surfaces a registered rule violation (0.083667ms)
✔ hard rules engine (0.647209ms)
▶ requirement command dispatcher
  ✔ status returns state for a created requirement (8.232416ms)
  ✔ acceptance set persists AC-01..AC-02 (8.942875ms)
  ✔ test-contract set requires --kind and --report-action (12.886083ms)
  ✔ ready -> begin through the dispatcher (32.740958ms)
  ✔ reopen after close (29.965ms)
  ✔ generate creates a placeholder artifact file (11.249833ms)
  ✔ rejects missing --requirement-id (3.675542ms)
✔ requirement command dispatcher (108.913917ms)
▶ requirement layout
  ✔ artifactFilename maps known types (0.07625ms)
  ✔ ARTIFACT_FILES covers the v2 types (0.055792ms)
  ✔ migrateLayout reports not-migrated when no legacy archive (2.654708ms)
✔ requirement layout (2.901792ms)
▶ typescript harness
  ✔ runs a TypeScript assertion (0.419041ms)
  ✔ can import a source module (0.95875ms)
✔ typescript harness (2.071708ms)
▶ requirement state machine
  ✔ createRequirement writes a v2 manifest at draft (10.717625ms)
  ✔ createRequirement is idempotent on matching identity (7.770167ms)
  ✔ createRequirement rejects name mismatch on existing id (7.728292ms)
  ✔ assertTransition enforces legal transitions (0.082166ms)
  ✔ ready gate: requires designed state + non-empty resolution + AC (58.653334ms)
  ✔ full lifecycle: ready -> begin -> test -> review -> finish -> close (48.891292ms)
  ✔ finish gate rejects without passing test evidence (8.050625ms)
  ✔ review changes-requested does not advance to reviewed (11.827917ms)
  ✔ reopen closed -> implementing (13.004792ms)
  ✔ setAcceptanceCriteria + setTestContract persist (12.034209ms)
  ✔ manifest is written under the v2 direct layout (no by-id) (4.075792ms)
  ✔ STATES includes the full v2 lifecycle (0.052917ms)
  ✔ loadRequirement raises on missing archive (3.708334ms)
  ✔ revision increments on each mutate (29.086375ms)
✔ requirement state machine (216.556083ms)
ℹ tests 154
ℹ suites 39
ℹ pass 154
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 841.864709
npm notice run project-intelligence@0.6.1 test:unit
npm notice run node scripts/run-unit-tests.mjs
```

### 2026-07-23T06:04:33.618377+00:00 · verify / service

- 结果：failed
- 已执行测试数：0
- 验收标准：AC-11
- 覆盖范围：`src/__tests__/test-evidence.test.ts`, `src/commands/test.ts`, `src/testing/render.ts`, `src/testing/sanitize.ts`
- Git 提交：`5f3ad66c9355153e765351291f5c8d8e3620ce22`
- 代码快照：`ab3ec916d9421026d9477494bd4aea1674aad047f3dfb64d9efeaadfa50fc70c`
- 命令：`npm run typecheck && npm run build && npm run test:unit`

```text
npm notice run project-intelligence@0.6.1 typecheck
npm notice run tsc --noEmit -p tsconfig.json
Version synced to 0.6.1 across package.json, src/version.ts, dist/version.js, both plugin.json, and application.py.
npm notice run project-intelligence@0.6.1 build
npm notice run node scripts/gen-version.mjs && tsc -p tsconfig.json
eck command (178.2475ms)
▶ standards inference
  ✔ infers PascalCase naming from >=3 pascal components (0.347167ms)
  ✔ infers backend Service suffix from >=3 services (0.118041ms)
  ✔ infers ui-pattern from redundancy candidates (0.048083ms)
✔ standards inference (0.570125ms)
▶ hard rules engine
  ✔ returns no violations with the empty default set (0.557917ms)
  ✔ surfaces a registered rule violation (0.082875ms)
✔ hard rules engine (0.67475ms)
▶ requirement command dispatcher
  ✔ status returns state for a created requirement (11.519958ms)
  ✔ acceptance set persists AC-01..AC-02 (20.20125ms)
  ✔ test-contract set requires --kind and --report-action (33.783541ms)
  ✔ ready -> begin through the dispatcher (58.58725ms)
  ✔ reopen after close (59.383834ms)
  ✔ generate creates a placeholder artifact file (11.905375ms)
  ✔ rejects missing --requirement-id (0.140292ms)
✔ requirement command dispatcher (196.454917ms)
▶ requirement layout
  ✔ artifactFilename maps known types (0.073ms)
  ✔ ARTIFACT_FILES covers the v2 types (0.054875ms)
  ✔ migrateLayout reports not-migrated when no legacy archive (0.238666ms)
✔ requirement layout (0.486417ms)
▶ typescript harness
  ✔ runs a TypeScript assertion (0.526083ms)
  ✔ can import a source module (1.359375ms)
✔ typescript harness (2.839083ms)
▶ requirement state machine
  ✔ createRequirement writes a v2 manifest at draft (11.666125ms)
  ✔ createRequirement is idempotent on matching identity (5.546042ms)
  ✔ createRequirement rejects name mismatch on existing id (7.989083ms)
  ✔ assertTransition enforces legal transitions (0.112541ms)
  ✔ ready gate: requires designed state + non-empty resolution + AC (61.335542ms)
  ✔ full lifecycle: ready -> begin -> test -> review -> finish -> close (114.155125ms)
  ✔ finish gate rejects without passing test evidence (8.882834ms)
  ✔ review changes-requested does not advance to reviewed (12.755625ms)
  ✔ reopen closed -> implementing (11.963708ms)
  ✔ setAcceptanceCriteria + setTestContract persist (11.950459ms)
  ✔ manifest is written under the v2 direct layout (no by-id) (3.853875ms)
  ✔ STATES includes the full v2 lifecycle (0.068667ms)
  ✔ loadRequirement raises on missing archive (0.143167ms)
  ✔ revision increments on each mutate (12.116209ms)
✔ requirement state machine (263.631209ms)
▶ sanitizeText
  ✔ redacts header values (Authorization/Cookie) (3.289584ms)
  ✔ redacts key=value secrets (0.188ms)
  ✔ redacts raw token formats (0.133667ms)
  ✔ redacts database URLs and URL userinfo (0.107167ms)
  ✔ redacts PRC identity and mainland mobile (4.0715ms)
  ✔ preserves benign Chinese text (0.153584ms)
✔ sanitizeText (8.977875ms)
▶ manualEvidenceValid
  ✔ rejects generic phrases (0.227083ms)
  ✔ accepts specific descriptions (0.132875ms)
✔ manualEvidenceValid (0.560167ms)
▶ executedTestCount
  ✔ extracts unittest 'Ran N tests' (0.292166ms)
  ✔ extracts 'N passed' (0.172125ms)
  ✔ returns 0 for empty formatter output (AC-11) (0.041917ms)
✔ executedTestCount (0.615792ms)
▶ phasePassed
  ✔ green requires exit 0 AND a real test count (0.107ms)
  ✔ red requires non-zero exit + expected-failure match (0.08175ms)
  ✔ manual uses manualEvidenceValid (0.037542ms)
✔ phasePassed (0.263417ms)
▶ test command (AC-11: rejects forged pass)
  ✔ records green evidence when a real test passes (25.806542ms)
  ✔ rejects a formatter pass as evidence (no test count) (25.851708ms)
  ✔ advances requirement state via recordTestResult (75.973834ms)
✔ test command (AC-11: rejects forged pass) (127.839042ms)
▶ evaluateTestEvidence
  ✔ ready=true when no files changed (6.993584ms)
  ✔ ready=false when task mismatch (12.577ms)
✔ evaluateTestEvidence (19.646291ms)
▶ renderTestEvidence
  ✔ renders a markdown table with the task (0.082291ms)
✔ renderTestEvidence (0.1135ms)
▶ COMMAND_ERROR_CODES
  ✔ includes the gate-relevant exit codes (0.035083ms)
✔ COMMAND_ERROR_CODES (0.056416ms)
ℹ tests 175
ℹ suites 47
ℹ pass 175
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1061.908625
npm notice run project-intelligence@0.6.1 test:unit
npm notice run node scripts/run-unit-tests.mjs
```

### 2026-07-23T06:13:22.187867+00:00 · verify / service

- 结果：failed
- 已执行测试数：0
- 验收标准：AC-05, AC-06, AC-11
- 覆盖范围：`src/__tests__/review-finish-graph.test.ts`, `src/commands/finish.ts`, `src/commands/graph-tools.ts`, `src/commands/maintain.ts`, `src/commands/query.ts`, `src/commands/review.ts`, `src/graph/sources.ts`
- Git 提交：`5f3ad66c9355153e765351291f5c8d8e3620ce22`
- 代码快照：`0cb101466113d6bdf8148c8988eae68ea17b88daa07524e82895879f6955f3b6`
- 命令：`npm run typecheck && npm run build && npm run test:unit`

```text
npm notice run project-intelligence@0.6.1 typecheck
npm notice run tsc --noEmit -p tsconfig.json
Version synced to 0.6.1 across package.json, src/version.ts, dist/version.js, both plugin.json, and application.py.
npm notice run project-intelligence@0.6.1 build
npm notice run node scripts/gen-version.mjs && tsc -p tsconfig.json
EQ-R2 → verified）
review：approved（需求 REQ-F → reviewed）
finish：需求 REQ-F 已完成（→ finished）
已刷新 .project-intel，索引了 2 个文本文件。
maintain：已刷新 .project-intel 并关闭需求 REQ-M（→ closed）
▶ review / finish / maintain commands (3.F)
  ✔ review approved advances verified -> reviewed (32.845209ms)
  ✔ review changes-requested stays verified (47.591333ms)
  ✔ finish writes closure-summary and advances reviewed -> finished (81.025375ms)
  ✔ finish rejects without approved review (AC-11 gate) (30.8005ms)
  ✔ maintain refreshes facts and closes the requirement (139.507709ms)
✔ review / finish / maintain commands (3.F) (332.73025ms)
▶ graph sources (3.G.1)
  ✔ gitnexusSummary missing when no .gitnexus (4.145583ms)
  ✔ gitnexusSummary present with valid meta (0.428375ms)
  ✔ understandSummary present with non-empty nodes (3.627ms)
  ✔ detectGraphSources returns both names (0.780042ms)
  ✔ understandGraphSummary aggregates domains (3.654542ms)
✔ graph sources (3.G.1) (13.00975ms)
▶ graph-tools + query commands (3.G.2)
  ✔ graph-tools reports source statuses (3.502583ms)
  ✔ query searches standards text (3.839292ms)
✔ graph-tools + query commands (3.G.2) (7.432542ms)
▶ typescript harness
  ✔ runs a TypeScript assertion (0.381833ms)
  ✔ can import a source module (1.400167ms)
✔ typescript harness (2.337792ms)
▶ requirement state machine
  ✔ createRequirement writes a v2 manifest at draft (18.94525ms)
  ✔ createRequirement is idempotent on matching identity (8.812417ms)
  ✔ createRequirement rejects name mismatch on existing id (8.17ms)
  ✔ assertTransition enforces legal transitions (0.108417ms)
  ✔ ready gate: requires designed state + non-empty resolution + AC (72.356666ms)
  ✔ full lifecycle: ready -> begin -> test -> review -> finish -> close (96.024083ms)
  ✔ finish gate rejects without passing test evidence (15.912417ms)
  ✔ review changes-requested does not advance to reviewed (12.997375ms)
  ✔ reopen closed -> implementing (30.542ms)
  ✔ setAcceptanceCriteria + setTestContract persist (42.294667ms)
  ✔ manifest is written under the v2 direct layout (no by-id) (7.940625ms)
  ✔ STATES includes the full v2 lifecycle (0.095125ms)
  ✔ loadRequirement raises on missing archive (3.393708ms)
  ✔ revision increments on each mutate (18.435167ms)
✔ requirement state machine (337.217958ms)
▶ sanitizeText
  ✔ redacts header values (Authorization/Cookie) (2.719792ms)
  ✔ redacts key=value secrets (0.126833ms)
  ✔ redacts raw token formats (0.073583ms)
  ✔ redacts database URLs and URL userinfo (0.059875ms)
  ✔ redacts PRC identity and mainland mobile (1.802042ms)
  ✔ preserves benign Chinese text (0.056416ms)
✔ sanitizeText (5.718417ms)
▶ manualEvidenceValid
  ✔ rejects generic phrases (0.121125ms)
  ✔ accepts specific descriptions (0.117625ms)
✔ manualEvidenceValid (0.639084ms)
▶ executedTestCount
  ✔ extracts unittest 'Ran N tests' (0.501958ms)
  ✔ extracts 'N passed' (0.161375ms)
  ✔ returns 0 for empty formatter output (AC-11) (0.045708ms)
✔ executedTestCount (0.909083ms)
▶ phasePassed
  ✔ green requires exit 0 AND a real test count (0.098416ms)
  ✔ red requires non-zero exit + expected-failure match (0.0625ms)
  ✔ manual uses manualEvidenceValid (0.032125ms)
✔ phasePassed (0.24975ms)
▶ test command (AC-11: rejects forged pass)
  ✔ records green evidence when a real test passes (32.893792ms)
  ✔ rejects a formatter pass as evidence (no test count) (31.62275ms)
  ✔ advances requirement state via recordTestResult (67.809583ms)
✔ test command (AC-11: rejects forged pass) (132.451125ms)
▶ evaluateTestEvidence
  ✔ ready=true when no files changed (0.349208ms)
  ✔ ready=false when task mismatch (4.173416ms)
✔ evaluateTestEvidence (4.591917ms)
▶ renderTestEvidence
  ✔ renders a markdown table with the task (0.086417ms)
✔ renderTestEvidence (0.117958ms)
▶ COMMAND_ERROR_CODES
  ✔ includes the gate-relevant exit codes (0.033042ms)
✔ COMMAND_ERROR_CODES (0.051625ms)
ℹ tests 187
ℹ suites 50
ℹ pass 187
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1237.685708
npm notice run project-intelligence@0.6.1 test:unit
npm notice run node scripts/run-unit-tests.mjs
```
