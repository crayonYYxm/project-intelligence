# LOCAL-20260727-180034 测试报告

- 测试类型：unit
- 阶段：green
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
  ✔ masks line and block comments and string contents (0.832ms)
✔ maskCommentsAndStrings (1.852833ms)
▶ scanBackendFile
  ✔ extracts a Spring controller endpoint and methods (.java) (3.971917ms)
  ✔ extracts Python def/class and Flask routes (.py) (3.41775ms)
  ✔ classifies a service by name and extracts transaction signals (0.563375ms)
  ✔ extracts config keys from yaml (0.648667ms)
  ✔ classifies repository files and extracts SQL ops from xml mapper (0.663458ms)
  ✔ extracts permission signals (0.254209ms)
  ✔ extracts error code signals (0.123917ms)
  ✔ requires bound framework imports and keeps Django class views (0.182583ms)
  ✔ labels malformed Python without accepting route facts (0.175417ms)
  ✔ applies configured backend entrypoint rules (0.193125ms)
✔ scanBackendFile (11.318333ms)
▶ BACKEND_SUFFIXES
  ✔ includes java, kt, py, go, ts, js (0.050791ms)
✔ BACKEND_SUFFIXES (0.087917ms)
▶ cli snapshot contract (AC-02)
  ✔ loads a well-formed snapshot (9.748584ms)
  ✔ captured every top-level command's help (4.939292ms)
  ✔ pins the JSON envelope shape on every probe (0.688292ms)
  ✔ the version command exits 0 and prints a semver (0.494875ms)
  ✔ usage errors exit non-zero with a non-ok envelope (0.567916ms)
✔ cli snapshot contract (AC-02) (21.637583ms)
▶ live Node CLI contract (AC-02/AC-10)
  ✔ dist/cli.js exists and is runnable (0.425208ms)
  ✔ version command exits 0 and prints a semver (118.272375ms)
  ✔ --version flag exits 0 and prints a semver (146.18625ms)
  ✔ every baseline command's --help is byte-for-byte compatible (1689.402417ms)
  ✔ top-level --help is byte-for-byte compatible (65.681583ms)
  ✔ top-level --help output contains all baseline commands (106.307292ms)
  ✔ subcommand --help output contains usage line and key flags (252.554084ms)
  ✔ unknown command exits 2 (102.390958ms)
  ✔ unknown flag exits 2 (68.961083ms)
  ✔ version --json produces a valid envelope with version field (74.385125ms)
  ✔ doctor --json produces a valid envelope with runtime=node (75.251667ms)
  ✔ usage error --json produces ok=false envelope (70.323166ms)
✔ live Node CLI contract (AC-02/AC-10) (2770.830208ms)
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
  ✔ prints --version alone (1.323ms)
  ✔ prints --version envelope in json mode (0.252458ms)
  ✔ runs a registered command (text mode) (0.391875ms)
  ✔ runs a registered command (json mode) with envelope (0.2095ms)
  ✔ rejects unknown command with exit 2 (text) (0.828167ms)
  ✔ rejects unknown command with exit 2 (json envelope) (2.010417ms)
  ✔ surfaces usage errors as exit 2 (0.415708ms)
  ✔ surfaces runtime errors as exit 1 (0.187ms)
  ✔ rejects missing subcommand (json exit 2) (0.205875ms)
  ✔ subcommand --help is intercepted and exits 0 (text) (0.324041ms)
  ✔ subcommand -h is intercepted and exits 0 (json) (0.148209ms)
  ✔ rejects unknown long flag with exit 2 (text) (0.056291ms)
  ✔ rejects unknown long flag with exit 2 (json envelope) (0.057667ms)
  ✔ accepts known value flag and its value (not mistaken for a flag) (0.044ms)
  ✔ rejects unknown flag even after a valid value flag (0.043458ms)
✔ dispatch (7.797209ms)
▶ normalizeForCompare
  ✔ masks ISO-8601 timestamps (5.512667ms)
  ✔ masks 40-char git hashes (0.142458ms)
  ✔ masks epoch-second/milli integers (0.09125ms)
  ✔ masks absolute repo roots (POSIX) (0.197125ms)
  ✔ normalizes Windows backslashes and masks sample root (0.300292ms)
  ✔ collapses mtime integers regardless of value (2.987375ms)
  ✔ applies longest-root-first masking so nested roots win (1.592375ms)
