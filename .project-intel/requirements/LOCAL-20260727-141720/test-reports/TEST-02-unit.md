# LOCAL-20260727-141720 测试报告

- 测试类型：unit
- 阶段：green
- 结果：passed
- 验收标准：AC-01,AC-02,AC-03,AC-04
- 文件范围：src/requirements/state-machine.ts, src/requirements/layout.ts, src/commands/requirement.ts, src/commands/orchestration.ts, src/requirements/scope.ts, src/__tests__/state-machine.test.ts, src/__tests__/requirement-command.test.ts

## 执行结果

### node --import tsx --test src/__tests__/state-machine.test.ts src/__tests__/requirement-command.test.ts

- exitCode: 0
- executedCount: 49

```text
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ requirement command dispatcher
  ✔ status returns state for a created requirement (22.102708ms)
  ✔ intake persists document actions and later selection blocks generation (29.06375ms)
  ✔ acceptance set persists AC-01..AC-02 (22.455875ms)
  ✔ query reads v2 and legacy by-id archives and supports --file (24.326208ms)
  ✔ test-contract set requires --kind and --report-action (26.779375ms)
  ✔ test-contract register validates and normalizes a structured report path (32.077125ms)
  ✔ ready -> begin through the dispatcher (360.829792ms)
  ✔ reopen after close (28.787625ms)
  ✔ generate enforces lifecycle order and creates a requirement scaffold (29.165167ms)
  ✔ generate refuses implicit overwrite and --replace really rebuilds the scaffold (64.141208ms)
  ✔ rejects missing --requirement-id (3.267458ms)
  ✔ add persists artifact registration into the manifest (145.341458ms)
  ✔ rejects arbitrary delivery-document content (80.138875ms)
  ✔ design registration rejects missing source evidence paths (155.464416ms)
  ✔ design registration ignores symbols that exist only in comments or strings (96.983167ms)
  ✔ add registers a structured test report as current requirement evidence (297.76775ms)
  ✔ diagnose records a Bug root cause (ticketKind=bug) (44.946208ms)
  ✔ diagnose rejects missing source evidence paths (36.748542ms)
  ✔ diagnose rejects symbols that only appear in comments or strings (36.641291ms)
  ✔ diagnose rejects non-bug requirements (31.302041ms)
  ✔ defer adds a readiness blocker for design (29.10725ms)
  ✔ resolve-finding marks a review finding resolved (34.810083ms)
  ✔ resolve-finding rejects unknown finding IDs (23.291375ms)
✔ requirement command dispatcher (1656.816834ms)
▶ requirement layout
  ✔ artifactFilename maps known types (0.059875ms)
  ✔ ARTIFACT_FILES covers the v2 types (0.068625ms)
  ✔ migrateLayout reports not-migrated when no legacy archive (0.135625ms)
  ✔ migrateLayout copies legacy by-id archives and rewrites manifest paths (1.391416ms)
✔ requirement layout (1.770917ms)
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ requirement state machine
  ✔ createRequirement writes a v2 manifest at draft (28.351958ms)
  ✔ createRequirement is idempotent on matching identity (20.33425ms)
  ✔ createRequirement rejects name mismatch on existing id (19.928917ms)
  ✔ createRequirement canonicalizes numeric ids by ticket kind (41.550791ms)
  ✔ createRequirement rejects conflicting duplicate intake fields (21.265875ms)
  ✔ assertTransition enforces legal transitions (0.097625ms)
  ✔ ready gate: requires designed state + non-empty resolution + AC (360.700916ms)
  ✔ ready revalidates requirement.md against the latest manifest acceptance criteria (290.558958ms)
  ✔ full lifecycle: ready -> begin -> test -> review -> finish -> close (538.160708ms)
  ✔ finish gate rejects without passing test evidence (318.400416ms)
  ✔ finish gate rejects without a passed review round (380.643083ms)
  ✔ review failed does not advance to reviewed (383.548375ms)
  ✔ reopen closed -> draft (returns to document state, not implementing) (27.838ms)
  ✔ reopen only reuses documents that still match their recorded digest (438.523958ms)
  ✔ setAcceptanceCriteria + setTestContract persist (26.711625ms)
  ✔ manifest is written under an id-title directory with a cross-platform safe title (18.963666ms)
  ✔ numeric bug ids use the canonical id together with the title (18.857708ms)
  ✔ loadRequirement rejects ambiguous id-title directories (0.539167ms)
  ✔ STATES includes the full v2 lifecycle (0.039458ms)
  ✔ loadRequirement raises on missing archive (0.096667ms)
  ✔ revision increments on each mutate (28.398917ms)
  ✔ mutate keeps a legacy v1 manifest in the legacy by-id directory (4.875708ms)
✔ requirement state machine (2969.496584ms)
ℹ tests 49
ℹ suites 3
ℹ pass 49
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 3084.343416

```
