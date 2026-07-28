# LOCAL-20260728-114105 测试报告

- 测试类型：unit
- 阶段：green
- 结果：passed
- 验收标准：AC-01,AC-02,AC-03,AC-04,AC-05,AC-06,AC-07
- 文件范围：README.md, docs/project-intelligence-guide.md, evals/skill-behavior-scenarios.json, plugins/project-intelligence/assets/plugin-intro.html, plugins/project-intelligence/skills/project-debug/SKILL.md, plugins/project-intelligence/skills/project-design/SKILL.md, plugins/project-intelligence/skills/project-finish/SKILL.md, plugins/project-intelligence/skills/project-intake/SKILL.md, plugins/project-intelligence/skills/project-spec/SKILL.md, plugins/project-intelligence/skills/project-test/SKILL.md, scripts/validate-skill-evals.mjs, src/__tests__/cli-contract.test.ts, src/__tests__/install-hooks.test.ts, src/__tests__/requirement-command.test.ts, src/__tests__/state-machine.test.ts, src/__tests__/test-evidence.test.ts, src/__tests__/zcode-compat.test.ts, src/app/dispatcher.ts, src/cli/command-flags.ts, src/commands/agent-rules.ts, src/commands/init.ts, src/commands/requirement.ts, src/commands/test.ts, src/requirements/documents.ts, src/requirements/state-machine.ts

## 执行结果

### npm test

- exitCode: 0
- executedCount: 280

