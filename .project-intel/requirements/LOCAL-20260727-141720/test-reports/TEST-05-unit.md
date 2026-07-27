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
