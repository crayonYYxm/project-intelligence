# 需求与 Bug 目录使用编号加标题 · 测试报告

- 需求号：`LOCAL-20260727-141720`
- 当前状态：verified
- 证据数量：6

## 验收标准映射

- AC-01：已记录证据 — 新建 Requirement 或 Bug 后，实际目录名为规范化编号-安全标题，且所有生成文档与 manifest artifact 路径均指向该目录。
- AC-02：已记录证据 — 标题含空格、中文、斜杠、反斜杠、Windows 禁止字符、控制字符或尾随句点/空格时，生成结果跨平台安全、非空且稳定。
- AC-03：已记录证据 — 仅提供需求编号时，可继续读取和更新新的编号-标题目录、历史仅编号目录及旧版 by-id/<id> 目录。
- AC-04：已记录证据 — 需求查询、旧布局迁移、测试证据与收口路径不因目录名变化而失效；同编号存在多个档案时返回明确错误。

## 执行记录

### TEST-01 · unit

- 阶段：red
- 结果：预期失败已复现
- 验收标准：AC-01, AC-02, AC-03, AC-04
- 文件范围：src/__tests__/requirement-command.test.ts, src/__tests__/state-machine.test.ts, src/commands/orchestration.ts, src/commands/requirement.ts, src/requirements/layout.ts, src/requirements/scope.ts, src/requirements/state-machine.ts
- 明细报告：`.project-intel/requirements/LOCAL-20260727-141720/test-reports/TEST-01-unit.md`

#### 执行明细

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

### TEST-02 · unit

- 阶段：green
- 结果：passed
- 验收标准：AC-01, AC-02, AC-03, AC-04
- 文件范围：src/__tests__/requirement-command.test.ts, src/__tests__/state-machine.test.ts, src/commands/orchestration.ts, src/commands/requirement.ts, src/requirements/layout.ts, src/requirements/scope.ts, src/requirements/state-machine.ts
- 明细报告：`.project-intel/requirements/LOCAL-20260727-141720/test-reports/TEST-02-unit.md`

#### 执行明细

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

### TEST-03 · unit

- 阶段：regression
- 结果：passed
- 验收标准：AC-01, AC-02, AC-03, AC-04
- 文件范围：README.md, plugins/project-intelligence/assets/plugin-intro.html, plugins/project-intelligence/skills/project-design/SKILL.md, plugins/project-intelligence/skills/project-finish/SKILL.md, plugins/project-intelligence/skills/project-intake/SKILL.md, plugins/project-intelligence/skills/project-knowledge/SKILL.md, plugins/project-intelligence/skills/project-plan/SKILL.md, plugins/project-intelligence/skills/project-spec/SKILL.md, plugins/project-intelligence/skills/project-task/SKILL.md, src/__tests__/requirement-command.test.ts, src/__tests__/review-finish-graph.test.ts, src/__tests__/state-machine.test.ts, src/__tests__/test-evidence.test.ts, src/commands/agent-rules.ts, src/commands/init.ts, src/commands/orchestration.ts, src/commands/requirement.ts, src/requirements/layout.ts, src/requirements/scope.ts, src/requirements/state-machine.ts
- 明细报告：`.project-intel/requirements/LOCAL-20260727-141720/test-reports/TEST-03-unit.md`