✔ normalizeForCompare (15.48525ms)
▶ compareJsonOutputs
  ✔ returns null for equal normalized values (1.196ms)
  ✔ reports the first differing path (0.126667ms)
  ✔ reports missing keys with direction (1.768292ms)
  ✔ reports array length mismatches (0.078166ms)
✔ compareJsonOutputs (6.078625ms)
▶ frontend scanner
  ✔ extracts vue component props/emits (9.60475ms)
  ✔ extracts react props from interface (0.454291ms)
  ✔ extracts hooks by use* filename (0.560666ms)
  ✔ extracts routes and redundancy candidates (2.52075ms)
  ✔ extractVueProps from defineProps object form (0.161125ms)
  ✔ extractEmits filters to valid names (0.057209ms)
  ✔ extractApiEndpoints from request/fetch calls (0.178416ms)
✔ frontend scanner (20.285291ms)
▶ files scanner
  ✔ discoverFiles walks and categorizes (1.257666ms)
  ✔ discoverFiles excludes node_modules/.git (0.518916ms)
  ✔ uses stable code-point ordering across operating systems (0.912583ms)
  ✔ categorize and simpleMatch basics (0.276542ms)
✔ files scanner (3.369542ms)
▶ incremental scan cache
  ✔ reuses unchanged frontend facts without reading the file again (1.296ms)
  ✔ uses nanosecond-compatible file signatures and invalidates changed entries (0.660458ms)
✔ incremental scan cache (2.5475ms)
▶ quality scanner
  ✔ packageFrameworks detects Vue+TypeScript from deps (0.235166ms)
  ✔ detectPackage reads package.json scripts and frameworks (0.82475ms)
  ✔ packageManager detects npm/pnpm/yarn by lockfile (0.180167ms)
  ✔ detectQualityCommands: Python project STILL recognizes pytest/ruff/mypy (P1.3) (1.330708ms)
  ✔ detectQualityCommands: JS project infers eslint/tsc from config presence (1.422ms)
✔ quality scanner (4.159666ms)
FixtureGraph 已安装，开始运行分析："/opt/homebrew/Cellar/node/26.3.0/bin/node" -e "process.stdout.write('graph-ok')"
FixtureGraph 开始执行，超时上限 900 秒。
GitNexus：仓库内 runner 需要显式使用 --allow-repo-runner。
▶ graph command authorization
  ✔ preserves and detects Windows absolute paths on POSIX (2.34025ms)
  ✔ allows repository-contained absolute paths and rejects outside paths (0.448ms)
  ✔ requires explicit permission for repo runners and environment commands (0.408542ms)
✔ graph command authorization (4.681792ms)
▶ graph setup execution
  ✔ executes an authorized installed analyzer and captures evidence (90.051166ms)
  ✔ records a skipped result instead of executing an unauthorized runner (0.530625ms)
✔ graph setup execution (90.729ms)
▶ adapter block management
  ✔ rejects paths outside the allowed set (1.0575ms)
  ✔ replaceSingleManagedBlock creates then updates (0.510208ms)
  ✔ upsert then remove a managed block (1.267292ms)
✔ adapter block management (3.690792ms)
▶ adapters command family
  ✔ apply writes codex + claude blocks; status reports current (2.5065ms)
  ✔ preview is dry-run (no files written) (0.337542ms)
  ✔ remove clears blocks (1.125166ms)
  ✔ status --check returns non-zero when not current (0.743292ms)
  ✔ adapterTargets both returns 3 targets (codex, claude, claude-nested) (1.280042ms)
✔ adapters command family (6.288209ms)
▶ top-level install command
  ✔ creates .claude/ and applies adapters; --hooks writes templates (3.130959ms)
✔ top-level install command (3.291292ms)
▶ agent install command
  ✔ agentInstallCommands builds codex+claude for all (0.11825ms)
  ✔ --dry-run classifies present when cli exists, missing otherwise (0.399833ms)
  ✔ rejects invalid target (0.397792ms)
