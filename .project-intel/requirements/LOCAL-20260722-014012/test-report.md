# 修复 Windows 市场克隆符号链接失败 · 测试报告

- 需求号：`LOCAL-20260722-014012`
- 当前状态：最近一次执行通过

## 测试计划

- AC-01：计划验证，尚未执行。
- AC-02：计划验证，尚未执行。
- AC-03：计划验证，尚未执行。

## 执行记录

尚未执行。只有写入实际命令、结果和验收标准映射后，本文档才可作为完成证据。

### 2026-07-21T17:55:46.467622+00:00 · regression / unit

- 结果：passed
- 已执行测试数：2
- 验收标准：AC-03
- 覆盖范围：`.understand-anything/knowledge-graph.json`, `plugins/project-intelligence/tests/test_project_intel.py`
- Git 提交：`ad7c8ad4d3aee7801ad126ac3e69d08736dcf24e`
- 代码快照：`12bc2f220af5344304ca5244ce6246ad540012be322a9e28725b4f7fdde3e772`
- 命令：`python3 plugins/project-intelligence/tests/test_project_intel.py GraphToolCommandTests.test_detect_graph_actions_marks_gitnexus_as_download_and_run StabilityAndPackagingTests.test_understand_graph_uses_windows_portable_directory`

```text
..
----------------------------------------------------------------------
Ran 2 tests in 0.006s

OK
```

### 2026-07-21T17:57:34.500338+00:00 · verify / unit

- 结果：passed
- 已执行测试数：2
- 验收标准：AC-01, AC-02, AC-03
- 覆盖范围：`.understand-anything/knowledge-graph.json`, `plugins/project-intelligence/tests/test_project_intel.py`
- Git 提交：`ad7c8ad4d3aee7801ad126ac3e69d08736dcf24e`
- 代码快照：`8b0875467958368fb308fd3375fcdafb96204f6b632d85e3cda4df42821ab56e`
- 命令：`python3 plugins/project-intelligence/tests/test_project_intel.py GraphToolCommandTests.test_detect_graph_actions_marks_gitnexus_as_download_and_run StabilityAndPackagingTests.test_understand_graph_uses_windows_portable_directory`

```text
..
----------------------------------------------------------------------
Ran 2 tests in 0.006s

OK
```

### 2026-07-21T18:07:53.952042+00:00 · verify / unit