#### 执行明细

    # LOCAL-20260727-141720 测试报告
    
    - 测试类型：unit
    - 阶段：regression
    - 结果：passed
    - 验收标准：AC-01,AC-02,AC-03,AC-04
    - 文件范围：README.md, plugins/project-intelligence/assets/plugin-intro.html, plugins/project-intelligence/skills/project-design/SKILL.md, plugins/project-intelligence/skills/project-finish/SKILL.md, plugins/project-intelligence/skills/project-intake/SKILL.md, plugins/project-intelligence/skills/project-knowledge/SKILL.md, plugins/project-intelligence/skills/project-plan/SKILL.md, plugins/project-intelligence/skills/project-spec/SKILL.md, plugins/project-intelligence/skills/project-task/SKILL.md, src/__tests__/requirement-command.test.ts, src/__tests__/review-finish-graph.test.ts, src/__tests__/state-machine.test.ts, src/__tests__/test-evidence.test.ts, src/commands/agent-rules.ts, src/commands/init.ts, src/commands/orchestration.ts, src/commands/requirement.ts, src/requirements/layout.ts, src/requirements/scope.ts, src/requirements/state-machine.ts
    
    ## 执行结果
    
    ### npm test
    
    - exitCode: 0
    - executedCount: 259
    
    ```text
    Skill behavior scenario contracts verified: 27 scenarios, 17 skills
    ▶ maskCommentsAndStrings
      ✔ masks line and block comments and string contents (1.010917ms)
    ✔ maskCommentsAndStrings (2.118666ms)
    ▶ scanBackendFile
      ✔ extracts a Spring controller endpoint and methods (.java) (3.746666ms)
      ✔ extracts Python def/class and Flask routes (.py) (1.189875ms)
      ✔ classifies a service by name and extracts transaction signals (0.211583ms)
      ✔ extracts config keys from yaml (0.248667ms)
      ✔ classifies repository files and extracts SQL ops from xml mapper (0.279209ms)
      ✔ extracts permission signals (1.1015ms)
      ✔ extracts error code signals (0.222666ms)
      ✔ requires bound framework imports and keeps Django class views (0.312833ms)
      ✔ labels malformed Python without accepting route facts (0.166292ms)
      ✔ applies configured backend entrypoint rules (0.343792ms)
    ✔ scanBackendFile (8.262417ms)
    ▶ BACKEND_SUFFIXES
      ✔ includes java, kt, py, go, ts, js (0.087792ms)
    ✔ BACKEND_SUFFIXES (0.156958ms)
    ▶ cli snapshot contract (AC-02)
      ✔ loads a well-formed snapshot (3.575583ms)
      ✔ captured every top-level command's help (1.522958ms)
      ✔ pins the JSON envelope shape on every probe (0.486209ms)
      ✔ the version command exits 0 and prints a semver (0.390208ms)
      ✔ usage errors exit non-zero with a non-ok envelope (0.134833ms)
    ✔ cli snapshot contract (AC-02) (7.470041ms)
    ▶ live Node CLI contract (AC-02/AC-10)
      ✔ dist/cli.js exists and is runnable (0.152375ms)
      ✔ version command exits 0 and prints a semver (118.244666ms)
      ✔ --version flag exits 0 and prints a semver (114.80975ms)
      ✔ every baseline command's --help is byte-for-byte compatible (1839.669083ms)
      ✔ top-level --help is byte-for-byte compatible (76.568709ms)
      ✔ top-level --help output contains all baseline commands (69.614041ms)
      ✔ subcommand --help output contains usage line and key flags (280.043875ms)
      ✔ unknown command exits 2 (71.113375ms)
      ✔ unknown flag exits 2 (69.409459ms)
      ✔ version --json produces a valid envelope with version field (71.731708ms)
      ✔ doctor --json produces a valid envelope with runtime=node (75.184917ms)
      ✔ usage error --json produces ok=false envelope (71.408292ms)
    ✔ live Node CLI contract (AC-02/AC-10) (2858.725291ms)
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
      ✔ prints --version alone (2.215416ms)
      ✔ prints --version envelope in json mode (0.25075ms)
      ✔ runs a registered command (text mode) (0.2535ms)
      ✔ runs a registered command (json mode) with envelope (0.097875ms)
      ✔ rejects unknown command with exit 2 (text) (0.771334ms)
      ✔ rejects unknown command with exit 2 (json envelope) (3.301958ms)
      ✔ surfaces usage errors as exit 2 (3.81225ms)
      ✔ surfaces runtime errors as exit 1 (0.344375ms)
      ✔ rejects missing subcommand (json exit 2) (0.179708ms)
      ✔ subcommand --help is intercepted and exits 0 (text) (0.310042ms)
      ✔ subcommand -h is intercepted and exits 0 (json) (0.152375ms)
      ✔ rejects unknown long flag with exit 2 (text) (0.064625ms)
      ✔ rejects unknown long flag with exit 2 (json envelope) (0.063958ms)
      ✔ accepts known value flag and its value (not mistaken for a flag) (0.0605ms)
      ✔ rejects unknown flag even after a valid value flag (0.053875ms)
    ✔ dispatch (13.507959ms)
    ▶ normalizeForCompare
      ✔ masks ISO-8601 timestamps (2.65075ms)
      ✔ masks 40-char git hashes (0.159334ms)
      ✔ masks epoch-second/milli integers (0.061791ms)
      ✔ masks absolute repo roots (POSIX) (0.054833ms)
      ✔ normalizes Windows backslashes and masks sample root (0.369042ms)
      ✔ collapses mtime integers regardless of value (0.192875ms)
      ✔ applies longest-root-first masking so nested roots win (0.13075ms)
    ✔ normalizeForCompare (5.168417ms)
    ▶ compareJsonOutputs
      ✔ returns null for equal normalized values (0.312291ms)
      ✔ reports the first differing path (0.136541ms)
      ✔ reports missing keys with direction (0.169ms)
      ✔ reports array length mismatches (0.057042ms)
    ✔ compareJsonOutputs (0.879917ms)
    ▶ frontend scanner
      ✔ extracts vue component props/emits (3.819167ms)
      ✔ extracts react props from interface (0.427542ms)
      ✔ extracts hooks by use* filename (0.178666ms)
      ✔ extracts routes and redundancy candidates (1.015208ms)
      ✔ extractVueProps from defineProps object form (1.410041ms)
      ✔ extractEmits filters to valid names (0.157458ms)
      ✔ extractApiEndpoints from request/fetch calls (0.550375ms)
    ✔ frontend scanner (10.8335ms)
    ▶ files scanner
      ✔ discoverFiles walks and categorizes (1.512833ms)
      ✔ discoverFiles excludes node_modules/.git (0.381417ms)
      ✔ uses stable code-point ordering across operating systems (0.286792ms)
      ✔ categorize and simpleMatch basics (0.146125ms)
    ✔ files scanner (2.541958ms)
    ▶ incremental scan cache
      ✔ reuses unchanged frontend facts without reading the file again (0.223458ms)
      ✔ uses nanosecond-compatible file signatures and invalidates changed entries (0.315292ms)
    ✔ incremental scan cache (0.580584ms)
    ▶ quality scanner
      ✔ packageFrameworks detects Vue+TypeScript from deps (0.107459ms)
      ✔ detectPackage reads package.json scripts and frameworks (0.864167ms)
      ✔ packageManager detects npm/pnpm/yarn by lockfile (0.53075ms)
      ✔ detectQualityCommands: Python project STILL recognizes pytest/ruff/mypy (P1.3) (0.573667ms)
      ✔ detectQualityCommands: JS project infers eslint/tsc from config presence (0.954291ms)
    ✔ quality scanner (3.254834ms)
    FixtureGraph 已安装，开始运行分析："/opt/homebrew/Cellar/node/26.3.0/bin/node" -e "process.stdout.write('graph-ok')"
    FixtureGraph 开始执行，超时上限 900 秒。
    GitNexus：仓库内 runner 需要显式使用 --allow-repo-runner。
    ▶ graph command authorization
      ✔ preserves and detects Windows absolute paths on POSIX (1.777542ms)
      ✔ allows repository-contained absolute paths and rejects outside paths (0.387417ms)
      ✔ requires explicit permission for repo runners and environment commands (0.32575ms)
    ✔ graph command authorization (3.371083ms)
    ▶ graph setup execution
      ✔ executes an authorized installed analyzer and captures evidence (87.326209ms)
      ✔ records a skipped result instead of executing an unauthorized runner (0.615125ms)
    ✔ graph setup execution (88.129791ms)
    ▶ adapter block management
      ✔ rejects paths outside the allowed set (0.727333ms)
      ✔ replaceSingleManagedBlock creates then updates (0.327667ms)
      ✔ upsert then remove a managed block (0.8585ms)
    ✔ adapter block management (3.397875ms)
    ▶ adapters command family
      ✔ apply writes codex + claude blocks; status reports current (2.06675ms)
      ✔ preview is dry-run (no files written) (0.312625ms)
      ✔ remove clears blocks (0.8115ms)
      ✔ status --check returns non-zero when not current (0.647834ms)
      ✔ adapterTargets both returns 3 targets (codex, claude, claude-nested) (1.525292ms)
    ✔ adapters command family (5.713ms)
    ▶ top-level install command
      ✔ creates .claude/ and applies adapters; --hooks writes templates (2.664625ms)
    ✔ top-level install command (2.827875ms)
    ▶ agent install command
      ✔ agentInstallCommands builds codex+claude for all (0.28725ms)
      ✔ --dry-run classifies present when cli exists, missing otherwise (0.682833ms)
      ✔ rejects invalid target (0.255167ms)
    ✔ agent install command (1.37025ms)
    ▶ git hooks (AC-07: no python3)
      ✔ hook body calls project-intel (Node CLI), never python3 (0.120167ms)
      ✔ writeHookTemplates writes 3 hooks + README under .project-intel/hooks (0.915959ms)
    ✔ git hooks (AC-07: no python3) (1.137209ms)
    ▶ sanitizeErrorText
      ✔ redacts authorization bearer tokens (1.569583ms)
      ✔ redacts cookies (0.164916ms)
      ✔ redacts password/secret/token/api_key (0.06475ms)
      ✔ redacts aws credentials (0.043ms)
      ✔ redacts URL userinfo (0.037917ms)
      ✔ leaves benign text intact (0.779042ms)
    ✔ sanitizeErrorText (4.186167ms)
    ▶ extractGlobalJson
      ✔ strips --json and reports mode (1.565875ms)
      ✔ preserves argv when --json absent (0.178291ms)
    ✔ extractGlobalJson (1.971292ms)
    ▶ jsonEnvelope
      ✔ shapes a success envelope (0.130625ms)
      ✔ classifies exit 2 as USAGE_ERROR with sanitized in-place error (0.09ms)
      ✔ classifies non-2 failure as COMMAND_FAILED with default message (0.052708ms)
      ✔ trims the output field (0.032875ms)
    ✔ jsonEnvelope (0.409791ms)
    ▶ parseGlobal / splitArgv
      ✔ parses --project value (0.095667ms)
      ✔ parses --project= form (0.033833ms)
      ✔ parses --json (0.030041ms)
      ✔ rejects unknown long option before subcommand with exit-2 UsageError (0.067667ms)
      ✔ splitArgv separates global, command, and rest (0.070334ms)
      ✔ splitArgv returns null when no subcommand (0.031125ms)
    ✔ parseGlobal / splitArgv (0.44625ms)
    ▶ withLock (in-process)
      ✔ blocks same-process re-entrant acquire (no deadlock) (63.649416ms)
      ✔ releases the lockfile after the critical section (0.353083ms)
    ✔ withLock (in-process) (64.597083ms)
    ▶ withLock (multi-process contention)
      ✔ grants exclusive access across child processes (1048.862125ms)
    ✔ withLock (multi-process contention) (1048.937416ms)
    ▶ paths
      ✔ toPosix converts separators (1.000167ms)
      ✔ normalizeBusinessPath strips leading ./ and normalizes (0.202875ms)
      ✔ isAbsolutePathLike detects posix, windows drive, unc (0.096333ms)
      ✔ resolveInside rejects traversal outside root (0.7495ms)
      ✔ expandUser leaves non-home paths alone (0.082333ms)
    ✔ paths (3.330625ms)
    ▶ atomic-write
      ✔ writes text with a trailing newline, UTF-8 preserved (6.869834ms)
      ✔ writes JSON without ascii escaping and creates parent dirs (5.4825ms)
      ✔ preserves existing file mode (14.637167ms)
      ✔ loadJson returns default on missing/corrupt (0.654708ms)
      ✔ loadJsonStrict raises on corrupt/non-object (0.608166ms)
    ✔ atomic-write (28.533833ms)
    中文测试
    {
      "name": "中文"
    }
    err 中文
    ▶ subprocess.spawn (argv)
      ✔ runs a successful command and captures output (121.181833ms)
      ✔ returns 127 when the binary is missing (9.681375ms)
      ✔ returns a non-zero code on argv usage error (18.257125ms)
    ✔ subprocess.spawn (argv) (151.560416ms)
    ▶ subprocess.which / commandExists
      ✔ finds node on PATH (1.348083ms)
      ✔ returns null for a missing command (0.6455ms)
    ✔ subprocess.which / commandExists (2.195833ms)
    ▶ subprocess.runShell (shell form)
      ✔ supports pipes and redirects (8.141209ms)
      ✔ supports environment variable expansion (10.487333ms)
      ✔ returns 0 for a true compound command (5.98075ms)
      ✔ surfaces non-zero exit of a failed command (4.165417ms)
    ✔ subprocess.runShell (shell form) (29.114875ms)
    ▶ output (UTF-8)
      ✔ print writes a UTF-8 line including Chinese (0.655917ms)
      ✔ printJson renders without ASCII escaping (0.10575ms)
      ✔ printError writes to stderr (0.073833ms)
    ✔ output (UTF-8) (0.953792ms)
    ▶ io.yaml
      ✔ parses flat key: value (1.721917ms)
      ✔ strips quoted values (0.108125ms)
      ✔ coerces scalars (0.186875ms)
    ✔ io.yaml (2.120458ms)
    ▶ io.markdown
      ✔ parses ATX headings with level and text (0.32025ms)
      ✔ normalizeHeading collapses whitespace (0.054166ms)
      ✔ hasMeaningfulContent rejects blank/placeholder (0.205ms)
    ✔ io.markdown (0.682875ms)
    已初始化 .project-intel，索引了 4 个文本文件。
    {
      "dryRun": true,
      "manifest": {
        "schemaVersion": 2,
        "toolVersion": "0.7.1",
        "projectRoot": ".",
        "generatedAt": "2026-07-27T06:30:58.669Z",
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
        "generatedAt": "2026-07-27T06:30:58.720Z",
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
        ".project-intel/requirements/<requirement-id>-<title>/*.md"
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
      ✔ writes the .project-intel layout (manifest/config/knowledge/status) (198.125458ms)
      ✔ --dry-run does not write files (56.676333ms)
      ✔ refresh re-writes without tooling (502.2875ms)
      ✔ strict + no-graph is a usage error (3.657166ms)
      ✔ ensureProjectIntelGitignore writes local-only rules (0.72175ms)
    ✔ init command (762.511417ms)
    ▶ doctor command
      ✔ reports node runtime, not python (8.093041ms)
      ✔ detects initialized state after init (431.989208ms)
    ✔ doctor command (440.295042ms)
    ▶ check command
      ✔ passes with no hard rules configured (326.19ms)
      ✔ --dry-run does not write status (320.939291ms)
    ✔ check command (647.287ms)
    ▶ standards inference
      ✔ infers PascalCase naming from >=3 pascal components (0.313958ms)
      ✔ infers backend Service suffix from >=2 services (0.080042ms)
      ✔ infers ui-pattern from redundancy candidates (0.051792ms)
      ✔ ports backend API, layering and operational inference categories (0.113916ms)
    ✔ standards inference (0.638ms)
    ▶ project domain candidates
      ✔ aggregates repeated non-generic parent segments in stable order (0.660666ms)
    ✔ project domain candidates (0.695ms)
    ▶ standards documents
      ✔ renders detailed frontend and backend facts instead of count-only placeholders (0.932ms)
    ✔ standards documents (1.025792ms)
    ▶ hard rules engine
      ✔ returns no violations with the empty default set (0.069333ms)
      ✔ surfaces a registered rule violation (0.070958ms)
    ✔ hard rules engine (0.187667ms)
    已初始化 .project-intel，索引了 3 个文本文件。
    已初始化 .project-intel，索引了 3 个文本文件。
    ▶ requirement command dispatcher
      ✔ status returns state for a created requirement (39.305584ms)
      ✔ intake persists document actions and later selection blocks generation (46.075708ms)
      ✔ acceptance set persists AC-01..AC-02 (42.2445ms)
      ✔ query reads v2 and legacy by-id archives and supports --file (50.742583ms)
      ✔ test-contract set requires --kind and --report-action (91.002292ms)
      ✔ test-contract register validates and normalizes a structured report path (119.532ms)
      ✔ ready -> begin through the dispatcher (849.149417ms)
      ✔ reopen after close (66.983291ms)
      ✔ generate enforces lifecycle order and creates a requirement scaffold (69.45375ms)
      ✔ generate refuses implicit overwrite and --replace really rebuilds the scaffold (85.848334ms)
      ✔ rejects missing --requirement-id (3.705958ms)
      ✔ add persists artifact registration into the manifest (423.905458ms)
      ✔ rejects arbitrary delivery-document content (172.769125ms)
      ✔ design registration rejects missing source evidence paths (270.620542ms)
      ✔ design registration ignores symbols that exist only in comments or strings (226.026458ms)
      ✔ add registers a structured test report as current requirement evidence (505.809375ms)
      ✔ diagnose records a Bug root cause (ticketKind=bug) (96.915542ms)
      ✔ diagnose rejects missing source evidence paths (67.744542ms)
      ✔ diagnose rejects symbols that only appear in comments or strings (74.160709ms)
      ✔ diagnose rejects non-bug requirements (33.620042ms)
      ✔ defer adds a readiness blocker for design (31.180625ms)
      ✔ resolve-finding marks a review finding resolved (54.86925ms)
      ✔ resolve-finding rejects unknown finding IDs (29.636958ms)
    ✔ requirement command dispatcher (3452.897292ms)
    ▶ requirement layout
      ✔ artifactFilename maps known types (0.0605ms)
      ✔
    ```

