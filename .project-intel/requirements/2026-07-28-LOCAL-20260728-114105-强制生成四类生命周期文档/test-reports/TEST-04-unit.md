# LOCAL-20260728-114105 测试报告

- 测试类型：unit
- 阶段：green
- 结果：passed
- 验收标准：AC-01,AC-02,AC-03,AC-04,AC-05,AC-06,AC-07
- 文件范围：README.md, docs/project-intelligence-guide.md, evals/skill-behavior-scenarios.json, plugins/project-intelligence/assets/plugin-intro.html, plugins/project-intelligence/skills/project-debug/SKILL.md, plugins/project-intelligence/skills/project-design/SKILL.md, plugins/project-intelligence/skills/project-finish/SKILL.md, plugins/project-intelligence/skills/project-intake/SKILL.md, plugins/project-intelligence/skills/project-spec/SKILL.md, plugins/project-intelligence/skills/project-test/SKILL.md, scripts/validate-skill-evals.mjs, src/__tests__/cli-contract.test.ts, src/__tests__/install-hooks.test.ts, src/__tests__/requirement-command.test.ts, src/__tests__/state-machine.test.ts, src/__tests__/test-evidence.test.ts, src/__tests__/zcode-compat.test.ts, src/app/dispatcher.ts, src/cli/command-flags.ts, src/commands/agent-rules.ts, src/commands/init.ts, src/commands/requirement.ts, src/commands/test.ts, src/requirements/documents.ts, src/requirements/state-machine.ts

## 执行结果

### npm test

- exitCode: 0
- executedCount: 281

