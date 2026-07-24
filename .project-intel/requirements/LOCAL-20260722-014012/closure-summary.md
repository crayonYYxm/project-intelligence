# 修复 Windows 市场克隆符号链接失败 · 复盘收口总结

- 需求号：`LOCAL-20260722-014012`
- 当前状态：closed

## 需求结果

当前实现、测试和评审记录已汇总，等待 `project-finish` 对当前 Git 快照执行最终门禁。

## 变更范围

### 业务源码与测试变更

- `.ua/.trash-1784630749/assemble-review.json`
- `.ua/.trash-1784630749/assembled-graph.json`
- `.ua/.trash-1784630749/batch-1-part-1.json`
- `.ua/.trash-1784630749/batch-1-part-2.json`
- `.ua/.trash-1784630749/batch-1-part-3.json`
- `.ua/.trash-1784630749/batch-1-part-4.json`
- `.ua/.trash-1784630749/batch-10.json`
- `.ua/.trash-1784630749/batch-11.json`
- `.ua/.trash-1784630749/batch-12.json`
- `.ua/.trash-1784630749/batch-2.json`
- `.ua/.trash-1784630749/batch-3-part-1.json`
- `.ua/.trash-1784630749/batch-3-part-2.json`
- `.ua/.trash-1784630749/batch-3-part-3.json`
- `.ua/.trash-1784630749/batch-4.json`
- `.ua/.trash-1784630749/batch-5.json`
- `.ua/.trash-1784630749/batch-6.json`
- `.ua/.trash-1784630749/batch-7.json`
- `.ua/.trash-1784630749/batch-8.json`
- `.ua/.trash-1784630749/batch-9.json`
- `.ua/.trash-1784630749/batches.json`
- `.ua/.trash-1784630749/fingerprint-input.json`
- `.ua/.trash-1784630749/layers.json`
- `.ua/.trash-1784630749/review.json`
- `.ua/.trash-1784630749/tmp/arch-input.json`
- `.ua/.trash-1784630749/tmp/build-tour-input.cjs`
- `.ua/.trash-1784630749/tmp/gen_batch1.py`
- `.ua/.trash-1784630749/tmp/ua-arch-analyze.cjs`
- `.ua/.trash-1784630749/tmp/ua-arch-input.json`
- `.ua/.trash-1784630749/tmp/ua-arch-results.json`
- `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-1.json`
- `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-10.json`
- `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-11.json`
- `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-12.json`
- `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-2.json`
- `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-3.json`
- `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-4.json`
- `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-5.json`
- `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-6.json`
- `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-7.json`
- `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-8.json`
- `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-9.json`
- `.ua/.trash-1784630749/tmp/ua-file-extract-results-1.json`
- `.ua/.trash-1784630749/tmp/ua-file-extract-results-10.json`
- `.ua/.trash-1784630749/tmp/ua-file-extract-results-11.json`
- `.ua/.trash-1784630749/tmp/ua-file-extract-results-12.json`
- `.ua/.trash-1784630749/tmp/ua-file-extract-results-2.json`
- `.ua/.trash-1784630749/tmp/ua-file-extract-results-3.json`
- `.ua/.trash-1784630749/tmp/ua-file-extract-results-4.json`
- `.ua/.trash-1784630749/tmp/ua-file-extract-results-5.json`
- `.ua/.trash-1784630749/tmp/ua-file-extract-results-6.json`
- `.ua/.trash-1784630749/tmp/ua-file-extract-results-7.json`
- `.ua/.trash-1784630749/tmp/ua-file-extract-results-8.json`
- `.ua/.trash-1784630749/tmp/ua-file-extract-results-9.json`
- `.ua/.trash-1784630749/tmp/ua-import-map-input.json`
- `.ua/.trash-1784630749/tmp/ua-import-map-output.json`
- `.ua/.trash-1784630749/tmp/ua-inline-validate.cjs`
- `.ua/.trash-1784630749/tmp/ua-scan-files.json`
- `.ua/.trash-1784630749/tmp/ua-tour-analyze.cjs`
- `.ua/.trash-1784630749/tmp/ua-tour-input.json`
- `.ua/.trash-1784630749/tmp/ua-tour-results.json`
- `.ua/.trash-1784630749/tour.json`
- `.ua/.understandignore`
- `.ua/config.json`
- `.ua/fingerprints.json`
- `.ua/intermediate/scan-result.json`
- `.ua/knowledge-graph.json`
- `.ua/meta.json`
- `.understand-anything`
- `.understand-anything/.trash-1784630749/assemble-review.json`
- `.understand-anything/.trash-1784630749/assembled-graph.json`
- `.understand-anything/.trash-1784630749/batch-1-part-1.json`
- `.understand-anything/.trash-1784630749/batch-1-part-2.json`
- `.understand-anything/.trash-1784630749/batch-1-part-3.json`
- `.understand-anything/.trash-1784630749/batch-1-part-4.json`
- `.understand-anything/.trash-1784630749/batch-10.json`
- `.understand-anything/.trash-1784630749/batch-11.json`
- `.understand-anything/.trash-1784630749/batch-12.json`
- `.understand-anything/.trash-1784630749/batch-2.json`
- `.understand-anything/.trash-1784630749/batch-3-part-1.json`
- `.understand-anything/.trash-1784630749/batch-3-part-2.json`
- `.understand-anything/.trash-1784630749/batch-3-part-3.json`
- `.understand-anything/.trash-1784630749/batch-4.json`
- `.understand-anything/.trash-1784630749/batch-5.json`
- `.understand-anything/.trash-1784630749/batch-6.json`
- `.understand-anything/.trash-1784630749/batch-7.json`
- `.understand-anything/.trash-1784630749/batch-8.json`
- `.understand-anything/.trash-1784630749/batch-9.json`
- `.understand-anything/.trash-1784630749/batches.json`
- `.understand-anything/.trash-1784630749/fingerprint-input.json`
- `.understand-anything/.trash-1784630749/layers.json`
- `.understand-anything/.trash-1784630749/review.json`
- `.understand-anything/.trash-1784630749/tmp/arch-input.json`
- `.understand-anything/.trash-1784630749/tmp/build-tour-input.cjs`
- `.understand-anything/.trash-1784630749/tmp/gen_batch1.py`
- `.understand-anything/.trash-1784630749/tmp/ua-arch-analyze.cjs`
- `.understand-anything/.trash-1784630749/tmp/ua-arch-input.json`
- `.understand-anything/.trash-1784630749/tmp/ua-arch-results.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-1.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-10.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-11.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-12.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-2.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-3.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-4.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-5.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-6.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-7.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-8.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-9.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-1.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-10.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-11.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-12.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-2.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-3.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-4.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-5.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-6.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-7.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-8.json`
- `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-9.json`
- `.understand-anything/.trash-1784630749/tmp/ua-import-map-input.json`
- `.understand-anything/.trash-1784630749/tmp/ua-import-map-output.json`
- `.understand-anything/.trash-1784630749/tmp/ua-inline-validate.cjs`
- `.understand-anything/.trash-1784630749/tmp/ua-scan-files.json`
- `.understand-anything/.trash-1784630749/tmp/ua-tour-analyze.cjs`
- `.understand-anything/.trash-1784630749/tmp/ua-tour-input.json`
- `.understand-anything/.trash-1784630749/tmp/ua-tour-results.json`
- `.understand-anything/.trash-1784630749/tour.json`
- `.understand-anything/.understandignore`
- `.understand-anything/config.json`
- `.understand-anything/fingerprints.json`
- `.understand-anything/intermediate/scan-result.json`
- `.understand-anything/knowledge-graph.json`
- `.understand-anything/meta.json`
- `plugins/project-intelligence/tests/test_project_intel.py`

