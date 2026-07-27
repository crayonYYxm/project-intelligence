# LOCAL-20260724-181500 测试报告

- 测试类型：unit
- 阶段：green
- 结果：passed
- 验收标准：AC-01,AC-02,AC-03,AC-04,AC-05
- 文件范围：marketplace.json, package.json, plugins/project-intelligence/.zcode-plugin/plugin.json, scripts/check-release.mjs, scripts/check-package.mjs, src/commands/finish.ts, src/commands/test.ts, src/requirements/state-machine.ts, src/__tests__/zcode-compat.test.ts, src/__tests__/test-evidence.test.ts, src/__tests__/review-finish-graph.test.ts

## 执行结果

### node --import tsx --test src/__tests__/zcode-compat.test.ts src/__tests__/test-evidence.test.ts src/__tests__/review-finish-graph.test.ts

- exitCode: 0
- executedCount: 45

```text
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
finish：需求 REQ-F 已完成（→ finished）
已初始化 .project-intel，索引了 3 个文本文件。
finish：需求 REQ-F-AUTO 已完成（→ finished）
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
finish：需求 REQ-M 已完成（→ finished）
已刷新 .project-intel，索引了 6 个文本文件。
maintain：已刷新 .project-intel 并关闭需求 REQ-M（→ closed）

## .project-intel/standards/api.md:3

# API 标准

所有接口必须返回 JSON。
▶ review / finish / maintain commands (3.F)
  ✔ review passed advances verified -> reviewed (706.301ms)
  ✔ review failed stays verified (791.012542ms)
  ✔ review sanitizes summary and finding text before persisting (724.683125ms)
  ✔ finish writes closure-summary and advances reviewed -> finished (853.638083ms)
  ✔ finish automatically generates and registers the closure summary (796.385917ms)
  ✔ finish rejects without passed review (AC-11 gate) (715.785167ms)
  ✔ maintain refreshes facts and closes the requirement (1154.25475ms)
✔ review / finish / maintain commands (3.F) (5743.694875ms)
▶ graph sources (3.G.1)
  ✔ gitnexusSummary missing when no .gitnexus (0.367709ms)
  ✔ gitnexusSummary present with valid meta (0.929292ms)
  ✔ understandSummary present with non-empty nodes (1.187084ms)
  ✔ detectGraphSources returns both names (1.570167ms)
  ✔ understandGraphSummary aggregates domains (0.684708ms)
✔ graph sources (3.G.1) (5.047916ms)
▶ graph-tools + query commands (3.G.2)
  ✔ graph-tools reports source statuses (1.357875ms)
  ✔ query searches standards text (0.99625ms)
  ✔ query rejects an uninitialized project (0.299875ms)
✔ graph-tools + query commands (3.G.2) (2.7555ms)
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ sanitizeText
  ✔ redacts header values (Authorization/Cookie) (3.866042ms)
  ✔ redacts key=value secrets (0.18525ms)
  ✔ redacts raw token formats (0.202292ms)
  ✔ redacts database URLs and URL userinfo (0.139584ms)
  ✔ redacts PRC identity and mainland mobile (3.502542ms)
  ✔ preserves benign Chinese text (0.124959ms)
✔ sanitizeText (9.453917ms)
▶ manualEvidenceValid
  ✔ rejects generic phrases (0.1845ms)
  ✔ accepts specific descriptions (0.091917ms)
✔ manualEvidenceValid (0.440917ms)
▶ executedTestCount
  ✔ extracts unittest 'Ran N tests' (0.500292ms)
  ✔ extracts 'N passed' (0.294208ms)
  ✔ returns 0 for empty formatter output (AC-11) (0.065208ms)
  ✔ extracts the Node test runner summary (0.935291ms)
✔ executedTestCount (1.988ms)
▶ inspectTestReport
  ✔ accepts structured JSON and rejects free-form pass text (1.317666ms)
  ✔ parses JUnit, TAP and unittest failures (0.477667ms)
✔ inspectTestReport (1.866959ms)
▶ phasePassed
  ✔ green requires exit 0 AND a real test count (0.145292ms)
  ✔ red requires non-zero exit + expected-failure match (0.092208ms)
  ✔ manual uses manualEvidenceValid (0.050292ms)
✔ phasePassed (0.356291ms)
▶ test command (AC-11: rejects forged pass)
  ✔ records green evidence when a real test passes (17.887292ms)
  ✔ rejects a formatter pass as evidence (no test count) (14.652083ms)
  ✔ advances requirement state via recordTestResult (530.804459ms)
  ✔ keeps the requirement implementing after an expected RED failure (612.384292ms)
  ✔ creates and appends the canonical requirement test report (623.421125ms)
  ✔ registers a structured report without re-running a command (520.61925ms)
  ✔ rejects a free-form registered pass report (456.678875ms)
✔ test command (AC-11: rejects forged pass) (2776.827334ms)
▶ evaluateTestEvidence
  ✔ ready=true when no files changed (0.470875ms)
  ✔ ready=false when task mismatch (0.419334ms)
✔ evaluateTestEvidence (0.98575ms)
▶ renderTestEvidence
  ✔ renders a markdown table with the task (0.143208ms)
✔ renderTestEvidence (0.193041ms)
▶ COMMAND_ERROR_CODES
  ✔ includes the gate-relevant exit codes (0.064042ms)
✔ COMMAND_ERROR_CODES (0.122792ms)
▶ ZCode plugin compatibility
  ✔ ships a root marketplace and native ZCode plugin manifest (0.943792ms)
  ✔ contains no symbolic links in tracked distribution paths (15.951791ms)
✔ ZCode plugin compatibility (17.688375ms)
ℹ tests 45
ℹ suites 13
ℹ pass 45
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 5994.121584

```