- 结果：passed
- 已执行测试数：2
- 验收标准：AC-01, AC-02, AC-03
- 覆盖范围：`.ua/.trash-1784630749/assemble-review.json`, `.ua/.trash-1784630749/assembled-graph.json`, `.ua/.trash-1784630749/batch-1-part-1.json`, `.ua/.trash-1784630749/batch-1-part-2.json`, `.ua/.trash-1784630749/batch-1-part-3.json`, `.ua/.trash-1784630749/batch-1-part-4.json`, `.ua/.trash-1784630749/batch-10.json`, `.ua/.trash-1784630749/batch-11.json`, `.ua/.trash-1784630749/batch-12.json`, `.ua/.trash-1784630749/batch-2.json`, `.ua/.trash-1784630749/batch-3-part-1.json`, `.ua/.trash-1784630749/batch-3-part-2.json`, `.ua/.trash-1784630749/batch-3-part-3.json`, `.ua/.trash-1784630749/batch-4.json`, `.ua/.trash-1784630749/batch-5.json`, `.ua/.trash-1784630749/batch-6.json`, `.ua/.trash-1784630749/batch-7.json`, `.ua/.trash-1784630749/batch-8.json`, `.ua/.trash-1784630749/batch-9.json`, `.ua/.trash-1784630749/batches.json`, `.ua/.trash-1784630749/fingerprint-input.json`, `.ua/.trash-1784630749/layers.json`, `.ua/.trash-1784630749/review.json`, `.ua/.trash-1784630749/tmp/arch-input.json`, `.ua/.trash-1784630749/tmp/build-tour-input.cjs`, `.ua/.trash-1784630749/tmp/gen_batch1.py`, `.ua/.trash-1784630749/tmp/ua-arch-analyze.cjs`, `.ua/.trash-1784630749/tmp/ua-arch-input.json`, `.ua/.trash-1784630749/tmp/ua-arch-results.json`, `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-1.json`, `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-10.json`, `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-11.json`, `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-12.json`, `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-2.json`, `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-3.json`, `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-4.json`, `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-5.json`, `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-6.json`, `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-7.json`, `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-8.json`, `.ua/.trash-1784630749/tmp/ua-file-analyzer-input-9.json`, `.ua/.trash-1784630749/tmp/ua-file-extract-results-1.json`, `.ua/.trash-1784630749/tmp/ua-file-extract-results-10.json`, `.ua/.trash-1784630749/tmp/ua-file-extract-results-11.json`, `.ua/.trash-1784630749/tmp/ua-file-extract-results-12.json`, `.ua/.trash-1784630749/tmp/ua-file-extract-results-2.json`, `.ua/.trash-1784630749/tmp/ua-file-extract-results-3.json`, `.ua/.trash-1784630749/tmp/ua-file-extract-results-4.json`, `.ua/.trash-1784630749/tmp/ua-file-extract-results-5.json`, `.ua/.trash-1784630749/tmp/ua-file-extract-results-6.json`, `.ua/.trash-1784630749/tmp/ua-file-extract-results-7.json`, `.ua/.trash-1784630749/tmp/ua-file-extract-results-8.json`, `.ua/.trash-1784630749/tmp/ua-file-extract-results-9.json`, `.ua/.trash-1784630749/tmp/ua-import-map-input.json`, `.ua/.trash-1784630749/tmp/ua-import-map-output.json`, `.ua/.trash-1784630749/tmp/ua-inline-validate.cjs`, `.ua/.trash-1784630749/tmp/ua-scan-files.json`, `.ua/.trash-1784630749/tmp/ua-tour-analyze.cjs`, `.ua/.trash-1784630749/tmp/ua-tour-input.json`, `.ua/.trash-1784630749/tmp/ua-tour-results.json`, `.ua/.trash-1784630749/tour.json`, `.ua/.understandignore`, `.ua/config.json`, `.ua/fingerprints.json`, `.ua/intermediate/scan-result.json`, `.ua/knowledge-graph.json`, `.ua/meta.json`, `.understand-anything`, `.understand-anything/.trash-1784630749/assemble-review.json`, `.understand-anything/.trash-1784630749/assembled-graph.json`, `.understand-anything/.trash-1784630749/batch-1-part-1.json`, `.understand-anything/.trash-1784630749/batch-1-part-2.json`, `.understand-anything/.trash-1784630749/batch-1-part-3.json`, `.understand-anything/.trash-1784630749/batch-1-part-4.json`, `.understand-anything/.trash-1784630749/batch-10.json`, `.understand-anything/.trash-1784630749/batch-11.json`, `.understand-anything/.trash-1784630749/batch-12.json`, `.understand-anything/.trash-1784630749/batch-2.json`, `.understand-anything/.trash-1784630749/batch-3-part-1.json`, `.understand-anything/.trash-1784630749/batch-3-part-2.json`, `.understand-anything/.trash-1784630749/batch-3-part-3.json`, `.understand-anything/.trash-1784630749/batch-4.json`, `.understand-anything/.trash-1784630749/batch-5.json`, `.understand-anything/.trash-1784630749/batch-6.json`, `.understand-anything/.trash-1784630749/batch-7.json`, `.understand-anything/.trash-1784630749/batch-8.json`, `.understand-anything/.trash-1784630749/batch-9.json`, `.understand-anything/.trash-1784630749/batches.json`, `.understand-anything/.trash-1784630749/fingerprint-input.json`, `.understand-anything/.trash-1784630749/layers.json`, `.understand-anything/.trash-1784630749/review.json`, `.understand-anything/.trash-1784630749/tmp/arch-input.json`, `.understand-anything/.trash-1784630749/tmp/build-tour-input.cjs`, `.understand-anything/.trash-1784630749/tmp/gen_batch1.py`, `.understand-anything/.trash-1784630749/tmp/ua-arch-analyze.cjs`, `.understand-anything/.trash-1784630749/tmp/ua-arch-input.json`, `.understand-anything/.trash-1784630749/tmp/ua-arch-results.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-1.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-10.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-11.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-12.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-2.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-3.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-4.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-5.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-6.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-7.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-8.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-analyzer-input-9.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-1.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-10.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-11.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-12.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-2.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-3.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-4.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-5.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-6.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-7.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-8.json`, `.understand-anything/.trash-1784630749/tmp/ua-file-extract-results-9.json`, `.understand-anything/.trash-1784630749/tmp/ua-import-map-input.json`, `.understand-anything/.trash-1784630749/tmp/ua-import-map-output.json`, `.understand-anything/.trash-1784630749/tmp/ua-inline-validate.cjs`, `.understand-anything/.trash-1784630749/tmp/ua-scan-files.json`, `.understand-anything/.trash-1784630749/tmp/ua-tour-analyze.cjs`, `.understand-anything/.trash-1784630749/tmp/ua-tour-input.json`, `.understand-anything/.trash-1784630749/tmp/ua-tour-results.json`, `.understand-anything/.trash-1784630749/tour.json`, `.understand-anything/.understandignore`, `.understand-anything/config.json`, `.understand-anything/fingerprints.json`, `.understand-anything/intermediate/scan-result.json`, `.understand-anything/knowledge-graph.json`, `.understand-anything/meta.json`, `plugins/project-intelligence/tests/test_project_intel.py`
- Git 提交：`ad7c8ad4d3aee7801ad126ac3e69d08736dcf24e`
- 代码快照：`8b0875467958368fb308fd3375fcdafb96204f6b632d85e3cda4df42821ab56e`
- 命令：`python3 plugins/project-intelligence/tests/test_project_intel.py GraphToolCommandTests.test_detect_graph_actions_marks_gitnexus_as_download_and_run StabilityAndPackagingTests.test_understand_graph_uses_windows_portable_directory`

```text
..
----------------------------------------------------------------------
Ran 2 tests in 0.008s

OK
```