### TEST-04 · unit

- 阶段：regression
- 结果：passed
- 验收标准：AC-01, AC-02, AC-03, AC-04
- 文件范围：README.md, plugins/project-intelligence/assets/plugin-intro.html, plugins/project-intelligence/skills/project-design/SKILL.md, plugins/project-intelligence/skills/project-finish/SKILL.md, plugins/project-intelligence/skills/project-intake/SKILL.md, plugins/project-intelligence/skills/project-knowledge/SKILL.md, plugins/project-intelligence/skills/project-plan/SKILL.md, plugins/project-intelligence/skills/project-spec/SKILL.md, plugins/project-intelligence/skills/project-task/SKILL.md, src/__tests__/requirement-command.test.ts, src/__tests__/review-finish-graph.test.ts, src/__tests__/state-machine.test.ts, src/__tests__/test-evidence.test.ts, src/commands/agent-rules.ts, src/commands/init.ts, src/commands/orchestration.ts, src/commands/requirement.ts, src/requirements/layout.ts, src/requirements/scope.ts, src/requirements/state-machine.ts
- 明细报告：`.project-intel/requirements/LOCAL-20260727-141720/test-reports/TEST-04-unit.md`

#### 执行明细

    # LOCAL-20260727-141720 测试报告
    
    - 测试类型：unit
    - 阶段：regression
    - 结果：passed
    - 验收标准：AC-01,AC-02,AC-03,AC-04
    - 文件范围：README.md, plugins/project-intelligence/assets/plugin-intro.html, plugins/project-intelligence/skills/project-design/SKILL.md, plugins/project-intelligence/skills/project-finish/SKILL.md, plugins/project-intelligence/skills/project-intake/SKILL.md, plugins/project-intelligence/skills/project-knowledge/SKILL.md, plugins/project-intelligence/skills/project-plan/SKILL.md, plugins/project-intelligence/skills/project-spec/SKILL.md, plugins/project-intelligence/skills/project-task/SKILL.md, src/__tests__/requirement-command.test.ts, src/__tests__/review-finish-graph.test.ts, src/__tests__/state-machine.test.ts, src/__tests__/test-evidence.test.ts, src/commands/agent-rules.ts, src/commands/init.ts, src/commands/orchestration.ts, src/commands/requirement.ts, src/requirements/layout.ts, src/requirements/scope.ts, src/requirements/state-machine.ts
    
    ## 执行结果
    
    ### npm test
    
    - exitCode: 0
    - executedCount: 260
    
    ```text
    Skill behavior scenario contracts verified: 27 scenarios, 17 skills
    ▶ maskCommentsAndStrings
      ✔ masks line and block comments and string contents (1.102792ms)
    ✔ maskCommentsAndStrings (2.484417ms)
    ▶ scanBackendFile
      ✔ extracts a Spring controller endpoint and methods (.java) (2.981834ms)
      ✔ extracts Python def/class and Flask routes (.py) (2.227083ms)
      ✔ classifies a service by name and extracts transaction signals (4.697125ms)
      ✔ extracts config keys from yaml (2.565584ms)
      ✔ classifies repository files and extracts SQL ops from xml mapper (1.181458ms)
      ✔ extracts permission signals (0.265375ms)
      ✔ extracts error code signals (0.281875ms)
      ✔ requires bound framework imports and keeps Django class views (2.844583ms)
      ✔ labels malformed Python without accepting route facts (1.073375ms)
      ✔ applies configured backend entrypoint rules (0.220292ms)
    ✔ scanBackendFile (19.865792ms)
    ▶ BACKEND_SUFFIXES
      ✔ includes java, kt, py, go, ts, js (0.118708ms)
    ✔ BACKEND_SUFFIXES (0.213708ms)
    ▶ cli snapshot contract (AC-02)
      ✔ loads a well-formed snapshot (0.638917ms)
      ✔ captured every top-level command's help (0.702042ms)
      ✔ pins the JSON envelope shape on every probe (0.205333ms)
      ✔ the version command exits 0 and prints a semver (2.476167ms)
      ✔ usage errors exit non-zero with a non-ok envelope (0.56275ms)
    ✔ cli snapshot contract (AC-02) (5.621917ms)
    ▶ live Node CLI contract (AC-02/AC-10)
      ✔ dist/cli.js exists and is runnable (0.344708ms)
      ✔ version command exits 0 and prints a semver (151.982625ms)
      ✔ --version flag exits 0 and prints a semver (116.90875ms)
      ✔ every baseline command's --help is byte-for-byte compatible (1928.83ms)
      ✔ top-level --help is byte-for-byte compatible (76.785416ms)
      ✔ top-level --help output contains all baseline commands (75.502792ms)
      ✔ subcommand --help output contains usage line and key flags (256.012708ms)
      ✔ unknown command exits 2 (74.610917ms)
      ✔ unknown flag exits 2 (77.118125ms)
      ✔ version --json produces a valid envelope with version field (89.45125ms)
      ✔ doctor --json produces a valid envelope with runtime=node (99.169ms)
      ✔ usage error --json produces ok=false envelope (77.628792ms)
    ✔ live Node CLI contract (AC-02/AC-10) (3025.023792ms)
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
      ✔ prints --version alone (1.033416ms)
      ✔ prints --version envelope in json mode (0.233209ms)
      ✔ runs a registered command (text mode) (0.347208ms)
      ✔ runs a registered command (json mode) with envelope (0.149458ms)
      ✔ rejects unknown command with exit 2 (text) (0.528917ms)
      ✔ rejects unknown command with exit 2 (json envelope) (0.63025ms)
      ✔ surfaces usage errors as exit 2 (0.357708ms)
      ✔ surfaces runtime errors as exit 1 (0.697583ms)
      ✔ rejects missing subcommand (json exit 2) (1.525625ms)
      ✔ subcommand --help is intercepted and exits 0 (text) (0.703ms)
      ✔ subcommand -h is intercepted and exits 0 (json) (0.274042ms)
      ✔ rejects unknown long flag with exit 2 (text) (0.089417ms)
      ✔ rejects unknown long flag with exit 2 (json envelope) (0.069458ms)
      ✔ accepts known value flag and its value (not mistaken for a flag) (0.047375ms)
      ✔ rejects unknown flag even after a valid value flag (0.079792ms)
    ✔ dispatch (8.766167ms)
    ▶ normalizeForCompare
      ✔ masks ISO-8601 timestamps (2.050375ms)
      ✔ masks 40-char git hashes (0.115625ms)
      ✔ masks epoch-second/milli integers (0.059334ms)
      ✔ masks absolute repo roots (POSIX) (0.055959ms)
      ✔ normalizes Windows backslashes and masks sample root (0.060583ms)
      ✔ collapses mtime integers regardless of value (0.14025ms)
      ✔ applies longest-root-first masking so nested roots win (0.102958ms)
    ✔ normalizeForCompare (3.472917ms)
    ▶ compareJsonOutputs
      ✔ returns null for equal normalized values (0.349208ms)
      ✔ reports the first differing path (0.164292ms)
      ✔ reports missing keys with direction (0.129541ms)
      ✔ reports array length mismatches (0.094833ms)
    ✔ compareJsonOutputs (1.029958ms)
    ▶ frontend scanner
      ✔ extracts vue component props/emits (5.029041ms)
      ✔ extracts react props from interface (2.951583ms)
      ✔ extracts hooks by use* filename (0.623375ms)
      ✔ extracts routes and redundancy candidates (1.123666ms)
      ✔ extractVueProps from defineProps object form (0.294541ms)
      ✔ extractEmits filters to valid names (0.369792ms)
      ✔ extractApiEndpoints from request/fetch calls (0.765375ms)
    ✔ frontend scanner (12.957333ms)
    ▶ files scanner
      ✔ discoverFiles walks and categorizes (1.008125ms)
      ✔ discoverFiles excludes node_modules/.git (1.099625ms)
      ✔ uses stable code-point ordering across operating systems (1.737ms)
      ✔ categorize and simpleMatch basics (0.177375ms)
    ✔ files scanner (4.263167ms)
    ▶ incremental scan cache
      ✔ reuses unchanged frontend facts without reading the file again (0.279375ms)
      ✔ uses nanosecond-compatible file signatures and invalidates changed entries (0.713ms)
    ✔ incremental scan cache (1.0735ms)
    ▶ quality scanner
      ✔ packageFrameworks detects Vue+TypeScript from deps (0.1805ms)
      ✔ detectPackage reads package.json scripts and frameworks (0.871084ms)
      ✔ packageManager detects npm/pnpm/yarn by lockfile (0.296958ms)
      ✔ detectQualityCommands: Python project STILL recognizes pytest/ruff/mypy (P1.3) (0.7165ms)
      ✔ detectQualityCommands: JS project infers eslint/tsc from config presence (0.529917ms)
    ✔ quality scanner (2.72825ms)
    FixtureGraph 已安装，开始运行分析："/opt/homebrew/Cellar/node/26.3.0/bin/node" -e "process.stdout.write('graph-ok')"
    FixtureGraph 开始执行，超时上限 900 秒。
    GitNexus：仓库内 runner 需要显式使用 --allow-repo-runner。
    ▶ graph command authorization
      ✔ preserves and detects Windows absolute paths on POSIX (2.026833ms)
      ✔ allows repository-contained absolute paths and rejects outside paths (0.344042ms)
      ✔ requires explicit permission for repo runners and environment commands (0.948959ms)
    ✔ graph command authorization (5.094667ms)
    ▶ graph setup execution
      ✔ executes an authorized installed analyzer and captures evidence (95.675125ms)
      ✔ records a skipped result instead of executing an unauthorized runner (0.50675ms)
    ✔ graph setup execution (96.702792ms)
    ▶ adapter block management
      ✔ rejects paths outside the allowed set (1.144292ms)
      ✔ replaceSingleManagedBlock creates then updates (0.366584ms)
      ✔ upsert then remove a managed block (1.492083ms)
    ✔ adapter block management (4.173459ms)
    ▶ adapters command family
      ✔ apply writes codex + claude blocks; status reports current (1.780834ms)
      ✔ preview is dry-run (no files written) (0.564083ms)
      ✔ remove clears blocks (1.242083ms)
      ✔ status --check returns non-zero when not current (0.710792ms)
      ✔ adapterTargets both returns 3 targets (codex, claude, claude-nested) (1.194875ms)
    ✔ adapters command family (5.886125ms)
    ▶ top-level install command
      ✔ creates .claude/ and applies adapters; --hooks writes templates (1.263625ms)
    ✔ top-level install command (1.33225ms)
    ▶ agent install command
      ✔ agentInstallCommands builds codex+claude for all (0.105834ms)
      ✔ --dry-run classifies present when cli exists, missing otherwise (0.530875ms)
      ✔ rejects invalid target (0.333459ms)
    ✔ agent install command (1.091ms)
    ▶ git hooks (AC-07: no python3)
      ✔ hook body calls project-intel (Node CLI), never python3 (4.133917ms)
      ✔ writeHookTemplates writes 3 hooks + README under .project-intel/hooks (7.844625ms)
    ✔ git hooks (AC-07: no python3) (12.184958ms)
    ▶ sanitizeErrorText
      ✔ redacts authorization bearer tokens (1.33225ms)
      ✔ redacts cookies (0.175875ms)
      ✔ redacts password/secret/token/api_key (0.111583ms)
      ✔ redacts aws credentials (0.0535ms)
      ✔ redacts URL userinfo (0.043625ms)
      ✔ leaves benign text intact (0.623125ms)
    ✔ sanitizeErrorText (3.926291ms)
    ▶ extractGlobalJson
      ✔ strips --json and reports mode (1.207ms)
      ✔ preserves argv when --json absent (0.084625ms)
    ✔ extractGlobalJson (1.527417ms)
    ▶ jsonEnvelope
      ✔ shapes a success envelope (0.111958ms)
      ✔ classifies exit 2 as USAGE_ERROR with sanitized in-place error (0.085583ms)
      ✔ classifies non-2 failure as COMMAND_FAILED with default message (0.04725ms)
      ✔ trims the output field (0.03025ms)
    ✔ jsonEnvelope (0.356125ms)
    ▶ parseGlobal / splitArgv
      ✔ parses --project value (0.098375ms)
      ✔ parses --project= form (0.032958ms)
      ✔ parses --json (0.168916ms)
      ✔ rejects unknown long option before subcommand with exit-2 UsageError (0.173417ms)
      ✔ splitArgv separates global, command, and rest (0.156583ms)
      ✔ splitArgv returns null when no subcommand (0.628417ms)
    ✔ parseGlobal / splitArgv (1.434958ms)
    ▶ withLock (in-process)
      ✔ blocks same-process re-entrant acquire (no deadlock) (68.432959ms)
      ✔ releases the lockfile after the critical section (0.667833ms)
    ✔ withLock (in-process) (73.855041ms)
    ▶ withLock (multi-process contention)
      ✔ grants exclusive access across child processes (1185.589792ms)
    ✔ withLock (multi-process contention) (1185.718542ms)
    ▶ paths
      ✔ toPosix converts separators (0.8065ms)
      ✔ normalizeBusinessPath strips leading ./ and normalizes (0.136709ms)
      ✔ isAbsolutePathLike detects posix, windows drive, unc (0.141875ms)
      ✔ resolveInside rejects traversal outside root (0.725875ms)
      ✔ expandUser leaves non-home paths alone (0.0745ms)
    ✔ paths (3.044041ms)
    ▶ atomic-write
      ✔ writes text with a trailing newline, UTF-8 preserved (8.951958ms)
      ✔ writes JSON without ascii escaping and creates parent dirs (5.724125ms)
      ✔ preserves existing file mode (8.859292ms)
      ✔ loadJson returns default on missing/corrupt (0.406041ms)
      ✔ loadJsonStrict raises on corrupt/non-object (0.406833ms)
    ✔ atomic-write (24.595084ms)
    中文测试
    {
      "name": "中文"
    }
    err 中文
    ▶ subprocess.spawn (argv)
      ✔ runs a successful command and captures output (95.86425ms)
      ✔ returns 127 when the binary is missing (8.102375ms)
      ✔ returns a non-zero code on argv usage error (28.262834ms)
    ✔ subprocess.spawn (argv) (135.354083ms)
    ▶ subprocess.which / commandExists
      ✔ finds node on PATH (0.405625ms)
      ✔ returns null for a missing command (1.0185ms)
    ✔ subprocess.which / commandExists (1.574208ms)
    ▶ subprocess.runShell (shell form)
      ✔ supports pipes and redirects (10.779333ms)
      ✔ supports environment variable expansion (11.147958ms)
      ✔ returns 0 for a true compound command (6.191917ms)
      ✔ surfaces non-zero exit of a failed command (7.274958ms)
    ✔ subprocess.runShell (shell form) (36.0115ms)
    ▶ output (UTF-8)
      ✔ print writes a UTF-8 line including Chinese (0.411625ms)
      ✔ printJson renders without ASCII escaping (0.233792ms)
      ✔ printError writes to stderr (0.068125ms)
    ✔ output (UTF-8) (0.81625ms)
    ▶ io.yaml
      ✔ parses flat key: value (1.52925ms)
      ✔ strips quoted values (0.088375ms)
      ✔ coerces scalars (1.299167ms)
    ✔ io.yaml (2.990042ms)
    ▶ io.markdown
      ✔ parses ATX headings with level and text (0.15ms)
      ✔ normalizeHeading collapses whitespace (0.034ms)
      ✔ hasMeaningfulContent rejects blank/placeholder (0.115333ms)
    ✔ io.markdown (0.34375ms)
    已初始化 .project-intel，索引了 4 个文本文件。
    {
      "dryRun": true,
      "manifest": {
        "schemaVersion": 2,
        "toolVersion": "0.7.1",
        "projectRoot": ".",
        "generatedAt": "2026-07-27T06:32:30.083Z",
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
        "generatedAt": "2026-07-27T06:32:30.124Z",
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
        ".project-intel/requirements/<requirement-id>-<title>/*.md"
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
      ✔ writes the .project-intel layout (manifest/config/knowledge/status) (226.745166ms)
      ✔ --dry-run does not write files (43.495667ms)
      ✔ refresh re-writes without tooling (550.445083ms)
      ✔ strict + no-graph is a usage error (4.091625ms)
      ✔ ensureProjectIntelGitignore writes local-only rules (4.023208ms)
    ✔ init command (832.715875ms)
    ▶ doctor command
      ✔ reports node runtime, not python (25.581375ms)
      ✔ detects initialized state after init (395.740125ms)
    ✔ doctor command (421.437167ms)
    ▶ check command
      ✔ passes with no hard rules configured (323.897042ms)
      ✔ --dry-run does not write status (359.818791ms)
    ✔ check command (683.831792ms)
    ▶ standards inference
      ✔ infers PascalCase naming from >=3 pascal components (0.278834ms)
      ✔ infers backend Service suffix from >=2 services (0.082666ms)
      ✔ infers ui-pattern from redundancy candidates (0.043208ms)
      ✔ ports backend API, layering and operational inference categories (0.119167ms)
    ✔ standards inference (0.591042ms)
    ▶ project domain candidates
      ✔ aggregates repeated non-generic parent segments in stable order (0.591792ms)
    ✔ project domain candidates (0.617166ms)
    ▶ standards documents
      ✔ renders detailed frontend and backend facts instead of count-only placeholders (1.330958ms)
    ✔ standards documents (1.39225ms)
    ▶ hard rules engine
      ✔ returns no violations with the empty default set (0.097708ms)
      ✔ surfaces a registered rule violation (0.121291ms)
    ✔ hard rules engine (0.303292ms)
    已初始化 .project-intel，索引了 3 个文本文件。
    已初始化 .project-intel，索引了 3 个文本文件。
    ▶ requirement command dispatcher
      ✔ status returns state for a created requirement (62.625583ms)
      ✔ plan writes into the resolved id-title requirement directory (69.262708ms)
      ✔ intake persists document actions and later selection blocks generation (77.220833ms)
      ✔ acceptance set persists AC-01..AC-02 (65.902084ms)
      ✔ query reads v2 and legacy by-id archives and supports --file (75.328417ms)
      ✔ test-contract set requires --kind and --report-action (114.996917ms)
      ✔ test-contract register validates and normalizes a structured report path (104.071125ms)
      ✔ ready -> begin through the dispatcher (798.103708ms)
      ✔ reopen after close (78.66275ms)
      ✔ generate enforces lifecycle order and creates a requirement scaffold (62.154125ms)
      ✔ generate refuses implicit overwrite and --replace really rebuilds the scaffold (70.531084ms)
      ✔ rejects missing --requirement-id (3.21675ms)
      ✔ add persists artifact registration into the manifest (448.017458ms)
      ✔ rejects arbitrary delivery-document content (164.290334ms)
      ✔ design registration rejects missing source evidence paths (306.151709ms)
      ✔ design registration ignores symbols that exist only in comments or strings (234.459167ms)
      ✔ add registers a structured test report as current requirement evidence (577.951167ms)
      ✔ diagnose records a Bug root cause (ticketKind=bug) (102.398667ms)
      ✔ diagnose rejects missing source evidence paths (47.574333ms)
      ✔ diagnose rejects symbols that only appear in comments or strings (48.037709ms)
      ✔ diagnose rejects non-bug requirements (33.188958ms)
      ✔ defer adds a readiness blocker for design (29.749167ms)
      ✔ resolve-finding marks a review finding resolved (33.928375ms)
      ✔ resolve-finding rejects unknown finding IDs (35.032208ms)
    ✔ requirement command dispat
    ```

