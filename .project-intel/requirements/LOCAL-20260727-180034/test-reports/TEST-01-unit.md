# LOCAL-20260727-180034 测试报告

- 测试类型：unit
- 阶段：red
- 结果：passed
- 验收标准：AC-01,AC-02,AC-03,AC-04,AC-05
- 文件范围：src/__tests__/state-machine.test.ts, src/__tests__/requirement-command.test.ts

## 执行结果

### npm test -- src/__tests__/state-machine.test.ts src/__tests__/requirement-command.test.ts

- exitCode: 1
- executedCount: 238

```text
Skill behavior scenario contracts verified: 27 scenarios, 17 skills
▶ maskCommentsAndStrings
  ✔ masks line and block comments and string contents (0.91425ms)
✔ maskCommentsAndStrings (2.366792ms)
▶ scanBackendFile
  ✔ extracts a Spring controller endpoint and methods (.java) (13.817709ms)
  ✔ extracts Python def/class and Flask routes (.py) (2.003375ms)
  ✔ classifies a service by name and extracts transaction signals (0.486333ms)
  ✔ extracts config keys from yaml (0.410583ms)
  ✔ classifies repository files and extracts SQL ops from xml mapper (0.973084ms)
  ✔ extracts permission signals (0.4815ms)
  ✔ extracts error code signals (0.279042ms)
  ✔ requires bound framework imports and keeps Django class views (0.254625ms)
  ✔ labels malformed Python without accepting route facts (0.100334ms)
  ✔ applies configured backend entrypoint rules (0.173125ms)
✔ scanBackendFile (20.083625ms)
▶ BACKEND_SUFFIXES
  ✔ includes java, kt, py, go, ts, js (0.05775ms)
✔ BACKEND_SUFFIXES (0.094208ms)
▶ cli snapshot contract (AC-02)
  ✔ loads a well-formed snapshot (1.37425ms)
  ✔ captured every top-level command's help (1.577208ms)
  ✔ pins the JSON envelope shape on every probe (0.671083ms)
  ✔ the version command exits 0 and prints a semver (0.589209ms)
  ✔ usage errors exit non-zero with a non-ok envelope (0.361625ms)
✔ cli snapshot contract (AC-02) (5.806667ms)
▶ live Node CLI contract (AC-02/AC-10)
  ✔ dist/cli.js exists and is runnable (0.442708ms)
  ✔ version command exits 0 and prints a semver (179.717666ms)
  ✔ --version flag exits 0 and prints a semver (148.612167ms)
  ✔ every baseline command's --help is byte-for-byte compatible (1909.824959ms)
  ✔ top-level --help is byte-for-byte compatible (79.116292ms)
  ✔ top-level --help output contains all baseline commands (75.178458ms)
  ✔ subcommand --help output contains usage line and key flags (221.86875ms)
  ✔ unknown command exits 2 (71.678417ms)
  ✔ unknown flag exits 2 (70.576083ms)
  ✔ version --json produces a valid envelope with version field (73.44875ms)
  ✔ doctor --json produces a valid envelope with runtime=node (72.282417ms)
  ✔ usage error --json produces ok=false envelope (69.875125ms)
✔ live Node CLI contract (AC-02/AC-10) (2973.379583ms)
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
无法识别的参数：--definitely-invalid
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
无法识别的参数：--nope
▶ dispatch
  ✔ prints --version alone (3.3075ms)
  ✔ prints --version envelope in json mode (0.199458ms)
  ✔ runs a registered command (text mode) (0.205917ms)
  ✔ runs a registered command (json mode) with envelope (0.346666ms)
  ✔ rejects unknown command with exit 2 (text) (1.9825ms)
  ✔ rejects unknown command with exit 2 (json envelope) (1.2435ms)
  ✔ surfaces usage errors as exit 2 (0.179709ms)
  ✔ surfaces runtime errors as exit 1 (0.09875ms)
  ✔ rejects missing subcommand (json exit 2) (0.075292ms)
  ✔ subcommand --help is intercepted and exits 0 (text) (0.1505ms)
  ✔ subcommand -h is intercepted and exits 0 (json) (0.078458ms)
  ✔ rejects unknown long flag with exit 2 (text) (0.050458ms)
  ✔ rejects unknown long flag with exit 2 (json envelope) (0.059333ms)
  ✔ accepts known value flag and its value (not mistaken for a flag) (0.389625ms)
  ✔ rejects unknown flag even after a valid value flag (0.095833ms)
✔ dispatch (10.794458ms)
▶ normalizeForCompare
  ✔ masks ISO-8601 timestamps (10.235292ms)
  ✔ masks 40-char git hashes (0.390833ms)
  ✔ masks epoch-second/milli integers (0.1775ms)
  ✔ masks absolute repo roots (POSIX) (0.143416ms)
  ✔ normalizes Windows backslashes and masks sample root (0.274875ms)
  ✔ collapses mtime integers regardless of value (0.40525ms)
  ✔ applies longest-root-first masking so nested roots win (0.085417ms)
✔ normalizeForCompare (13.424167ms)
▶ compareJsonOutputs
  ✔ returns null for equal normalized values (0.315ms)
  ✔ reports the first differing path (0.075125ms)
  ✔ reports missing keys with direction (0.620417ms)
  ✔ reports array length mismatches (0.207667ms)
✔ compareJsonOutputs (1.549ms)
▶ frontend scanner
  ✔ extracts vue component props/emits (36.637458ms)
  ✔ extracts react props from interface (0.835333ms)
  ✔ extracts hooks by use* filename (0.589084ms)
  ✔ extracts routes and redundancy candidates (0.851708ms)
  ✔ extractVueProps from defineProps object form (0.620667ms)
  ✔ extractEmits filters to valid names (0.358792ms)
  ✔ extractApiEndpoints from request/fetch calls (0.375708ms)
✔ frontend scanner (41.765083ms)
▶ files scanner
  ✔ discoverFiles walks and categorizes (2.085875ms)
  ✔ discoverFiles excludes node_modules/.git (1.081458ms)
  ✔ uses stable code-point ordering across operating systems (4.47275ms)
  ✔ categorize and simpleMatch basics (0.1835ms)
✔ files scanner (8.101292ms)
▶ incremental scan cache
  ✔ reuses unchanged frontend facts without reading the file again (0.227042ms)
  ✔ uses nanosecond-compatible file signatures and invalidates changed entries (0.362667ms)
✔ incremental scan cache (0.640875ms)
▶ quality scanner
  ✔ packageFrameworks detects Vue+TypeScript from deps (0.078417ms)
  ✔ detectPackage reads package.json scripts and frameworks (0.427125ms)
  ✔ packageManager detects npm/pnpm/yarn by lockfile (0.15375ms)
  ✔ detectQualityCommands: Python project STILL recognizes pytest/ruff/mypy (P1.3) (0.623042ms)
  ✔ detectQualityCommands: JS project infers eslint/tsc from config presence (1.14275ms)
✔ quality scanner (2.617542ms)
FixtureGraph 已安装，开始运行分析："/opt/homebrew/Cellar/node/26.3.0/bin/node" -e "process.stdout.write('graph-ok')"
FixtureGraph 开始执行，超时上限 900 秒。
GitNexus：仓库内 runner 需要显式使用 --allow-repo-runner。
▶ graph command authorization
  ✔ preserves and detects Windows absolute paths on POSIX (2.671292ms)
  ✔ allows repository-contained absolute paths and rejects outside paths (0.456916ms)
  ✔ requires explicit permission for repo runners and environment commands (0.252291ms)
✔ graph command authorization (4.639542ms)
▶ graph setup execution
  ✔ executes an authorized installed analyzer and captures evidence (87.418583ms)
  ✔ records a skipped result instead of executing an unauthorized runner (0.697167ms)
✔ graph setup execution (88.37425ms)
▶ adapter block management
  ✔ rejects paths outside the allowed set (0.579041ms)
  ✔ replaceSingleManagedBlock creates then updates (0.220291ms)
  ✔ upsert then remove a managed block (0.607166ms)
✔ adapter block management (2.1545ms)
▶ adapters command family
  ✔ apply writes codex + claude blocks; status reports current (0.835875ms)
  ✔ preview is dry-run (no files written) (0.139042ms)
  ✔ remove clears blocks (0.373916ms)
  ✔ status --check returns non-zero when not current (0.253917ms)
  ✔ adapterTargets both returns 3 targets (codex, claude, claude-nested) (0.655375ms)
✔ adapters command family (2.419ms)
▶ top-level install command
  ✔ creates .claude/ and applies adapters; --hooks writes templates (0.930292ms)
✔ top-level install command (0.9915ms)
▶ agent install command
  ✔ agentInstallCommands builds codex+claude for all (0.103958ms)
  ✔ --dry-run classifies present when cli exists, missing otherwise (0.280125ms)
  ✔ rejects invalid target (0.111375ms)
✔ agent install command (0.544209ms)
▶ git hooks (AC-07: no python3)
  ✔ hook body calls project-intel (Node CLI), never python3 (0.042875ms)
  ✔ writeHookTemplates writes 3 hooks + README under .project-intel/hooks (0.522417ms)
✔ git hooks (AC-07: no python3) (0.60125ms)
▶ sanitizeErrorText
  ✔ redacts authorization bearer tokens (1.778667ms)
  ✔ redacts cookies (0.113875ms)
  ✔ redacts password/secret/token/api_key (0.05975ms)
  ✔ redacts aws credentials (0.046958ms)
  ✔ redacts URL userinfo (0.04225ms)
  ✔ leaves benign text intact (0.376125ms)
✔ sanitizeErrorText (3.810833ms)
▶ extractGlobalJson
  ✔ strips --json and reports mode (1.395958ms)
  ✔ preserves argv when --json absent (0.157959ms)
✔ extractGlobalJson (1.710042ms)
▶ jsonEnvelope
  ✔ shapes a success envelope (0.2875ms)
  ✔ classifies exit 2 as USAGE_ERROR with sanitized in-place error (0.183333ms)
  ✔ classifies non-2 failure as COMMAND_FAILED with default message (0.108834ms)
  ✔ trims the output field (0.061708ms)
✔ jsonEnvelope (0.87625ms)
▶ parseGlobal / splitArgv
  ✔ parses --project value (0.204375ms)
  ✔ parses --project= form (0.071666ms)
  ✔ parses --json (0.05175ms)
  ✔ rejects unknown long option before subcommand with exit-2 UsageError (0.251167ms)
  ✔ splitArgv separates global, command, and rest (1.558792ms)
  ✔ splitArgv returns null when no subcommand (0.082166ms)
✔ parseGlobal / splitArgv (2.442375ms)
▶ withLock (in-process)
  ✔ blocks same-process re-entrant acquire (no deadlock) (63.953958ms)
  ✔ releases the lockfile after the critical section (0.510625ms)
✔ withLock (in-process) (66.075584ms)
▶ withLock (multi-process contention)
  ✔ grants exclusive access across child processes (1160.17375ms)
✔ withLock (multi-process contention) (1160.244541ms)
▶ paths
  ✔ toPosix converts separators (0.46325ms)
  ✔ normalizeBusinessPath strips leading ./ and normalizes (0.081667ms)
  ✔ isAbsolutePathLike detects posix, windows drive, unc (0.075833ms)
  ✔ resolveInside rejects traversal outside root (0.358083ms)
  ✔ expandUser leaves non-home paths alone (0.049584ms)
✔ paths (1.645958ms)
▶ atomic-write
  ✔ writes text with a trailing newline, UTF-8 preserved (7.05375ms)
  ✔ writes JSON without ascii escaping and creates parent dirs (5.258417ms)
  ✔ preserves existing file mode (16.678208ms)
  ✔ loadJson returns default on missing/corrupt (0.447958ms)
  ✔ loadJsonStrict raises on corrupt/non-object (0.366416ms)
✔ atomic-write (30.203708ms)
中文测试
{
  "name": "中文"
}
err 中文
▶ subprocess.spawn (argv)
  ✔ runs a successful command and captures output (98.341959ms)
  ✔ returns 127 when the binary is missing (4.908625ms)
  ✔ returns a non-zero code on argv usage error (24.924166ms)
✔ subprocess.spawn (argv) (133.993625ms)
▶ subprocess.which / commandExists
  ✔ finds node on PATH (1.488875ms)
  ✔ returns null for a missing command (0.706042ms)
✔ subprocess.which / commandExists (2.622625ms)
▶ subprocess.runShell (shell form)
  ✔ supports pipes and redirects (9.438833ms)
  ✔ supports environment variable expansion (11.417167ms)
  ✔ returns 0 for a true compound command (4.947792ms)
  ✔ surfaces non-zero exit of a failed command (5.020708ms)
✔ subprocess.runShell (shell form) (31.083166ms)
▶ output (UTF-8)
  ✔ print writes a UTF-8 line including Chinese (0.835167ms)
  ✔ printJson renders without ASCII escaping (0.153292ms)
  ✔ printError writes to stderr (0.150167ms)
✔ output (UTF-8) (1.301375ms)
▶ io.yaml
  ✔ parses flat key: value (1.720208ms)
  ✔ strips quoted values (0.147916ms)
  ✔ coerces scalars (0.191875ms)
✔ io.yaml (2.205875ms)
▶ io.markdown
  ✔ parses ATX headings with level and text (0.243292ms)
  ✔ normalizeHeading collapses whitespace (0.044417ms)
  ✔ hasMeaningfulContent rejects blank/placeholder (0.215709ms)
✔ io.markdown (0.602083ms)
已初始化 .project-intel，索引了 4 个文本文件。
{
  "dryRun": true,
  "manifest": {
    "schemaVersion": 2,
    "toolVersion": "0.7.3",
    "projectRoot": ".",
    "generatedAt": "2026-07-27T10:06:13.352Z",
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
    "generatedAt": "2026-07-27T10:06:13.446Z",
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
  ✔ writes the .project-intel layout (manifest/config/knowledge/status) (199.074166ms)
  ✔ --dry-run does not write files (101.185208ms)
  ✔ refresh re-writes without tooling (543.141667ms)
  ✔ strict + no-graph is a usage error (3.817667ms)
  ✔ ensureProjectIntelGitignore writes local-only rules (0.459917ms)
✔ init command (848.965458ms)
▶ doctor command
  ✔ reports node runtime, not python (9.712167ms)
  ✔ detects initialized state after init (313.750916ms)
✔ doctor command (323.584375ms)
▶ check command
  ✔ passes with no hard rules configured (264.717209ms)
  ✔ --dry-run does not write status (339.800084ms)
✔ check command (604.744459ms)
▶ standards inference
  ✔ infers PascalCase naming from >=3 pascal components (0.408083ms)
  ✔ infers backend Service suffix from >=2 services (0.113542ms)
  ✔ infers ui-pattern from redundancy candidates (0.052541ms)
  ✔ ports backend API, layering and operational inference categories (0.150166ms)
✔ standards inference (0.870917ms)
▶ project domain candidates
  ✔ aggregates repeated non-generic parent segments in stable order (0.604583ms)
✔ project domain candidates (0.634208ms)
▶ standards documents
  ✔ renders detailed frontend and backend facts instead of count-only placeholders (0.982667ms)
✔ standards documents (1.013084ms)
▶ hard rules engine
  ✔ returns no violations with the empty default set (0.041458ms)
  ✔ surfaces a registered rule violation (0.080125ms)
✔ hard rules engine (0.147083ms)
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ requirement command dispatcher
  ✔ status returns state for a created requirement (46.528958ms)
  ✔ plan writes into the resolved id-title requirement directory (64.304125ms)
  ✖ intake persists document actions and later selection blocks generation (47.577ms)
  ✖ intake requires a valid user supplied version date (91.041833ms)
  ✔ acceptance set persists AC-01..AC-02 (56.216417ms)
  ✔ query reads v2 and legacy by-id archives and supports --file (70.853708ms)
  ✔ test-contract set requires --kind and --report-action (100.057167ms)
  ✔ test-contract register validates and normalizes a structured report path (87.296667ms)
  ✔ ready -> begin through the dispatcher (722.481125ms)
  ✔ reopen after close (57.791875ms)
  ✔ generate enforces lifecycle order and creates a requirement scaffold (67.129ms)
  ✔ generate refuses implicit overwrite and --replace really rebuilds the scaffold (112.34375ms)
  ✔ rejects missing --requirement-id (3.2675ms)
  ✔ add persists artifact registration into the manifest (319.707125ms)
  ✔ rejects arbitrary delivery-document content (107.433625ms)
  ✔ design registration rejects missing source evidence paths (172.5115ms)
  ✔ design registration ignores symbols that exist only in comments or strings (233.156875ms)
  ✔ add registers a structured test report as current requirement evidence (442.525833ms)
  ✔ diagnose records a Bug root cause (ticketKind=bug) (67.634875ms)
  ✔ diagnose rejects missing source evidence paths (47.139875ms)
  ✔ diagnose rejects symbols that only appear in comments or strings (32.039667ms)
  ✔ diagnose rejects non-bug requirements (32.735042ms)
  ✔ defer adds a readiness blocker for design (34.795208ms)
  ✔ resolve-finding marks a review finding resolved (36.469709ms)
  ✔ resolve-fi
```
