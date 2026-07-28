# LOCAL-20260728-114105 测试报告

- 测试类型：unit
- 阶段：green
- 结果：passed
- 验收标准：AC-01,AC-02,AC-03,AC-04,AC-05,AC-06,AC-07
- 文件范围：README.md, docs/project-intelligence-guide.md, evals/skill-behavior-scenarios.json, plugins/project-intelligence/assets/plugin-intro.html, plugins/project-intelligence/skills/project-debug/SKILL.md, plugins/project-intelligence/skills/project-design/SKILL.md, plugins/project-intelligence/skills/project-finish/SKILL.md, plugins/project-intelligence/skills/project-intake/SKILL.md, plugins/project-intelligence/skills/project-spec/SKILL.md, plugins/project-intelligence/skills/project-test/SKILL.md, scripts/validate-skill-evals.mjs, src/__tests__/cli-contract.test.ts, src/__tests__/install-hooks.test.ts, src/__tests__/requirement-command.test.ts, src/__tests__/state-machine.test.ts, src/__tests__/test-evidence.test.ts, src/__tests__/zcode-compat.test.ts, src/app/dispatcher.ts, src/cli/command-flags.ts, src/commands/agent-rules.ts, src/commands/init.ts, src/commands/requirement.ts, src/commands/test.ts, src/requirements/documents.ts, src/requirements/state-machine.ts

## 执行结果

### npm test

- exitCode: 0
- executedCount: 282

