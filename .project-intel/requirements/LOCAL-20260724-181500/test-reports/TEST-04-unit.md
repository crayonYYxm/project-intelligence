# LOCAL-20260724-181500 测试报告

- 测试类型：unit
- 阶段：regression
- 结果：passed
- 验收标准：AC-01,AC-02,AC-03,AC-04,AC-05
- 文件范围：marketplace.json, package.json, plugins/project-intelligence/.zcode-plugin/plugin.json, scripts/gen-version.mjs, scripts/check-release.mjs, scripts/check-package.mjs, src/commands/finish.ts, src/commands/test.ts, src/requirements/state-machine.ts, src/testing/render.ts, src/__tests__/zcode-compat.test.ts, src/__tests__/test-evidence.test.ts, src/__tests__/review-finish-graph.test.ts

## 执行结果

### npm test && npm run typecheck && npm run check-release

- exitCode: 0
- executedCount: 255

```text
Skill behavior scenario contracts verified: 27 scenarios, 17 skills
▶ maskCommentsAndStrings
  ✔ masks line and block comments and string contents (1.051084ms)
✔ maskCommentsAndStrings (2.381542ms)
▶ scanBackendFile
  ✔ extracts a Spring controller endpoint and methods (.java) (6.929959ms)
  ✔ extracts Python def/class and Flask routes (.py) (2.396083ms)
  ✔ classifies a service by name and extracts transaction signals (0.438917ms)
  ✔ extracts config keys from yaml (0.403042ms)
  ✔ classifies repository files and extracts SQL ops from xml mapper (0.532792ms)
  ✔ extracts permission signals (0.232792ms)
  ✔ extracts error code signals (0.180458ms)
  ✔ requires bound framework imports and keeps Django class views (0.419125ms)
  ✔ labels malformed Python without accepting route facts (0.263042ms)
  ✔ applies configured backend entrypoint rules (0.376834ms)
✔ scanBackendFile (12.686833ms)
▶ BACKEND_SUFFIXES
  ✔ includes java, kt, py, go, ts, js (0.130541ms)
✔ BACKEND_SUFFIXES (0.265958ms)
▶ cli snapshot contract (AC-02)
  ✔ loads a well-formed snapshot (2.222625ms)
  ✔ captured every top-level command's help (3.0745ms)
  ✔ pins the JSON envelope shape on every probe (0.768292ms)
  ✔ the version command exits 0 and prints a semver (0.872541ms)
  ✔ usage errors exit non-zero with a non-ok envelope (0.438083ms)
✔ cli snapshot contract (AC-02) (9.043916ms)
▶ live Node CLI contract (AC-02/AC-10)
  ✔ dist/cli.js exists and is runnable (0.289916ms)
  ✔ version command exits 0 and prints a semver (160.049583ms)
  ✔ --version flag exits 0 and prints a semver (193.581667ms)
  ✔ every baseline command's --help is byte-for-byte compatible (2874.708709ms)
  ✔ top-level --help is byte-for-byte compatible (131.740959ms)
  ✔ top-level --help output contains all baseline commands (129.54325ms)
  ✔ subcommand --help output contains usage line and key flags (396.646792ms)
  ✔ unknown command exits 2 (132.167167ms)
  ✔ unknown flag exits 2 (129.752042ms)
  ✔ version --json produces a valid envelope with version field (132.936542ms)
  ✔ doctor --json produces a valid envelope with runtime=node (137.396208ms)
  ✔ usage error --json produces ok=false envelope (125.795875ms)
✔ live Node CLI contract (AC-02/AC-10) (4545.5095ms)
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
  ✔ prints --version alone (2.111417ms)
  ✔ prints --version envelope in json mode (0.506917ms)
  ✔ runs a registered command (text mode) (0.429416ms)
  ✔ runs a registered command (json mode) with envelope (0.197583ms)
  ✔ rejects unknown command with exit 2 (text) (0.6465ms)
  ✔ rejects unknown command with exit 2 (json envelope) (0.904416ms)
  ✔ surfaces usage errors as exit 2 (0.250625ms)
  ✔ surfaces runtime errors as exit 1 (0.299041ms)
  ✔ rejects missing subcommand (json exit 2) (3.962875ms)
  ✔ subcommand --help is intercepted and exits 0 (text) (0.686583ms)
  ✔ subcommand -h is intercepted and exits 0 (json) (0.195542ms)
  ✔ rejects unknown long flag with exit 2 (text) (0.107208ms)
  ✔ rejects unknown long flag with exit 2 (json envelope) (0.10825ms)
  ✔ accepts known value flag and its value (not mistaken for a flag) (0.079834ms)
  ✔ rejects unknown flag even after a valid value flag (0.089625ms)
✔ dispatch (12.457417ms)
▶ normalizeForCompare
  ✔ masks ISO-8601 timestamps (2.315375ms)
  ✔ masks 40-char git hashes (0.21225ms)
  ✔ masks epoch-second/milli integers (0.123209ms)
  ✔ masks absolute repo roots (POSIX) (0.111542ms)
  ✔ normalizes Windows backslashes and masks sample root (0.112958ms)
  ✔ collapses mtime integers regardless of value (0.134334ms)
  ✔ applies longest-root-first masking so nested roots win (0.118333ms)
✔ normalizeForCompare (12.394167ms)
▶ compareJsonOutputs
  ✔ returns null for equal normalized values (1.174792ms)
  ✔ reports the first differing path (0.169541ms)
  ✔ reports missing keys with direction (0.238917ms)
  ✔ reports array length mismatches (0.111291ms)
✔ compareJsonOutputs (2.044458ms)
▶ frontend scanner
  ✔ extracts vue component props/emits (4.075958ms)
  ✔ extracts react props from interface (1.019625ms)
  ✔ extracts hooks by use* filename (1.922708ms)
  ✔ extracts routes and redundancy candidates (1.499459ms)
  ✔ extractVueProps from defineProps object form (1.157083ms)
  ✔ extractEmits filters to valid names (0.303041ms)
  ✔ extractApiEndpoints from request/fetch calls (0.928834ms)
✔ frontend scanner (14.236541ms)
▶ files scanner
  ✔ discoverFiles walks and categorizes (2.067166ms)
  ✔ discoverFiles excludes node_modules/.git (0.930875ms)
  ✔ uses stable code-point ordering across operating systems (1.161917ms)
  ✔ categorize and simpleMatch basics (0.321583ms)
✔ files scanner (4.788459ms)
▶ incremental scan cache
  ✔ reuses unchanged frontend facts without reading the file again (0.54275ms)
  ✔ uses nanosecond-compatible file signatures and invalidates changed entries (1.012167ms)
✔ incremental scan cache (1.685833ms)
▶ quality scanner
  ✔ packageFrameworks detects Vue+TypeScript from deps (0.23825ms)
  ✔ detectPackage reads package.json scripts and frameworks (1.0655ms)
  ✔ packageManager detects npm/pnpm/yarn by lockfile (0.542459ms)
  ✔ detectQualityCommands: Python project STILL recognizes pytest/ruff/mypy (P1.3) (1.200625ms)
  ✔ detectQualityCommands: JS project infers eslint/tsc from config presence (1.267334ms)
✔ quality scanner (4.555166ms)
FixtureGraph 已安装，开始运行分析："/opt/homebrew/Cellar/node/26.3.0/bin/node" -e "process.stdout.write('graph-ok')"
FixtureGraph 开始执行，超时上限 900 秒。
GitNexus：仓库内 runner 需要显式使用 --allow-repo-runner。
▶ graph command authorization
  ✔ preserves and detects Windows absolute paths on POSIX (2.129417ms)
  ✔ allows repository-contained absolute paths and rejects outside paths (0.293833ms)
  ✔ requires explicit permission for repo runners and environment commands (0.262125ms)
✔ graph command authorization (3.711458ms)
▶ graph setup execution
  ✔ executes an authorized installed analyzer and captures evidence (129.219625ms)
  ✔ records a skipped result instead of executing an unauthorized runner (0.703209ms)
✔ graph setup execution (130.099916ms)
▶ adapter block management
  ✔ rejects paths outside the allowed set (1.278542ms)
  ✔ replaceSingleManagedBlock creates then updates (0.41025ms)
  ✔ upsert then remove a managed block (1.486083ms)
✔ adapter block management (4.630333ms)
▶ adapters command family
  ✔ apply writes codex + claude blocks; status reports current (2.241625ms)
  ✔ preview is dry-run (no files written) (0.294625ms)
  ✔ remove clears blocks (0.711333ms)
  ✔ status --check returns non-zero when not current (0.478541ms)
  ✔ adapterTargets both returns 3 targets (codex, claude, claude-nested) (1.160917ms)
✔ adapters command family (5.741875ms)
▶ top-level install command
  ✔ creates .claude/ and applies adapters; --hooks writes templates (1.8415ms)
✔ top-level install command (1.964583ms)
▶ agent install command
  ✔ agentInstallCommands builds codex+claude for all (0.272792ms)
  ✔ --dry-run classifies present when cli exists, missing otherwise (0.80675ms)
  ✔ rejects invalid target (0.186833ms)
✔ agent install command (1.397375ms)
▶ git hooks (AC-07: no python3)
  ✔ hook body calls project-intel (Node CLI), never python3 (0.140792ms)
  ✔ writeHookTemplates writes 3 hooks + README under .project-intel/hooks (0.837958ms)
✔ git hooks (AC-07: no python3) (1.06975ms)
▶ sanitizeErrorText
  ✔ redacts authorization bearer tokens (2.555583ms)
  ✔ redacts cookies (0.198875ms)
  ✔ redacts password/secret/token/api_key (0.111833ms)
  ✔ redacts aws credentials (0.084125ms)
  ✔ redacts URL userinfo (0.167625ms)
  ✔ leaves benign text intact (0.714042ms)
✔ sanitizeErrorText (5.283ms)
▶ extractGlobalJson
  ✔ strips --json and reports mode (1.361375ms)
  ✔ preserves argv when --json absent (0.111167ms)
✔ extractGlobalJson (1.651958ms)
▶ jsonEnvelope
  ✔ shapes a success envelope (0.231625ms)
  ✔ classifies exit 2 as USAGE_ERROR with sanitized in-place error (0.14025ms)
  ✔ classifies non-2 failure as COMMAND_FAILED with default message (0.092666ms)
  ✔ trims the output field (0.064792ms)
✔ jsonEnvelope (0.699667ms)
▶ parseGlobal / splitArgv
  ✔ parses --project value (0.198083ms)
  ✔ parses --project= form (0.091584ms)
  ✔ parses --json (0.062834ms)
  ✔ rejects unknown long option before subcommand with exit-2 UsageError (0.143625ms)
  ✔ splitArgv separates global, command, and rest (0.165625ms)
  ✔ splitArgv returns null when no subcommand (0.119833ms)
✔ parseGlobal / splitArgv (1.013ms)
▶ withLock (in-process)
  ✔ blocks same-process re-entrant acquire (no deadlock) (64.178208ms)
  ✔ releases the lockfile after the critical section (1.057083ms)
✔ withLock (in-process) (66.5445ms)
▶ withLock (multi-process contention)
  ✔ grants exclusive access across child processes (1473.047625ms)
✔ withLock (multi-process contention) (1473.216792ms)
▶ paths
  ✔ toPosix converts separators (0.962875ms)
  ✔ normalizeBusinessPath strips leading ./ and normalizes (0.351792ms)
  ✔ isAbsolutePathLike detects posix, windows drive, unc (0.311166ms)
  ✔ resolveInside rejects traversal outside root (0.796125ms)
  ✔ expandUser leaves non-home paths alone (0.128042ms)
✔ paths (5.332958ms)
▶ atomic-write
  ✔ writes text with a trailing newline, UTF-8 preserved (7.282042ms)
  ✔ writes JSON without ascii escaping and creates parent dirs (9.255708ms)
  ✔ preserves existing file mode (9.9545ms)
  ✔ loadJson returns default on missing/corrupt (0.681459ms)
  ✔ loadJsonStrict raises on corrupt/non-object (0.954459ms)
✔ atomic-write (28.615375ms)
中文测试
{
  "name": "中文"
}
err 中文
▶ subprocess.spawn (argv)
  ✔ runs a successful command and captures output (162.24925ms)
  ✔ returns 127 when the binary is missing (4.356458ms)
  ✔ returns a non-zero code on argv usage error (34.029334ms)
✔ subprocess.spawn (argv) (202.046ms)
▶ subprocess.which / commandExists
  ✔ finds node on PATH (0.57125ms)
  ✔ returns null for a missing command (0.513042ms)
✔ subprocess.which / commandExists (1.253542ms)
▶ subprocess.runShell (shell form)
  ✔ supports pipes and redirects (13.8385ms)
  ✔ supports environment variable expansion (12.849792ms)
  ✔ returns 0 for a true compound command (6.022ms)
  ✔ surfaces non-zero exit of a failed command (6.638542ms)
✔ subprocess.runShell (shell form) (39.909792ms)
▶ output (UTF-8)
  ✔ print writes a UTF-8 line including Chinese (1.659125ms)
  ✔ printJson renders without ASCII escaping (0.433958ms)
  ✔ printError writes to stderr (0.278042ms)
✔ output (UTF-8) (2.78075ms)
▶ io.yaml
  ✔ parses flat key: value (2.47025ms)
  ✔ strips quoted values (0.468125ms)
  ✔ coerces scalars (0.219916ms)
✔ io.yaml (3.302667ms)
▶ io.markdown
  ✔ parses ATX headings with level and text (0.314ms)
  ✔ normalizeHeading collapses whitespace (0.118625ms)
  ✔ hasMeaningfulContent rejects blank/placeholder (0.2085ms)
✔ io.markdown (0.758791ms)
已初始化 .project-intel，索引了 4 个文本文件。
{
  "dryRun": true,
  "manifest": {
    "schemaVersion": 2,
    "toolVersion": "0.7.0",
    "projectRoot": ".",
    "generatedAt": "2026-07-27T01:34:51.253Z",
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
    "generatedAt": "2026-07-27T01:34:51.361Z",
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
  ✔ writes the .project-intel layout (manifest/config/knowledge/status) (242.937209ms)
  ✔ --dry-run does not write files (115.965375ms)
  ✔ refresh re-writes without tooling (499.908166ms)
  ✔ strict + no-graph is a usage error (0.39775ms)
  ✔ ensureProjectIntelGitignore writes local-only rules (0.970792ms)
✔ init command (862.234709ms)
▶ doctor command
  ✔ reports node runtime, not python (5.641083ms)
  ✔ detects initialized state after init (426.990542ms)
✔ doctor command (432.849875ms)
▶ check command
  ✔ passes with no hard rules configured (318.577166ms)
  ✔ --dry-run does not write status (254.921167ms)
✔ check command (573.786125ms)
▶ standards inference
  ✔ infers PascalCase naming from >=3 pascal components (0.636791ms)
  ✔ infers backend Service suffix from >=2 services (0.218375ms)
  ✔ infers ui-pattern from redundancy candidates (0.111ms)
  ✔ ports backend API, layering and operational inference categories (0.233458ms)
✔ standards inference (1.33975ms)
▶ project domain candidates
  ✔ aggregates repeated non-generic parent segments in stable order (1.483541ms)
✔ project domain candidates (1.612709ms)
▶ standards documents
  ✔ renders detailed frontend and backend facts instead of count-only placeholders (1.915125ms)
✔ standards documents (2.000291ms)
▶ hard rules engine
  ✔ returns no violations with the empty default set (0.1185ms)
  ✔ surfaces a registered rule violation (0.111166ms)
✔ hard rules engine (0.344958ms)
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ requirement command dispatcher
  ✔ status returns state for a created requirement (60.240584ms)
  ✔ intake persists document actions and later selection blocks generation (69.284083ms)
  ✔ acceptance set persists AC-01..AC-02 (57.858459ms)
  ✔ query reads v2 and legacy by-id archives and supports --file (104.3135ms)
  ✔ test-contract set requires --kind and --report-action (72.595625ms)
  ✔ test-contract register validates and normalizes a structured report path (111.485958ms)
  ✔ ready -> begin through the dispatcher (851.9905ms)
  ✔ reopen after close (82.865375ms)
  ✔ generate enforces lifecycle order and creates a requirement scaffold (77.347667ms)
  ✔ generate refuses implicit overwrite and --replace really rebuilds the scaffold (92.61875ms)
  ✔ rejects missing --requirement-id (0.277916ms)
  ✔ add persists artifact registration into the manifest (447.003708ms)
  ✔ rejects arbitrary delivery-document content (188.464667ms)
  ✔ design registration rejects missing source evidence paths (293.689208ms)
  ✔ design registration ignores symbols that exist only in comments or strings (210.12375ms)
  ✔ add registers a structured test report as current requirement evidence (607.043792ms)
  ✔ diagnose records a Bug root cause (ticketKind=bug) (68.013583ms)
  ✔ diagnose rejects missing source evidence paths (62.127333ms)
  ✔ diagnose rejects symbols that only appear in comments or strings (58.791625ms)
  ✔ diagnose rejects non-bug requirements (72.629083ms)
  ✔ defer adds a readiness blocker for design (63.832875ms)
  ✔ resolve-finding marks a review finding resolved (54.186542ms)
  ✔ resolve-finding rejects unknown finding IDs (45.442916ms)
✔ requirement command dispatcher (3756.196291ms)
▶ requirement layout
  ✔ artifactFilename maps known
```
