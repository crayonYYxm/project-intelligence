# LOCAL-20260728-114105 测试报告

- 测试类型：unit
- 阶段：green
- 结果：passed
- 验收标准：AC-01,AC-02,AC-03,AC-04,AC-05,AC-06,AC-07
- 文件范围：README.md, docs/project-intelligence-guide.md, evals/skill-behavior-scenarios.json, plugins/project-intelligence/assets/plugin-intro.html, plugins/project-intelligence/skills/project-debug/SKILL.md, plugins/project-intelligence/skills/project-design/SKILL.md, plugins/project-intelligence/skills/project-finish/SKILL.md, plugins/project-intelligence/skills/project-intake/SKILL.md, plugins/project-intelligence/skills/project-spec/SKILL.md, plugins/project-intelligence/skills/project-test/SKILL.md, scripts/validate-skill-evals.mjs, src/__tests__/cli-contract.test.ts, src/__tests__/install-hooks.test.ts, src/__tests__/requirement-command.test.ts, src/__tests__/review-finish-graph.test.ts, src/__tests__/state-machine.test.ts, src/__tests__/test-evidence.test.ts, src/__tests__/zcode-compat.test.ts, src/app/dispatcher.ts, src/cli/command-flags.ts, src/commands/agent-rules.ts, src/commands/init.ts, src/commands/requirement.ts, src/commands/test.ts, src/requirements/documents.ts, src/requirements/state-machine.ts

## 执行结果

### npm test

- exitCode: 0
- executedCount: 282