✔ agent install command (1.047416ms)
▶ git hooks (AC-07: no python3)
  ✔ hook body calls project-intel (Node CLI), never python3 (0.09875ms)
  ✔ writeHookTemplates writes 3 hooks + README under .project-intel/hooks (1.25825ms)
✔ git hooks (AC-07: no python3) (1.480708ms)
▶ sanitizeErrorText
  ✔ redacts authorization bearer tokens (1.066958ms)
  ✔ redacts cookies (0.064459ms)
  ✔ redacts password/secret/token/api_key (0.130709ms)
  ✔ redacts aws credentials (0.198625ms)
  ✔ redacts URL userinfo (0.105334ms)
  ✔ leaves benign text intact (0.76575ms)
✔ sanitizeErrorText (3.694458ms)
▶ extractGlobalJson
  ✔ strips --json and reports mode (1.312875ms)
  ✔ preserves argv when --json absent (0.195ms)
✔ extractGlobalJson (1.729ms)
▶ jsonEnvelope
  ✔ shapes a success envelope (0.308542ms)
  ✔ classifies exit 2 as USAGE_ERROR with sanitized in-place error (0.168917ms)
  ✔ classifies non-2 failure as COMMAND_FAILED with default message (0.092583ms)
  ✔ trims the output field (0.086125ms)
✔ jsonEnvelope (0.8435ms)
▶ parseGlobal / splitArgv
  ✔ parses --project value (0.186292ms)
  ✔ parses --project= form (0.066417ms)
  ✔ parses --json (0.09725ms)
  ✔ rejects unknown long option before subcommand with exit-2 UsageError (0.155625ms)
  ✔ splitArgv separates global, command, and rest (0.153834ms)
  ✔ splitArgv returns null when no subcommand (0.080958ms)
✔ parseGlobal / splitArgv (0.906042ms)
▶ withLock (in-process)
  ✔ blocks same-process re-entrant acquire (no deadlock) (66.719583ms)
  ✔ releases the lockfile after the critical section (0.4145ms)
✔ withLock (in-process) (67.704958ms)
▶ withLock (multi-process contention)
  ✔ grants exclusive access across child processes (1057.180083ms)
✔ withLock (multi-process contention) (1057.316042ms)
▶ paths
  ✔ toPosix converts separators (0.760792ms)
  ✔ normalizeBusinessPath strips leading ./ and normalizes (0.162291ms)
  ✔ isAbsolutePathLike detects posix, windows drive, unc (0.14175ms)
  ✔ resolveInside rejects traversal outside root (0.643708ms)
  ✔ expandUser leaves non-home paths alone (0.145667ms)
✔ paths (2.798083ms)
▶ atomic-write
  ✔ writes text with a trailing newline, UTF-8 preserved (8.718ms)
  ✔ writes JSON without ascii escaping and creates parent dirs (6.810334ms)
  ✔ preserves existing file mode (12.485292ms)
  ✔ loadJson returns default on missing/corrupt (0.703292ms)
  ✔ loadJsonStrict raises on corrupt/non-object (1.7375ms)
✔ atomic-write (30.8145ms)
中文测试
{
  "name": "中文"
}
err 中文
▶ subprocess.spawn (argv)
  ✔ runs a successful command and captures output (139.174666ms)
  ✔ returns 127 when the binary is missing (20.829084ms)
  ✔ returns a non-zero code on argv usage error (29.438125ms)
✔ subprocess.spawn (argv) (190.814459ms)
▶ subprocess.which / commandExists
  ✔ finds node on PATH (1.747125ms)
  ✔ returns null for a missing command (0.306292ms)
✔ subprocess.which / commandExists (2.243708ms)
▶ subprocess.runShell (shell form)
  ✔ supports pipes and redirects (19.57675ms)
  ✔ supports environment variable expansion (17.830208ms)
  ✔ returns 0 for a true compound command (5.267084ms)
  ✔ surfaces non-zero exit of a failed command (7.83425ms)
✔ subprocess.runShell (shell form) (50.783083ms)
▶ output (UTF-8)
  ✔ print writes a UTF-8 line including Chinese (0.840583ms)
  ✔ printJson renders without ASCII escaping (0.204916ms)
  ✔ printError writes to stderr (0.057708ms)
✔ output (UTF-8) (1.219958ms)
▶ io.yaml
  ✔ parses flat key: value (0.753292ms)
  ✔ strips quoted values (0.057167ms)
  ✔ coerces scalars (0.255083ms)
