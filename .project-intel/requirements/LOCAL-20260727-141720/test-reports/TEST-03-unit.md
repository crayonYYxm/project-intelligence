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