```text
Skill behavior scenario contracts verified: 27 scenarios, 17 skills
▶ maskCommentsAndStrings
  ✔ masks line and block comments and string contents (0.880042ms)
✔ maskCommentsAndStrings (3.241792ms)
▶ scanBackendFile
  ✔ extracts a Spring controller endpoint and methods (.java) (5.845958ms)
  ✔ extracts Python def/class and Flask routes (.py) (3.467792ms)
  ✔ classifies a service by name and extracts transaction signals (0.348708ms)
  ✔ extracts config keys from yaml (0.286ms)
  ✔ classifies repository files and extracts SQL ops from xml mapper (1.068375ms)
  ✔ extracts permission signals (0.27525ms)
  ✔ extracts error code signals (0.177709ms)
  ✔ requires bound framework imports and keeps Django class views (0.411041ms)
  ✔ labels malformed Python without accepting route facts (0.222417ms)
  ✔ applies configured backend entrypoint rules (0.248417ms)
✔ scanBackendFile (13.061666ms)
▶ BACKEND_SUFFIXES
  ✔ includes java, kt, py, go, ts, js (0.063292ms)
✔ BACKEND_SUFFIXES (0.107125ms)
▶ cli snapshot contract (AC-02)
  ✔ loads a well-formed snapshot (1.242334ms)
  ✔ captured every top-level command's help (1.888084ms)
  ✔ pins the JSON envelope shape on every probe (0.3445ms)
  ✔ the version command exits 0 and prints a semver (0.359ms)
  ✔ usage errors exit non-zero with a non-ok envelope (0.516167ms)
✔ cli snapshot contract (AC-02) (7.123833ms)
▶ live Node CLI contract (AC-02/AC-10)
  ✔ dist/cli.js exists and is runnable (0.790625ms)
  ✔ version command exits 0 and prints a semver (148.996667ms)
  ✔ --version flag exits 0 and prints a semver (133.999708ms)
  ✔ every baseline command's --help is byte-for-byte compatible (1492.169583ms)
  ✔ mandatory document commands no longer advertise later or defer (406.586541ms)
  ✔ lifecycle rejects the removed no-op report-action flag (66.457958ms)
  ✔ top-level --help is byte-for-byte compatible (71.076125ms)
  ✔ top-level --help output contains all baseline commands (71.381833ms)
  ✔ subcommand --help output contains usage line and key flags (233.315333ms)
  ✔ unknown command exits 2 (66.78075ms)
  ✔ unknown flag exits 2 (69.699541ms)
  ✔ version --json produces a valid envelope with version field (72.251333ms)
  ✔ doctor --json produces a valid envelope with runtime=node (74.549375ms)
  ✔ usage error --json produces ok=false envelope (67.691666ms)
✔ live Node CLI contract (AC-02/AC-10) (2976.517625ms)
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
无法识别的命令：nope

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
  ✔ prints --version alone (2.542167ms)
  ✔ prints --version envelope in json mode (0.24825ms)
  ✔ runs a registered command (text mode) (0.371125ms)
  ✔ runs a registered command (json mode) with envelope (1.155042ms)
  ✔ rejects unknown command with exit 2 (text) (0.660084ms)
  ✔ rejects unknown command with exit 2 (json envelope) (0.474333ms)
  ✔ surfaces usage errors as exit 2 (1.9555ms)
  ✔ surfaces runtime errors as exit 1 (0.371041ms)
  ✔ rejects missing subcommand (json exit 2) (1.291041ms)
  ✔ subcommand --help is intercepted and exits 0 (text) (0.319834ms)
  ✔ subcommand -h is intercepted and exits 0 (json) (0.15825ms)
  ✔ rejects unknown long flag with exit 2 (text) (0.099ms)
  ✔ rejects unknown long flag with exit 2 (json envelope) (0.133125ms)
  ✔ accepts known value flag and its value (not mistaken for a flag) (0.101583ms)
  ✔ rejects unknown flag even after a valid value flag (0.090167ms)
✔ dispatch (12.351334ms)
▶ normalizeForCompare
  ✔ masks ISO-8601 timestamps (2.70625ms)
  ✔ masks 40-char git hashes (0.102125ms)
  ✔ masks epoch-second/milli integers (0.057917ms)
  ✔ masks absolute repo roots (POSIX) (0.37025ms)
  ✔ normalizes Windows backslashes and masks sample root (0.141ms)
  ✔ collapses mtime integers regardless of value (0.102584ms)
  ✔ applies longest-root-first masking so nested roots win (0.082583ms)
✔ normalizeForCompare (4.418042ms)
▶ compareJsonOutputs
  ✔ returns null for equal normalized values (0.138ms)
  ✔ reports the first differing path (0.056375ms)
  ✔ reports missing keys with direction (0.274833ms)
  ✔ reports array length mismatches (0.150209ms)
✔ compareJsonOutputs (0.80175ms)
▶ frontend scanner
  ✔ extracts vue component props/emits (3.949042ms)
  ✔ extracts react props from interface (1.171042ms)
  ✔ extracts hooks by use* filename (0.464875ms)
  ✔ extracts routes and redundancy candidates (0.691333ms)
  ✔ extractVueProps from defineProps object form (0.169584ms)
  ✔ extractEmits filters to valid names (0.067584ms)
  ✔ extractApiEndpoints from request/fetch calls (0.467542ms)
✔ frontend scanner (8.684875ms)
▶ files scanner
  ✔ discoverFiles walks and categorizes (1.409417ms)
  ✔ discoverFiles excludes node_modules/.git (0.718209ms)
  ✔ uses stable code-point ordering across operating systems (1.703ms)
  ✔ categorize and simpleMatch basics (0.329375ms)
✔ files scanner (4.420333ms)
▶ incremental scan cache
  ✔ reuses unchanged frontend facts without reading the file again (0.534541ms)
  ✔ uses nanosecond-compatible file signatures and invalidates changed entries (0.821917ms)
✔ incremental scan cache (1.481792ms)
▶ quality scanner
  ✔ packageFrameworks detects Vue+TypeScript from deps (0.18025ms)
  ✔ detectPackage reads package.json scripts and frameworks (0.928875ms)
  ✔ packageManager detects npm/pnpm/yarn by lockfile (0.361625ms)
  ✔ detectQualityCommands: Python project STILL recognizes pytest/ruff/mypy (P1.3) (0.74325ms)
  ✔ detectQualityCommands: JS project infers eslint/tsc from config presence (0.737542ms)
✔ quality scanner (3.06875ms)
FixtureGraph 已安装，开始运行分析："/opt/homebrew/Cellar/node/26.3.0/bin/node" -e "process.stdout.write('graph-ok')"
FixtureGraph 开始执行，超时上限 900 秒。
GitNexus：仓库内 runner 需要显式使用 --allow-repo-runner。
▶ graph command authorization
  ✔ preserves and detects Windows absolute paths on POSIX (5.771667ms)
  ✔ allows repository-contained absolute paths and rejects outside paths (0.336042ms)
  ✔ requires explicit permission for repo runners and environment commands (0.168459ms)
✔ graph command authorization (7.7485ms)
▶ graph setup execution
  ✔ executes an authorized installed analyzer and captures evidence (117.272292ms)
  ✔ records a skipped result instead of executing an unauthorized runner (0.607125ms)
✔ graph setup execution (118.019458ms)
▶ adapter block management
  ✔ rejects paths outside the allowed set (1.183292ms)
  ✔ replaceSingleManagedBlock creates then updates (0.416792ms)
  ✔ upsert then remove a managed block (0.792ms)
✔ adapter block management (3.648917ms)
▶ adapters command family
  ✔ apply writes codex + claude blocks; status reports current (2.234459ms)
  ✔ preview is dry-run (no files written) (0.431416ms)
  ✔ remove clears blocks (1.864375ms)
  ✔ status --check returns non-zero when not current (1.054083ms)
  ✔ adapterTargets both returns 3 targets (codex, claude, claude-nested) (0.838709ms)
  ✔ managed Codex and Claude rules require four documents and design-derived specs (0.837584ms)
✔ adapters command family (10.847375ms)
▶ top-level install command
  ✔ creates .claude/ and applies adapters; --hooks writes templates (2.619167ms)
✔ top-level install command (2.694708ms)
▶ agent install command
  ✔ agentInstallCommands builds codex+claude for all (0.194625ms)
  ✔ --dry-run classifies present when cli exists, missing otherwise (0.71575ms)
  ✔ rejects invalid target (0.258458ms)
✔ agent install command (1.362667ms)
▶ git hooks (AC-07: no python3)
  ✔ hook body calls project-intel (Node CLI), never python3 (0.088ms)
  ✔ writeHookTemplates writes 3 hooks + README under .project-intel/hooks (1.827958ms)
✔ git hooks (AC-07: no python3) (1.99ms)
▶ sanitizeErrorText
  ✔ redacts authorization bearer tokens (1.744209ms)
  ✔ redacts cookies (0.139459ms)
  ✔ redacts password/secret/token/api_key (0.206833ms)
  ✔ redacts aws credentials (0.114625ms)
  ✔ redacts URL userinfo (0.828625ms)
  ✔ leaves benign text intact (0.647875ms)
✔ sanitizeErrorText (8.035959ms)
▶ extractGlobalJson
  ✔ strips --json and reports mode (1.352166ms)
  ✔ preserves argv when --json absent (0.421083ms)
✔ extractGlobalJson (2.013334ms)
▶ jsonEnvelope
  ✔ shapes a success envelope (0.152417ms)
  ✔ classifies exit 2 as USAGE_ERROR with sanitized in-place error (0.084583ms)
  ✔ classifies non-2 failure as COMMAND_FAILED with default message (0.059667ms)
  ✔ trims the output field (0.038916ms)
✔ jsonEnvelope (0.433917ms)
▶ parseGlobal / splitArgv
  ✔ parses --project value (0.098875ms)
  ✔ parses --project= form (0.030833ms)
  ✔ parses --json (0.024625ms)
  ✔ rejects unknown long option before subcommand with exit-2 UsageError (0.071292ms)
  ✔ splitArgv separates global, command, and rest (0.065ms)
  ✔ splitArgv returns null when no subcommand (0.02375ms)
✔ parseGlobal / splitArgv (0.367209ms)
▶ withLock (in-process)
  ✔ blocks same-process re-entrant acquire (no deadlock) (62.992792ms)
  ✔ releases the lockfile after the critical section (0.59825ms)
✔ withLock (in-process) (65.947458ms)
▶ withLock (multi-process contention)
  ✔ grants exclusive access across child processes (1099.102167ms)
✔ withLock (multi-process contention) (1099.181541ms)
▶ paths
  ✔ toPosix converts separators (1.20175ms)
  ✔ normalizeBusinessPath strips leading ./ and normalizes (0.156833ms)
  ✔ isAbsolutePathLike detects posix, windows drive, unc (2.572042ms)
  ✔ resolveInside rejects traversal outside root (2.145042ms)
  ✔ expandUser leaves non-home paths alone (0.14425ms)
✔ paths (7.98775ms)
▶ atomic-write
  ✔ writes text with a trailing newline, UTF-8 preserved (13.961875ms)
  ✔ writes JSON without ascii escaping and creates parent dirs (6.995042ms)
  ✔ preserves existing file mode (12.228917ms)
  ✔ loadJson returns default on missing/corrupt (1.4215ms)
  ✔ loadJsonStrict raises on corrupt/non-object (0.786834ms)
✔ atomic-write (35.801542ms)
中文测试
{
  "name": "中文"
}
err 中文
▶ subprocess.spawn (argv)
  ✔ runs a successful command and captures output (97.276125ms)
  ✔ returns 127 when the binary is missing (7.299792ms)
  ✔ returns a non-zero code on argv usage error (33.53925ms)
✔ subprocess.spawn (argv) (139.253542ms)
▶ subprocess.which / commandExists
  ✔ finds node on PATH (0.583917ms)
  ✔ returns null for a missing command (1.324291ms)
✔ subprocess.which / commandExists (2.057292ms)
▶ subprocess.runShell (shell form)
  ✔ supports pipes and redirects (12.97425ms)
  ✔ supports environment variable expansion (13.441042ms)
  ✔ returns 0 for a true compound command (5.430375ms)
  ✔ surfaces non-zero exit of a failed command (4.979625ms)
✔ subprocess.runShell (shell form) (37.102ms)
▶ output (UTF-8)
  ✔ print writes a UTF-8 line including Chinese (0.728916ms)
  ✔ printJson renders without ASCII escaping (0.18925ms)
  ✔ printError writes to stderr (0.099625ms)
✔ output (UTF-8) (1.161125ms)
▶ io.yaml
  ✔ parses flat key: value (1.180208ms)
  ✔ strips quoted values (0.084083ms)
  ✔ coerces scalars (0.0975ms)
✔ io.yaml (1.561458ms)
▶ io.markdown
  ✔ parses ATX headings with level and text (0.114333ms)
  ✔ normalizeHeading collapses whitespace (0.073292ms)
  ✔ hasMeaningfulContent rejects blank/placeholder (0.350459ms)
✔ io.markdown (0.608042ms)
已初始化 .project-intel，索引了 4 个文本文件。
{
  "dryRun": true,
  "manifest": {
    "schemaVersion": 2,
    "toolVersion": "0.7.4",
    "projectRoot": ".",
    "generatedAt": "2026-07-28T04:15:24.207Z",
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
    "generatedAt": "2026-07-28T04:15:24.289Z",
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
  ✔ writes the .project-intel layout (manifest/config/knowledge/status) (246.05225ms)
  ✔ --dry-run does not write files (90.658917ms)
  ✔ refresh re-writes without tooling (689.737833ms)
  ✔ strict + no-graph is a usage error (3.575375ms)
  ✔ ensureProjectIntelGitignore writes local-only rules (4.343458ms)
✔ init command (1036.19175ms)
▶ doctor command
  ✔ reports node runtime, not python (15.793333ms)
  ✔ detects initialized state after init (342.07825ms)
✔ doctor command (358.056666ms)
▶ check command
  ✔ passes with no hard rules configured (360.465125ms)
  ✔ --dry-run does not write status (384.379083ms)
✔ check command (745.0085ms)
▶ standards inference
  ✔ infers PascalCase naming from >=3 pascal components (0.29175ms)
  ✔ infers backend Service suffix from >=2 services (0.083958ms)
  ✔ infers ui-pattern from redundancy candidates (0.046042ms)
  ✔ ports backend API, layering and operational inference categories (0.119167ms)
✔ standards inference (0.617458ms)
▶ project domain candidates
  ✔ aggregates repeated non-generic parent segments in stable order (0.63525ms)
✔ project domain candidates (0.664125ms)
▶ standards documents
  ✔ renders detailed frontend and backend facts instead of count-only placeholders (0.703334ms)
✔ standards documents (0.7245ms)
▶ hard rules engine
  ✔ returns no violations with the empty default set (0.039791ms)
  ✔ surfaces a registered rule violation (0.051834ms)
✔ hard rules engine (0.115667ms)
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ requirement command dispatcher
  ✔ status returns state for a created requirement (72.802ms)
  ✔ plan writes into the resolved id-title requirement directory (66.201291ms)
  ✔ intake defaults both mandatory document actions to generate (50.94725ms)
  ✔ intake uses a supplied design as the source while generating the missing spec (65.038708ms)
  ✔ intake rejects later for mandatory lifecycle documents (0.397792ms)
  ✔ intake requires a valid user supplied version date (0.162584ms)
  ✔ task-only intake remains a read-only analysis without a version date (0.100916ms)
  ✔ task intake with a version date registers a dated LOCAL requirement (55.022458ms)
  ✔ acceptance set persists AC-01..AC-02 (84.749125ms)
  ✔ query reads v2 and legacy by-id archives and supports --file (98.261542ms)
  ✔ status remains readable for a legacy manifest without workflow selections (12.959709ms)
  ✔ test-contract set requires --kind and --report-action (78.885292ms)
  ✔ test-contract register validates and normalizes a structured report path (57.488292ms)
  ✔ ready -> begin through the dispatcher (795.312542ms)
  ✔ reopen after close (87.805583ms)
  ✔ generate enforces lifecycle order and creates a requirement scaffold (103.17075ms)
  ✔ generate refuses implicit overwrite and --replace really rebuilds the scaffold (138.891083ms)
  ✔ rejects missing --requirement-id (3.563167ms)
  ✔ add persists artifact registration into the manifest (379.507084ms)
  ✔ rejects arbitrary delivery-document content (172.849459ms)
  ✔ des
```