✔ io.yaml (1.216791ms)
▶ io.markdown
  ✔ parses ATX headings with level and text (0.408042ms)
  ✔ normalizeHeading collapses whitespace (0.084208ms)
  ✔ hasMeaningfulContent rejects blank/placeholder (0.297833ms)
✔ io.markdown (0.907167ms)
已初始化 .project-intel，索引了 4 个文本文件。
{
  "dryRun": true,
  "manifest": {
    "schemaVersion": 2,
    "toolVersion": "0.7.3",
    "projectRoot": ".",
    "generatedAt": "2026-07-27T10:12:52.726Z",
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
    "generatedAt": "2026-07-27T10:12:52.783Z",
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
  ✔ writes the .project-intel layout (manifest/config/knowledge/status) (238.4855ms)
  ✔ --dry-run does not write files (63.045209ms)
  ✔ refresh re-writes without tooling (612.274584ms)
  ✔ strict + no-graph is a usage error (3.977667ms)
  ✔ ensureProjectIntelGitignore writes local-only rules (7.811458ms)
✔ init command (926.481292ms)
▶ doctor command
  ✔ reports node runtime, not python (39.969ms)
  ✔ detects initialized state after init (363.995583ms)
✔ doctor command (404.088375ms)
▶ check command
  ✔ passes with no hard rules configured (347.635958ms)
  ✔ --dry-run does not write status (377.735667ms)
✔ check command (725.566291ms)
▶ standards inference
  ✔ infers PascalCase naming from >=3 pascal components (0.469834ms)
  ✔ infers backend Service suffix from >=2 services (0.097666ms)
  ✔ infers ui-pattern from redundancy candidates (0.104584ms)
  ✔ ports backend API, layering and operational inference categories (0.578542ms)
✔ standards inference (1.538584ms)
▶ project domain candidates
  ✔ aggregates repeated non-generic parent segments in stable order (0.871083ms)
✔ project domain candidates (0.919875ms)
▶ standards documents
  ✔ renders detailed frontend and backend facts instead of count-only placeholders (1.71675ms)
✔ standards documents (1.818958ms)
▶ hard rules engine
  ✔ returns no violations with the empty default set (0.163167ms)
  ✔ surfaces a registered rule violation (0.200167ms)
✔ hard rules engine (0.473333ms)
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ requirement command dispatcher
  ✔ status returns state for a created requirement (58.797584ms)
  ✔ plan writes into the resolved id-title requirement directory (61.608542ms)
  ✔ intake persists document actions and later selection blocks generation (84.070875ms)
  ✔ intake requires a valid user supplied version date (0.841917ms)
  ✔ task-only intake remains a read-only analysis without a version date (3.266333ms)
  ✔ task intake with a version date registers a dated LOCAL requirement (54.120209ms)
  ✔ acceptance set persists AC-01..AC-02 (61.765292ms)
  ✔ query reads v2 and legacy by-id archives and supports --file (77.566ms)
  ✔ test-contract set requires --kind and --report-action (104.657959ms)
  ✔ test-contract register validates and normalizes a structured report path (68.557958ms)
  ✔ ready -> begin through the dispatcher (761.357959ms)
  ✔ reopen after close (58.315875ms)
  ✔ generate enforces lifecycle order and creates a requirement scaffold (86.518458ms)
  ✔ generate refuses implicit overwrite and --replace really rebuilds the scaffold (123.907875ms)
  ✔ rejects missing --requirement-id (3.652958ms)
  ✔ add persists artifact registration into the manifest (495.462333ms)
  ✔ rejects arbitrary delivery-document content (148.290042ms)
  ✔ design registration rejects missing source evidence paths (313.605917ms)
  ✔ design registration ignores symbols that exist only in comments or strings (196.43ms)
  ✔ add registers a structured test report as current requirement evidence (586.937833ms)
  ✔ diagnose records a Bug root cause (ticketKind=bug) (70.651208ms)
  ✔ diagnose rejects missing source evidence paths (47.591667ms)
  ✔ diagnose rejects symbols that only appear in comments or strings (43.43675ms)
  ✔ diagnose rejects non-bug requ
```
