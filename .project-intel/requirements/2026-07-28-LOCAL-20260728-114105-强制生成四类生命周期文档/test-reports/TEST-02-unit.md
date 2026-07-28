# LOCAL-20260728-114105 测试报告

- 测试类型：unit
- 阶段：red
- 结果：passed
- 验收标准：AC-01,AC-02,AC-03,AC-04,AC-05,AC-06,AC-07
- 文件范围：README.md, docs/project-intelligence-guide.md, evals/skill-behavior-scenarios.json, plugins/project-intelligence/assets/plugin-intro.html, plugins/project-intelligence/skills/project-debug/SKILL.md, plugins/project-intelligence/skills/project-design/SKILL.md, plugins/project-intelligence/skills/project-finish/SKILL.md, plugins/project-intelligence/skills/project-intake/SKILL.md, plugins/project-intelligence/skills/project-spec/SKILL.md, plugins/project-intelligence/skills/project-test/SKILL.md, scripts/validate-skill-evals.mjs, src/__tests__/cli-contract.test.ts, src/__tests__/install-hooks.test.ts, src/__tests__/requirement-command.test.ts, src/__tests__/state-machine.test.ts, src/__tests__/zcode-compat.test.ts, src/commands/agent-rules.ts, src/commands/init.ts, src/commands/requirement.ts, src/requirements/state-machine.ts

## 执行结果

### node --import tsx --test src/__tests__/state-machine.test.ts src/__tests__/requirement-command.test.ts src/__tests__/cli-contract.test.ts

- exitCode: 1
- executedCount: 86

