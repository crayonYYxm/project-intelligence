# LOCAL-20260728-114105 测试报告

- 测试类型：unit
- 阶段：red
- 结果：passed
- 验收标准：AC-01,AC-02,AC-03,AC-04,AC-05,AC-06,AC-07
- 文件范围：evals/skill-behavior-scenarios.json, scripts/validate-skill-evals.mjs, src/__tests__/install-hooks.test.ts, src/__tests__/requirement-command.test.ts, src/__tests__/state-machine.test.ts, src/__tests__/zcode-compat.test.ts

## 执行结果

### node --import tsx --test src/__tests__/requirement-command.test.ts src/__tests__/state-machine.test.ts src/__tests__/install-hooks.test.ts src/__tests__/zcode-compat.test.ts

- exitCode: 1
- executedCount: 82

```text
▶ adapter block management
  ✔ rejects paths outside the allowed set (0.584958ms)
  ✔ replaceSingleManagedBlock creates then updates (0.184625ms)
  ✔ upsert then remove a managed block (0.727625ms)
✔ adapter block management (1.90375ms)
▶ adapters command family
  ✔ apply writes codex + claude blocks; status reports current (1.0355ms)
  ✔ preview is dry-run (no files written) (0.289166ms)
  ✔ remove clears blocks (0.475ms)
  ✔ status --check returns non-zero when not current (0.25675ms)
  ✔ adapterTargets both returns 3 targets (codex, claude, claude-nested) (0.824167ms)
  ✖ managed Codex and Claude rules require four documents and design-derived specs (1.619875ms)
✖ adapters command family (4.689916ms)
▶ top-level install command
  ✔ creates .claude/ and applies adapters; --hooks writes templates (1.0595ms)
✔ top-level install command (1.157292ms)
▶ agent install command
  ✔ agentInstallCommands builds codex+claude for all (0.085083ms)
  ✔ --dry-run classifies present when cli exists, missing otherwise (0.539542ms)
  ✔ rejects invalid target (0.115458ms)
✔ agent install command (0.792125ms)
▶ git hooks (AC-07: no python3)
  ✔ hook body calls project-intel (Node CLI), never python3 (0.044916ms)
  ✔ writeHookTemplates writes 3 hooks + README under .project-intel/hooks (0.491042ms)
✔ git hooks (AC-07: no python3) (0.582333ms)
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ requirement command dispatcher
  ✔ status returns state for a created requirement (29.61075ms)
  ✔ plan writes into the resolved id-title requirement directory (27.646791ms)
  ✖ intake defaults both mandatory document actions to generate (16.426666ms)
  ✖ intake uses a supplied design as the source while generating the missing spec (0.545292ms)
  ✖ intake rejects later for mandatory lifecycle documents (16.171042ms)
  ✔ intake requires a valid user supplied version date (0.229208ms)
  ✔ task-only intake remains a read-only analysis without a version date (0.093ms)
  ✔ task intake with a version date registers a dated LOCAL requirement (16.623625ms)
  ✔ acceptance set persists AC-01..AC-02 (21.021375ms)
  ✔ query reads v2 and legacy by-id archives and supports --file (22.012958ms)
  ✔ test-contract set requires --kind and --report-action (26.085083ms)
  ✔ test-contract register validates and normalizes a structured report path (26.588917ms)
  ✔ ready -> begin through the dispatcher (350.962166ms)
  ✔ reopen after close (24.901875ms)
  ✔ generate enforces lifecycle order and creates a requirement scaffold (42.156083ms)
  ✔ generate refuses implicit overwrite and --replace really rebuilds the scaffold (65.294959ms)
  ✔ rejects missing --requirement-id (3.306208ms)
  ✔ add persists artifact registration into the manifest (133.227084ms)
  ✔ rejects arbitrary delivery-document content (96.8605ms)
  ✔ design registration rejects missing source evidence paths (129.441417ms)
  ✔ design registration ignores symbols that exist only in comments or strings (81.734125ms)
  ✔ add registers a structured test report as current requirement evidence (302.236292ms)
  ✔ diagnose records a Bug root cause (ticketKind=bug) (47.911667ms)
  ✔ diagnose rejects missing source evidence paths (36.106458ms)
  ✔ diagnose rejects symbols that only appear in comments or strings (25.218375ms)
  ✔ diagnose rejects non-bug requirements (27.371834ms)
  ✖ defer rejects all four mandatory lifecycle documents (24.946292ms)
  ✔ resolve-finding marks a review finding resolved (24.956083ms)
  ✔ resolve-finding rejects unknown finding IDs (21.530584ms)
✖ requirement command dispatcher (1642.529458ms)
▶ requirement layout
  ✔ artifactFilename maps known types (0.089833ms)
  ✔ ARTIFACT_FILES covers the v2 types (0.039833ms)
  ✔ migrateLayout reports not-migrated when no legacy archive (0.1415ms)
  ✔ migrateLayout copies legacy by-id archives and rewrites manifest paths (1.273333ms)
✔ requirement layout (1.915334ms)
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ requirement state machine
  ✖ createRequirement writes a v2 manifest at draft (31.039333ms)
  ✖ createRequirement rejects later for mandatory lifecycle documents (19.439458ms)
  ✔ createRequirement is idempotent on matching identity (18.520125ms)
  ✔ createRequirement rejects name mismatch on existing id (16.100834ms)
  ✔ createRequirement canonicalizes numeric ids by ticket kind (30.584542ms)
  ✔ createRequirement rejects conflicting duplicate intake fields (18.09775ms)
  ✔ assertTransition enforces legal transitions (0.096625ms)
  ✔ ready gate: requires designed state + non-empty resolution + AC (365.802375ms)
  ✔ ready revalidates requirement.md against the latest manifest acceptance criteria (280.626875ms)
  ✔ full lifecycle: ready -> begin -> test -> review -> finish -> close (483.738583ms)
  ✔ finish gate rejects without passing test evidence (334.792417ms)
  ✔ finish gate rejects without a passed review round (357.231125ms)
  ✔ review failed does not advance to reviewed (351.348208ms)
  ✔ reopen closed -> draft (returns to document state, not implementing) (24.152208ms)
  ✔ reopen only reuses documents that still match their recorded digest (404.172833ms)
  ✔ setAcceptanceCriteria + setTestContract persist (23.841583ms)
  ✖ test contracts cannot defer the mandatory test document (23.983375ms)
  ✖ recordLater rejects every mandatory lifecycle document (23.851084ms)
  ✔ manifest is written under an id-title directory with a cross-platform safe title (16.05525ms)
  ✔ normalizes user supplied version dates and writes dated requirement directories (30.990959ms)
  ✔ limits id-title directories by UTF-8 byte length (15.189292ms)
  ✔ includes the date prefix in the UTF-8 directory byte limit (0.090125ms)
  ✔ numeric bug ids use the canonical id together with the title (15.767584ms)
  ✔ generated lifecycle docs use id-title document filenames (46.984625ms)
  ✔ generated requirement, design, and test docs follow the sample document standards (52.047125ms)
  ✔ loadRequirement rejects ambiguous id-title directories (0.533542ms)
  ✔ createRequirement does not overwrite an unrecognized id-title manifest (12.724667ms)
  ✔ STATES includes the full v2 lifecycle (0.074083ms)
  ✔ loadRequirement raises on missing archive (0.323792ms)
  ✔ revision increments on each mutate (26.250458ms)
  ✔ mutate keeps a legacy v1 manifest in the legacy by-id directory (4.947334ms)
✖ requirement state machine (3030.542666ms)
▶ ZCode plugin compatibility
  ✔ ships a root marketplace and native ZCode plugin manifest (0.928709ms)
  ✖ ships the shared mandatory four-document workflow used by ZCode (1.94725ms)
  ✔ contains no symbolic links in tracked distribution paths (11.135458ms)
✖ ZCode plugin compatibility (14.543958ms)
ℹ tests 82
ℹ suites 9
ℹ pass 72
ℹ fail 10
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 3238.584459

✖ failing tests:

test at src/__tests__/install-hooks.test.ts:5:2295
✖ managed Codex and Claude rules require four documents and design-derived specs (1.619875ms)
  AssertionError [ERR_ASSERTION]: The input did not match the regular expression /四类必选文档/. Input:
  
  '## Project Intelligence\n' +
    '\n' +
    'This repository uses `.project-intel/` for project facts, standards, requirement history, test evidence, review, finish, and maintenance.\n' +
    '\n' +
    'Use the plugin skill namespace when available:\n' +
    '\n' +
    '- Implementation or bug work: `$project-intelligence:project-intake` → `$project-intelligence:project-spec` → `$project-intelligence:project-design` → `$project-intelligence:project-test` → `$project-intelligence:project-task`.\n' +
    '- Debugging: `$project-intelligence:project-debug` before fixing.\n' +
    '- Review only: `$project-intelligence:project-review`; do not finish or maintain from review.\n' +
    '- Completion: `$project-intelligence:project-finish`; run `$project-intelligence:project-maintain` only after finish succeeds.\n' +
    '- Knowledge, standards, quality, refresh, and init use their matching `$project-intelligence:*` skills.\n' +
    '\n' +
    "For requirement-level work, carry one requirement ID through every CLI call. Ask the user for a version date and pass it to intake with `--version-date`; do not silently use today's date. New archives keep readable files under `.project-intel/requirements/<YYYY-MM-DD>-<id>-<title>/`; legacy `<id>-<title>/` and `<id>/` archives remain readable. Each new archive contains titled Markdown files such as `<id>-<title>-需求文档.md` or `<id>-<title>-Bug文档.md`, `<id>-<title>-设计文档.md`, optional `<id>-<title>-实施计划.md`, `<id>-<title>-测试文档.md`, `<id>-<title>-收口文档.md`, plus `manifest.json`. Legacy short names remain readable.\n" +
    '\n' +
    '`project-intel init` and `project-intel refresh` are fact-only by default. Root adapters are changed only by explicit `project-intel adapters apply`, `project-intel install`, or `project-intel refresh --adapters`.'
  
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/install-hooks.test.ts:105:14)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Suite.processPendingSubtests (node:internal/test_runner/test:960:18)
      at Test.postRun (node:internal/test_runner/test:1522:19)
      at Test.run (node:internal/test_runner/test:1447:12)
      at async Suite.processPendingSubtests (node:internal/test_runner/test:960:7) {
    generatedMessage: true,
    code: 'ERR_ASSERTION',
    actual: "## Project Intelligence\n\nThis repository uses `.project-intel/` for project facts, standards, requirement history, test evidence, review, finish, and maintenance.\n\nUse the plugin skill namespace when available:\n\n- Implementation or bug work: `$project-intelligence:project-intake` → `$project-intelligence:project-spec` → `$project-intelligence:project-design` → `$project-intelligence:project-test` → `$project-intelligence:project-task`.\n- Debugging: `$project-intelligence:project-debug` before fixing.\n- Review only: `$project-intelligence:project-review`; do not finish or maintain from review.\n- Completion: `$project-intelligence:project-finish`; run `$project-intelligence:project-maintain` only after finish succeeds.\n- Knowledge, standards, quality, refresh, and init use their matching `$project-intelligence:*` skills.\n\nFor requirement-level work, carry one requirement ID through every CLI call. Ask the user for a version date and pass it to intake with `--version-date`; do not silently use today's date. New archives keep readable files under `.project-intel/requirements/<YYYY-MM-DD>-<id>-<title>/`; legacy `<id>-<title>/` and `<id>/` archives remain readable. Each new archive contains titled Markdown files such as `<id>-<title>-需求文档.md` or `<id>-<title>-Bug文档.md`, `<id>-<title>-设计文档.md`, optional `<id>-<title>-实施计划.md`, `<id>-<title>-测试文档.md`, `<id>-<title>-收口文档.md`, plus `manifest.json`. Legacy short names remain readable.\n\n`project-intel init` and `project-intel refresh` are fact-only by default. Root adapters are changed only by explicit `project-intel adapters apply`, `project-intel install`, or `project-intel refresh --adapters`.",
    expected: /四类必选文档/,
    operator: 'match',
    diff: 'simple'
  }

test at src/__tests__/requirement-command.test.ts:1:1597
✖ intake defaults both mandatory document actions to generate (16.426666ms)
  TypeError: Cannot read properties of undefined (reading 'action')
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/requirement-command.test.ts:66:88)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Suite.processPendingSubtests (node:internal/test_runner/test:960:18)
      at Test.postRun (node:internal/test_runner/test:1522:19)
      at Test.run (node:internal/test_runner/test:1447:12)
      at async Suite.processPendingSubtests (node:internal/test_runner/test:960:7)

test at src/__tests__/requirement-command.test.ts:1:2394
✖ intake uses a supplied design as the source while generating the missing spec (0.545292ms)
  Error [RequirementError]: 只有 action=register 时才能提供已有文档路径。
      at createRequirement (/Users/xumeng/Desktop/code/project-intelligence/src/requirements/state-machine.ts:309:28)
      at runIntake (/Users/xumeng/Desktop/code/project-intelligence/src/commands/orchestration.ts:92:13)
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/requirement-command.test.ts:74:5)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Suite.processPendingSubtests (node:internal/test_runner/test:960:18)
      at Test.postRun (node:internal/test_runner/test:1522:19)
      at Test.run (node:internal/test_runner/test:1447:12)
      at async Suite.processPendingSubtests (node:internal/test_runner/test:960:7) {
    exitCode: 2
  }

test at src/__tests__/requirement-command.test.ts:1:3284
✖ intake rejects later for mandatory lifecycle documents (16.171042ms)
  AssertionError [ERR_ASSERTION]: Missing expected exception.
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/requirement-command.test.ts:94:12)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Suite.processPendingSubtests (node:internal/test_runner/test:960:18)
      at Test.postRun (node:internal/test_runner/test:1522:19)
      at Test.run (node:internal/test_runner/test:1447:12)
      at async Suite.processPendingSubtests (node:internal/test_runner/test:960:7) {
    generatedMessage: false,
    code: 'ERR_ASSERTION',
    actual: undefined,
    expected: /必选|later/,
    operator: 'throws',
    diff: 'simple'
  }

test at src/__tests__/requirement-command.test.ts:1:17879
✖ defer rejects all four mandatory lifecycle documents (24.946292ms)
  AssertionError [ERR_ASSERTION]: Missing expected exception.
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/requirement-command.test.ts:473:14)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Suite.processPendingSubtests (node:internal/test_runner/test:960:18)
      at Test.postRun (node:internal/test_runner/test:1522:19)
      at Test.run (node:internal/test_runner/test:1447:12)
      at async Suite.processPendingSubtests (node:internal/test_runner/test:960:7) {
    generatedMessage: false,
    code: 'ERR_ASSERTION',
    actual: undefined,
    expected: /必选|不能延期|不支持 defer/,
    operator: 'throws',
    diff: 'simple'
  }

test at src/__tests__/state-machine.test.ts:1:1159
✖ createRequirement writes a v2 manifest at draft (31.039333ms)
  TypeError: Cannot read properties of undefined (reading 'action')
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/state-machine.test.ts:58:81)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Test.start (node:internal/test_runner/test:1242:17)
      at node:internal/test_runner/test:1867:71
      at node:internal/per_context/primordials:466:82
      at new Promise (<anonymous>)
      at new SafePromise (node:internal/per_context/primordials:435:3)
      at node:internal/per_context/primordials:466:9
      at Array.map (<anonymous>)

test at src/__tests__/state-machine.test.ts:1:1624
✖ createRequirement rejects later for mandatory lifecycle documents (19.439458ms)
  AssertionError [ERR_ASSERTION]: Missing expected exception.
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/state-machine.test.ts:64:12)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Suite.processPendingSubtests (node:internal/test_runner/test:960:18)
      at Test.postRun (node:internal/test_runner/test:1522:19)
      at Test.run (node:internal/test_runner/test:1447:12)
      at async Promise.all (index 0)
      at async Suite.run (node:internal/test_runner/test:1869:7)
      at async startSubtestAfterBootstrap (node:internal/test_runner/harness:387:3) {
    generatedMessage: false,
    code: 'ERR_ASSERTION',
    actual: undefined,
    expected: /必选|later/,
    operator: 'throws',
    diff: 'simple'
  }

test at src/__tests__/state-machine.test.ts:1:7086
✖ test contracts cannot defer the mandatory test document (23.983375ms)
  AssertionError [ERR_ASSERTION]: Missing expected exception.
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/state-machine.test.ts:208:12)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Suite.processPendingSubtests (node:internal/test_runner/test:960:18)
      at Test.postRun (node:internal/test_runner/test:1522:19)
      at Test.run (node:internal/test_runner/test:1447:12)
      at async Suite.processPendingSubtests (node:internal/test_runner/test:960:7) {
    generatedMessage: false,
    code: 'ERR_ASSERTION',
    actual: undefined,
    expected: /必选|later/,
    operator: 'throws',
    diff: 'simple'
  }

test at src/__tests__/state-machine.test.ts:1:7499
✖ recordLater rejects every mandatory lifecycle document (23.851084ms)
  AssertionError [ERR_ASSERTION]: Missing expected exception.
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/state-machine.test.ts:231:14)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Suite.processPendingSubtests (node:internal/test_runner/test:960:18)
      at Test.postRun (node:internal/test_runner/test:1522:19)
      at Test.run (node:internal/test_runner/test:1447:12)
      at async Suite.processPendingSubtests (node:internal/test_runner/test:960:7) {
    generatedMessage: false,
    code: 'ERR_ASSERTION',
    actual: undefined,
    expected: /必选|不能延期|不支持 defer/,
    operator: 'throws',
    diff: 'simple'
  }

test at src/__tests__/zcode-compat.test.ts:1:1199
✖ ships the shared mandatory four-document workflow used by ZCode (1.94725ms)
  AssertionError [ERR_ASSERTION]: The input did not match the regular expression /four durable lifecycle documents are mandatory/i. Input:
  
  '---\n' +
    'name: project-intake\n' +
    'description: Use at the start of implementation intent to register and route a Bug or Requirement before any code or test execution. 我要做一个需求, 实现这个功能, 修复这个 Bug, 接入这个需求, 需求入口分析, 需求分流, readiness, quick/standard/complex. Do not use for read-only knowledge, standalone design-only, review-only, plugin installation, or project-fact refresh requests.\n' +
    '---\n' +
    '\n' +
    '# Project Intake\n' +
    '\n' +
    'Use this before code changes when a request may become implementation work.\n' +
    '\n' +
    '1. Read `.project-intel/manifest.json` when it exists. If facts are missing, run read-only `project-intel doctor` or `project-intel init --dry-run`; run `init` only after the user explicitly authorizes initialization.\n' +
    '2. Run the intake analysis without writing a file by default:\n' +
    '\n' +
    '```bash\n' +
    'project-intel intake --task "<requirement>"\n' +
    '```\n' +
    '\n' +
    '3. Classify the track:\n' +
    '   - `quick`: small local behavior, copy, style, config, or low-risk fix.\n' +
    '   - `standard`: normal feature/change that needs lightweight spec and plan in context.\n' +
    '   - `complex`: cross-module, API/data/auth/payment/cache/async/release/compatibility/security/performance work.\n' +
    '4. If readiness is `needs-clarifi
```
