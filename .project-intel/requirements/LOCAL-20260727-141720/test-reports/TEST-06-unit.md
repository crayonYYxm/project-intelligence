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