```text
▶ cli snapshot contract (AC-02)
  ✔ loads a well-formed snapshot (0.715ms)
  ✔ captured every top-level command's help (0.622625ms)
  ✔ pins the JSON envelope shape on every probe (0.192417ms)
  ✔ the version command exits 0 and prints a semver (0.153042ms)
  ✔ usage errors exit non-zero with a non-ok envelope (0.088875ms)
✔ cli snapshot contract (AC-02) (2.212958ms)
▶ live Node CLI contract (AC-02/AC-10)
  ✔ dist/cli.js exists and is runnable (0.11225ms)
  ✔ version command exits 0 and prints a semver (66.132959ms)
  ✔ --version flag exits 0 and prints a semver (60.288041ms)
  ✔ every baseline command's --help is byte-for-byte compatible (998.240875ms)
  ✖ mandatory document commands no longer advertise later or defer (61.380083ms)
  ✖ lifecycle rejects the removed no-op report-action flag (114.685458ms)
  ✔ top-level --help is byte-for-byte compatible (60.21225ms)
  ✔ top-level --help output contains all baseline commands (58.161083ms)
  ✔ subcommand --help output contains usage line and key flags (174.949ms)
  ✔ unknown command exits 2 (61.172584ms)
  ✔ unknown flag exits 2 (57.538875ms)
  ✔ version --json produces a valid envelope with version field (59.56ms)
  ✔ doctor --json produces a valid envelope with runtime=node (61.536708ms)
  ✔ usage error --json produces ok=false envelope (57.947667ms)
✖ live Node CLI contract (AC-02/AC-10) (1892.3285ms)
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ requirement command dispatcher
  ✔ status returns state for a created requirement (28.800875ms)
  ✔ plan writes into the resolved id-title requirement directory (22.489875ms)
  ✔ intake defaults both mandatory document actions to generate (19.980375ms)
  ✖ intake uses a supplied design as the source while generating the missing spec (20.08775ms)
  ✔ intake rejects later for mandatory lifecycle documents (0.322167ms)
  ✔ intake requires a valid user supplied version date (0.143958ms)
  ✔ task-only intake remains a read-only analysis without a version date (0.101083ms)
  ✔ task intake with a version date registers a dated LOCAL requirement (19.235709ms)
  ✔ acceptance set persists AC-01..AC-02 (20.7465ms)
  ✔ query reads v2 and legacy by-id archives and supports --file (22.717083ms)
  ✖ status remains readable for a legacy manifest without workflow selections (0.502833ms)
  ✔ test-contract set requires --kind and --report-action (25.755709ms)
  ✔ test-contract register validates and normalizes a structured report path (27.007417ms)
  ✔ ready -> begin through the dispatcher (346.714625ms)
  ✔ reopen after close (40.388334ms)
  ✔ generate enforces lifecycle order and creates a requirement scaffold (45.852125ms)
  ✔ generate refuses implicit overwrite and --replace really rebuilds the scaffold (54.888083ms)
  ✔ rejects missing --requirement-id (0.3055ms)
  ✔ add persists artifact registration into the manifest (102.649209ms)
  ✔ rejects arbitrary delivery-document content (118.044083ms)
  ✔ design registration rejects missing source evidence paths (100.389542ms)
  ✔ design registration ignores symbols that exist only in comments or strings (83.466417ms)
  ✔ add registers a structured test report as current requirement evidence (289.371333ms)
  ✔ diagnose records a Bug root cause (ticketKind=bug) (49.83075ms)
  ✔ diagnose rejects missing source evidence paths (32.104541ms)
  ✔ diagnose rejects symbols that only appear in comments or strings (30.328209ms)
  ✔ diagnose rejects non-bug requirements (28.485625ms)
  ✔ defer rejects all four mandatory lifecycle documents (87.730708ms)
  ✔ resolve-finding marks a review finding resolved (39.976584ms)
  ✔ resolve-finding rejects unknown finding IDs (43.917834ms)
✖ requirement command dispatcher (1703.449ms)
▶ requirement layout
  ✔ artifactFilename maps known types (0.080708ms)
  ✔ ARTIFACT_FILES covers the v2 types (0.032375ms)
  ✔ migrateLayout reports not-migrated when no legacy archive (3.587667ms)
  ✔ migrateLayout copies legacy by-id archives and rewrites manifest paths (8.639875ms)
✔ requirement layout (12.421375ms)
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ requirement state machine
  ✔ createRequirement writes a v2 manifest at draft (25.928959ms)
  ✔ createRequirement rejects later for mandatory lifecycle documents (2.916708ms)
  ✔ createRequirement is idempotent on matching identity (19.27875ms)
  ✔ createRequirement rejects name mismatch on existing id (17.892167ms)
  ✔ createRequirement canonicalizes numeric ids by ticket kind (39.695291ms)
  ✔ createRequirement rejects conflicting duplicate intake fields (18.497209ms)
  ✔ assertTransition enforces legal transitions (0.082959ms)
  ✔ ready gate: requires designed state + non-empty resolution + AC (300.1455ms)
  ✔ ready revalidates requirement.md against the latest manifest acceptance criteria (311.813292ms)
  ✔ full lifecycle: ready -> begin -> test -> review -> finish -> close (475.779917ms)
  ✔ finish gate rejects without passing test evidence (342.857666ms)
  ✔ finish gate rejects without a passed review round (363.398ms)
  ✖ finish gate rejects when the mandatory test document was deleted (400.432833ms)
  ✖ finish gate rejects when the mandatory test document was tampered (389.947167ms)
  ✔ review failed does not advance to reviewed (356.906042ms)
  ✔ reopen closed -> draft (returns to document state, not implementing) (23.986834ms)
  ✔ reopen only reuses documents that still match their recorded digest (403.002333ms)
  ✔ setAcceptanceCriteria + setTestContract persist (25.01675ms)
  ✔ test contracts cannot defer the mandatory test document (20.009ms)
  ✔ recordLater rejects every mandatory lifecycle document (80.612625ms)
  ✔ manifest is written under an id-title directory with a cross-platform safe title (15.231375ms)
  ✔ normalizes user supplied version dates and writes dated requirement directories (29.679834ms)
  ✔ limits id-title directories by UTF-8 byte length (14.203083ms)
  ✔ includes the date prefix in the UTF-8 directory byte limit (0.084458ms)
  ✔ numeric bug ids use the canonical id together with the title (14.851875ms)
  ✔ generated lifecycle docs use id-title document filenames (48.052208ms)
  ✔ generated requirement, design, and test docs follow the sample document standards (50.892458ms)
  ✔ loadRequirement rejects ambiguous id-title directories (0.502334ms)
  ✔ createRequirement does not overwrite an unrecognized id-title manifest (12.509459ms)
  ✔ STATES includes the full v2 lifecycle (0.074791ms)
  ✔ loadRequirement raises on missing archive (0.121208ms)
  ✔ revision increments on each mutate (23.59425ms)
  ✔ mutate keeps a legacy v1 manifest in the legacy by-id directory (4.999666ms)
✖ requirement state machine (3834.125667ms)
ℹ tests 86
ℹ suites 5
ℹ pass 80
ℹ fail 6
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 4032.713459

✖ failing tests:

test at src/__tests__/cli-contract.test.ts:1:3667
✖ mandatory document commands no longer advertise later or defer (61.380083ms)
  AssertionError [ERR_ASSERTION]: intake --help still advertises deferral
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/cli-contract.test.ts:148:14)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Suite.processPendingSubtests (node:internal/test_runner/test:960:18)
      at Test.postRun (node:internal/test_runner/test:1522:19)
      at Test.run (node:internal/test_runner/test:1447:12)
      at async Suite.processPendingSubtests (node:internal/test_runner/test:960:7) {
    generatedMessage: false,
    code: 'ERR_ASSERTION',
    actual: 'usage: project-intel intake [-h] [--task TASK]\n                            [--requirement-id REQUIREMENT_ID]\n                            [--requirement-name REQUIREMENT_NAME]\n                            [--ticket-kind {bug,requirement}]\n                            [--external-api {yes,no}]\n                            [--requirement-action {generate,register,later}]\n                            [--requirement-path REQUIREMENT_PATH]\n                            [--design-action {generate,register,later}]\n                            [--design-path DESIGN_PATH]\n                            [--track {auto,quick,standard,complex}] [--write]\n                            [--legacy]\n\noptions:\n  -h, --help            show this help message and exit\n  --task TASK           兼容的中文任务摘要；需求级流程可使用 --requirement-name\n  --requirement-id REQUIREMENT_ID\n                        正式需求号；省略时需求级流程生成 LOCAL 时间编号\n  --requirement-name REQUIREMENT_NAME\n                        需求名称\n  --ticket-kind {bug,requirement}\n                        单据类型；默认 requirement\n  --external-api {yes,no}\n                        明确确认是否影响对外接口\n  --requirement-action {generate,register,later}\n                        需求文档动作\n  --requirement-path REQUIREMENT_PATH\n                        requirement-action=register 时的仓库相对路径\n  --design-action {generate,register,later}\n                        设计文档动作\n  --design-path DESIGN_PATH\n                        design-action=register 时的仓库相对路径\n  --track {auto,quick,standard,complex}\n                        显式指定 quick/standard/complex；默认自动判断\n  --write               仅旧 --legacy 模式写入共享 intake 报告\n  --legacy              显式使用旧的非需求级兼容流程',
    expected: /\blater\b|\bdefer\b/i,
    operator: 'doesNotMatch',
    diff: 'simple'
  }

test at src/__tests__/cli-contract.test.ts:1:4124
✖ lifecycle rejects the removed no-op report-action flag (114.685458ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  
  0 !== 2
  
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/cli-contract.test.ts:156:12)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Suite.processPendingSubtests (node:internal/test_runner/test:960:18)
      at Test.postRun (node:internal/test_runner/test:1522:19)
      at Test.run (node:internal/test_runner/test:1447:12)
      at async Suite.processPendingSubtests (node:internal/test_runner/test:960:7) {
    generatedMessage: true,
    code: 'ERR_ASSERTION',
    actual: 0,
    expected: 2,
    operator: 'strictEqual',
    diff: 'simple'
  }

test at src/__tests__/requirement-command.test.ts:1:2394
✖ intake uses a supplied design as the source while generating the missing spec (20.08775ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  + actual - expected
  
  + undefined
  - '设计先行需求'
  
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/requirement-command.test.ts:95:12)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Suite.processPendingSubtests (node:internal/test_runner/test:960:18)
      at Test.postRun (node:internal/test_runner/test:1522:19)
      at Test.run (node:internal/test_runner/test:1447:12)
      at async Suite.processPendingSubtests (node:internal/test_runner/test:960:7) {
    generatedMessage: true,
    code: 'ERR_ASSERTION',
    actual: undefined,
    expected: '设计先行需求',
    operator: 'strictEqual',
    diff: 'simple'
  }

test at src/__tests__/requirement-command.test.ts:1:7050
✖ status remains readable for a legacy manifest without workflow selections (0.502833ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  + actual - expected
  
  + undefined
  - '旧版需求'
  
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/requirement-command.test.ts:232:12)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Suite.processPendingSubtests (node:internal/test_runner/test:960:18)
      at Test.postRun (node:internal/test_runner/test:1522:19)
      at Test.run (node:internal/test_runner/test:1447:12)
      at async Suite.processPendingSubtests (node:internal/test_runner/test:960:7) {
    generatedMessage: true,
    code: 'ERR_ASSERTION',
    actual: undefined,
    expected: '旧版需求',
    operator: 'strictEqual',
    diff: 'simple'
  }

test at src/__tests__/state-machine.test.ts:1:5495
✖ finish gate rejects when the mandatory test document was deleted (400.432833ms)
  AssertionError [ERR_ASSERTION]: Missing expected exception.
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/state-machine.test.ts:172:12)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Suite.processPendingSubtests (node:internal/test_runner/test:960:18)
      at Test.postRun (node:internal/test_runner/test:1522:19)
      at Test.run (node:internal/test_runner/test:1447:12)
      at async Suite.processPendingSubtests (node:internal/test_runner/test:960:7) {
    generatedMessage: false,
    code: 'ERR_ASSERTION',
    actual: undefined,
    expected: /测试文档/,
    operator: 'throws',
    diff: 'simple'
  }

test at src/__tests__/state-machine.test.ts:1:5919
✖ finish gate rejects when the mandatory test document was tampered (389.947167ms)
  AssertionError [ERR_ASSERTION]: Missing expected exception.
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/state-machine.test.ts:184:12)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Suite.processPendingSubtests (node:internal/test_runner/test:960:18)
      at Test.postRun (node:internal/test_runner/test:1522:19)
      at Test.run (node:internal/test_runner/test:1447:12)
      at async Suite.processPendingSubtests (node:internal/test_runner/test:960:7) {
    generatedMessage: false,
    code: 'ERR_ASSERTION',
    actual: undefined,
    expected: /测试文档/,
    operator: 'throws',
    diff: 'simple'
  }

```
