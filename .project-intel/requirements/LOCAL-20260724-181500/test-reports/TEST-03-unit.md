# LOCAL-20260724-181500 测试报告

- 测试类型：unit
- 阶段：regression
- 结果：passed
- 验收标准：AC-01,AC-02,AC-03,AC-04,AC-05
- 文件范围：marketplace.json, package.json, plugins/project-intelligence/.zcode-plugin/plugin.json, scripts/check-release.mjs, scripts/check-package.mjs, src/commands/finish.ts, src/commands/test.ts, src/requirements/state-machine.ts, src/__tests__/zcode-compat.test.ts, src/__tests__/test-evidence.test.ts, src/__tests__/review-finish-graph.test.ts

## 执行结果

### npm test && npm run typecheck && npm run check-release

- exitCode: 0
- executedCount: 254

```text
Skill behavior scenario contracts verified: 27 scenarios, 17 skills
▶ maskCommentsAndStrings
  ✔ masks line and block comments and string contents (6.938209ms)
✔ maskCommentsAndStrings (8.182792ms)
▶ scanBackendFile
  ✔ extracts a Spring controller endpoint and methods (.java) (9.207541ms)
  ✔ extracts Python def/class and Flask routes (.py) (2.209083ms)
  ✔ classifies a service by name and extracts transaction signals (2.308458ms)
  ✔ extracts config keys from yaml (1.085958ms)
  ✔ classifies repository files and extracts SQL ops from xml mapper (0.599916ms)
  ✔ extracts permission signals (0.255291ms)
  ✔ extracts error code signals (0.318ms)
  ✔ requires bound framework imports and keeps Django class views (0.362708ms)
  ✔ labels malformed Python without accepting route facts (0.167583ms)
  ✔ applies configured backend entrypoint rules (0.409833ms)
✔ scanBackendFile (17.491542ms)
▶ BACKEND_SUFFIXES
  ✔ includes java, kt, py, go, ts, js (0.185334ms)
✔ BACKEND_SUFFIXES (0.284458ms)
▶ cli snapshot contract (AC-02)
  ✔ loads a well-formed snapshot (2.148792ms)
  ✔ captured every top-level command's help (1.686459ms)
  ✔ pins the JSON envelope shape on every probe (0.331459ms)
  ✔ the version command exits 0 and prints a semver (0.304208ms)
  ✔ usage errors exit non-zero with a non-ok envelope (0.19525ms)
✔ cli snapshot contract (AC-02) (6.3485ms)
▶ live Node CLI contract (AC-02/AC-10)
  ✔ dist/cli.js exists and is runnable (0.2075ms)
  ✔ version command exits 0 and prints a semver (153.026875ms)
  ✔ --version flag exits 0 and prints a semver (152.643625ms)
  ✔ every baseline command's --help is byte-for-byte compatible (2798.42125ms)
  ✔ top-level --help is byte-for-byte compatible (124.035709ms)
  ✔ top-level --help output contains all baseline commands (123.2745ms)
  ✔ subcommand --help output contains usage line and key flags (366.747791ms)
  ✔ unknown command exits 2 (125.725917ms)
  ✔ unknown flag exits 2 (124.873459ms)
  ✔ version --json produces a valid envelope with version field (121.659125ms)
  ✔ doctor --json produces a valid envelope with runtime=node (125.147125ms)
  ✔ usage error --json produces ok=false envelope (117.480417ms)
✔ live Node CLI contract (AC-02/AC-10) (4333.915917ms)
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
  ✔ prints --version alone (1.459083ms)
  ✔ prints --version envelope in json mode (0.190625ms)
  ✔ runs a registered command (text mode) (0.30525ms)
  ✔ runs a registered command (json mode) with envelope (0.143291ms)
  ✔ rejects unknown command with exit 2 (text) (0.530875ms)
  ✔ rejects unknown command with exit 2 (json envelope) (1.762375ms)
  ✔ surfaces usage errors as exit 2 (0.323209ms)
  ✔ surfaces runtime errors as exit 1 (0.292791ms)
  ✔ rejects missing subcommand (json exit 2) (0.173291ms)
  ✔ subcommand --help is intercepted and exits 0 (text) (0.315334ms)
  ✔ subcommand -h is intercepted and exits 0 (json) (0.178875ms)
  ✔ rejects unknown long flag with exit 2 (text) (0.270667ms)
  ✔ rejects unknown long flag with exit 2 (json envelope) (0.184375ms)
  ✔ accepts known value flag and its value (not mistaken for a flag) (0.101042ms)
  ✔ rejects unknown flag even after a valid value flag (0.230209ms)
✔ dispatch (8.021042ms)
▶ normalizeForCompare
  ✔ masks ISO-8601 timestamps (3.663ms)
  ✔ masks 40-char git hashes (0.281958ms)
  ✔ masks epoch-second/milli integers (0.685583ms)
  ✔ masks absolute repo roots (POSIX) (0.184375ms)
  ✔ normalizes Windows backslashes and masks sample root (0.164ms)
  ✔ collapses mtime integers regardless of value (0.382458ms)
  ✔ applies longest-root-first masking so nested roots win (0.563375ms)
✔ normalizeForCompare (7.872458ms)
▶ compareJsonOutputs
  ✔ returns null for equal normalized values (0.41625ms)
  ✔ reports the first differing path (0.440125ms)
  ✔ reports missing keys with direction (0.276667ms)
  ✔ reports array length mismatches (0.099583ms)
✔ compareJsonOutputs (1.60075ms)
▶ frontend scanner
  ✔ extracts vue component props/emits (3.743125ms)
  ✔ extracts react props from interface (0.847916ms)
  ✔ extracts hooks by use* filename (0.352459ms)
  ✔ extracts routes and redundancy candidates (0.827292ms)
  ✔ extractVueProps from defineProps object form (0.275875ms)
  ✔ extractEmits filters to valid names (0.094625ms)
  ✔ extractApiEndpoints from request/fetch calls (0.327208ms)
✔ frontend scanner (8.75275ms)
▶ files scanner
  ✔ discoverFiles walks and categorizes (2.219667ms)
  ✔ discoverFiles excludes node_modules/.git (2.192875ms)
  ✔ uses stable code-point ordering across operating systems (1.709792ms)
  ✔ categorize and simpleMatch basics (0.377875ms)
✔ files scanner (6.931875ms)
▶ incremental scan cache
  ✔ reuses unchanged frontend facts without reading the file again (0.4365ms)
  ✔ uses nanosecond-compatible file signatures and invalidates changed entries (0.752709ms)
✔ incremental scan cache (1.299375ms)
▶ quality scanner
  ✔ packageFrameworks detects Vue+TypeScript from deps (0.201792ms)
  ✔ detectPackage reads package.json scripts and frameworks (0.956166ms)
  ✔ packageManager detects npm/pnpm/yarn by lockfile (0.285458ms)
  ✔ detectQualityCommands: Python project STILL recognizes pytest/ruff/mypy (P1.3) (0.846459ms)
  ✔ detectQualityCommands: JS project infers eslint/tsc from config presence (0.930208ms)
✔ quality scanner (3.372708ms)
FixtureGraph 已安装，开始运行分析："/opt/homebrew/Cellar/node/26.3.0/bin/node" -e "process.stdout.write('graph-ok')"
FixtureGraph 开始执行，超时上限 900 秒。
GitNexus：仓库内 runner 需要显式使用 --allow-repo-runner。
▶ graph command authorization
  ✔ preserves and detects Windows absolute paths on POSIX (3.197083ms)
  ✔ allows repository-contained absolute paths and rejects outside paths (0.565917ms)
  ✔ requires explicit permission for repo runners and environment commands (0.344166ms)
✔ graph command authorization (5.331083ms)
▶ graph setup execution
  ✔ executes an authorized installed analyzer and captures evidence (120.105084ms)
  ✔ records a skipped result instead of executing an unauthorized runner (0.520416ms)
✔ graph setup execution (120.783041ms)
▶ adapter block management
  ✔ rejects paths outside the allowed set (1.513291ms)
  ✔ replaceSingleManagedBlock creates then updates (0.443083ms)
  ✔ upsert then remove a managed block (1.94475ms)
✔ adapter block management (5.1425ms)
▶ adapters command family
  ✔ apply writes codex + claude blocks; status reports current (2.326833ms)
  ✔ preview is dry-run (no files written) (0.399125ms)
  ✔ remove clears blocks (1.164417ms)
  ✔ status --check returns non-zero when not current (0.746167ms)
  ✔ adapterTargets both returns 3 targets (codex, claude, claude-nested) (1.404916ms)
✔ adapters command family (6.4095ms)
▶ top-level install command
  ✔ creates .claude/ and applies adapters; --hooks writes templates (2.680458ms)
✔ top-level install command (2.873542ms)
▶ agent install command
  ✔ agentInstallCommands builds codex+claude for all (0.285917ms)
  ✔ --dry-run classifies present when cli exists, missing otherwise (0.675583ms)
  ✔ rejects invalid target (0.215542ms)
✔ agent install command (1.310875ms)
▶ git hooks (AC-07: no python3)
  ✔ hook body calls project-intel (Node CLI), never python3 (0.145709ms)
  ✔ writeHookTemplates writes 3 hooks + README under .project-intel/hooks (1.140375ms)
✔ git hooks (AC-07: no python3) (1.383583ms)
▶ sanitizeErrorText
  ✔ redacts authorization bearer tokens (8.433083ms)
  ✔ redacts cookies (0.144834ms)
  ✔ redacts password/secret/token/api_key (0.1065ms)
  ✔ redacts aws credentials (0.080833ms)
  ✔ redacts URL userinfo (0.072708ms)
  ✔ leaves benign text intact (0.656334ms)
✔ sanitizeErrorText (10.867375ms)
▶ extractGlobalJson
  ✔ strips --json and reports mode (1.15875ms)
  ✔ preserves argv when --json absent (0.09825ms)
✔ extractGlobalJson (1.4005ms)
▶ jsonEnvelope
  ✔ shapes a success envelope (0.202625ms)
  ✔ classifies exit 2 as USAGE_ERROR with sanitized in-place error (0.125542ms)
  ✔ classifies non-2 failure as COMMAND_FAILED with default message (0.084542ms)
  ✔ trims the output field (0.054667ms)
✔ jsonEnvelope (0.609041ms)
▶ parseGlobal / splitArgv
  ✔ parses --project value (0.171083ms)
  ✔ parses --project= form (0.270709ms)
  ✔ parses --json (0.119917ms)
  ✔ rejects unknown long option before subcommand with exit-2 UsageError (0.15325ms)
  ✔ splitArgv separates global, command, and rest (0.133875ms)
  ✔ splitArgv returns null when no subcommand (0.053167ms)
✔ parseGlobal / splitArgv (1.07975ms)
▶ withLock (in-process)
  ✔ blocks same-process re-entrant acquire (no deadlock) (63.294041ms)
  ✔ releases the lockfile after the critical section (0.715958ms)
✔ withLock (in-process) (65.786125ms)
▶ withLock (multi-process contention)
  ✔ grants exclusive access across child processes (1487.678125ms)
✔ withLock (multi-process contention) (1487.820625ms)
▶ paths
  ✔ toPosix converts separators (1.031042ms)
  ✔ normalizeBusinessPath strips leading ./ and normalizes (0.193375ms)
  ✔ isAbsolutePathLike detects posix, windows drive, unc (0.509667ms)
  ✔ resolveInside rejects traversal outside root (1.181583ms)
  ✔ expandUser leaves non-home paths alone (0.198541ms)
✔ paths (7.451792ms)
▶ atomic-write
  ✔ writes text with a trailing newline, UTF-8 preserved (8.936667ms)
  ✔ writes JSON without ascii escaping and creates parent dirs (7.292625ms)
  ✔ preserves existing file mode (11.16375ms)
  ✔ loadJson returns default on missing/corrupt (0.86725ms)
  ✔ loadJsonStrict raises on corrupt/non-object (0.688209ms)
✔ atomic-write (29.3455ms)
中文测试
{
  "name": "中文"
}
err 中文
▶ subprocess.spawn (argv)
  ✔ runs a successful command and captures output (118.119291ms)
  ✔ returns 127 when the binary is missing (13.319292ms)
  ✔ returns a non-zero code on argv usage error (33.652666ms)
✔ subprocess.spawn (argv) (166.526625ms)
▶ subprocess.which / commandExists
  ✔ finds node on PATH (1.001291ms)
  ✔ returns null for a missing command (0.44825ms)
✔ subprocess.which / commandExists (1.621458ms)
▶ subprocess.runShell (shell form)
  ✔ supports pipes and redirects (10.083625ms)
  ✔ supports environment variable expansion (14.501375ms)
  ✔ returns 0 for a true compound command (6.960584ms)
  ✔ surfaces non-zero exit of a failed command (5.828583ms)
✔ subprocess.runShell (shell form) (37.696875ms)
▶ output (UTF-8)
  ✔ print writes a UTF-8 line including Chinese (0.792709ms)
  ✔ printJson renders without ASCII escaping (0.170458ms)
  ✔ printError writes to stderr (0.091208ms)
✔ output (UTF-8) (1.192208ms)
▶ io.yaml
  ✔ parses flat key: value (1.491417ms)
  ✔ strips quoted values (0.137042ms)
  ✔ coerces scalars (0.174958ms)
✔ io.yaml (1.908166ms)
▶ io.markdown
  ✔ parses ATX headings with level and text (0.206709ms)
  ✔ normalizeHeading collapses whitespace (0.046583ms)
  ✔ hasMeaningfulContent rejects blank/placeholder (0.199208ms)
✔ io.markdown (0.534584ms)
已初始化 .project-intel，索引了 4 个文本文件。
{
  "dryRun": true,
  "manifest": {
    "schemaVersion": 2,
    "toolVersion": "0.7.0",
    "projectRoot": ".",
    "generatedAt": "2026-07-27T01:31:00.426Z",
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
    "generatedAt": "2026-07-27T01:31:00.503Z",
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
    ".project-intel/requirements/<requirement-id>/*.md"
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
  ✔ writes the .project-intel layout (manifest/config/knowledge/status) (239.216ms)
  ✔ --dry-run does not write files (85.505833ms)
  ✔ refresh re-writes without tooling (486.832458ms)
  ✔ strict + no-graph is a usage error (0.56425ms)
  ✔ ensureProjectIntelGitignore writes local-only rules (0.870916ms)
✔ init command (816.069917ms)
▶ doctor command
  ✔ reports node runtime, not python (12.048958ms)
  ✔ detects initialized state after init (400.27775ms)
✔ doctor command (412.527709ms)
▶ check command
  ✔ passes with no hard rules configured (320.584458ms)
  ✔ --dry-run does not write status (233.97925ms)
✔ check command (554.759ms)
▶ standards inference
  ✔ infers PascalCase naming from >=3 pascal components (0.620125ms)
  ✔ infers backend Service suffix from >=2 services (0.170583ms)
  ✔ infers ui-pattern from redundancy candidates (0.086167ms)
  ✔ ports backend API, layering and operational inference categories (0.228916ms)
✔ standards inference (1.257334ms)
▶ project domain candidates
  ✔ aggregates repeated non-generic parent segments in stable order (1.200209ms)
✔ project domain candidates (1.351459ms)
▶ standards documents
  ✔ renders detailed frontend and backend facts instead of count-only placeholders (1.676375ms)
✔ standards documents (1.735625ms)
▶ hard rules engine
  ✔ returns no violations with the empty default set (0.091459ms)
  ✔ surfaces a registered rule violation (0.095416ms)
✔ hard rules engine (0.242ms)
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ requirement command dispatcher
  ✔ status returns state for a created requirement (55.570458ms)
  ✔ intake persists document actions and later selection blocks generation (63.117333ms)
  ✔ acceptance set persists AC-01..AC-02 (58.074709ms)
  ✔ query reads v2 and legacy by-id archives and supports --file (77.438125ms)
  ✔ test-contract set requires --kind and --report-action (78.989042ms)
  ✔ test-contract register validates and normalizes a structured report path (103.705208ms)
  ✔ ready -> begin through the dispatcher (843.6025ms)
  ✔ reopen after close (86.743417ms)
  ✔ generate enforces lifecycle order and creates a requirement scaffold (83.094583ms)
  ✔ generate refuses implicit overwrite and --replace really rebuilds the scaffold (102.26425ms)
  ✔ rejects missing --requirement-id (3.627583ms)
  ✔ add persists artifact registration into the manifest (350.213958ms)
  ✔ rejects arbitrary delivery-document content (270.577125ms)
  ✔ design registration rejects missing source evidence paths (265.927458ms)
  ✔ design registration ignores symbols that exist only in comments or strings (261.612916ms)
  ✔ add registers a structured test report as current requirement evidence (537.82475ms)
  ✔ diagnose records a Bug root cause (ticketKind=bug) (71.747875ms)
  ✔ diagnose rejects missing source evidence paths (85.336666ms)
  ✔ diagnose rejects symbols that only appear in comments or strings (82.042125ms)
  ✔ diagnose rejects non-bug requirements (63.114875ms)
  ✔ defer adds a readiness blocker for design (61.121ms)
  ✔ resolve-finding marks a review finding resolved (60.823125ms)
  ✔ resolve-finding rejects unknown finding IDs (46.349875ms)
✔ requirement command dispatcher (3715.579417ms)
▶ requirement layout
  ✔ artifactFilename maps known 
```