### TEST-05 · unit

- 阶段：regression
- 结果：passed
- 验收标准：AC-01, AC-02, AC-03, AC-04
- 文件范围：README.md, plugins/project-intelligence/assets/plugin-intro.html, plugins/project-intelligence/skills/project-design/SKILL.md, plugins/project-intelligence/skills/project-finish/SKILL.md, plugins/project-intelligence/skills/project-intake/SKILL.md, plugins/project-intelligence/skills/project-knowledge/SKILL.md, plugins/project-intelligence/skills/project-plan/SKILL.md, plugins/project-intelligence/skills/project-spec/SKILL.md, plugins/project-intelligence/skills/project-task/SKILL.md, src/__tests__/requirement-command.test.ts, src/__tests__/review-finish-graph.test.ts, src/__tests__/state-machine.test.ts, src/__tests__/test-evidence.test.ts, src/commands/agent-rules.ts, src/commands/init.ts, src/commands/orchestration.ts, src/commands/requirement.ts, src/requirements/layout.ts, src/requirements/scope.ts, src/requirements/state-machine.ts
- 明细报告：`.project-intel/requirements/LOCAL-20260727-141720/test-reports/TEST-05-unit.md`

#### 执行明细

    # LOCAL-20260727-141720 测试报告
    
    - 测试类型：unit
    - 阶段：regression
    - 结果：passed
    - 验收标准：AC-01,AC-02,AC-03,AC-04
    - 文件范围：README.md, plugins/project-intelligence/assets/plugin-intro.html, plugins/project-intelligence/skills/project-design/SKILL.md, plugins/project-intelligence/skills/project-finish/SKILL.md, plugins/project-intelligence/skills/project-intake/SKILL.md, plugins/project-intelligence/skills/project-knowledge/SKILL.md, plugins/project-intelligence/skills/project-plan/SKILL.md, plugins/project-intelligence/skills/project-spec/SKILL.md, plugins/project-intelligence/skills/project-task/SKILL.md, src/__tests__/requirement-command.test.ts, src/__tests__/review-finish-graph.test.ts, src/__tests__/state-machine.test.ts, src/__tests__/test-evidence.test.ts, src/commands/agent-rules.ts, src/commands/init.ts, src/commands/orchestration.ts, src/commands/requirement.ts, src/requirements/layout.ts, src/requirements/scope.ts, src/requirements/state-machine.ts
    
    ## 执行结果
    
    ### npm test
    
    - exitCode: 0
    - executedCount: 260
    
    ```text
    Skill behavior scenario contracts verified: 27 scenarios, 17 skills
    ▶ maskCommentsAndStrings
      ✔ masks line and block comments and string contents (1.026209ms)
    ✔ maskCommentsAndStrings (1.874667ms)
    ▶ scanBackendFile
      ✔ extracts a Spring controller endpoint and methods (.java) (7.64025ms)
      ✔ extracts Python def/class and Flask routes (.py) (2.225167ms)
      ✔ classifies a service by name and extracts transaction signals (0.540958ms)
      ✔ extracts config keys from yaml (0.982541ms)
      ✔ classifies repository files and extracts SQL ops from xml mapper (0.375584ms)
      ✔ extracts permission signals (0.345667ms)
      ✔ extracts error code signals (0.271875ms)
      ✔ requires bound framework imports and keeps Django class views (0.399542ms)
      ✔ labels malformed Python without accepting route facts (0.165708ms)
      ✔ applies configured backend entrypoint rules (0.581083ms)
    ✔ scanBackendFile (14.134875ms)
    ▶ BACKEND_SUFFIXES
      ✔ includes java, kt, py, go, ts, js (0.111375ms)
    ✔ BACKEND_SUFFIXES (0.188625ms)
    ▶ cli snapshot contract (AC-02)
      ✔ loads a well-formed snapshot (3.275291ms)
      ✔ captured every top-level command's help (2.886417ms)
      ✔ pins the JSON envelope shape on every probe (0.277417ms)
      ✔ the version command exits 0 and prints a semver (0.220167ms)
      ✔ usage errors exit non-zero with a non-ok envelope (0.138208ms)
    ✔ cli snapshot contract (AC-02) (7.510083ms)
    ▶ live Node CLI contract (AC-02/AC-10)
      ✔ dist/cli.js exists and is runnable (0.127792ms)
      ✔ version command exits 0 and prints a semver (118.5435ms)
      ✔ --version flag exits 0 and prints a semver (141.542709ms)
      ✔ every baseline command's --help is byte-for-byte compatible (2161.857042ms)
      ✔ top-level --help is byte-for-byte compatible (139.694792ms)
      ✔ top-level --help output contains all baseline commands (88.678958ms)
      ✔ subcommand --help output contains usage line and key flags (295.122625ms)
      ✔ unknown command exits 2 (73.473958ms)
      ✔ unknown flag exits 2 (72.734709ms)
      ✔ version --json produces a valid envelope with version field (77.8695ms)
      ✔ doctor --json produces a valid envelope with runtime=node (77.449084ms)
      ✔ usage error --json produces ok=false envelope (79.613666ms)
    ✔ live Node CLI contract (AC-02/AC-10) (3327.3975ms)
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
    无法识别的参数：--definitely-invalid
    无法识别的参数：--nope
    ▶ dispatch
      ✔ prints --version alone (1.443417ms)
      ✔ prints --version envelope in json mode (0.237125ms)
      ✔ runs a registered command (text mode) (0.332291ms)
      ✔ runs a registered command (json mode) with envelope (0.956792ms)
      ✔ rejects unknown command with exit 2 (text) (0.788083ms)
      ✔ rejects unknown command with exit 2 (json envelope) (0.731542ms)
      ✔ surfaces usage errors as exit 2 (0.533ms)
      ✔ surfaces runtime errors as exit 1 (0.254375ms)
      ✔ rejects missing subcommand (json exit 2) (0.155916ms)
      ✔ subcommand --help is intercepted and exits 0 (text) (0.2975ms)
      ✔ subcommand -h is intercepted and exits 0 (json) (0.171792ms)
      ✔ rejects unknown long flag with exit 2 (text) (0.096875ms)
      ✔ rejects unknown long flag with exit 2 (json envelope) (0.117291ms)
      ✔ accepts known value flag and its value (not mistaken for a flag) (0.148583ms)
      ✔ rejects unknown flag even after a valid value flag (0.099334ms)
    ✔ dispatch (7.832ms)
    ▶ normalizeForCompare
      ✔ masks ISO-8601 timestamps (2.464583ms)
      ✔ masks 40-char git hashes (0.083125ms)
      ✔ masks epoch-second/milli integers (0.050708ms)
      ✔ masks absolute repo roots (POSIX) (0.050708ms)
      ✔ normalizes Windows backslashes and masks sample root (0.113917ms)
      ✔ collapses mtime integers regardless of value (0.231ms)
      ✔ applies longest-root-first masking so nested roots win (0.153417ms)
    ✔ normalizeForCompare (4.3445ms)
    ▶ compareJsonOutputs
      ✔ returns null for equal normalized values (0.260625ms)
      ✔ reports the first differing path (0.12ms)
      ✔ reports missing keys with direction (0.210458ms)
      ✔ reports array length mismatches (0.09425ms)
    ✔ compareJsonOutputs (0.904167ms)
    ▶ frontend scanner
      ✔ extracts vue component props/emits (2.19475ms)
      ✔ extracts react props from interface (0.394459ms)
      ✔ extracts hooks by use* filename (0.180542ms)
      ✔ extracts routes and redundancy candidates (0.41775ms)
      ✔ extractVueProps from defineProps object form (0.13ms)
      ✔ extractEmits filters to valid names (0.048875ms)
      ✔ extractApiEndpoints from request/fetch calls (0.493542ms)
    ✔ frontend scanner (4.70825ms)
    ▶ files scanner
      ✔ discoverFiles walks and categorizes (1.332875ms)
      ✔ discoverFiles excludes node_modules/.git (0.370833ms)
      ✔ uses stable code-point ordering across operating systems (6.538792ms)
      ✔ categorize and simpleMatch basics (0.560625ms)
    ✔ files scanner (8.98975ms)
    ▶ incremental scan cache
      ✔ reuses unchanged frontend facts without reading the file again (1.255292ms)
      ✔ uses nanosecond-compatible file signatures and invalidates changed entries (0.560084ms)
    ✔ incremental scan cache (2.655875ms)
    ▶ quality scanner
      ✔ packageFrameworks detects Vue+TypeScript from deps (0.290833ms)
      ✔ detectPackage reads package.json scripts and frameworks (1.387042ms)
      ✔ packageManager detects npm/pnpm/yarn by lockfile (0.567167ms)
      ✔ detectQualityCommands: Python project STILL recognizes pytest/ruff/mypy (P1.3) (1.855708ms)
      ✔ detectQualityCommands: JS project infers eslint/tsc from config presence (1.204167ms)
    ✔ quality scanner (5.702167ms)
    FixtureGraph 已安装，开始运行分析："/opt/homebrew/Cellar/node/26.3.0/bin/node" -e "process.stdout.write('graph-ok')"
    FixtureGraph 开始执行，超时上限 900 秒。
    GitNexus：仓库内 runner 需要显式使用 --allow-repo-runner。
    ▶ graph command authorization
      ✔ preserves and detects Windows absolute paths on POSIX (2.073375ms)
      ✔ allows repository-contained absolute paths and rejects outside paths (0.166292ms)
      ✔ requires explicit permission for repo runners and environment commands (0.146333ms)
    ✔ graph command authorization (3.522584ms)
    ▶ graph setup execution
      ✔ executes an authorized installed analyzer and captures evidence (99.182667ms)
      ✔ records a skipped result instead of executing an unauthorized runner (0.463958ms)
    ✔ graph setup execution (99.790708ms)
    ▶ adapter block management
      ✔ rejects paths outside the allowed set (0.93175ms)
      ✔ replaceSingleManagedBlock creates then updates (0.405833ms)
      ✔ upsert then remove a managed block (1.912166ms)
    ✔ adapter block management (4.30775ms)
    ▶ adapters command family
      ✔ apply writes codex + claude blocks; status reports current (1.549209ms)
      ✔ preview is dry-run (no files written) (0.36075ms)
      ✔ remove clears blocks (0.768ms)
      ✔ status --check returns non-zero when not current (0.783417ms)
      ✔ adapterTargets both returns 3 targets (codex, claude, claude-nested) (1.535583ms)
    ✔ adapters command family (5.340083ms)
    ▶ top-level install command
      ✔ creates .claude/ and applies adapters; --hooks writes templates (2.055875ms)
    ✔ top-level install command (2.193542ms)
    ▶ agent install command
      ✔ agentInstallCommands builds codex+claude for all (0.122458ms)
      ✔ --dry-run classifies present when cli exists, missing otherwise (0.423292ms)
      ✔ rejects invalid target (0.148916ms)
    ✔ agent install command (0.771083ms)
    ▶ git hooks (AC-07: no python3)
      ✔ hook body calls project-intel (Node CLI), never python3 (0.228167ms)
      ✔ writeHookTemplates writes 3 hooks + README under .project-intel/hooks (1.1185ms)
    ✔ git hooks (AC-07: no python3) (1.431833ms)
    ▶ sanitizeErrorText
      ✔ redacts authorization bearer tokens (0.848167ms)
      ✔ redacts cookies (0.088708ms)
      ✔ redacts password/secret/token/api_key (0.095333ms)
      ✔ redacts aws credentials (0.052041ms)
      ✔ redacts URL userinfo (0.041375ms)
      ✔ leaves benign text intact (0.445041ms)
    ✔ sanitizeErrorText (2.517958ms)
    ▶ extractGlobalJson
      ✔ strips --json and reports mode (0.955375ms)
      ✔ preserves argv when --json absent (0.054792ms)
    ✔ extractGlobalJson (1.528167ms)
    ▶ jsonEnvelope
      ✔ shapes a success envelope (0.101875ms)
      ✔ classifies exit 2 as USAGE_ERROR with sanitized in-place error (0.07125ms)
      ✔ classifies non-2 failure as COMMAND_FAILED with default message (0.046958ms)
      ✔ trims the output field (0.030625ms)
    ✔ jsonEnvelope (0.34925ms)
    ▶ parseGlobal / splitArgv
      ✔ parses --project value (0.426375ms)
      ✔ parses --project= form (0.138333ms)
      ✔ parses --json (0.067416ms)
      ✔ rejects unknown long option before subcommand with exit-2 UsageError (0.136042ms)
      ✔ splitArgv separates global, command, and rest (0.121875ms)
      ✔ splitArgv returns null when no subcommand (0.05275ms)
    ✔ parseGlobal / splitArgv (1.104333ms)
    ▶ withLock (in-process)
      ✔ blocks same-process re-entrant acquire (no deadlock) (67.217208ms)
      ✔ releases the lockfile after the critical section (0.506666ms)
    ✔ withLock (in-process) (68.378917ms)
    ▶ withLock (multi-process contention)
      ✔ grants exclusive access across child processes (1339.147958ms)
    ✔ withLock (multi-process contention) (1339.229083ms)
    ▶ paths
      ✔ toPosix converts separators (1.209709ms)
      ✔ normalizeBusinessPath strips leading ./ and normalizes (0.349625ms)
      ✔ isAbsolutePathLike detects posix, windows drive, unc (0.165833ms)
      ✔ resolveInside rejects traversal outside root (0.655125ms)
      ✔ expandUser leaves non-home paths alone (0.135875ms)
    ✔ paths (4.003041ms)
    ▶ atomic-write
      ✔ writes text with a trailing newline, UTF-8 preserved (8.8685ms)
      ✔ writes JSON without ascii escaping and creates parent dirs (7.28025ms)
      ✔ preserves existing file mode (9.109125ms)
      ✔ loadJson returns default on missing/corrupt (1.691ms)
      ✔ loadJsonStrict raises on corrupt/non-object (0.835083ms)
    ✔ atomic-write (28.163792ms)
    中文测试
    {
      "name": "中文"
    }
    err 中文
    ▶ subprocess.spawn (argv)
      ✔ runs a successful command and captures output (214.023084ms)
      ✔ returns 127 when the binary is missing (3.659125ms)
      ✔ returns a non-zero code on argv usage error (39.29525ms)
    ✔ subprocess.spawn (argv) (257.736625ms)
    ▶ subprocess.which / commandExists
      ✔ finds node on PATH (0.274125ms)
      ✔ returns null for a missing command (0.388833ms)
    ✔ subprocess.which / commandExists (0.916417ms)
    ▶ subprocess.runShell (shell form)
      ✔ supports pipes and redirects (14.203042ms)
      ✔ supports environment variable expansion (13.159792ms)
      ✔ returns 0 for a true compound command (6.917166ms)
      ✔ surfaces non-zero exit of a failed command (11.321875ms)
    ✔ subprocess.runShell (shell form) (45.97275ms)
    ▶ output (UTF-8)
      ✔ print writes a UTF-8 line including Chinese (0.955166ms)
      ✔ printJson renders without ASCII escaping (0.176667ms)
      ✔ printError writes to stderr (0.10725ms)
    ✔ output (UTF-8) (1.441917ms)
    ▶ io.yaml
      ✔ parses flat key: value (2.017291ms)
      ✔ strips quoted values (0.305833ms)
      ✔ coerces scalars (0.143625ms)
    ✔ io.yaml (2.5555ms)
    ▶ io.markdown
      ✔ parses ATX headings with level and text (0.14075ms)
      ✔ normalizeHeading collapses whitespace (0.034417ms)
      ✔ hasMeaningfulContent rejects blank/placeholder (0.102292ms)
    ✔ io.markdown (0.317ms)
    已初始化 .project-intel，索引了 4 个文本文件。
    {
      "dryRun": true,
      "manifest": {
        "schemaVersion": 2,
        "toolVersion": "0.7.1",
        "projectRoot": ".",
        "generatedAt": "2026-07-27T06:36:46.462Z",
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
        "generatedAt": "2026-07-27T06:36:46.543Z",
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
        ".project-intel/requirements/<requirement-id>-<title>/*.md"
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
      ✔ writes the .project-intel layout (manifest/config/knowledge/status) (229.259458ms)
      ✔ --dry-run does not write files (92.376542ms)
      ✔ refresh re-writes without tooling (629.455583ms)
      ✔ strict + no-graph is a usage error (4.868542ms)
      ✔ ensureProjectIntelGitignore writes local-only rules (1.068166ms)
    ✔ init command (958.299375ms)
    ▶ doctor command
      ✔ reports node runtime, not python (9.443666ms)
      ✔ detects initialized state after init (292.6335ms)
    ✔ doctor command (302.253708ms)
    ▶ check command
      ✔ passes with no hard rules configured (422.678292ms)
      ✔ --dry-run does not write status (309.864417ms)
    ✔ check command (732.68925ms)
    ▶ standards inference
      ✔ infers PascalCase naming from >=3 pascal components (0.587083ms)
      ✔ infers backend Service suffix from >=2 services (0.241292ms)
      ✔ infers ui-pattern from redundancy candidates (0.133458ms)
      ✔ ports backend API, layering and operational inference categories (0.147209ms)
    ✔ standards inference (1.261875ms)
    ▶ project domain candidates
      ✔ aggregates repeated non-generic parent segments in stable order (0.665708ms)
    ✔ project domain candidates (0.7015ms)
    ▶ standards documents
      ✔ renders detailed frontend and backend facts instead of count-only placeholders (0.844291ms)
    ✔ standards documents (0.907917ms)
    ▶ hard rules engine
      ✔ returns no violations with the empty default set (0.114625ms)
      ✔ surfaces a registered rule violation (0.119792ms)
    ✔ hard rules engine (0.289417ms)
    已初始化 .project-intel，索引了 3 个文本文件。
    已初始化 .project-intel，索引了 3 个文本文件。
    ▶ requirement command dispatcher
      ✔ status returns state for a created requirement (62.09775ms)
      ✔ plan writes into the resolved id-title requirement directory (93.52125ms)
      ✔ intake persists document actions and later selection blocks generation (97.42275ms)
      ✔ acceptance set persists AC-01..AC-02 (93.479542ms)
      ✔ query reads v2 and legacy by-id archives and supports --file (139.775042ms)
      ✔ test-contract set requires --kind and --report-action (97.292083ms)
      ✔ test-contract register validates and normalizes a structured report path (88.0655ms)
      ✔ ready -> begin through the dispatcher (808.798875ms)
      ✔ reopen after close (76.7965ms)
      ✔ generate enforces lifecycle order and creates a requirement scaffold (80.213625ms)
      ✔ generate refuses implicit overwrite and --replace really rebuilds the scaffold (105.1835ms)
      ✔ rejects missing --requirement-id (3.2715ms)
      ✔ add persists artifact registration into the manifest (463.827125ms)
      ✔ rejects arbitrary delivery-document content (159.829541ms)
      ✔ design registration rejects missing source evidence paths (261.778375ms)
      ✔ design registration ignores symbols that exist only in comments or strings (280.981583ms)
      ✔ add registers a structured test report as current requirement evidence (458.88375ms)
      ✔ diagnose records a Bug root cause (ticketKind=bug) (120.761125ms)
      ✔ diagnose rejects missing source evidence paths (66.764833ms)
      ✔ diagnose rejects symbols that only appear in comments or strings (53.003375ms)
      ✔ diagnose rejects non-bug requirements (61.178ms)
      ✔ defer adds a readiness blocker for design (41.893333ms)
      ✔ resolve-finding marks a review finding resolved (56.471292ms)
      ✔ resolve-finding rejects unknown finding IDs (41.938791ms)
    ✔ requirement command dispatcher (3817.08129
    ```