```text
Skill behavior scenario contracts verified: 27 scenarios, 17 skills
▶ maskCommentsAndStrings
  ✔ masks line and block comments and string contents (0.396417ms)
✔ maskCommentsAndStrings (0.864667ms)
▶ scanBackendFile
  ✔ extracts a Spring controller endpoint and methods (.java) (2.925583ms)
  ✔ extracts Python def/class and Flask routes (.py) (3.202834ms)
  ✔ classifies a service by name and extracts transaction signals (1.133041ms)
  ✔ extracts config keys from yaml (1.384958ms)
  ✔ classifies repository files and extracts SQL ops from xml mapper (0.879875ms)
  ✔ extracts permission signals (0.162541ms)
  ✔ extracts error code signals (0.898292ms)
  ✔ requires bound framework imports and keeps Django class views (0.875584ms)
  ✔ labels malformed Python without accepting route facts (0.177791ms)
  ✔ applies configured backend entrypoint rules (0.3345ms)
✔ scanBackendFile (13.135875ms)
▶ BACKEND_SUFFIXES
  ✔ includes java, kt, py, go, ts, js (0.235458ms)
✔ BACKEND_SUFFIXES (0.512125ms)
▶ cli snapshot contract (AC-02)
  ✔ loads a well-formed snapshot (0.502875ms)
  ✔ captured every top-level command's help (0.579041ms)
  ✔ pins the JSON envelope shape on every probe (0.136833ms)
  ✔ the version command exits 0 and prints a semver (0.41275ms)
  ✔ usage errors exit non-zero with a non-ok envelope (0.271834ms)
✔ cli snapshot contract (AC-02) (2.559ms)
▶ live Node CLI contract (AC-02/AC-10)
  ✔ dist/cli.js exists and is runnable (0.351083ms)
  ✔ version command exits 0 and prints a semver (117.256584ms)
  ✔ --version flag exits 0 and prints a semver (96.1605ms)
  ✔ every baseline command's --help is byte-for-byte compatible (1170.884375ms)
  ✔ mandatory document commands no longer advertise later or defer (365.044083ms)
  ✔ lifecycle rejects the removed no-op report-action flag (61.111458ms)
  ✔ top-level --help is byte-for-byte compatible (58.374833ms)
  ✔ top-level --help output contains all baseline commands (61.359708ms)
  ✔ subcommand --help output contains usage line and key flags (186.804917ms)
  ✔ unknown command exits 2 (65.505292ms)
  ✔ unknown flag exits 2 (62.920916ms)
  ✔ version --json produces a valid envelope with version field (58.250542ms)
  ✔ doctor --json produces a valid envelope with runtime=node (65.084416ms)
  ✔ usage error --json produces ok=false envelope (61.804166ms)
✔ live Node CLI contract (AC-02/AC-10) (2431.510583ms)
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
  ✔ prints --version alone (0.761584ms)
  ✔ prints --version envelope in json mode (0.106791ms)
  ✔ runs a registered command (text mode) (0.161958ms)
  ✔ runs a registered command (json mode) with envelope (0.072125ms)
  ✔ rejects unknown command with exit 2 (text) (0.276208ms)
  ✔ rejects unknown command with exit 2 (json envelope) (0.377542ms)
  ✔ surfaces usage errors as exit 2 (0.087291ms)
  ✔ surfaces runtime errors as exit 1 (0.078375ms)
  ✔ rejects missing subcommand (json exit 2) (0.815583ms)
  ✔ subcommand --help is intercepted and exits 0 (text) (0.3765ms)
  ✔ subcommand -h is intercepted and exits 0 (json) (0.175542ms)
  ✔ rejects unknown long flag with exit 2 (text) (0.119334ms)
  ✔ rejects unknown long flag with exit 2 (json envelope) (0.126375ms)
  ✔ accepts known value flag and its value (not mistaken for a flag) (0.08925ms)
  ✔ rejects unknown flag even after a valid value flag (0.1035ms)
✔ dispatch (4.581416ms)
▶ normalizeForCompare
  ✔ masks ISO-8601 timestamps (1.083125ms)
  ✔ masks 40-char git hashes (0.063459ms)
  ✔ masks epoch-second/milli integers (0.049583ms)
  ✔ masks absolute repo roots (POSIX) (0.054833ms)
  ✔ normalizes Windows backslashes and masks sample root (0.053916ms)
  ✔ collapses mtime integers regardless of value (0.066875ms)
  ✔ applies longest-root-first masking so nested roots win (0.058375ms)
✔ normalizeForCompare (2.844ms)
▶ compareJsonOutputs
  ✔ returns null for equal normalized values (0.119166ms)
  ✔ reports the first differing path (0.049084ms)
  ✔ reports missing keys with direction (0.104709ms)
  ✔ reports array length mismatches (0.046709ms)
✔ compareJsonOutputs (0.419417ms)
▶ frontend scanner
  ✔ extracts vue component props/emits (1.612292ms)
  ✔ extracts react props from interface (0.46175ms)
  ✔ extracts hooks by use* filename (0.215375ms)
  ✔ extracts routes and redundancy candidates (0.453ms)
  ✔ extractVueProps from defineProps object form (0.140041ms)
  ✔ extractEmits filters to valid names (0.050417ms)
  ✔ extractApiEndpoints from request/fetch calls (0.168625ms)
✔ frontend scanner (3.69325ms)
▶ files scanner
  ✔ discoverFiles walks and categorizes (1.294416ms)
  ✔ discoverFiles excludes node_modules/.git (0.388125ms)
  ✔ uses stable code-point ordering across operating systems (0.279833ms)
  ✔ categorize and simpleMatch basics (0.118834ms)
✔ files scanner (2.195417ms)
▶ incremental scan cache
  ✔ reuses unchanged frontend facts without reading the file again (0.200625ms)
  ✔ uses nanosecond-compatible file signatures and invalidates changed entries (0.283791ms)
✔ incremental scan cache (0.526833ms)
▶ quality scanner
  ✔ packageFrameworks detects Vue+TypeScript from deps (0.080209ms)
  ✔ detectPackage reads package.json scripts and frameworks (0.39ms)
  ✔ packageManager detects npm/pnpm/yarn by lockfile (0.125042ms)
  ✔ detectQualityCommands: Python project STILL recognizes pytest/ruff/mypy (P1.3) (0.44225ms)
  ✔ detectQualityCommands: JS project infers eslint/tsc from config presence (0.437458ms)
✔ quality scanner (1.52825ms)
FixtureGraph 已安装，开始运行分析："/opt/homebrew/Cellar/node/26.3.0/bin/node" -e "process.stdout.write('graph-ok')"
FixtureGraph 开始执行，超时上限 900 秒。
GitNexus：仓库内 runner 需要显式使用 --allow-repo-runner。
▶ graph command authorization
  ✔ preserves and detects Windows absolute paths on POSIX (2.763875ms)
  ✔ allows repository-contained absolute paths and rejects outside paths (0.21325ms)
  ✔ requires explicit permission for repo runners and environment commands (0.168166ms)
✔ graph command authorization (5.085583ms)
▶ graph setup execution
  ✔ executes an authorized installed analyzer and captures evidence (74.940334ms)
  ✔ records a skipped result instead of executing an unauthorized runner (1.42725ms)
✔ graph setup execution (76.486791ms)
▶ adapter block management
  ✔ rejects paths outside the allowed set (0.669375ms)
  ✔ replaceSingleManagedBlock creates then updates (0.186166ms)
  ✔ upsert then remove a managed block (0.839458ms)
✔ adapter block management (2.235458ms)
▶ adapters command family
  ✔ apply writes codex + claude blocks; status reports current (0.859958ms)
  ✔ preview is dry-run (no files written) (0.137958ms)
  ✔ remove clears blocks (0.380125ms)
  ✔ status --check returns non-zero when not current (0.251875ms)
  ✔ adapterTargets both returns 3 targets (codex, claude, claude-nested) (0.620584ms)
  ✔ managed Codex and Claude rules require four documents and design-derived specs (0.185958ms)
✔ adapters command family (2.591666ms)
▶ top-level install command
  ✔ creates .claude/ and applies adapters; --hooks writes templates (0.838791ms)
✔ top-level install command (0.878708ms)
▶ agent install command
  ✔ agentInstallCommands builds codex+claude for all (0.064042ms)
  ✔ --dry-run classifies present when cli exists, missing otherwise (0.265042ms)
  ✔ rejects invalid target (0.097042ms)
✔ agent install command (0.468208ms)
▶ git hooks (AC-07: no python3)
  ✔ hook body calls project-intel (Node CLI), never python3 (0.044583ms)
  ✔ writeHookTemplates writes 3 hooks + README under .project-intel/hooks (0.464709ms)
✔ git hooks (AC-07: no python3) (0.539917ms)
▶ sanitizeErrorText
  ✔ redacts authorization bearer tokens (0.744667ms)
  ✔ redacts cookies (0.067042ms)
  ✔ redacts password/secret/token/api_key (0.051ms)
  ✔ redacts aws credentials (0.043416ms)
  ✔ redacts URL userinfo (0.03525ms)
  ✔ leaves benign text intact (0.343333ms)
✔ sanitizeErrorText (2.747958ms)
▶ extractGlobalJson
  ✔ strips --json and reports mode (2.531708ms)
  ✔ preserves argv when --json absent (0.29575ms)
✔ extractGlobalJson (3.01525ms)
▶ jsonEnvelope
  ✔ shapes a success envelope (0.130916ms)
  ✔ classifies exit 2 as USAGE_ERROR with sanitized in-place error (0.074541ms)
  ✔ classifies non-2 failure as COMMAND_FAILED with default message (0.045125ms)
  ✔ trims the output field (0.030083ms)
✔ jsonEnvelope (0.379417ms)
▶ parseGlobal / splitArgv
  ✔ parses --project value (0.093125ms)
  ✔ parses --project= form (0.036625ms)
  ✔ parses --json (0.035ms)
  ✔ rejects unknown long option before subcommand with exit-2 UsageError (0.06925ms)
  ✔ splitArgv separates global, command, and rest (0.069542ms)
  ✔ splitArgv returns null when no subcommand (0.027666ms)
✔ parseGlobal / splitArgv (0.389542ms)
▶ withLock (in-process)
  ✔ blocks same-process re-entrant acquire (no deadlock) (63.298333ms)
  ✔ releases the lockfile after the critical section (1.060666ms)
✔ withLock (in-process) (65.222375ms)
▶ withLock (multi-process contention)
  ✔ grants exclusive access across child processes (812.828291ms)
✔ withLock (multi-process contention) (812.905167ms)
▶ paths
  ✔ toPosix converts separators (0.374834ms)
  ✔ normalizeBusinessPath strips leading ./ and normalizes (0.058125ms)
  ✔ isAbsolutePathLike detects posix, windows drive, unc (0.059792ms)
  ✔ resolveInside rejects traversal outside root (1.78475ms)
  ✔ expandUser leaves non-home paths alone (0.136042ms)
✔ paths (3.460666ms)
▶ atomic-write
  ✔ writes text with a trailing newline, UTF-8 preserved (4.861292ms)
  ✔ writes JSON without ascii escaping and creates parent dirs (6.697542ms)
  ✔ preserves existing file mode (9.096041ms)
  ✔ loadJson returns default on missing/corrupt (0.621ms)
  ✔ loadJsonStrict raises on corrupt/non-object (1.026375ms)
✔ atomic-write (22.727584ms)
中文测试
{
  "name": "中文"
}
err 中文
▶ subprocess.spawn (argv)
  ✔ runs a successful command and captures output (55.037208ms)
  ✔ returns 127 when the binary is missing (11.667584ms)
  ✔ returns a non-zero code on argv usage error (18.782709ms)
✔ subprocess.spawn (argv) (86.320625ms)
▶ subprocess.which / commandExists
  ✔ finds node on PATH (0.743708ms)
  ✔ returns null for a missing command (1.885042ms)
✔ subprocess.which / commandExists (2.783583ms)
▶ subprocess.runShell (shell form)
  ✔ supports pipes and redirects (7.960292ms)
  ✔ supports environment variable expansion (9.847542ms)
  ✔ returns 0 for a true compound command (4.110666ms)
  ✔ surfaces non-zero exit of a failed command (4.71975ms)
✔ subprocess.runShell (shell form) (26.877167ms)
▶ output (UTF-8)
  ✔ print writes a UTF-8 line including Chinese (1.03625ms)
  ✔ printJson renders without ASCII escaping (0.096833ms)
  ✔ printError writes to stderr (0.046292ms)
✔ output (UTF-8) (1.275083ms)
▶ io.yaml
  ✔ parses flat key: value (0.690833ms)
  ✔ strips quoted values (0.044375ms)
  ✔ coerces scalars (0.08625ms)
✔ io.yaml (0.865208ms)
▶ io.markdown
  ✔ parses ATX headings with level and text (0.101625ms)
  ✔ normalizeHeading collapses whitespace (0.022791ms)
  ✔ hasMeaningfulContent rejects blank/placeholder (0.092708ms)
✔ io.markdown (0.247ms)
已初始化 .project-intel，索引了 4 个文本文件。
{
  "dryRun": true,
  "manifest": {
    "schemaVersion": 2,
    "toolVersion": "0.7.4",
    "projectRoot": ".",
    "generatedAt": "2026-07-28T04:07:21.612Z",
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
    "generatedAt": "2026-07-28T04:07:21.643Z",
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
  ✔ writes the .project-intel layout (manifest/config/knowledge/status) (209.806708ms)
  ✔ --dry-run does not write files (34.754541ms)
  ✔ refresh re-writes without tooling (532.739042ms)
  ✔ strict + no-graph is a usage error (3.812ms)
  ✔ ensureProjectIntelGitignore writes local-only rules (4.012167ms)
✔ init command (786.628917ms)
▶ doctor command
  ✔ reports node runtime, not python (28.52225ms)
  ✔ detects initialized state after init (363.45575ms)
✔ doctor command (392.085708ms)
▶ check command
  ✔ passes with no hard rules configured (347.945292ms)
  ✔ --dry-run does not write status (350.847458ms)
✔ check command (698.900625ms)
▶ standards inference
  ✔ infers PascalCase naming from >=3 pascal components (0.303166ms)
  ✔ infers backend Service suffix from >=2 services (0.077584ms)
  ✔ infers ui-pattern from redundancy candidates (0.041875ms)
  ✔ ports backend API, layering and operational inference categories (0.116417ms)
✔ standards inference (0.611042ms)
▶ project domain candidates
  ✔ aggregates repeated non-generic parent segments in stable order (0.729042ms)
✔ project domain candidates (0.768334ms)
▶ standards documents
  ✔ renders detailed frontend and backend facts instead of count-only placeholders (0.896959ms)
✔ standards documents (0.938084ms)
▶ hard rules engine
  ✔ returns no violations with the empty default set (0.12725ms)
  ✔ surfaces a registered rule violation (0.972292ms)
✔ hard rules engine (1.190292ms)
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ requirement command dispatcher
  ✔ status returns state for a created requirement (44.4665ms)
  ✔ plan writes into the resolved id-title requirement directory (47.126208ms)
  ✔ intake defaults both mandatory document actions to generate (32.245458ms)
  ✔ intake uses a supplied design as the source while generating the missing spec (45.265541ms)
  ✔ intake rejects later for mandatory lifecycle documents (3.139041ms)
  ✔ intake requires a valid user supplied version date (0.691542ms)
  ✔ task-only intake remains a read-only analysis without a version date (2.989167ms)
  ✔ task intake with a version date registers a dated LOCAL requirement (40.091458ms)
  ✔ acceptance set persists AC-01..AC-02 (44.29825ms)
  ✔ query reads v2 and legacy by-id archives and supports --file (68.592375ms)
  ✔ status remains readable for a legacy manifest without workflow selections (9.479833ms)
  ✔ test-contract set requires --kind and --report-action (89.1985ms)
  ✔ test-contract register validates and normalizes a structured report path (74.53125ms)
  ✔ ready -> begin through the dispatcher (683.101291ms)
  ✔ reopen after close (60.558333ms)
  ✔ generate enforces lifecycle order and creates a requirement scaffold (70.387042ms)
  ✔ generate refuses implicit overwrite and --replace really rebuilds the scaffold (122.683042ms)
  ✔ rejects missing --requirement-id (2.959209ms)
  ✔ add persists artifact registration into the manifest (418.113291ms)
  ✔ rejects arbitrary delivery-document content (120.303084ms)
  ✔ d
```
