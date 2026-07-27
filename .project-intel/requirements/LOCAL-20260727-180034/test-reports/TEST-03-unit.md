# LOCAL-20260727-180034 测试报告

- 测试类型：unit
- 阶段：regression
- 结果：passed
- 验收标准：AC-01,AC-02,AC-03,AC-04,AC-05,AC-06
- 文件范围：README.md, docs/project-intelligence-guide.md, plugins/project-intelligence/skills/project-design/SKILL.md, plugins/project-intelligence/skills/project-finish/SKILL.md, plugins/project-intelligence/skills/project-intake/SKILL.md, plugins/project-intelligence/skills/project-knowledge/SKILL.md, plugins/project-intelligence/skills/project-plan/SKILL.md, plugins/project-intelligence/skills/project-spec/SKILL.md, plugins/project-intelligence/skills/project-task/SKILL.md, src/__tests__/requirement-command.test.ts, src/__tests__/state-machine.test.ts, src/cli/command-flags.ts, src/commands/agent-rules.ts, src/commands/init.ts, src/commands/orchestration.ts, src/requirements/artifacts.ts, src/requirements/layout.ts, src/requirements/scope.ts, src/requirements/state-machine.ts

## 执行结果

### npm test

- exitCode: 0
- executedCount: 267

```text
Skill behavior scenario contracts verified: 27 scenarios, 17 skills
▶ maskCommentsAndStrings
  ✔ masks line and block comments and string contents (0.46575ms)
✔ maskCommentsAndStrings (1.031875ms)
▶ scanBackendFile
  ✔ extracts a Spring controller endpoint and methods (.java) (5.795583ms)
  ✔ extracts Python def/class and Flask routes (.py) (4.044083ms)
  ✔ classifies a service by name and extracts transaction signals (0.5555ms)
  ✔ extracts config keys from yaml (2.273458ms)
  ✔ classifies repository files and extracts SQL ops from xml mapper (0.87375ms)
  ✔ extracts permission signals (0.421458ms)
  ✔ extracts error code signals (0.347125ms)
  ✔ requires bound framework imports and keeps Django class views (0.611ms)
  ✔ labels malformed Python without accepting route facts (0.200167ms)
  ✔ applies configured backend entrypoint rules (0.430125ms)
✔ scanBackendFile (16.290417ms)
▶ BACKEND_SUFFIXES
  ✔ includes java, kt, py, go, ts, js (0.145584ms)
✔ BACKEND_SUFFIXES (0.28525ms)
▶ cli snapshot contract (AC-02)
  ✔ loads a well-formed snapshot (1.138542ms)
  ✔ captured every top-level command's help (1.882458ms)
  ✔ pins the JSON envelope shape on every probe (0.352625ms)
  ✔ the version command exits 0 and prints a semver (0.336166ms)
  ✔ usage errors exit non-zero with a non-ok envelope (0.216792ms)
✔ cli snapshot contract (AC-02) (5.201334ms)
▶ live Node CLI contract (AC-02/AC-10)
  ✔ dist/cli.js exists and is runnable (0.311ms)
  ✔ version command exits 0 and prints a semver (146.385542ms)
  ✔ --version flag exits 0 and prints a semver (131.079125ms)
  ✔ every baseline command's --help is byte-for-byte compatible (1783.070667ms)
  ✔ top-level --help is byte-for-byte compatible (67.173375ms)
  ✔ top-level --help output contains all baseline commands (67.8615ms)
  ✔ subcommand --help output contains usage line and key flags (228.706ms)
  ✔ unknown command exits 2 (80.250417ms)
  ✔ unknown flag exits 2 (83.757459ms)
  ✔ version --json produces a valid envelope with version field (71.77675ms)
  ✔ doctor --json produces a valid envelope with runtime=node (76.240833ms)
  ✔ usage error --json produces ok=false envelope (69.144167ms)
✔ live Node CLI contract (AC-02/AC-10) (2806.456417ms)
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
无法识别的命令：nope
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
  ✔ prints --version alone (2.073833ms)
  ✔ prints --version envelope in json mode (0.25175ms)
  ✔ runs a registered command (text mode) (0.509041ms)
  ✔ runs a registered command (json mode) with envelope (0.1145ms)
  ✔ rejects unknown command with exit 2 (text) (0.3505ms)
  ✔ rejects unknown command with exit 2 (json envelope) (2.0865ms)
  ✔ surfaces usage errors as exit 2 (0.290667ms)
  ✔ surfaces runtime errors as exit 1 (2.082583ms)
  ✔ rejects missing subcommand (json exit 2) (0.308375ms)
  ✔ subcommand --help is intercepted and exits 0 (text) (0.432917ms)
  ✔ subcommand -h is intercepted and exits 0 (json) (0.206625ms)
  ✔ rejects unknown long flag with exit 2 (text) (0.111292ms)
  ✔ rejects unknown long flag with exit 2 (json envelope) (0.111ms)
  ✔ accepts known value flag and its value (not mistaken for a flag) (0.137958ms)
  ✔ rejects unknown flag even after a valid value flag (0.139542ms)
✔ dispatch (10.930625ms)
▶ normalizeForCompare
  ✔ masks ISO-8601 timestamps (2.617541ms)
  ✔ masks 40-char git hashes (0.117417ms)
  ✔ masks epoch-second/milli integers (0.056584ms)
  ✔ masks absolute repo roots (POSIX) (0.052584ms)
  ✔ normalizes Windows backslashes and masks sample root (0.061875ms)
  ✔ collapses mtime integers regardless of value (0.076125ms)
  ✔ applies longest-root-first masking so nested roots win (0.062209ms)
✔ normalizeForCompare (4.370959ms)
▶ compareJsonOutputs
  ✔ returns null for equal normalized values (0.122834ms)
  ✔ reports the first differing path (0.049792ms)
  ✔ reports missing keys with direction (0.09375ms)
  ✔ reports array length mismatches (0.047792ms)
✔ compareJsonOutputs (0.4225ms)
▶ frontend scanner
  ✔ extracts vue component props/emits (3.77725ms)
  ✔ extracts react props from interface (0.476083ms)
  ✔ extracts hooks by use* filename (0.186875ms)
  ✔ extracts routes and redundancy candidates (4.014333ms)
  ✔ extractVueProps from defineProps object form (0.432459ms)
  ✔ extractEmits filters to valid names (0.116208ms)
  ✔ extractApiEndpoints from request/fetch calls (0.396416ms)
✔ frontend scanner (11.500959ms)
▶ files scanner
  ✔ discoverFiles walks and categorizes (2.516416ms)
  ✔ discoverFiles excludes node_modules/.git (1.08975ms)
  ✔ uses stable code-point ordering across operating systems (0.754583ms)
  ✔ categorize and simpleMatch basics (0.3035ms)
✔ files scanner (4.976458ms)
▶ incremental scan cache
  ✔ reuses unchanged frontend facts without reading the file again (1.139375ms)
  ✔ uses nanosecond-compatible file signatures and invalidates changed entries (0.950166ms)
✔ incremental scan cache (2.206042ms)
▶ quality scanner
  ✔ packageFrameworks detects Vue+TypeScript from deps (0.590167ms)
  ✔ detectPackage reads package.json scripts and frameworks (1.637042ms)
  ✔ packageManager detects npm/pnpm/yarn by lockfile (0.556542ms)
  ✔ detectQualityCommands: Python project STILL recognizes pytest/ruff/mypy (P1.3) (3.002375ms)
  ✔ detectQualityCommands: JS project infers eslint/tsc from config presence (1.984958ms)
✔ quality scanner (8.146208ms)
FixtureGraph 已安装，开始运行分析："/opt/homebrew/Cellar/node/26.3.0/bin/node" -e "process.stdout.write('graph-ok')"
FixtureGraph 开始执行，超时上限 900 秒。
GitNexus：仓库内 runner 需要显式使用 --allow-repo-runner。
▶ graph command authorization
  ✔ preserves and detects Windows absolute paths on POSIX (3.831083ms)
  ✔ allows repository-contained absolute paths and rejects outside paths (0.21175ms)
  ✔ requires explicit permission for repo runners and environment commands (0.154125ms)
✔ graph command authorization (4.765083ms)
▶ graph setup execution
  ✔ executes an authorized installed analyzer and captures evidence (113.989958ms)
  ✔ records a skipped result instead of executing an unauthorized runner (0.332791ms)
✔ graph setup execution (114.483958ms)
▶ adapter block management
  ✔ rejects paths outside the allowed set (0.678125ms)
  ✔ replaceSingleManagedBlock creates then updates (0.232084ms)
  ✔ upsert then remove a managed block (1.448375ms)
✔ adapter block management (3.18525ms)
▶ adapters command family
  ✔ apply writes codex + claude blocks; status reports current (1.600625ms)
  ✔ preview is dry-run (no files written) (0.466709ms)
  ✔ remove clears blocks (1.278959ms)
  ✔ status --check returns non-zero when not current (0.898834ms)
  ✔ adapterTargets both returns 3 targets (codex, claude, claude-nested) (1.440542ms)
✔ adapters command family (6.007667ms)
▶ top-level install command
  ✔ creates .claude/ and applies adapters; --hooks writes templates (2.801208ms)
✔ top-level install command (2.867875ms)
▶ agent install command
  ✔ agentInstallCommands builds codex+claude for all (0.108209ms)
  ✔ --dry-run classifies present when cli exists, missing otherwise (0.331125ms)
  ✔ rejects invalid target (0.103ms)
✔ agent install command (0.595958ms)
▶ git hooks (AC-07: no python3)
  ✔ hook body calls project-intel (Node CLI), never python3 (0.043667ms)
  ✔ writeHookTemplates writes 3 hooks + README under .project-intel/hooks (1.159625ms)
✔ git hooks (AC-07: no python3) (1.25ms)
▶ sanitizeErrorText
  ✔ redacts authorization bearer tokens (1.525917ms)
  ✔ redacts cookies (0.1515ms)
  ✔ redacts password/secret/token/api_key (0.097167ms)
  ✔ redacts aws credentials (0.119041ms)
  ✔ redacts URL userinfo (0.122625ms)
  ✔ leaves benign text intact (1.019166ms)
✔ sanitizeErrorText (4.237625ms)
▶ extractGlobalJson
  ✔ strips --json and reports mode (1.374292ms)
  ✔ preserves argv when --json absent (0.141ms)
✔ extractGlobalJson (1.722708ms)
▶ jsonEnvelope
  ✔ shapes a success envelope (0.223167ms)
  ✔ classifies exit 2 as USAGE_ERROR with sanitized in-place error (0.136167ms)
  ✔ classifies non-2 failure as COMMAND_FAILED with default message (0.237625ms)
  ✔ trims the output field (0.136791ms)
✔ jsonEnvelope (0.916791ms)
▶ parseGlobal / splitArgv
  ✔ parses --project value (1.3685ms)
  ✔ parses --project= form (0.083333ms)
  ✔ parses --json (0.035875ms)
  ✔ rejects unknown long option before subcommand with exit-2 UsageError (0.083041ms)
  ✔ splitArgv separates global, command, and rest (0.22875ms)
  ✔ splitArgv returns null when no subcommand (0.05025ms)
✔ parseGlobal / splitArgv (1.966583ms)
▶ withLock (in-process)
  ✔ blocks same-process re-entrant acquire (no deadlock) (61.821709ms)
  ✔ releases the lockfile after the critical section (0.359708ms)
✔ withLock (in-process) (63.403916ms)
▶ withLock (multi-process contention)
  ✔ grants exclusive access across child processes (1102.772709ms)
✔ withLock (multi-process contention) (1102.8555ms)
▶ paths
  ✔ toPosix converts separators (0.5675ms)
  ✔ normalizeBusinessPath strips leading ./ and normalizes (0.311959ms)
  ✔ isAbsolutePathLike detects posix, windows drive, unc (0.343041ms)
  ✔ resolveInside rejects traversal outside root (0.79325ms)
  ✔ expandUser leaves non-home paths alone (0.139208ms)
✔ paths (3.343292ms)
▶ atomic-write
  ✔ writes text with a trailing newline, UTF-8 preserved (6.841334ms)
  ✔ writes JSON without ascii escaping and creates parent dirs (5.274041ms)
  ✔ preserves existing file mode (10.749167ms)
  ✔ loadJson returns default on missing/corrupt (0.88725ms)
  ✔ loadJsonStrict raises on corrupt/non-object (0.511625ms)
✔ atomic-write (24.754958ms)
中文测试
{
  "name": "中文"
}
err 中文
▶ subprocess.spawn (argv)
  ✔ runs a successful command and captures output (100.8585ms)
  ✔ returns 127 when the binary is missing (4.609291ms)
  ✔ returns a non-zero code on argv usage error (26.219542ms)
✔ subprocess.spawn (argv) (132.929958ms)
▶ subprocess.which / commandExists
  ✔ finds node on PATH (1.52625ms)
  ✔ returns null for a missing command (0.659334ms)
✔ subprocess.which / commandExists (2.432833ms)
▶ subprocess.runShell (shell form)
  ✔ supports pipes and redirects (12.025333ms)
  ✔ supports environment variable expansion (11.394458ms)
  ✔ returns 0 for a true compound command (4.891791ms)
  ✔ surfaces non-zero exit of a failed command (6.205875ms)
✔ subprocess.runShell (shell form) (34.720875ms)
▶ output (UTF-8)
  ✔ print writes a UTF-8 line including Chinese (0.374167ms)
  ✔ printJson renders without ASCII escaping (0.070667ms)
  ✔ printError writes to stderr (0.042625ms)
✔ output (UTF-8) (0.547792ms)
▶ io.yaml
  ✔ parses flat key: value (0.896625ms)
  ✔ strips quoted values (0.081291ms)
  ✔ coerces scalars (0.301875ms)
✔ io.yaml (1.388916ms)
▶ io.markdown
  ✔ parses ATX headings with level and text (0.178584ms)
  ✔ normalizeHeading collapses whitespace (0.0345ms)
  ✔ hasMeaningfulContent rejects blank/placeholder (0.11675ms)
✔ io.markdown (0.38125ms)
已初始化 .project-intel，索引了 4 个文本文件。
{
  "dryRun": true,
  "manifest": {
    "schemaVersion": 2,
    "toolVersion": "0.7.3",
    "projectRoot": ".",
    "generatedAt": "2026-07-27T10:14:36.457Z",
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
    "generatedAt": "2026-07-27T10:14:36.524Z",
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
    ".project-intel/requirements/<YYYY-MM-DD>-<requirement-id>-<title>/*.md"
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
  ✔ writes the .project-intel layout (manifest/config/knowledge/status) (230.793833ms)
  ✔ --dry-run does not write files (74.868916ms)
  ✔ refresh re-writes without tooling (635.047625ms)
  ✔ strict + no-graph is a usage error (3.67175ms)
  ✔ ensureProjectIntelGitignore writes local-only rules (8.264042ms)
✔ init command (953.673125ms)
▶ doctor command
  ✔ reports node runtime, not python (18.392584ms)
  ✔ detects initialized state after init (359.726208ms)
✔ doctor command (378.247625ms)
▶ check command
  ✔ passes with no hard rules configured (361.231167ms)
  ✔ --dry-run does not write status (385.534542ms)
✔ check command (746.883ms)
▶ standards inference
  ✔ infers PascalCase naming from >=3 pascal components (0.317916ms)
  ✔ infers backend Service suffix from >=2 services (0.08975ms)
  ✔ infers ui-pattern from redundancy candidates (0.212833ms)
  ✔ ports backend API, layering and operational inference categories (0.149208ms)
✔ standards inference (0.872458ms)
▶ project domain candidates
  ✔ aggregates repeated non-generic parent segments in stable order (0.696458ms)
✔ project domain candidates (0.731667ms)
▶ standards documents
  ✔ renders detailed frontend and backend facts instead of count-only placeholders (0.996292ms)
✔ standards documents (1.037583ms)
▶ hard rules engine
  ✔ returns no violations with the empty default set (0.051792ms)
  ✔ surfaces a registered rule violation (0.059ms)
✔ hard rules engine (0.148625ms)
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ requirement command dispatcher
  ✔ status returns state for a created requirement (61.409708ms)
  ✔ plan writes into the resolved id-title requirement directory (58.077542ms)
  ✔ intake persists document actions and later selection blocks generation (60.926791ms)
  ✔ intake requires a valid user supplied version date (0.955958ms)
  ✔ task-only intake remains a read-only analysis without a version date (0.297583ms)
  ✔ task intake with a version date registers a dated LOCAL requirement (47.958375ms)
  ✔ acceptance set persists AC-01..AC-02 (67.732833ms)
  ✔ query reads v2 and legacy by-id archives and supports --file (74.457917ms)
  ✔ test-contract set requires --kind and --report-action (104.895459ms)
  ✔ test-contract register validates and normalizes a structured report path (73.419541ms)
  ✔ ready -> begin through the dispatcher (882.342416ms)
  ✔ reopen after close (101.273709ms)
  ✔ generate enforces lifecycle order and creates a requirement scaffold (90.959917ms)
  ✔ generate refuses implicit overwrite and --replace really rebuilds the scaffold (123.890833ms)
  ✔ rejects missing --requirement-id (3.6555ms)
  ✔ add persists artifact registration into the manifest (326.373958ms)
  ✔ rejects arbitrary delivery-document content (170.352083ms)
  ✔ design registration rejects missing source evidence paths (317.238958ms)
  ✔ design registration ignores symbols that exist only in comments or strings (204.140209ms)
  ✔ add registers a structured test report as current requirement evidence (626.213375ms)
  ✔ diagnose records a Bug root cause (ticketKind=bug) (77.822375ms)
  ✔ diagnose rejects missing source evidence paths (48.012792ms)
  ✔ diagnose rejects symbols that only appear in comments or strings (31.134416ms)
  ✔ diagnose rejects non-bu
```
