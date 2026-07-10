---
name: project-init
description: Use when the user wants to initialize, set up, or bootstrap project intelligence for the first time. 初始化项目, 项目初始化, 搭建项目, 创建项目, 项目搭建, 初始化.
---

# Project Init

Use this skill when the user says to initialize, set up, or bootstrap project intelligence for a repository.

Commands:

```bash
project-intel graph-tools --json
project-intel init
project-intel init --no-graph
project-intel init --interactive
project-intel init --setup-missing
project-intel init --strict
```

`init` generates `.project-intel/` with standards, knowledge, graph summaries, quality configuration, tooling checks, and reports. It also installs/refreshes the local Claude adapter under `.claude/CLAUDE.md` and maintains root-level `AGENTS.md` and `CLAUDE.md` managed blocks so project rules are visible even when a dedicated Project Intelligence skill does not trigger. Project Intelligence skills are provided by the plugin itself — `init` does not duplicate them into the project. It checks optional tools such as GitNexus, Understand-Anything, Node/package managers, and quality commands. Missing optional tools do not block initialization unless strict graph setup is requested.

Preserve user/team content in `AGENTS.md` and `CLAUDE.md`; only update the Project Intelligence managed block.

Do not ask the user to run `project-intel install` after `init` just to get Project Intelligence skills; skills come from the plugin. Keep `install` for repairing adapter files, regenerating entrypoints, or generating/activating optional hooks.

By default, `init` checks graph tools before writing project facts and runs analyzers that are already executable. Missing tools are reported without calling `input()`. Use `--interactive` only in an interactive terminal, and use `--setup-missing` only after the user explicitly approves installation. Understand-Anything is optional but supported on both Codex and Claude Code:

- `installed`: a real `understand` CLI or `PROJECT_INTEL_UNDERSTAND_COMMAND` is available, so `init` can run analysis directly.
- `agent-installed`: Codex/Claude Code plugin files are installed and enabled, but the shell cannot run analysis. In Claude Code, tell the user to run `/reload-plugins` after a fresh install/enable, then `/understand . --language zh`. After the graph finishes, immediately continue with `/project-refresh` or `project-intel refresh`.
- `partially-installed`: current agent already has Understand-Anything, but another platform still has an install option. Offer both the `/understand` follow-up and the missing-platform install option.
- `installable`: Understand-Anything is not installed, disabled, or the Claude Code install is broken. Ask whether to install/enable/repair it. If approved, use `init --setup-missing` or run the selected install command before `init`.
- `missing`: no supported install path was detected. Print the setup suggestion and continue without graph enhancement.

In noninteractive agent shells such as Codex/Claude tool runs, first run `graph-tools --json`, inspect `installOptions`, and ask the user in Chinese whether to run all graph setup, install GitNexus, install/enable Understand-Anything for Codex or Claude Code, run the `/understand` follow-up, or skip. Plain `init` never waits for input. Support combination answers such as `1,2`, `1+3`, `全部`, or `all`.

Use a concise Chinese choice prompt, for example:

```text
检测到可选图谱工具：
1. GitNexus：可下载并运行分析
2. Understand-Anything：已安装到 agent，当前 shell 不能直接分析
3. Understand-Anything：可安装或启用到 Claude Code

请选择：
1. 全部准备：GitNexus + Understand-Anything 安装/启用 + 后续分析提示
2. 准备 GitNexus 并分析
3. 安装/启用/修复 Understand-Anything 到 Claude Code，并验证插件状态
4. GitNexus + Understand-Anything 后续分析
5. 跳过图谱增强并继续初始化

也可以输入组合：`2,3` 表示同时准备 GitNexus 和 Claude Code 的 Understand-Anything。
```

After the user answers:
- If they approved all supported installs, run `init --setup-missing`.
- If they approved only part of the list, install that subset first, run installed shell analyzers such as GitNexus, then run `init`.
- If they choose any Understand-Anything analysis option and only an agent skill is available, explain that shell code cannot inject slash commands into the active Claude Code prompt. After Claude Code install/enable succeeds, the remaining action is `/reload-plugins`, then `/understand . --language zh`. Once the graph finishes, immediately run `/project-refresh` or the CLI fallback `project-intel refresh`.
- If they chose to skip graph setup and analysis, run `init --no-graph`.
- Keep all user-facing narration in Chinese unless the user asked for another language.

Use `--setup-missing` only when the user has already approved automatic setup. For GitNexus this usually means downloading the CLI via `npx` and immediately running `analyze`, not a separate global install. For Understand-Anything, install according to the chosen target:

- Codex: `curl -fsSL https://raw.githubusercontent.com/Egonex-AI/Understand-Anything/main/install.sh | bash -s codex`
- Claude Code CLI: `claude plugin marketplace add Egonex-AI/Understand-Anything`, then `claude plugin install understand-anything@understand-anything`, then `claude plugin enable understand-anything@understand-anything`. Verify with `claude plugin list`; do not report success if the plugin is disabled or failed to load.
- Claude Code slash UI equivalent: `/plugin marketplace add Egonex-AI/Understand-Anything`, then `/plugin install understand-anything`. The plugin name is `understand-anything`; the CLI form uses `understand-anything@understand-anything` only to specify the marketplace explicitly.

Do not use the Codex installer as a substitute for Claude Code plugin installation, and do not claim Claude Code cannot install it just because it is absent from the official Anthropic marketplace. Use the Understand-Anything marketplace repo instead.

If Claude Code shows `understand-anything@local` with `failed to load` or `Marketplace local not found`, treat it as a broken install rather than a usable plugin. Run the marketplace install/repair flow above and ask for `/reload-plugins` only after verification succeeds.

After initialization or after any external graph generation finishes, use `/project-refresh` to update existing project facts. If slash commands cannot be issued programmatically, run `project-intel refresh`.
