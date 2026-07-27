# LOCAL-20260727-164522 测试报告

- 测试类型：unit
- 阶段：verify
- 结果：passed
- 验收标准：AC-01,AC-02,AC-03,AC-04,AC-05
- 文件范围：src/requirements/state-machine.ts, src/requirements/documents.ts, src/__tests__/state-machine.test.ts, src/__tests__/review-finish-graph.test.ts, README.md, marketplace.json, package-lock.json, package.json, plugins/project-intelligence/.claude-plugin/plugin.json, plugins/project-intelligence/.codex-plugin/plugin.json, plugins/project-intelligence/.zcode-plugin/plugin.json, plugins/project-intelligence/assets/plugin-intro.html, plugins/project-intelligence/skills/project-design/SKILL.md, plugins/project-intelligence/skills/project-finish/SKILL.md, plugins/project-intelligence/skills/project-intake/SKILL.md, plugins/project-intelligence/skills/project-knowledge/SKILL.md, plugins/project-intelligence/skills/project-orchestrate/SKILL.md, plugins/project-intelligence/skills/project-plan/SKILL.md, plugins/project-intelligence/skills/project-review/SKILL.md, plugins/project-intelligence/skills/project-spec/SKILL.md, plugins/project-intelligence/skills/project-task/SKILL.md, plugins/project-intelligence/skills/project-test/SKILL.md, src/__tests__/helpers.ts, src/__tests__/requirement-command.test.ts, src/__tests__/test-evidence.test.ts, src/cli.ts, src/commands/agent-rules.ts, src/commands/finish.ts, src/commands/orchestration.ts, src/commands/requirement.ts, src/commands/test.ts, src/requirements/artifacts.ts, src/requirements/layout.ts, src/version.ts, 2026-07-14-新增活动页面预填模板预览与用户指引优化/plan/index.md, 2026-07-14-新增活动页面预填模板预览与用户指引优化/prd.md, 2026-07-14-新增活动页面预填模板预览与用户指引优化/retrospective.md, 2026-07-14-新增活动页面预填模板预览与用户指引优化/test.md, 2026-07-14-新增活动页面预填模板预览与用户指引优化/收口档案.md

## 执行结果

### npm test -- src/__tests__/state-machine.test.ts src/__tests__/review-finish-graph.test.ts

- exitCode: 0
- executedCount: 262

