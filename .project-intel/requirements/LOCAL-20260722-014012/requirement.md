# LOCAL-20260722-014012 修复 Windows 市场克隆符号链接失败 需求文档

## 文档信息

- 需求号：`LOCAL-20260722-014012`
- 需求名称：修复 Windows 市场克隆符号链接失败
- 单据类型：Bug

## 背景与现状

GitHub 仓库当前将 `.understand-anything` 提交为指向 `.ua` 的符号链接。ZCode 在 Windows 上克隆市场仓库时，普通用户环境通常无权创建符号链接，Git 检出因此以 `EPERM` 失败，继而造成市场文件缺失并退化到缓存。

## 目标

将 Understand-Anything 图谱目录以普通目录形式提交到 `.understand-anything`，消除 Windows 克隆对符号链接权限的依赖，同时保持现有图谱发现路径与读取行为不变。

## 业务场景

Windows 用户通过 ZCode 或 Git 克隆 `crayonYYxm/project-intelligence` 市场仓库时，仓库所有文件应在无开发者模式、无管理员权限的普通环境中完成检出。Project Intelligence 随后仍应从 `.understand-anything/knowledge-graph.json` 发现并读取 Understand-Anything 图谱。

## 范围

- 删除 Git 中 `.understand-anything -> .ua` 的符号链接条目。
- 将现有 `.ua` 目录迁移为真实的 `.understand-anything` 目录，保留其中图谱文件。
- 增加仓库结构回归测试，防止再次提交该符号链接或恢复 `.ua` 兼容目录。

## 非目标

不修改图谱生成算法、Project Intelligence 运行时接口、npm 包版本或发布流程；根因仅在 Git 仓库目录形态。


## 复现条件

1. 在当前提交执行 `git ls-files -s .understand-anything`，可见文件模式为 `120000`。
2. 在未启用开发者模式且无管理员权限的 Windows 环境克隆市场仓库。
3. Git/ZCode 创建 `.understand-anything` 符号链接时返回 `EPERM`，市场文件未完整检出。

## 当前行为

`.understand-anything` 是符号链接而非普通目录；Windows 克隆成功依赖额外系统权限。

## 预期行为

`.understand-anything` 是仓库中可直接检出的普通目录，`.ua` 不再作为仓库目录存在，图谱仍可从规范路径被识别。

## 业务规则与异常边界

- 仓库不得以 Git 模式 `120000` 跟踪 `.understand-anything`。
- `.understand-anything/knowledge-graph.json` 必须保留并可读取。
- 不依赖 Windows 开发者模式、管理员权限或 `core.symlinks` 配置。
- 其他测试中为安全边界临时创建的符号链接夹具不属于本次仓库结构限制。

## 验收标准

- AC-01：仓库根目录 `.understand-anything` 是真实目录且不是符号链接，Git 不再以 `120000` 模式跟踪该路径。
- AC-02：仓库中不存在 `.ua` 目录，`.understand-anything/knowledge-graph.json` 仍存在并能被图谱检测逻辑识别。
- AC-03：新增仓库结构回归测试通过，现有单元测试与发布包检查无回归。

## 外部接口影响

不影响外部接口。依据是改动仅涉及 Git 仓库目录形态和测试，不修改 CLI、HTTP/API、配置字段或 npm 包导出。

## 待确认事项

无。用户已明确给出根因与首选迁移方式，仓库现状也验证了符号链接指向 `.ua`。
