# LOCAL-20260727-141720 测试报告

- 测试类型：unit
- 阶段：red
- 结果：passed
- 验收标准：AC-01,AC-02,AC-03,AC-04
- 文件范围：src/requirements/state-machine.ts, src/requirements/layout.ts, src/commands/requirement.ts, src/commands/orchestration.ts, src/requirements/scope.ts, src/__tests__/state-machine.test.ts, src/__tests__/requirement-command.test.ts

## 执行结果

### node --import tsx --test src/__tests__/state-machine.test.ts src/__tests__/requirement-command.test.ts

- exitCode: 1
- executedCount: 49

```text
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ requirement command dispatcher
  ✔ status returns state for a created requirement (29.028834ms)
  ✔ intake persists document actions and later selection blocks generation (27.366125ms)
  ✔ acceptance set persists AC-01..AC-02 (23.084834ms)
  ✔ query reads v2 and legacy by-id archives and supports --file (27.952708ms)
  ✔ test-contract set requires --kind and --report-action (28.029875ms)
  ✔ test-contract register validates and normalizes a structured report path (29.063375ms)
  ✔ ready -> begin through the dispatcher (360.744209ms)
  ✔ reopen after close (28.996667ms)
  ✔ generate enforces lifecycle order and creates a requirement scaffold (26.984334ms)
  ✔ generate refuses implicit overwrite and --replace really rebuilds the scaffold (54.208833ms)
  ✔ rejects missing --requirement-id (3.335ms)
  ✔ add persists artifact registration into the manifest (159.07775ms)
  ✔ rejects arbitrary delivery-document content (72.804917ms)
  ✔ design registration rejects missing source evidence paths (155.000625ms)
  ✔ design registration ignores symbols that exist only in comments or strings (105.781875ms)
  ✔ add registers a structured test report as current requirement evidence (292.611584ms)
  ✔ diagnose records a Bug root cause (ticketKind=bug) (39.051584ms)
  ✔ diagnose rejects missing source evidence paths (39.105791ms)
  ✔ diagnose rejects symbols that only appear in comments or strings (36.76275ms)
  ✔ diagnose rejects non-bug requirements (27.94425ms)
  ✔ defer adds a readiness blocker for design (30.999ms)
  ✔ resolve-finding marks a review finding resolved (41.774125ms)
  ✔ resolve-finding rejects unknown finding IDs (22.297583ms)
✔ requirement command dispatcher (1663.098041ms)
▶ requirement layout
  ✔ artifactFilename maps known types (0.046541ms)
  ✔ ARTIFACT_FILES covers the v2 types (0.030833ms)
  ✔ migrateLayout reports not-migrated when no legacy archive (0.127416ms)
  ✖ migrateLayout copies legacy by-id archives and rewrites manifest paths (6.396833ms)
✖ requirement layout (6.713375ms)
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ requirement state machine
  ✔ createRequirement writes a v2 manifest at draft (30.258167ms)
  ✔ createRequirement is idempotent on matching identity (20.77075ms)
  ✔ createRequirement rejects name mismatch on existing id (19.139583ms)
  ✔ createRequirement canonicalizes numeric ids by ticket kind (37.687916ms)
  ✔ createRequirement rejects conflicting duplicate intake fields (21.046791ms)
  ✔ assertTransition enforces legal transitions (0.110584ms)
  ✔ ready gate: requires designed state + non-empty resolution + AC (376.143042ms)
  ✔ ready revalidates requirement.md against the latest manifest acceptance criteria (290.305875ms)
  ✔ full lifecycle: ready -> begin -> test -> review -> finish -> close (527.239083ms)
  ✔ finish gate rejects without passing test evidence (331.393ms)
  ✔ finish gate rejects without a passed review round (374.018458ms)
  ✔ review failed does not advance to reviewed (385.956959ms)
  ✔ reopen closed -> draft (returns to document state, not implementing) (30.598917ms)
  ✔ reopen only reuses documents that still match their recorded digest (455.761833ms)
  ✔ setAcceptanceCriteria + setTestContract persist (29.310792ms)
  ✖ manifest is written under an id-title directory with a cross-platform safe title (25.297333ms)
  ✖ numeric bug ids use the canonical id together with the title (20.60525ms)
  ✖ loadRequirement rejects ambiguous id-title directories (1.058042ms)
  ✔ STATES includes the full v2 lifecycle (0.070334ms)
  ✔ loadRequirement raises on missing archive (0.1145ms)
  ✔ revision increments on each mutate (28.337125ms)
  ✔ mutate keeps a legacy v1 manifest in the legacy by-id directory (5.129542ms)
✖ requirement state machine (3011.613875ms)
ℹ tests 49
ℹ suites 3
ℹ pass 45
ℹ fail 4
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 3189.285792

✖ failing tests:

test at src/__tests__/requirement-command.test.ts:1:17091
✖ migrateLayout copies legacy by-id archives and rewrites manifest paths (6.396833ms)
  AssertionError [ERR_ASSERTION]: The expression evaluated to a falsy value:
  
    assert.ok(dryRun.to?.endsWith(join(".project-intel", "requirements", "REQ-OLD-旧版布局迁移")))
  
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/requirement-command.test.ts:452:12)
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
    operator: '==',
    diff: 'simple'
  }

test at src/__tests__/state-machine.test.ts:1:6572
✖ manifest is written under an id-title directory with a cross-platform safe title (25.297333ms)
  AssertionError [ERR_ASSERTION]: The expression evaluated to a falsy value:
  
    assert.ok(dir.endsWith(join(".project-intel", "requirements", "REQ-8-布局-标题-Windows")))
  
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/state-machine.test.ts:188:12)
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
    operator: '==',
    diff: 'simple'
  }

test at src/__tests__/state-machine.test.ts:1:7094
✖ numeric bug ids use the canonical id together with the title (20.60525ms)
  AssertionError [ERR_ASSERTION]: The expression evaluated to a falsy value:
  
    assert.ok(requirementDir(root, "bug123").endsWith(
  
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/state-machine.test.ts:198:12)
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
    operator: '==',
    diff: 'simple'
  }

test at src/__tests__/state-machine.test.ts:1:7453
✖ loadRequirement rejects ambiguous id-title directories (1.058042ms)
  AssertionError [ERR_ASSERTION]: The input did not match the regular expression /存在多个需求档案/. Input:
  
  'RequirementError: 未找到需求档案：REQ-DUP'
  
      at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/state-machine.test.ts:217:12)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:internal/test_runner/test:1382:25)
      at Suite.processPendingSubtests (node:internal/test_runner/test:960:18)
      at Test.postRun (node:internal/test_runner/test:1522:19)
      at Test.run (node:internal/test_runner/test:1447:12)
      at async Suite.processPendingSubtests (node:internal/test_runner/test:960:7) {
    generatedMessage: true,
    code: 'ERR_ASSERTION',
    actual: RequirementError: 未找到需求档案：REQ-DUP
        at loadRequirement (/Users/xumeng/Desktop/code/project-intelligence/src/requirements/state-machine.ts:147:11)
        at <anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/state-machine.test.ts:217:25)
        at getActual (node:assert:580:5)
        at strict.throws (node:assert:728:24)
        at TestContext.<anonymous> (/Users/xumeng/Desktop/code/project-intelligence/src/__tests__/state-machine.test.ts:217:12)
        at Test.runInAsyncScope (node:async_hooks:226:14)
        at Test.run (node:internal/test_runner/test:1382:25)
        at Suite.processPendingSubtests (node:internal/test_runner/test:960:18)
        at Test.postRun (node:internal/test_runner/test:1522:19)
        at Test.run (node:internal/test_runner/test:1447:12),
    expected: /存在多个需求档案/,
    operator: 'throws',
    diff: 'simple'
  }

```