```text
Skill behavior scenario contracts verified: 27 scenarios, 17 skills
▶ maskCommentsAndStrings
  ✔ masks line and block comments and string contents (0.919667ms)
✔ maskCommentsAndStrings (2.237833ms)
▶ scanBackendFile
  ✔ extracts a Spring controller endpoint and methods (.java) (3.905ms)
  ✔ extracts Python def/class and Flask routes (.py) (3.571208ms)
  ✔ classifies a service by name and extracts transaction signals (1.057042ms)
  ✔ extracts config keys from yaml (0.528833ms)
  ✔ classifies repository files and extracts SQL ops from xml mapper (0.381292ms)
  ✔ extracts permission signals (3.244167ms)
  ✔ extracts error code signals (0.160458ms)
  ✔ requires bound framework imports and keeps Django class views (0.179875ms)
  ✔ labels malformed Python without accepting route facts (0.219458ms)
  ✔ applies configured backend entrypoint rules (0.528667ms)
✔ scanBackendFile (14.26775ms)
▶ BACKEND_SUFFIXES
  ✔ includes java, kt, py, go, ts, js (0.066417ms)
✔ BACKEND_SUFFIXES (0.110834ms)
▶ cli snapshot contract (AC-02)
  ✔ loads a well-formed snapshot (2.154125ms)
  ✔ captured every top-level command's help (1.632333ms)
  ✔ pins the JSON envelope shape on every probe (0.559292ms)
  ✔ the version command exits 0 and prints a semver (0.18525ms)
  ✔ usage errors exit non-zero with a non-ok envelope (0.118125ms)
✔ cli snapshot contract (AC-02) (6.34575ms)
▶ live Node CLI contract (AC-02/AC-10)
  ✔ dist/cli.js exists and is runnable (0.52725ms)
  ✔ version command exits 0 and prints a semver (179.3075ms)
  ✔ --version flag exits 0 and prints a semver (154.789833ms)
  ✔ every baseline command's --help is byte-for-byte compatible (1496.069125ms)
  ✔ mandatory document commands no longer advertise later or defer (448.623959ms)
  ✔ lifecycle rejects the removed no-op report-action flag (79.208791ms)
  ✔ top-level --help is byte-for-byte compatible (70.372125ms)
  ✔ top-level --help output contains all baseline commands (80.273459ms)
  ✔ subcommand --help output contains usage line and key flags (217.3795ms)
  ✔ unknown command exits 2 (65.76175ms)
  ✔ unknown flag exits 2 (65.823417ms)
  ✔ version --json produces a valid envelope with version field (76.446875ms)
  ✔ doctor --json produces a valid envelope with runtime=node (79.652959ms)
  ✔ usage error --json produces ok=false envelope (80.174041ms)
✔ live Node CLI contract (AC-02/AC-10) (3095.17925ms)
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
  ✔ prints --version alone (1.547666ms)
  ✔ prints --version envelope in json mode (0.26475ms)
  ✔ runs a registered command (text mode) (0.39075ms)
  ✔ runs a registered command (json mode) with envelope (0.162416ms)
  ✔ rejects unknown command with exit 2 (text) (0.950375ms)
  ✔ rejects unknown command with exit 2 (json envelope) (0.869875ms)
  ✔ surfaces usage errors as exit 2 (0.141167ms)
  ✔ surfaces runtime errors as exit 1 (0.832ms)
  ✔ rejects missing subcommand (json exit 2) (0.180541ms)
  ✔ subcommand --help is intercepted and exits 0 (text) (1.556042ms)
  ✔ subcommand -h is intercepted and exits 0 (json) (0.271875ms)
  ✔ rejects unknown long flag with exit 2 (text) (0.196875ms)
  ✔ rejects unknown long flag with exit 2 (json envelope) (0.197ms)
  ✔ accepts known value flag and its value (not mistaken for a flag) (0.067333ms)
  ✔ rejects unknown flag even after a valid value flag (0.057666ms)
✔ dispatch (9.930209ms)
▶ normalizeForCompare
  ✔ masks ISO-8601 timestamps (2.253ms)
  ✔ masks 40-char git hashes (0.292958ms)
  ✔ masks epoch-second/milli integers (0.145041ms)
  ✔ masks absolute repo roots (POSIX) (1.014708ms)
  ✔ normalizes Windows backslashes and masks sample root (0.08275ms)
  ✔ collapses mtime integers regardless of value (0.0825ms)
  ✔ applies longest-root-first masking so nested roots win (0.220958ms)
✔ normalizeForCompare (5.413333ms)
▶ compareJsonOutputs
  ✔ returns null for equal normalized values (0.133458ms)
  ✔ reports the first differing path (0.052625ms)
  ✔ reports missing keys with direction (0.0975ms)
  ✔ reports array length mismatches (0.048833ms)
✔ compareJsonOutputs (0.443042ms)
▶ frontend scanner
  ✔ extracts vue component props/emits (4.245958ms)
  ✔ extracts react props from interface (1.14875ms)
  ✔ extracts hooks by use* filename (0.926084ms)
  ✔ extracts routes and redundancy candidates (1.563292ms)
  ✔ extractVueProps from defineProps object form (1.290084ms)
  ✔ extractEmits filters to valid names (0.100208ms)
  ✔ extractApiEndpoints from request/fetch calls (0.440916ms)
✔ frontend scanner (11.236292ms)
▶ files scanner
  ✔ discoverFiles walks and categorizes (5.120208ms)
  ✔ discoverFiles excludes node_modules/.git (2.14325ms)
  ✔ uses stable code-point ordering across operating systems (2.009459ms)
  ✔ categorize and simpleMatch basics (2.50525ms)
✔ files scanner (12.040458ms)
▶ incremental scan cache
  ✔ reuses unchanged frontend facts without reading the file again (0.567542ms)
  ✔ uses nanosecond-compatible file signatures and invalidates changed entries (1.628791ms)
✔ incremental scan cache (2.304959ms)
▶ quality scanner
  ✔ packageFrameworks detects Vue+TypeScript from deps (0.227417ms)
  ✔ detectPackage reads package.json scripts and frameworks (1.535375ms)
  ✔ packageManager detects npm/pnpm/yarn by lockfile (0.672417ms)
  ✔ detectQualityCommands: Python project STILL recognizes pytest/ruff/mypy (P1.3) (0.761ms)
  ✔ detectQualityCommands: JS project infers eslint/tsc from config presence (2.093208ms)
✔ quality scanner (5.56675ms)
FixtureGraph 已安装，开始运行分析："/opt/homebrew/Cellar/node/26.3.0/bin/node" -e "process.stdout.write('graph-ok')"
FixtureGraph 开始执行，超时上限 900 秒。
GitNexus：仓库内 runner 需要显式使用 --allow-repo-runner。
▶ graph command authorization
  ✔ preserves and detects Windows absolute paths on POSIX (3.892709ms)
  ✔ allows repository-contained absolute paths and rejects outside paths (0.860667ms)
  ✔ requires explicit permission for repo runners and environment commands (0.423292ms)
✔ graph command authorization (6.074375ms)
▶ graph setup execution
  ✔ executes an authorized installed analyzer and captures evidence (127.192208ms)
  ✔ records a skipped result instead of executing an unauthorized runner (0.590584ms)
✔ graph setup execution (127.946291ms)
▶ adapter block management
  ✔ rejects paths outside the allowed set (1.448291ms)
  ✔ replaceSingleManagedBlock creates then updates (0.236041ms)
  ✔ upsert then remove a managed block (1.899875ms)
✔ adapter block management (4.555584ms)
▶ adapters command family
  ✔ apply writes codex + claude blocks; status reports current (3.440167ms)
  ✔ preview is dry-run (no files written) (0.470875ms)
  ✔ remove clears blocks (1.394ms)
  ✔ status --check returns non-zero when not current (1.704667ms)
  ✔ adapterTargets both returns 3 targets (codex, claude, claude-nested) (1.649834ms)
  ✔ managed Codex and Claude rules require four documents and design-derived specs (0.783167ms)
✔ adapters command family (10.173ms)
▶ top-level install command
  ✔ creates .claude/ and applies adapters; --hooks writes templates (2.816417ms)
✔ top-level install command (2.9355ms)
▶ agent install command
  ✔ agentInstallCommands builds codex+claude for all (0.155083ms)
  ✔ --dry-run classifies present when cli exists, missing otherwise (2.0735ms)
  ✔ rejects invalid target (0.468292ms)
✔ agent install command (2.821291ms)
▶ git hooks (AC-07: no python3)
  ✔ hook body calls project-intel (Node CLI), never python3 (0.078541ms)
  ✔ writeHookTemplates writes 3 hooks + README under .project-intel/hooks (1.583292ms)
✔ git hooks (AC-07: no python3) (1.756875ms)
▶ sanitizeErrorText
  ✔ redacts authorization bearer tokens (2.159917ms)
  ✔ redacts cookies (0.21975ms)
  ✔ redacts password/secret/token/api_key (1.036792ms)
  ✔ redacts aws credentials (0.112208ms)
  ✔ redacts URL userinfo (0.169625ms)
  ✔ leaves benign text intact (1.415416ms)
✔ sanitizeErrorText (7.502167ms)
▶ extractGlobalJson
  ✔ strips --json and reports mode (2.234584ms)
  ✔ preserves argv when --json absent (0.284333ms)
✔ extractGlobalJson (2.6505ms)
▶ jsonEnvelope
  ✔ shapes a success envelope (0.128584ms)
  ✔ classifies exit 2 as USAGE_ERROR with sanitized in-place error (0.10425ms)
  ✔ classifies non-2 failure as COMMAND_FAILED with default message (0.113708ms)
  ✔ trims the output field (0.036625ms)
✔ jsonEnvelope (0.470584ms)
▶ parseGlobal / splitArgv
  ✔ parses --project value (0.13925ms)
  ✔ parses --project= form (0.047917ms)
  ✔ parses --json (0.137333ms)
  ✔ rejects unknown long option before subcommand with exit-2 UsageError (0.83925ms)
  ✔ splitArgv separates global, command, and rest (0.122625ms)
  ✔ splitArgv returns null when no subcommand (0.033708ms)
✔ parseGlobal / splitArgv (1.506ms)
▶ withLock (in-process)
  ✔ blocks same-process re-entrant acquire (no deadlock) (65.509875ms)
  ✔ releases the lockfile after the critical section (1.11475ms)
✔ withLock (in-process) (67.366083ms)
▶ withLock (multi-process contention)
  ✔ grants exclusive access across child processes (1092.158958ms)
✔ withLock (multi-process contention) (1092.302084ms)
▶ paths
  ✔ toPosix converts separators (0.732958ms)
  ✔ normalizeBusinessPath strips leading ./ and normalizes (0.534875ms)
  ✔ isAbsolutePathLike detects posix, windows drive, unc (0.1265ms)
  ✔ resolveInside rejects traversal outside root (0.648417ms)
  ✔ expandUser leaves non-home paths alone (0.12475ms)
✔ paths (11.330291ms)
▶ atomic-write
  ✔ writes text with a trailing newline, UTF-8 preserved (7.532667ms)
  ✔ writes JSON without ascii escaping and creates parent dirs (5.038291ms)
  ✔ preserves existing file mode (9.815959ms)
  ✔ loadJson returns default on missing/corrupt (0.827416ms)
  ✔ loadJsonStrict raises on corrupt/non-object (1.196291ms)
✔ atomic-write (24.9675ms)
中文测试
{
  "name": "中文"
}
err 中文
▶ subprocess.spawn (argv)
  ✔ runs a successful command and captures output (106.293875ms)
  ✔ returns 127 when the binary is missing (8.07225ms)
  ✔ returns a non-zero code on argv usage error (29.320417ms)
✔ subprocess.spawn (argv) (144.899ms)
▶ subprocess.which / commandExists
  ✔ finds node on PATH (0.27525ms)
  ✔ returns null for a missing command (1.662375ms)
✔ subprocess.which / commandExists (2.178083ms)
▶ subprocess.runShell (shell form)
  ✔ supports pipes and redirects (10.330334ms)
  ✔ supports environment variable expansion (11.4205ms)
  ✔ returns 0 for a true compound command (4.113291ms)
  ✔ surfaces non-zero exit of a failed command (5.282416ms)
✔ subprocess.runShell (shell form) (31.49375ms)
▶ output (UTF-8)
  ✔ print writes a UTF-8 line including Chinese (0.3785ms)
  ✔ printJson renders without ASCII escaping (0.064417ms)
  ✔ printError writes to stderr (0.0385ms)
✔ output (UTF-8) (0.54525ms)
▶ io.yaml
  ✔ parses flat key: value (1.41575ms)
  ✔ strips quoted values (0.108708ms)
  ✔ coerces scalars (0.096542ms)
✔ io.yaml (1.683709ms)
▶ io.markdown
  ✔ parses ATX headings with level and text (0.113541ms)
  ✔ normalizeHeading collapses whitespace (0.027791ms)
  ✔ hasMeaningfulContent rejects blank/placeholder (0.107166ms)
✔ io.markdown (0.28875ms)
已初始化 .project-intel，索引了 4 个文本文件。
{
  "dryRun": true,
  "manifest": {
    "schemaVersion": 2,
    "toolVersion": "0.7.4",
    "projectRoot": ".",
    "generatedAt": "2026-07-28T04:24:27.815Z",
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
    "generatedAt": "2026-07-28T04:24:27.864Z",
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
  ✔ writes the .project-intel layout (manifest/config/knowledge/status) (205.569583ms)
  ✔ --dry-run does not write files (56.459542ms)
  ✔ refresh re-writes without tooling (609.140708ms)
  ✔ strict + no-graph is a usage error (3.669709ms)
  ✔ ensureProjectIntelGitignore writes local-only rules (0.729333ms)
✔ init command (877.001041ms)
▶ doctor command
  ✔ reports node runtime, not python (9.105125ms)
  ✔ detects initialized state after init (415.193875ms)
✔ doctor command (424.410916ms)
▶ check command
  ✔ passes with no hard rules configured (256.84525ms)
  ✔ --dry-run does not write status (407.76325ms)
✔ check command (664.725291ms)
▶ standards inference
  ✔ infers PascalCase naming from >=3 pascal components (0.306958ms)
  ✔ infers backend Service suffix from >=2 services (0.085ms)
  ✔ infers ui-pattern from redundancy candidates (0.067583ms)
  ✔ ports backend API, layering and operational inference categories (0.120833ms)
✔ standards inference (0.653375ms)
▶ project domain candidates
  ✔ aggregates repeated non-generic parent segments in stable order (0.686458ms)
✔ project domain candidates (0.74775ms)
▶ standards documents
  ✔ renders detailed frontend and backend facts instead of count-only placeholders (1.13725ms)
✔ standards documents (1.218333ms)
▶ hard rules engine
  ✔ returns no violations with the empty default set (0.054208ms)
  ✔ surfaces a registered rule violation (0.060541ms)
✔ hard rules engine (0.162458ms)
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ requirement command dispatcher
  ✔ status returns state for a created requirement (58.705417ms)
  ✔ plan writes into the resolved id-title requirement directory (53.7815ms)
  ✔ intake defaults both mandatory document actions to generate (45.782209ms)
  ✔ intake uses a supplied design as the source while generating the missing spec (38.897083ms)
  ✔ intake rejects later for mandatory lifecycle documents (0.633584ms)
  ✔ intake requires a valid user supplied version date (1.085292ms)
  ✔ task-only intake remains a read-only analysis without a version date (5.66375ms)
  ✔ task intake with a version date registers a dated LOCAL requirement (50.938125ms)
  ✔ acceptance set persists AC-01..AC-02 (64.745291ms)
  ✔ query reads v2 and legacy by-id archives and supports --file (88.694458ms)
  ✔ status remains readable for a legacy manifest without workflow selections (13.468334ms)
  ✔ test-contract set requires --kind and --report-action (111.321ms)
  ✔ test-contract register validates and normalizes a structured report path (63.157958ms)
  ✔ ready -> begin through the dispatcher (837.098584ms)
  ✔ reopen after close (64.286083ms)
  ✔ generate enforces lifecycle order and creates a requirement scaffold (60.171625ms)
  ✔ generate refuses implicit overwrite and --replace really rebuilds the scaffold (109.130417ms)
  ✔ rejects missing --requirement-id (7.853667ms)
  ✔ add persists artifact registration into the manifest (444.185125ms)
  ✔ rejects arbitrary delivery-document content (111.546166ms)
  ✔ design registrat
```