### TEST-06 · unit

- 阶段：regression
- 结果：passed
- 验收标准：AC-01, AC-02, AC-03, AC-04
- 文件范围：README.md, plugins/project-intelligence/assets/plugin-intro.html, plugins/project-intelligence/skills/project-design/SKILL.md, plugins/project-intelligence/skills/project-finish/SKILL.md, plugins/project-intelligence/skills/project-intake/SKILL.md, plugins/project-intelligence/skills/project-knowledge/SKILL.md, plugins/project-intelligence/skills/project-plan/SKILL.md, plugins/project-intelligence/skills/project-spec/SKILL.md, plugins/project-intelligence/skills/project-task/SKILL.md, src/__tests__/requirement-command.test.ts, src/__tests__/review-finish-graph.test.ts, src/__tests__/state-machine.test.ts, src/__tests__/test-evidence.test.ts, src/commands/agent-rules.ts, src/commands/init.ts, src/commands/orchestration.ts, src/commands/requirement.ts, src/requirements/layout.ts, src/requirements/scope.ts, src/requirements/state-machine.ts
- 明细报告：`.project-intel/requirements/LOCAL-20260727-141720/test-reports/TEST-06-unit.md`

#### 执行明细

    # LOCAL-20260727-141720 测试报告
    
    - 测试类型：unit
    - 阶段：regression
    - 结果：passed
    - 验收标准：AC-01,AC-02,AC-03,AC-04
    - 文件范围：README.md, plugins/project-intelligence/assets/plugin-intro.html, plugins/project-intelligence/skills/project-design/SKILL.md, plugins/project-intelligence/skills/project-finish/SKILL.md, plugins/project-intelligence/skills/project-intake/SKILL.md, plugins/project-intelligence/skills/project-knowledge/SKILL.md, plugins/project-intelligence/skills/project-plan/SKILL.md, plugins/project-intelligence/skills/project-spec/SKILL.md, plugins/project-intelligence/skills/project-task/SKILL.md, src/__tests__/requirement-command.test.ts, src/__tests__/review-finish-graph.test.ts, src/__tests__/state-machine.test.ts, src/__tests__/test-evidence.test.ts, src/commands/agent-rules.ts, src/commands/init.ts, src/commands/orchestration.ts, src/commands/requirement.ts, src/requirements/layout.ts, src/requirements/scope.ts, src/requirements/state-machine.ts
    
    ## 执行结果
    
    ### npm test
    
    - exitCode: 0
    - executedCount: 260
    
    ```text
    Skill behavior scenario contracts verified: 27 scenarios, 17 skills
    ▶ maskCommentsAndStrings
      ✔ masks line and block comments and string contents (0.653042ms)
    ✔ maskCommentsAndStrings (1.750959ms)
    ▶ scanBackendFile
      ✔ extracts a Spring controller endpoint and methods (.java) (4.217333ms)
      ✔ extracts Python def/class and Flask routes (.py) (1.741542ms)
      ✔ classifies a service by name and extracts transaction signals (1.286291ms)
      ✔ extracts config keys from yaml (0.703459ms)
      ✔ classifies repository files and extracts SQL ops from xml mapper (0.655292ms)
      ✔ extracts permission signals (0.262833ms)
      ✔ extracts error code signals (0.287542ms)
      ✔ requires bound framework imports and keeps Django class views (0.2135ms)
      ✔ labels malformed Python without accepting route facts (0.358917ms)
      ✔ applies configured backend entrypoint rules (0.194291ms)
    ✔ scanBackendFile (10.978125ms)
    ▶ BACKEND_SUFFIXES
      ✔ includes java, kt, py, go, ts, js (0.523417ms)
    ✔ BACKEND_SUFFIXES (0.692416ms)
    ▶ cli snapshot contract (AC-02)
      ✔ loads a well-formed snapshot (1.593875ms)
      ✔ captured every top-level command's help (0.87725ms)
      ✔ pins the JSON envelope shape on every probe (0.170583ms)
      ✔ the version command exits 0 and prints a semver (0.344ms)
      ✔ usage errors exit non-zero with a non-ok envelope (0.31175ms)
    ✔ cli snapshot contract (AC-02) (4.557291ms)
    ▶ live Node CLI contract (AC-02/AC-10)
      ✔ dist/cli.js exists and is runnable (0.2585ms)
      ✔ version command exits 0 and prints a semver (142.501417ms)
      ✔ --version flag exits 0 and prints a semver (119.7745ms)
      ✔ every baseline command's --help is byte-for-byte compatible (1597.918833ms)
      ✔ top-level --help is byte-for-byte compatible (68.205625ms)
      ✔ top-level --help output contains all baseline commands (66.967417ms)
      ✔ subcommand --help output contains usage line and key flags (204.402375ms)
      ✔ unknown command exits 2 (99.608833ms)
      ✔ unknown flag exits 2 (93.822875ms)
      ✔ version --json produces a valid envelope with version field (69.586958ms)
      ✔ doctor --json produces a valid envelope with runtime=node (79.639625ms)
      ✔ usage error --json produces ok=false envelope (69.047334ms)
    ✔ live Node CLI contract (AC-02/AC-10) (2612.353667ms)
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
    无法识别的参数：--definitely-invalid
    无法识别的参数：--nope
    ▶ dispatch
      ✔ prints --version alone (1.63375ms)
      ✔ prints --version envelope in json mode (0.214208ms)
      ✔ runs a registered command (text mode) (0.506333ms)
      ✔ runs a registered command (json mode) with envelope (0.54375ms)
      ✔ rejects unknown command with exit 2 (text) (27.421584ms)
      ✔ rejects unknown command with exit 2 (json envelope) (11.296625ms)
      ✔ surfaces usage errors as exit 2 (0.184959ms)
      ✔ surfaces runtime errors as exit 1 (0.092583ms)
      ✔ rejects missing subcommand (json exit 2) (0.086667ms)
      ✔ subcommand --help is intercepted and exits 0 (text) (0.150166ms)
      ✔ subcommand -h is intercepted and exits 0 (json) (0.077917ms)
      ✔ rejects unknown long flag with exit 2 (text) (0.044416ms)
      ✔ rejects unknown long flag with exit 2 (json envelope) (0.0475ms)
      ✔ accepts known value flag and its value (not mistaken for a flag) (0.040708ms)
      ✔ rejects unknown flag even after a valid value flag (0.046917ms)
    ✔ dispatch (48.3485ms)
    ▶ normalizeForCompare
      ✔ masks ISO-8601 timestamps (2.333875ms)
      ✔ masks 40-char git hashes (0.1485ms)
      ✔ masks epoch-second/milli integers (0.098666ms)
      ✔ masks absolute repo roots (POSIX) (0.099833ms)
      ✔ normalizes Windows backslashes and masks sample root (0.137667ms)
      ✔ collapses mtime integers regardless of value (0.135292ms)
      ✔ applies longest-root-first masking so nested roots win (0.118ms)
    ✔ normalizeForCompare (4.6245ms)
    ▶ compareJsonOutputs
      ✔ returns null for equal normalized values (0.229625ms)
      ✔ reports the first differing path (0.107166ms)
      ✔ reports missing keys with direction (0.177ms)
      ✔ reports array length mismatches (0.087583ms)
    ✔ compareJsonOutputs (0.823333ms)
    ▶ frontend scanner
      ✔ extracts vue component props/emits (7.978584ms)
      ✔ extracts react props from interface (0.885209ms)
      ✔ extracts hooks by use* filename (0.23025ms)
      ✔ extracts routes and redundancy candidates (0.463375ms)
      ✔ extractVueProps from defineProps object form (0.243583ms)
      ✔ extractEmits filters to valid names (0.074ms)
      ✔ extractApiEndpoints from request/fetch calls (1.274833ms)
    ✔ frontend scanner (13.383042ms)
    ▶ files scanner
      ✔ discoverFiles walks and categorizes (1.8585ms)
      ✔ discoverFiles excludes node_modules/.git (0.702417ms)
      ✔ uses stable code-point ordering across operating systems (0.679583ms)
      ✔ categorize and simpleMatch basics (0.313042ms)
    ✔ files scanner (4.09875ms)
    ▶ incremental scan cache
      ✔ reuses unchanged frontend facts without reading the file again (0.542625ms)
      ✔ uses nanosecond-compatible file signatures and invalidates changed entries (1.11975ms)
    ✔ incremental scan cache (1.856916ms)
    ▶ quality scanner
      ✔ packageFrameworks detects Vue+TypeScript from deps (0.286167ms)
      ✔ detectPackage reads package.json scripts and frameworks (0.611584ms)
      ✔ packageManager detects npm/pnpm/yarn by lockfile (0.14875ms)
      ✔ detectQualityCommands: Python project STILL recognizes pytest/ruff/mypy (P1.3) (0.49525ms)
      ✔ detectQualityCommands: JS project infers eslint/tsc from config presence (0.643417ms)
    ✔ quality scanner (2.283791ms)
    FixtureGraph 已安装，开始运行分析："/opt/homebrew/Cellar/node/26.3.0/bin/node" -e "process.stdout.write('graph-ok')"
    FixtureGraph 开始执行，超时上限 900 秒。
    GitNexus：仓库内 runner 需要显式使用 --allow-repo-runner。
    ▶ graph command authorization
      ✔ preserves and detects Windows absolute paths on POSIX (1.777834ms)
      ✔ allows repository-contained absolute paths and rejects outside paths (0.168708ms)
      ✔ requires explicit permission for repo runners and environment commands (0.152583ms)
    ✔ graph command authorization (3.057375ms)
    ▶ graph setup execution
      ✔ executes an authorized installed analyzer and captures evidence (84.293875ms)
      ✔ records a skipped result instead of executing an unauthorized runner (0.634ms)
    ✔ graph setup execution (85.050875ms)
    ▶ adapter block management
      ✔ rejects paths outside the allowed set (1.31175ms)
      ✔ replaceSingleManagedBlock creates then updates (0.314125ms)
      ✔ upsert then remove a managed block (0.772625ms)
    ✔ adapter block management (3.717333ms)
    ▶ adapters command family
      ✔ apply writes codex + claude blocks; status reports current (4.12425ms)
      ✔ preview is dry-run (no files written) (0.707708ms)
      ✔ remove clears blocks (0.969125ms)
      ✔ status --check returns non-zero when not current (0.860834ms)
      ✔ adapterTargets both returns 3 targets (codex, claude, claude-nested) (1.616542ms)
    ✔ adapters command family (8.769125ms)
    ▶ top-level install command
      ✔ creates .claude/ and applies adapters; --hooks writes templates (2.642917ms)
    ✔ top-level install command (2.738167ms)
    ▶ agent install command
      ✔ agentInstallCommands builds codex+claude for all (0.115042ms)
      ✔ --dry-run classifies present when cli exists, missing otherwise (0.32875ms)
      ✔ rejects invalid target (0.104417ms)
    ✔ agent install command (0.604334ms)
    ▶ git hooks (AC-07: no python3)
      ✔ hook body calls project-intel (Node CLI), never python3 (0.046959ms)
      ✔ writeHookTemplates writes 3 hooks + README under .project-intel/hooks (0.487375ms)
    ✔ git hooks (AC-07: no python3) (0.569292ms)
    ▶ sanitizeErrorText
      ✔ redacts authorization bearer tokens (1.225833ms)
      ✔ redacts cookies (0.069625ms)
      ✔ redacts password/secret/token/api_key (0.05175ms)
      ✔ redacts aws credentials (0.093625ms)
      ✔ redacts URL userinfo (0.06475ms)
      ✔ leaves benign text intact (0.409875ms)
    ✔ sanitizeErrorText (3.980083ms)
    ▶ extractGlobalJson
      ✔ strips --json and reports mode (0.647916ms)
      ✔ preserves argv when --json absent (0.055917ms)
    ✔ extractGlobalJson (0.797875ms)
    ▶ jsonEnvelope
      ✔ shapes a success envelope (0.143792ms)
      ✔ classifies exit 2 as USAGE_ERROR with sanitized in-place error (0.082958ms)
      ✔ classifies non-2 failure as COMMAND_FAILED with default message (0.052458ms)
      ✔ trims the output field (0.0335ms)
    ✔ jsonEnvelope (0.413167ms)
    ▶ parseGlobal / splitArgv
      ✔ parses --project value (0.321125ms)
      ✔ parses --project= form (0.14625ms)
      ✔ parses --json (0.112125ms)
      ✔ rejects unknown long option before subcommand with exit-2 UsageError (0.146792ms)
      ✔ splitArgv separates global, command, and rest (0.130458ms)
      ✔ splitArgv returns null when no subcommand (0.054125ms)
    ✔ parseGlobal / splitArgv (1.085792ms)
    ▶ withLock (in-process)
      ✔ blocks same-process re-entrant acquire (no deadlock) (64.107041ms)
      ✔ releases the lockfile after the critical section (0.470083ms)
    ✔ withLock (in-process) (67.270583ms)
    ▶ withLock (multi-process contention)
      ✔ grants exclusive access across child processes (967.195666ms)
    ✔ withLock (multi-process contention) (967.276208ms)
    ▶ paths
      ✔ toPosix converts separators (0.406ms)
      ✔ normalizeBusinessPath strips leading ./ and normalizes (0.06325ms)
      ✔ isAbsolutePathLike detects posix, windows drive, unc (0.072334ms)
      ✔ resolveInside rejects traversal outside root (0.308041ms)
      ✔ expandUser leaves non-home paths alone (0.046625ms)
    ✔ paths (1.477ms)
    ▶ atomic-write
      ✔ writes text with a trailing newline, UTF-8 preserved (7.222ms)
      ✔ writes JSON without ascii escaping and creates parent dirs (4.9605ms)
      ✔ preserves existing file mode (9.646875ms)
      ✔ loadJson returns default on missing/corrupt (1.410583ms)
      ✔ loadJsonStrict raises on corrupt/non-object (0.847875ms)
    ✔ atomic-write (24.3885ms)
    中文测试
    {
      "name": "中文"
    }
    err 中文
    ▶ subprocess.spawn (argv)
      ✔ runs a successful command and captures output (120.330709ms)
      ✔ returns 127 when the binary is missing (2.682375ms)
      ✔ returns a non-zero code on argv usage error (24.293625ms)
    ✔ subprocess.spawn (argv) (148.033375ms)
    ▶ subprocess.which / commandExists
      ✔ finds node on PATH (1.001375ms)
      ✔ returns null for a missing command (0.243542ms)
    ✔ subprocess.which / commandExists (1.366084ms)
    ▶ subprocess.runShell (shell form)
      ✔ supports pipes and redirects (8.414709ms)
      ✔ supports environment variable expansion (10.406584ms)
      ✔ returns 0 for a true compound command (4.515834ms)
      ✔ surfaces non-zero exit of a failed command (5.167083ms)
    ✔ subprocess.runShell (shell form) (28.833625ms)
    ▶ output (UTF-8)
      ✔ print writes a UTF-8 line including Chinese (0.370167ms)
      ✔ printJson renders without ASCII escaping (0.08275ms)
      ✔ printError writes to stderr (0.042917ms)
    ✔ output (UTF-8) (0.555958ms)
    ▶ io.yaml
      ✔ parses flat key: value (0.685125ms)
      ✔ strips quoted values (0.048792ms)
      ✔ coerces scalars (0.079125ms)
    ✔ io.yaml (0.853375ms)
    ▶ io.markdown
      ✔ parses ATX headings with level and text (0.354916ms)
      ✔ normalizeHeading collapses whitespace (0.0845ms)
      ✔ hasMeaningfulContent rejects blank/placeholder (0.142375ms)
    ✔ io.markdown (0.664209ms)
    已初始化 .project-intel，索引了 4 个文本文件。
    {
      "dryRun": true,
      "manifest": {
        "schemaVersion": 2,
        "toolVersion": "0.7.1",
        "projectRoot": ".",
        "generatedAt": "2026-07-27T06:38:57.000Z",
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
        "generatedAt": "2026-07-27T06:38:57.040Z",
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
        ".project-intel/requirements/<requirement-id>-<title>/*.md"
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
      ✔ writes the .project-intel layout (manifest/config/knowledge/status) (228.376125ms)
      ✔ --dry-run does not write files (47.383875ms)
      ✔ refresh re-writes without tooling (603.435ms)
      ✔ strict + no-graph is a usage error (7.851375ms)
      ✔ ensureProjectIntelGitignore writes local-only rules (6.853166ms)
    ✔ init command (894.650917ms)
    ▶ doctor command
      ✔ reports node runtime, not python (29.587708ms)
      ✔ detects initialized state after init (335.776959ms)
    ✔ doctor command (365.47625ms)
    ▶ check command
      ✔ passes with no hard rules configured (330.479208ms)
      ✔ --dry-run does not write status (383.400541ms)
    ✔ check command (713.985459ms)
    ▶ standards inference
      ✔ infers PascalCase naming from >=3 pascal components (0.27125ms)
      ✔ infers backend Service suffix from >=2 services (0.079542ms)
      ✔ infers ui-pattern from redundancy candidates (0.041917ms)
      ✔ ports backend API, layering and operational inference categories (0.118125ms)
    ✔ standards inference (0.579333ms)
    ▶ project domain candidates
      ✔ aggregates repeated non-generic parent segments in stable order (1.0155ms)
    ✔ project domain candidates (1.064209ms)
    ▶ standards documents
      ✔ renders detailed frontend and backend facts instead of count-only placeholders (2.118459ms)
    ✔ standards documents (2.172209ms)
    ▶ hard rules engine
      ✔ returns no violations with the empty default set (0.062125ms)
      ✔ surfaces a registered rule violation (0.063083ms)
    ✔ hard rules engine (0.173458ms)
    已初始化 .project-intel，索引了 3 个文本文件。
    已初始化 .project-intel，索引了 3 个文本文件。
    ▶ requirement command dispatcher
      ✔ status returns state for a created requirement (47.606125ms)
      ✔ plan writes into the resolved id-title requirement directory (45.266333ms)
      ✔ intake persists document actions and later selection blocks generation (63.991375ms)
      ✔ acceptance set persists AC-01..AC-02 (60.162708ms)
      ✔ query reads v2 and legacy by-id archives and supports --file (79.344167ms)
      ✔ test-contract set requires --kind and --report-action (80.396333ms)
      ✔ test-contract register validates and normalizes a structured report path (84.959ms)
      ✔ ready -> begin through the dispatcher (781.081584ms)
      ✔ reopen after close (77.892125ms)
      ✔ generate enforces lifecycle order and creates a requirement scaffold (70.778584ms)
      ✔ generate refuses implicit overwrite and --replace really rebuilds the scaffold (86.327875ms)
      ✔ rejects missing --requirement-id (3.402042ms)
      ✔ add persists artifact registration into the manifest (434.962292ms)
      ✔ rejects arbitrary delivery-document content (167.732666ms)
      ✔ design registration rejects missing source evidence paths (303.637ms)
      ✔ design registration ignores symbols that exist only in comments or strings (180.582584ms)
      ✔ add registers a structured test report as current requirement evidence (551.348ms)
      ✔ diagnose records a Bug root cause (ticketKind=bug) (102.596459ms)
      ✔ diagnose rejects missing source evidence paths (61.549667ms)
      ✔ diagnose rejects symbols that only appear in comments or strings (52.988333ms)
      ✔ diagnose rejects non-bug requirements (28.7275ms)
      ✔ defer adds a readiness blocker for design (34.910125ms)
      ✔ resolve-finding marks a review finding resolved (29.884ms)
      ✔ resolve-finding rejects unknown finding IDs (38.919459ms)
    ✔ requirement command dispatcher (3471.030875ms)
    ▶ re
    ```
