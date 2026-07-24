# LOCAL-20260722-014012 修复 Windows 市场克隆符号链接失败

## 1 BUG 现象

GitHub 仓库把 `.understand-anything` 提交为指向 `.ua` 的符号链接。ZCode 在未启用开发者模式且无管理员权限的 Windows 环境克隆市场仓库时，Git 无法创建该符号链接并返回 `EPERM`，导致市场文件缺失和缓存降级。正确行为应是普通 Windows 用户无需额外权限即可完整检出仓库。

## 2 原因分析

Git 索引将 `.understand-anything` 记录为模式 `120000`，其内容仅为目标 `.ua`。该模式要求克隆端创建文件系统符号链接，而 Windows 默认权限不能保证这一操作成功。现有运行时 `plugins/project-intelligence/scripts/project_intel_lib/graph.py#understand_summary` 已从 `.understand-anything/knowledge-graph.json` 读取图谱，因此问题不在读取逻辑，而在仓库使用符号链接提供规范目录。

## 3 修复方案

### 3.1 改造思路

1. 删除 `.understand-anything -> .ua` 符号链接。
2. 将现有 `.ua` 目录整体迁移为普通的 `.understand-anything` 目录，保留图谱内容和规范读取路径。
3. 在 `plugins/project-intelligence/tests/test_project_intel.py#StabilityAndPackagingTests` 增加仓库结构回归测试，约束规范目录必须为真实目录、旧目录不得存在且图谱仍能被检测。
4. 保持 CLI、图谱解析、npm 包内容和版本不变。

### 3.2 新旧代码对照

旧逻辑：Git 检出 `.understand-anything` 模式 `120000`，再由符号链接跳转到 `.ua`。

新逻辑：Git 直接检出 `.understand-anything/` 下的普通文件，运行时仍读取 `.understand-anything/knowledge-graph.json`。

### 3.3 逻辑变更说明

- Windows 克隆不再执行符号链接创建操作，因此不依赖开发者模式或管理员权限。
- macOS/Linux 读取路径不变，只是路径从符号链接解析改为普通目录访问。
- 回归测试同时检查 `.ua` 不存在和 `detect_graph_sources` 仍报告 Understand-Anything 图谱为 `present`，避免只修复检出却破坏功能。

## 4 影响范围

实际改动是仓库根目录图谱文件的路径迁移，以及 `plugins/project-intelligence/tests/test_project_intel.py` 的稳定性测试。受影响场景为 Git/ZCode 克隆市场仓库和本地读取 Understand-Anything 图谱；CLI 参数、外部接口、业务处理和 npm 安装内容不受影响。

## 5 风险评估

**风险等级**：低

**极端预测**：目录迁移遗漏图谱文件时，Project Intelligence 会把 Understand-Anything 图谱识别为缺失或无效，但不会影响不依赖该图谱的基础 CLI。

**紧急举措**：从 Git 历史恢复 `.ua` 内容并重新放入普通 `.understand-anything` 目录；不恢复符号链接，避免 Windows 再次触发 `EPERM`。