### 需求交付文档

- `.project-intel/requirements/LOCAL-20260722-014012/design.md`
- `.project-intel/requirements/LOCAL-20260722-014012/requirement.md`
- `.project-intel/requirements/LOCAL-20260722-014012/test-report.md`

## 验收标准结果

- AC-01：通过 — 仓库根目录 .understand-anything 是真实目录且不是符号链接，Git 不再以 120000 模式跟踪该路径。
- AC-02：通过 — 仓库中不存在 .ua 目录，.understand-anything/knowledge-graph.json 仍存在并能被图谱检测逻辑识别。
- AC-03：通过 — 新增仓库结构回归测试通过，现有单元测试与发布包检查无回归。

## 测试证据

- TEST-01 至 TEST-04 已因补全目录迁移的文件范围而失效，不作为最终验收依据。
- TEST-05：unit / passed；验收标准：AC-01, AC-02, AC-03；已覆盖 `.ua` 与 `.understand-anything` 的完整迁移路径及回归测试文件；报告：.project-intel/requirements/LOCAL-20260722-014012/test-report.md

## 评审结论

- REVIEW-01 已随需求重新打开而失效，不作为最终评审依据。
- REVIEW-02：passed — 完整目录迁移范围已纳入当前测试证据；Git 快照无符号链接，图谱读取和测试隔离正常，无阻塞或重要问题。

## 人工例外

- 无人工测试例外。

## 遗留问题

- 无已知未解决阻塞项。

## 复盘结论

本次变更已按同一需求号关联设计、验收标准、测试和评审；最终是否完成以当前快照的 `project-finish` 结果为准。


## 系统收口状态

- 状态：closed
- 更新时间：2026-07-21T18:10:56.858427+00:00
- 结论：当前文档已通过需求级收口门禁。
