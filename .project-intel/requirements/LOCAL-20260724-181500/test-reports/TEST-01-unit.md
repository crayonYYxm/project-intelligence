# LOCAL-20260724-181500 测试报告

- 测试类型：unit
- 阶段：red
- 结果：passed
- 验收标准：AC-01,AC-02,AC-03,AC-04,AC-05
- 文件范围：src/__tests__/zcode-compat.test.ts, src/__tests__/test-evidence.test.ts, src/__tests__/review-finish-graph.test.ts

## 执行结果

### node --import tsx --test src/__tests__/zcode-compat.test.ts src/__tests__/test-evidence.test.ts src/__tests__/review-finish-graph.test.ts

- exitCode: 1
- executedCount: 1382

```text
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
finish：需求 REQ-F 已完成（→ finished）
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
finish：需求 REQ-M 已完成（→ finished）
已刷新 .project-intel，索引了 6 个文本文件。
maintain：已刷新 .project-intel 并关闭需求 REQ-M（→ closed）

## .project-intel/standards/api.md:3

# API 标准

所有接口必须返回 JSON。
▶ review / finish / maintain commands (3.F)
  ✔ review passed advances verified -> reviewed (766.923208ms)
  ✔ review failed stays verified (747.059458ms)
  ✔ review sanitizes summary and finding text before persisting (670.836375ms)
  ✔ finish writes closure-summary and advances reviewed -> finished (823.199ms)
  ✖ finish automatically generates and registers the closure summary (787.138208ms)
  ✔ finish rejects without passed review (AC-11 gate) (703.452542ms)
  ✔ maintain refreshes facts and closes the requirement (1097.563084ms)
✖ review / finish / maintain commands (3.F) (5598.098375ms)
▶ graph sources (3.G.1)
  ✔ gitnexusSummary missing when no .gitnexus (0.676166ms)
  ✔ gitnexusSummary present with valid meta (0.777959ms)
  ✔ understandSummary present with non-empty nodes (0.442416ms)
  ✔ detectGraphSources returns both names (1.434583ms)
  ✔ understandGraphSummary aggregates domains (0.764792ms)
✔ graph sources (3.G.1) (4.342292ms)
▶ graph-tools + query commands (3.G.2)
  ✔ graph-tools reports source statuses (1.638791ms)
  ✔ query searches standards text (1.308ms)
  ✔ query rejects an uninitialized project (0.604625ms)
✔ graph-tools + query commands (3.G.2) (3.67075ms)
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ sanitizeText
  ✔ redacts header values (Authorization/Cookie) (3.834667ms)
  ✔ redacts key=value secrets (0.205833ms)
  ✔ redacts raw token formats (0.135708ms)
  ✔ redacts database URLs and URL userinfo (0.091542ms)
  ✔ redacts PRC identity and mainland mobile (3.534291ms)
  ✔ preserves benign Chinese text (0.107084ms)
✔ sanitizeText (8.84225ms)
▶ manualEvidenceValid
  ✔ rejects generic phrases (0.175916ms)
  ✔ accepts specific descriptions (0.072167ms)
✔ manualEvidenceValid (0.38075ms)
▶ executedTestCount
  ✔ extracts unittest 'Ran N tests' (0.469792ms)
  ✔ extracts 'N passed' (0.288542ms)
  ✔ returns 0 for empty formatter output (AC-11) (0.067416ms)
  ✔ extracts the Node test runner summary (0.78975ms)
✔ executedTestCount (1.74375ms)
▶ inspectTestReport
  ✔ accepts structured JSON and rejects free-form pass text (1.264208ms)
  ✔ parses JUnit, TAP and unittest failures (0.456084ms)
✔ inspectTestReport (1.852625ms)
▶ phasePassed
  ✔ green requires exit 0 AND a real test count (0.129209ms)
  ✔ red requires non-zero exit + expected-failure match (0.086917ms)
  ✔ manual uses manualEvidenceValid (0.045708ms)
✔ phasePassed (0.338375ms)
▶ test command (AC-11: rejects forged pass)
  ✔ records green evidence when a real test passes (21.0055ms)
  ✔ rejects a formatter pass as evidence (no test count) (14.584333ms)
  ✔ advances requirement state via recordTestResult (568.972875ms)
  ✖ creates and appends the canonical requirement test report (486.44825ms)
  ✔ registers a structured report without re-running a command (514.900042ms)
  ✔ rejects a free-form registered pass report (483.728542ms)
✖ test command (AC-11: rejects forged pass) (2090.051125ms)
▶ evaluateTestEvidence
  ✔ ready=true when no files changed (0.6505ms)
  ✔ ready=false when task mismatch (0.562667ms)
✔ evaluateTestEvidence (1.3115ms)
▶ renderTestEvidence
  ✔ renders a markdown table with the task (0.152959ms)
✔ renderTestEvidence (0.204875ms)
▶ COMMAND_ERROR_CODES
  ✔ includes the gate-relevant exit codes (0.066334ms)
✔ COMMAND_ERROR_CODES (0.104792ms)
▶ ZCode plugin compatibility
  ✖ ships a root marketplace and native ZCode plugin manifest (1.147458ms)
  ✖ contains no symbolic links in tracked distribution paths (0.213541ms)
✖ ZCode plugin compatibility (2.164709ms)
ℹ tests 44
ℹ suites 13
ℹ pass 40
ℹ fail 4
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 5943.99125

✖ failing tests:

test at src/__tests__/review-finish-graph.test.ts:1:2645
✖ finish automatically generates and registers the closure summary (787.138208ms)
  Error [RequirementError]: 缺少当前有效的复盘收口总结文件。
      at validateFinishRequirement (/Users/xumeng/Desktop/code/project-intelligence/src/requirements/state-machine.ts:809:11)
      at finishRequirement (/Users/xumeng/Desktop/code/project-intelligence/src/requirements/state-machine.ts:820:21)
      at runFinish (/Users/xumeng/Desktop/code/project-intelligence/src/commands/finish.ts:39:20)
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/review-finish-graph.test.ts:76:20)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Suite.processPendingSubtests (node:internal/test_runner/test:960:18)
      at Test.postRun (node:internal/test_runner/test:1522:19)
      at Test.run (node:internal/test_runner/test:1447:12)
      at async Suite.processPendingSubtests (node:internal/test_runner/test:960:7) {
    exitCode: 2
  }

test at src/__tests__/test-evidence.test.ts:1:5510
✖ creates and appends the canonical requirement test report (486.44825ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  
  false !== true
  
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/test-evidence.test.ts:153:12)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Suite.processPendingSubtests (node:internal/test_runner/test:960:18)
      at Test.postRun (node:internal/test_runner/test:1522:19)
      at Test.run (node:internal/test_runner/test:1447:12)
      at async Suite.processPendingSubtests (node:internal/test_runner/test:960:7) {
    generatedMessage: true,
    code: 'ERR_ASSERTION',
    actual: false,
    expected: true,
    operator: 'strictEqual',
    diff: 'simple'
  }

test at src/__tests__/zcode-compat.test.ts:1:436
✖ ships a root marketplace and native ZCode plugin manifest (1.147458ms)
  Error: ENOENT: no such file or directory, open '/Users/xumeng/Desktop/code/project-intelligence/marketplace.json'
      at readFileSync (node:fs:436:20)
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/zcode-compat.test.ts:12:36)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Test.start (node:internal/test_runner/test:1242:17)
      at node:internal/test_runner/test:1867:71
      at node:internal/per_context/primordials:466:82
      at new Promise (<anonymous>)
      at new SafePromise (node:internal/per_context/primordials:435:3)
      at node:internal/per_context/primordials:466:9 {
    errno: -2,
    code: 'ENOENT',
    syscall: 'open',
    path: '/Users/xumeng/Desktop/code/project-intelligence/marketplace.json'
  }

test at src/__tests__/zcode-compat.test.ts:1:1157
✖ contains no symbolic links in tracked distribution paths (0.213541ms)
  Error: ENOENT: no such file or directory, lstat '/Users/xumeng/Desktop/code/project-intelligence/marketplace.json'
      at lstatSync (node:fs:1694:25)
      at visit (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/zcode-compat.test.ts:35:20)
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/zcode-compat.test.ts:43:43)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Suite.processPendingSubtests (node:internal/test_runner/test:960:18)
      at Test.postRun (node:internal/test_runner/test:1522:19)
      at Test.run (node:internal/test_runner/test:1447:12)
      at async Promise.all (index 0)
      at async Suite.run (node:internal/test_runner/test:1869:7) {
    errno: -2,
    code: 'ENOENT',
    syscall: 'lstat',
    path: '/Users/xumeng/Desktop/code/project-intelligence/marketplace.json'
  }

```