```text
Skill behavior scenario contracts verified: 27 scenarios, 17 skills
▶ maskCommentsAndStrings
  ✔ masks line and block comments and string contents (0.907584ms)
✔ maskCommentsAndStrings (2.369292ms)
▶ scanBackendFile
  ✔ extracts a Spring controller endpoint and methods (.java) (5.00025ms)
  ✔ extracts Python def/class and Flask routes (.py) (3.155916ms)
  ✔ classifies a service by name and extracts transaction signals (0.494375ms)
  ✔ extracts config keys from yaml (0.322916ms)
  ✔ classifies repository files and extracts SQL ops from xml mapper (1.265792ms)
  ✔ extracts permission signals (0.174917ms)
  ✔ extracts error code signals (0.108625ms)
  ✔ requires bound framework imports and keeps Django class views (0.176ms)
  ✔ labels malformed Python without accepting route facts (0.935125ms)
  ✔ applies configured backend entrypoint rules (0.191875ms)
✔ scanBackendFile (13.001709ms)
▶ BACKEND_SUFFIXES
  ✔ includes java, kt, py, go, ts, js (0.048917ms)
✔ BACKEND_SUFFIXES (0.086583ms)
▶ cli snapshot contract (AC-02)
  ✔ loads a well-formed snapshot (2.002833ms)
  ✔ captured every top-level command's help (1.539584ms)
  ✔ pins the JSON envelope shape on every probe (0.440542ms)
  ✔ the version command exits 0 and prints a semver (0.231833ms)
  ✔ usage errors exit non-zero with a non-ok envelope (0.750209ms)
✔ cli snapshot contract (AC-02) (6.472292ms)
▶ live Node CLI contract (AC-02/AC-10)
  ✔ dist/cli.js exists and is runnable (0.161334ms)
  ✔ version command exits 0 and prints a semver (176.870584ms)
  ✔ --version flag exits 0 and prints a semver (147.856417ms)
  ✔ every baseline command's --help is byte-for-byte compatible (1624.639959ms)
  ✔ mandatory document commands no longer advertise later or defer (421.46575ms)
  ✔ lifecycle rejects the removed no-op report-action flag (85.345292ms)
  ✔ top-level --help is byte-for-byte compatible (76.809791ms)
  ✔ top-level --help output contains all baseline commands (76.520042ms)
  ✔ subcommand --help output contains usage line and key flags (210.543958ms)
  ✔ unknown command exits 2 (67.194666ms)
  ✔ unknown flag exits 2 (69.997417ms)
  ✔ version --json produces a valid envelope with version field (71.813584ms)
  ✔ doctor --json produces a valid envelope with runtime=node (88.405792ms)
  ✔ usage error --json produces ok=false envelope (82.397625ms)
✔ live Node CLI contract (AC-02/AC-10) (3200.691208ms)
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
  ✔ prints --version alone (2.310792ms)
  ✔ prints --version envelope in json mode (0.323625ms)
  ✔ runs a registered command (text mode) (0.545625ms)
  ✔ runs a registered command (json mode) with envelope (0.421458ms)
  ✔ rejects unknown command with exit 2 (text) (0.842375ms)
  ✔ rejects unknown command with exit 2 (json envelope) (0.782875ms)
  ✔ surfaces usage errors as exit 2 (0.345708ms)
  ✔ surfaces runtime errors as exit 1 (0.204167ms)
  ✔ rejects missing subcommand (json exit 2) (3.4645ms)
  ✔ subcommand --help is intercepted and exits 0 (text) (0.388292ms)
  ✔ subcommand -h is intercepted and exits 0 (json) (0.278667ms)
  ✔ rejects unknown long flag with exit 2 (text) (0.164125ms)
  ✔ rejects unknown long flag with exit 2 (json envelope) (0.205625ms)
  ✔ accepts known value flag and its value (not mistaken for a flag) (0.120208ms)
  ✔ rejects unknown flag even after a valid value flag (0.066625ms)
✔ dispatch (12.31925ms)
▶ normalizeForCompare
  ✔ masks ISO-8601 timestamps (1.14925ms)
  ✔ masks 40-char git hashes (0.067625ms)
  ✔ masks epoch-second/milli integers (0.048417ms)
  ✔ masks absolute repo roots (POSIX) (0.049916ms)
  ✔ normalizes Windows backslashes and masks sample root (0.055292ms)
  ✔ collapses mtime integers regardless of value (0.063167ms)
  ✔ applies longest-root-first masking so nested roots win (0.055ms)
✔ normalizeForCompare (2.1445ms)
▶ compareJsonOutputs
  ✔ returns null for equal normalized values (0.124875ms)
  ✔ reports the first differing path (0.063625ms)
  ✔ reports missing keys with direction (0.167875ms)
  ✔ reports array length mismatches (0.07025ms)
✔ compareJsonOutputs (0.543875ms)
▶ frontend scanner
  ✔ extracts vue component props/emits (4.903625ms)
  ✔ extracts react props from interface (0.800208ms)
  ✔ extracts hooks by use* filename (0.390417ms)
  ✔ extracts routes and redundancy candidates (0.838ms)
  ✔ extractVueProps from defineProps object form (0.3265ms)
  ✔ extractEmits filters to valid names (0.109375ms)
  ✔ extractApiEndpoints from request/fetch calls (5.862875ms)
✔ frontend scanner (14.755375ms)
▶ files scanner
  ✔ discoverFiles walks and categorizes (1.37575ms)
  ✔ discoverFiles excludes node_modules/.git (0.748166ms)
  ✔ uses stable code-point ordering across operating systems (1.984833ms)
  ✔ categorize and simpleMatch basics (0.318084ms)
✔ files scanner (4.638792ms)
▶ incremental scan cache
  ✔ reuses unchanged frontend facts without reading the file again (0.290208ms)
  ✔ uses nanosecond-compatible file signatures and invalidates changed entries (0.645584ms)
✔ incremental scan cache (0.995375ms)
▶ quality scanner
  ✔ packageFrameworks detects Vue+TypeScript from deps (0.089833ms)
  ✔ detectPackage reads package.json scripts and frameworks (0.54225ms)
  ✔ packageManager detects npm/pnpm/yarn by lockfile (0.302583ms)
  ✔ detectQualityCommands: Python project STILL recognizes pytest/ruff/mypy (P1.3) (1.617208ms)
  ✔ detectQualityCommands: JS project infers eslint/tsc from config presence (1.426583ms)
✔ quality scanner (4.095041ms)
FixtureGraph 已安装，开始运行分析："/opt/homebrew/Cellar/node/26.3.0/bin/node" -e "process.stdout.write('graph-ok')"
FixtureGraph 开始执行，超时上限 900 秒。
GitNexus：仓库内 runner 需要显式使用 --allow-repo-runner。
▶ graph command authorization
  ✔ preserves and detects Windows absolute paths on POSIX (2.0495ms)
  ✔ allows repository-contained absolute paths and rejects outside paths (0.661166ms)
  ✔ requires explicit permission for repo runners and environment commands (1.721625ms)
✔ graph command authorization (5.514333ms)
▶ graph setup execution
  ✔ executes an authorized installed analyzer and captures evidence (103.045875ms)
  ✔ records a skipped result instead of executing an unauthorized runner (3.040583ms)
✔ graph setup execution (106.258042ms)
▶ adapter block management
  ✔ rejects paths outside the allowed set (2.147708ms)
  ✔ replaceSingleManagedBlock creates then updates (0.543458ms)
  ✔ upsert then remove a managed block (1.235833ms)
✔ adapter block management (5.081958ms)
▶ adapters command family
  ✔ apply writes codex + claude blocks; status reports current (1.873875ms)
  ✔ preview is dry-run (no files written) (0.461ms)
  ✔ remove clears blocks (1.53725ms)
  ✔ status --check returns non-zero when not current (1.307083ms)
  ✔ adapterTargets both returns 3 targets (codex, claude, claude-nested) (0.993917ms)
  ✔ managed Codex and Claude rules require four documents and design-derived specs (0.558ms)
✔ adapters command family (7.134209ms)
▶ top-level install command
  ✔ creates .claude/ and applies adapters; --hooks writes templates (2.602709ms)
✔ top-level install command (2.693209ms)
▶ agent install command
  ✔ agentInstallCommands builds codex+claude for all (0.0885ms)
  ✔ --dry-run classifies present when cli exists, missing otherwise (0.882291ms)
  ✔ rejects invalid target (1.023083ms)
✔ agent install command (2.099291ms)
▶ git hooks (AC-07: no python3)
  ✔ hook body calls project-intel (Node CLI), never python3 (0.070375ms)
  ✔ writeHookTemplates writes 3 hooks + README under .project-intel/hooks (2.137334ms)
✔ git hooks (AC-07: no python3) (2.38875ms)
▶ sanitizeErrorText
  ✔ redacts authorization bearer tokens (0.925458ms)
  ✔ redacts cookies (0.067042ms)
  ✔ redacts password/secret/token/api_key (0.0885ms)
  ✔ redacts aws credentials (0.044541ms)
  ✔ redacts URL userinfo (0.036334ms)
  ✔ leaves benign text intact (1.73775ms)
✔ sanitizeErrorText (4.310375ms)
▶ extractGlobalJson
  ✔ strips --json and reports mode (1.085708ms)
  ✔ preserves argv when --json absent (0.13675ms)
✔ extractGlobalJson (1.386709ms)
▶ jsonEnvelope
  ✔ shapes a success envelope (0.332209ms)
  ✔ classifies exit 2 as USAGE_ERROR with sanitized in-place error (0.188667ms)
  ✔ classifies non-2 failure as COMMAND_FAILED with default message (0.165583ms)
  ✔ trims the output field (0.121209ms)
✔ jsonEnvelope (1.018292ms)
▶ parseGlobal / splitArgv
  ✔ parses --project value (0.218167ms)
  ✔ parses --project= form (0.051333ms)
  ✔ parses --json (0.145291ms)
  ✔ rejects unknown long option before subcommand with exit-2 UsageError (0.095334ms)
  ✔ splitArgv separates global, command, and rest (0.071042ms)
  ✔ splitArgv returns null when no subcommand (0.0265ms)
✔ parseGlobal / splitArgv (0.705916ms)
▶ withLock (in-process)
  ✔ blocks same-process re-entrant acquire (no deadlock) (67.043083ms)
  ✔ releases the lockfile after the critical section (0.662916ms)
✔ withLock (in-process) (68.962ms)
▶ withLock (multi-process contention)
  ✔ grants exclusive access across child processes (1257.641083ms)
✔ withLock (multi-process contention) (1257.772792ms)
▶ paths
  ✔ toPosix converts separators (0.398291ms)
  ✔ normalizeBusinessPath strips leading ./ and normalizes (0.06525ms)
  ✔ isAbsolutePathLike detects posix, windows drive, unc (0.063625ms)
  ✔ resolveInside rejects traversal outside root (0.572166ms)
  ✔ expandUser leaves non-home paths alone (0.097041ms)
✔ paths (1.82575ms)
▶ atomic-write
  ✔ writes text with a trailing newline, UTF-8 preserved (7.026625ms)
  ✔ writes JSON without ascii escaping and creates parent dirs (7.749792ms)
  ✔ preserves existing file mode (19.252083ms)
  ✔ loadJson returns default on missing/corrupt (3.9175ms)
  ✔ loadJsonStrict raises on corrupt/non-object (3.847542ms)
✔ atomic-write (42.260833ms)
中文测试
{
  "name": "中文"
}
err 中文
▶ subprocess.spawn (argv)
  ✔ runs a successful command and captures output (153.729625ms)
  ✔ returns 127 when the binary is missing (6.410916ms)
  ✔ returns a non-zero code on argv usage error (28.230208ms)
✔ subprocess.spawn (argv) (189.677209ms)
▶ subprocess.which / commandExists
  ✔ finds node on PATH (0.572917ms)
  ✔ returns null for a missing command (0.74325ms)
✔ subprocess.which / commandExists (2.297ms)
▶ subprocess.runShell (shell form)
  ✔ supports pipes and redirects (13.246041ms)
  ✔ supports environment variable expansion (15.741209ms)
  ✔ returns 0 for a true compound command (7.221291ms)
  ✔ surfaces non-zero exit of a failed command (8.016542ms)
✔ subprocess.runShell (shell form) (44.685583ms)
▶ output (UTF-8)
  ✔ print writes a UTF-8 line including Chinese (0.763792ms)
  ✔ printJson renders without ASCII escaping (0.1685ms)
  ✔ printError writes to stderr (0.090083ms)
✔ output (UTF-8) (1.174541ms)
▶ io.yaml
  ✔ parses flat key: value (1.411917ms)
  ✔ strips quoted values (0.112708ms)
  ✔ coerces scalars (0.175375ms)
✔ io.yaml (1.850833ms)
▶ io.markdown
  ✔ parses ATX headings with level and text (0.270083ms)
  ✔ normalizeHeading collapses whitespace (0.063625ms)
  ✔ hasMeaningfulContent rejects blank/placeholder (0.207417ms)
✔ io.markdown (0.637167ms)
已初始化 .project-intel，索引了 4 个文本文件。
{
  "dryRun": true,
  "manifest": {
    "schemaVersion": 2,
    "toolVersion": "0.7.4",
    "projectRoot": ".",
    "generatedAt": "2026-07-28T04:11:23.034Z",
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
    "generatedAt": "2026-07-28T04:11:23.094Z",
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
  ✔ writes the .project-intel layout (manifest/config/knowledge/status) (318.14525ms)
  ✔ --dry-run does not write files (68.341542ms)
  ✔ refresh re-writes without tooling (599.944875ms)
  ✔ strict + no-graph is a usage error (0.87625ms)
  ✔ ensureProjectIntelGitignore writes local-only rules (0.621208ms)
✔ init command (988.974375ms)
▶ doctor command
  ✔ reports node runtime, not python (2.491458ms)
  ✔ detects initialized state after init (369.36725ms)
✔ doctor command (371.981334ms)
▶ check command
  ✔ passes with no hard rules configured (316.115708ms)
  ✔ --dry-run does not write status (404.1295ms)
✔ check command (720.415208ms)
▶ standards inference
  ✔ infers PascalCase naming from >=3 pascal components (0.304ms)
  ✔ infers backend Service suffix from >=2 services (0.080042ms)
  ✔ infers ui-pattern from redundancy candidates (0.042125ms)
  ✔ ports backend API, layering and operational inference categories (0.129542ms)
✔ standards inference (0.629041ms)
▶ project domain candidates
  ✔ aggregates repeated non-generic parent segments in stable order (0.663167ms)
✔ project domain candidates (0.714667ms)
▶ standards documents
  ✔ renders detailed frontend and backend facts instead of count-only placeholders (0.962333ms)
✔ standards documents (0.994959ms)
▶ hard rules engine
  ✔ returns no violations with the empty default set (0.047666ms)
  ✔ surfaces a registered rule violation (0.185917ms)
✔ hard rules engine (0.321125ms)
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ requirement command dispatcher
  ✔ status returns state for a created requirement (71.175958ms)
  ✔ plan writes into the resolved id-title requirement directory (79.9995ms)
  ✔ intake defaults both mandatory document actions to generate (74.53525ms)
  ✔ intake uses a supplied design as the source while generating the missing spec (46.528625ms)
  ✔ intake rejects later for mandatory lifecycle documents (3.976709ms)
  ✔ intake requires a valid user supplied version date (0.507708ms)
  ✔ task-only intake remains a read-only analysis without a version date (0.417959ms)
  ✔ task intake with a version date registers a dated LOCAL requirement (57.363666ms)
  ✔ acceptance set persists AC-01..AC-02 (101.294542ms)
  ✔ query reads v2 and legacy by-id archives and supports --file (73.467083ms)
  ✔ status remains readable for a legacy manifest without workflow selections (9.44125ms)
  ✔ test-contract set requires --kind and --report-action (86.701ms)
  ✔ test-contract register validates and normalizes a structured report path (122.063333ms)
  ✔ ready -> begin through the dispatcher (792.312292ms)
  ✔ reopen after close (71.8155ms)
  ✔ generate enforces lifecycle order and creates a requirement scaffold (94.068667ms)
  ✔ generate refuses implicit overwrite and --replace really rebuilds the scaffold (128.8275ms)
  ✔ rejects missing --requirement-id (3.614916ms)
  ✔ add persists artifact registration into the manifest (273.305292ms)
  ✔ rejects arbitrary delivery-document content (174.530167ms)
  ✔ 
```