```text
Skill behavior scenario contracts verified: 27 scenarios, 17 skills
▶ maskCommentsAndStrings
  ✔ masks line and block comments and string contents (1.103084ms)
✔ maskCommentsAndStrings (2.4725ms)
▶ scanBackendFile
  ✔ extracts a Spring controller endpoint and methods (.java) (3.639416ms)
  ✔ extracts Python def/class and Flask routes (.py) (4.694042ms)
  ✔ classifies a service by name and extracts transaction signals (1.297583ms)
  ✔ extracts config keys from yaml (6.006083ms)
  ✔ classifies repository files and extracts SQL ops from xml mapper (1.438167ms)
  ✔ extracts permission signals (0.1995ms)
  ✔ extracts error code signals (0.109875ms)
  ✔ requires bound framework imports and keeps Django class views (0.159625ms)
  ✔ labels malformed Python without accepting route facts (0.080041ms)
  ✔ applies configured backend entrypoint rules (0.14925ms)
✔ scanBackendFile (18.315708ms)
▶ BACKEND_SUFFIXES
  ✔ includes java, kt, py, go, ts, js (0.044ms)
✔ BACKEND_SUFFIXES (0.07575ms)
▶ cli snapshot contract (AC-02)
  ✔ loads a well-formed snapshot (1.056ms)
  ✔ captured every top-level command's help (1.449042ms)
  ✔ pins the JSON envelope shape on every probe (0.558542ms)
  ✔ the version command exits 0 and prints a semver (0.784ms)
  ✔ usage errors exit non-zero with a non-ok envelope (0.347958ms)
✔ cli snapshot contract (AC-02) (5.7385ms)
▶ live Node CLI contract (AC-02/AC-10)
  ✔ dist/cli.js exists and is runnable (0.2565ms)
  ✔ version command exits 0 and prints a semver (139.334875ms)
  ✔ --version flag exits 0 and prints a semver (146.662875ms)
  ✔ every baseline command's --help is byte-for-byte compatible (1747.967833ms)
  ✔ top-level --help is byte-for-byte compatible (68.929916ms)
  ✔ top-level --help output contains all baseline commands (73.681083ms)
  ✔ subcommand --help output contains usage line and key flags (230.72425ms)
  ✔ unknown command exits 2 (85.040875ms)
  ✔ unknown flag exits 2 (70.869917ms)
  ✔ version --json produces a valid envelope with version field (68.122667ms)
  ✔ doctor --json produces a valid envelope with runtime=node (72.301041ms)
  ✔ usage error --json produces ok=false envelope (85.950375ms)
✔ live Node CLI contract (AC-02/AC-10) (2790.6785ms)
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
  ✔ prints --version alone (1.895667ms)
  ✔ prints --version envelope in json mode (0.428375ms)
  ✔ runs a registered command (text mode) (0.45325ms)
  ✔ runs a registered command (json mode) with envelope (0.507792ms)
  ✔ rejects unknown command with exit 2 (text) (0.690459ms)
  ✔ rejects unknown command with exit 2 (json envelope) (3.135333ms)
  ✔ surfaces usage errors as exit 2 (0.156875ms)
  ✔ surfaces runtime errors as exit 1 (0.104792ms)
  ✔ rejects missing subcommand (json exit 2) (0.078042ms)
  ✔ subcommand --help is intercepted and exits 0 (text) (0.490708ms)
  ✔ subcommand -h is intercepted and exits 0 (json) (0.93875ms)
  ✔ rejects unknown long flag with exit 2 (text) (0.094584ms)
  ✔ rejects unknown long flag with exit 2 (json envelope) (0.105208ms)
  ✔ accepts known value flag and its value (not mistaken for a flag) (0.096125ms)
  ✔ rejects unknown flag even after a valid value flag (0.234917ms)
✔ dispatch (11.169875ms)
▶ normalizeForCompare
  ✔ masks ISO-8601 timestamps (1.365542ms)
  ✔ masks 40-char git hashes (0.173375ms)
  ✔ masks epoch-second/milli integers (0.081916ms)
  ✔ masks absolute repo roots (POSIX) (0.06475ms)
  ✔ normalizes Windows backslashes and masks sample root (0.089958ms)
  ✔ collapses mtime integers regardless of value (0.071542ms)
  ✔ applies longest-root-first masking so nested roots win (0.062ms)
✔ normalizeForCompare (2.750417ms)
▶ compareJsonOutputs
  ✔ returns null for equal normalized values (0.411084ms)
  ✔ reports the first differing path (0.174042ms)
  ✔ reports missing keys with direction (0.373417ms)
  ✔ reports array length mismatches (0.15ms)
✔ compareJsonOutputs (1.38ms)
▶ frontend scanner
  ✔ extracts vue component props/emits (2.281583ms)
  ✔ extracts react props from interface (1.297083ms)
  ✔ extracts hooks by use* filename (0.469334ms)
  ✔ extracts routes and redundancy candidates (1.105417ms)
  ✔ extractVueProps from defineProps object form (0.17275ms)
  ✔ extractEmits filters to valid names (0.059625ms)
  ✔ extractApiEndpoints from request/fetch calls (2.224792ms)
✔ frontend scanner (15.963333ms)
▶ files scanner
  ✔ discoverFiles walks and categorizes (4.911459ms)
  ✔ discoverFiles excludes node_modules/.git (0.604417ms)
  ✔ uses stable code-point ordering across operating systems (0.841292ms)
  ✔ categorize and simpleMatch basics (0.160958ms)
✔ files scanner (7.58ms)
▶ incremental scan cache
  ✔ reuses unchanged frontend facts without reading the file again (0.304ms)
  ✔ uses nanosecond-compatible file signatures and invalidates changed entries (0.926083ms)
✔ incremental scan cache (1.34475ms)
▶ quality scanner
  ✔ packageFrameworks detects Vue+TypeScript from deps (0.186166ms)
  ✔ detectPackage reads package.json scripts and frameworks (0.922084ms)
  ✔ packageManager detects npm/pnpm/yarn by lockfile (4.246041ms)
  ✔ detectQualityCommands: Python project STILL recognizes pytest/ruff/mypy (P1.3) (2.358709ms)
  ✔ detectQualityCommands: JS project infers eslint/tsc from config presence (0.648458ms)
✔ quality scanner (8.573375ms)
FixtureGraph 已安装，开始运行分析："/opt/homebrew/Cellar/node/26.3.0/bin/node" -e "process.stdout.write('graph-ok')"
FixtureGraph 开始执行，超时上限 900 秒。
GitNexus：仓库内 runner 需要显式使用 --allow-repo-runner。
▶ graph command authorization
  ✔ preserves and detects Windows absolute paths on POSIX (1.132167ms)
  ✔ allows repository-contained absolute paths and rejects outside paths (0.239708ms)
  ✔ requires explicit permission for repo runners and environment commands (0.1765ms)
✔ graph command authorization (2.1145ms)
▶ graph setup execution
  ✔ executes an authorized installed analyzer and captures evidence (105.105083ms)
  ✔ records a skipped result instead of executing an unauthorized runner (0.592292ms)
✔ graph setup execution (105.829666ms)
▶ adapter block management
  ✔ rejects paths outside the allowed set (0.721375ms)
  ✔ replaceSingleManagedBlock creates then updates (0.200084ms)
  ✔ upsert then remove a managed block (0.761292ms)
✔ adapter block management (2.239875ms)
▶ adapters command family
  ✔ apply writes codex + claude blocks; status reports current (2.230042ms)
  ✔ preview is dry-run (no files written) (0.18475ms)
  ✔ remove clears blocks (1.160458ms)
  ✔ status --check returns non-zero when not current (0.651583ms)
  ✔ adapterTargets both returns 3 targets (codex, claude, claude-nested) (1.1125ms)
✔ adapters command family (5.559625ms)
▶ top-level install command
  ✔ creates .claude/ and applies adapters; --hooks writes templates (1.012083ms)
✔ top-level install command (1.07925ms)
▶ agent install command
  ✔ agentInstallCommands builds codex+claude for all (0.298542ms)
  ✔ --dry-run classifies present when cli exists, missing otherwise (0.744667ms)
  ✔ rejects invalid target (0.138375ms)
✔ agent install command (1.336333ms)
▶ git hooks (AC-07: no python3)
  ✔ hook body calls project-intel (Node CLI), never python3 (0.051208ms)
  ✔ writeHookTemplates writes 3 hooks + README under .project-intel/hooks (0.64775ms)
✔ git hooks (AC-07: no python3) (0.741042ms)
▶ sanitizeErrorText
  ✔ redacts authorization bearer tokens (2.187ms)
  ✔ redacts cookies (0.093042ms)
  ✔ redacts password/secret/token/api_key (0.057042ms)
  ✔ redacts aws credentials (0.041792ms)
  ✔ redacts URL userinfo (0.038709ms)
  ✔ leaves benign text intact (0.782542ms)
✔ sanitizeErrorText (4.61125ms)
▶ extractGlobalJson
  ✔ strips --json and reports mode (4.14475ms)
  ✔ preserves argv when --json absent (0.130583ms)
✔ extractGlobalJson (4.472916ms)
▶ jsonEnvelope
  ✔ shapes a success envelope (1.754208ms)
  ✔ classifies exit 2 as USAGE_ERROR with sanitized in-place error (0.132958ms)
  ✔ classifies non-2 failure as COMMAND_FAILED with default message (0.091584ms)
  ✔ trims the output field (0.080334ms)
✔ jsonEnvelope (2.273333ms)
▶ parseGlobal / splitArgv
  ✔ parses --project value (6.446708ms)
  ✔ parses --project= form (0.092666ms)
  ✔ parses --json (0.036125ms)
  ✔ rejects unknown long option before subcommand with exit-2 UsageError (0.216875ms)
  ✔ splitArgv separates global, command, and rest (0.082375ms)
  ✔ splitArgv returns null when no subcommand (0.058875ms)
✔ parseGlobal / splitArgv (7.354083ms)
▶ withLock (in-process)
  ✔ blocks same-process re-entrant acquire (no deadlock) (72.47375ms)
  ✔ releases the lockfile after the critical section (0.688875ms)
✔ withLock (in-process) (74.479459ms)
▶ withLock (multi-process contention)
  ✔ grants exclusive access across child processes (1045.150583ms)
✔ withLock (multi-process contention) (1045.257167ms)
▶ paths
  ✔ toPosix converts separators (0.757291ms)
  ✔ normalizeBusinessPath strips leading ./ and normalizes (0.091333ms)
  ✔ isAbsolutePathLike detects posix, windows drive, unc (0.0755ms)
  ✔ resolveInside rejects traversal outside root (0.561542ms)
  ✔ expandUser leaves non-home paths alone (0.176583ms)
✔ paths (2.742417ms)
▶ atomic-write
  ✔ writes text with a trailing newline, UTF-8 preserved (5.031167ms)
  ✔ writes JSON without ascii escaping and creates parent dirs (8.169708ms)
  ✔ preserves existing file mode (9.886417ms)
  ✔ loadJson returns default on missing/corrupt (0.775916ms)
  ✔ loadJsonStrict raises on corrupt/non-object (0.714375ms)
✔ atomic-write (24.935417ms)
中文测试
{
  "name": "中文"
}
err 中文
▶ subprocess.spawn (argv)
  ✔ runs a successful command and captures output (98.235375ms)
  ✔ returns 127 when the binary is missing (6.051084ms)
  ✔ returns a non-zero code on argv usage error (26.469417ms)
✔ subprocess.spawn (argv) (131.993708ms)
▶ subprocess.which / commandExists
  ✔ finds node on PATH (0.31775ms)
  ✔ returns null for a missing command (0.242542ms)
✔ subprocess.which / commandExists (1.191541ms)
▶ subprocess.runShell (shell form)
  ✔ supports pipes and redirects (9.601709ms)
  ✔ supports environment variable expansion (15.3435ms)
  ✔ returns 0 for a true compound command (11.288291ms)
  ✔ surfaces non-zero exit of a failed command (7.680041ms)
✔ subprocess.runShell (shell form) (44.800833ms)
▶ output (UTF-8)
  ✔ print writes a UTF-8 line including Chinese (0.894458ms)
  ✔ printJson renders without ASCII escaping (0.280375ms)
  ✔ printError writes to stderr (0.154292ms)
✔ output (UTF-8) (1.634167ms)
▶ io.yaml
  ✔ parses flat key: value (1.703792ms)
  ✔ strips quoted values (0.082167ms)
  ✔ coerces scalars (0.100291ms)
✔ io.yaml (1.978125ms)
▶ io.markdown
  ✔ parses ATX headings with level and text (0.118625ms)
  ✔ normalizeHeading collapses whitespace (0.028167ms)
  ✔ hasMeaningfulContent rejects blank/placeholder (0.103375ms)
✔ io.markdown (0.285042ms)
已初始化 .project-intel，索引了 4 个文本文件。
{
  "dryRun": true,
  "manifest": {
    "schemaVersion": 2,
    "toolVersion": "0.7.3",
    "projectRoot": ".",
    "generatedAt": "2026-07-27T09:48:07.585Z",
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
    "generatedAt": "2026-07-27T09:48:07.641Z",
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
  ✔ writes the .project-intel layout (manifest/config/knowledge/status) (217.936666ms)
  ✔ --dry-run does not write files (60.688416ms)
  ✔ refresh re-writes without tooling (605.964666ms)
  ✔ strict + no-graph is a usage error (8.044042ms)
  ✔ ensureProjectIntelGitignore writes local-only rules (7.9515ms)
✔ init command (901.316709ms)
▶ doctor command
  ✔ reports node runtime, not python (41.467625ms)
  ✔ detects initialized state after init (399.778166ms)
✔ doctor command (441.350708ms)
▶ check command
  ✔ passes with no hard rules configured (328.449583ms)
  ✔ --dry-run does not write status (411.9195ms)
✔ check command (740.485459ms)
▶ standards inference
  ✔ infers PascalCase naming from >=3 pascal components (0.327458ms)
  ✔ infers backend Service suffix from >=2 services (0.081916ms)
  ✔ infers ui-pattern from redundancy candidates (0.043667ms)
  ✔ ports backend API, layering and operational inference categories (0.119125ms)
✔ standards inference (0.64675ms)
▶ project domain candidates
  ✔ aggregates repeated non-generic parent segments in stable order (1.359291ms)
✔ project domain candidates (1.426708ms)
▶ standards documents
  ✔ renders detailed frontend and backend facts instead of count-only placeholders (1.888833ms)
✔ standards documents (1.970583ms)
▶ hard rules engine
  ✔ returns no violations with the empty default set (0.047833ms)
  ✔ surfaces a registered rule violation (0.056708ms)
✔ hard rules engine (0.157709ms)
已初始化 .project-intel，索引了 3 个文本文件。
已初始化 .project-intel，索引了 3 个文本文件。
▶ requirement command dispatcher
  ✔ status returns state for a created requirement (47.604792ms)
  ✔ plan writes into the resolved id-title requirement directory (62.363708ms)
  ✔ intake persists document actions and later selection blocks generation (56.676834ms)
  ✔ acceptance set persists AC-01..AC-02 (60.21125ms)
  ✔ query reads v2 and legacy by-id archives and supports --file (57.154ms)
  ✔ test-contract set requires --kind and --report-action (99.478083ms)
  ✔ test-contract register validates and normalizes a structured report path (93.297417ms)
  ✔ ready -> begin through the dispatcher (834.967ms)
  ✔ reopen after close (36.90925ms)
  ✔ generate enforces lifecycle order and creates a requirement scaffold (83.068208ms)
  ✔ generate refuses implicit overwrite and --replace really rebuilds the scaffold (113.833834ms)
  ✔ rejects missing --requirement-id (3.547541ms)
  ✔ add persists artifact registration into the manifest (471.210125ms)
  ✔ rejects arbitrary delivery-document content (151.469834ms)
  ✔ design registration rejects missing source evidence paths (261.075791ms)
  ✔ design registration ignores symbols that exist only in comments or strings (208.549208ms)
  ✔ add registers a structured test report as current requirement evidence (496.367333ms)
  ✔ diagnose records a Bug root cause (ticketKind=bug) (75.496416ms)
  ✔ diagnose rejects missing source evidence paths (63.876459ms)
  ✔ diagnose rejects symbols that only appear in comments or strings (59.109833ms)
  ✔ diagnose rejects non-bug requirements (55.927167ms)
  ✔ defer adds a readiness blocker for design (51.971708ms)
  ✔ resolve-finding marks a review finding resolved (57.790084ms)
  ✔ resolve-finding rejects unknown finding IDs (47.191791ms)
✔ requirement command dispatcher (3551.7269
```
