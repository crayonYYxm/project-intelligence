# 复盘记录：新增活动页面预填模板预览与用户指引优化

> feature-id: 2026-07-14-新增活动页面预填模板预览与用户指引优化
> 复盘日期：2026-07-15
> 关联文档：[prd.md](./prd.md) | [plan/index.md](./plan/index.md)
> 复盘范围：本次 feature 在联调与测试阶段暴露的“示例态/真实态切换不彻底”“指引触发与重放链路不一致”等问题，以及对应的修复过程与经验沉淀

## 1. 背景与目标回顾

本 feature 由两个前端入口共同承担：

1. **新增活动页**：保留样例预填的教学价值，但把“样例态”和“正式录入态”彻底拆开，通过 `submitBlockers` / `canSubmit` 收口提交规则，并提供“重置”一键回到干净表单。
2. **全局用户指引**：把“首次登录自动触发”与“右下角 ? 手动重放”两类场景显式建模，靠 sessionStorage 贯通跨页面连续指引，同时保证非首次登录、侧边菜单进入时不自动打断。

PRD 与设计文档把目标和决策写得很清晰，落地阶段的功能主干也已实现。本次复盘聚焦的是**联调测试阶段暴露的一组“态切换不彻底”瑕疵**——它们都不改变设计方向，而是实现细节上对“示例态残留”的清理不够干净。

## 2. 需求落地的四条核心规则

为统一认知，测试阶段把需求重新收敛成四条可验收规则：

1. **首次登录**：有用户指引弹窗；新增活动页带示例假数据；点击“重置”清空全部假数据并隐藏重置按钮。
2. **已登录过（接口返回 false）**：无用户指引弹窗；新增活动页示例数据全部清空。
3. **点击右下角 ?**：弹出用户指引，进入对应模块及二级页面（尤其是新增活动页）都保留用户指引。
4. **已登录过、侧边菜单进入有指引的页面**：不自动展示页面指引。

后续所有问题都围绕“这四条规则是否真正成立”展开验证。

## 3. 暴露的问题与修复过程

### 问题一：`:initial` 用挂载次数判断示例态，导致已登录用户仍自动选中流程模型

- **现象**：已登录用户进入新增活动页时，`ProcessModelConfig` 仍自动选中第一个流程模型和任务类型，并展示样例接单人，违反规则 2、规则 4。
- **根因**：`ProcessModelConfig` 的 `:initial` 绑定的是 `processModelConfigKey === 0`，只在首次挂载时为 `true`，与登录状态完全无关。它表达的是“第几次挂载”，而非“是否处于示例展示模式”。
- **修复**：新增 `isSampleMode` 数据标志，由 `applySampleDataPolicy` 根据登录/重放语义写入；`:initial` 改绑 `isSampleMode`。`ProcessModelConfig` 内部的“默认选中第一个模型”“默认选中第一个任务类型”两个分支都已加 `this.initial` 守卫，与该标志联动。
- **文件**：[insertActivityDetail.vue](../../../src/views/workflow/work/insertActivityDetail.vue)、[ProcessModelConfig.vue](../../../src/views/workflow/work/components/ProcessModelConfig.vue)

### 问题二：清空分支只清基本信息字段，流程模型残留导致重置/提交卡片仍显示

- **现象**：已登录用户进入新增活动页时，基本信息已清空，但“重置”按钮和“提交前请先完成”提示卡片仍显示。
- **根因**：`applySampleDataPolicy` 的清空分支只清了 `formData` 的基本信息字段，**没有清 `processModelConfig`，也没有 bump `processModelConfigKey` 重新挂载子组件**。由于该页受 keep-alive 缓存，首次登录场景残留下来的 `processModelConfig.modelId` 仍存在，`isFormClean` 因 `modelId` 非空而为 false，于是重置按钮和提示卡片继续显示。
- **修复**：清空分支判据由 `hasSampleBasicInfo` 改为 `!hasRealUserData`，并调用 `resetFormSilently()` 统一彻底重置（同步清 `processModelConfig`、bump key 重新挂载）。
- **文件**：[insertActivityDetail.vue](../../../src/views/workflow/work/insertActivityDetail.vue)

### 问题三：重放 session 残留 + firstLoginResult 取反不一致，导致部分页面指引丢失

- **现象**：联调时为方便测试把 `if (isFirst)` 临时改成 `if (!isFirst)`，结果出现“活动管理列表、新增活动等二级页面没有用户指引，但待办却有指引”。
- **根因**：两层叠加。
  1. 只反转了 `if` 分支，但 `this.firstLoginResult = isFirst` 没改，`firstLoginResult` 仍为 false，与“走了首次登录分支”自相矛盾，`checkModuleGuide` 的守卫 `!firstLoginResult && !isReplaySessionActive()` 直接 return，本不该弹指引。
  2. 待办仍能弹，说明 `isReplaySessionActive()` 为 true——即此前点过右下角 ? 重放测试，sessionStorage 里残留了 `user_guide_replay_active=1` 和已展示模块列表。登出时 `storeToken` watch 只清了 `user_guide_first_login`，**没清重放相关 sessionStorage**，导致重放会话跨登录仍然活着。于是：activity / insertActivity 已在 shown 列表 → 跳过；todo 未在 shown 列表 → 弹指引。
- **修复**：还原 `if (isFirst)`，改用“临时强制 `isFirst = true`”方式模拟首次登录测试；测试前清理 sessionStorage 残留。同时识别出登出未清重放 session 的真实小瑕疵（见第 5 节待办）。
- **文件**：[UserGuide/index.vue](../../../src/components/UserGuide/index.vue)

### 问题四：重置后任务类型仍显示样例“双线”

- **现象**：点击“重置”后，任务类型区仍显示示例值“双线”。
- **根因**：`ProcessModelConfig.loadTaskTypes` 在接口返回空时硬编码了样例任务类型 `{ typeCode: "SHUANGXIAN", typeName: "双线" }` 作为兜底，且**该兜底不受 `this.initial` 控制**。重置后以 `initial=false` 重新挂载时，仍会注入样例“双线”。
- **修复**：把样例兜底也限制在 `this.initial` 下，非示例模式保持为空，重置后任务类型区走 `emptyHint`（“请先选择任务类型”）兜底。
- **文件**：[ProcessModelConfig.vue](../../../src/views/workflow/work/components/ProcessModelConfig.vue)

## 4. 关键设计决策复盘

### 决策 A：示例态判据从“字段值匹配”升级为“是否有真实数据”

最初用 `hasSampleBasicInfo`（字段值是否等于 `SAMPLE_BASIC_INFO` 或以 `【示例】` 开头）作为清空判据。这在“整页都是示例”时有效，但无法覆盖“基本信息已清、流程模型仍残留”这类**中间状态**，导致漏清。

引入 `hasRealUserData`（识别用户真实填写的、非 `【示例】`、非样例模板的内容）后，清空判据变成“无真实数据则彻底重置”，覆盖了初始示例值、首次登录残留、中间态残留三种情况。`customerType` 因示例值 `"2"` 与合法真实值无法区分，刻意不纳入判断——这是权衡后的边界取舍。

**经验**：态切换的判据要面向“目标态”而非“当前态字段值”。用“是否已有真实数据”作为分水岭，比逐字段比对示例值更稳健。

### 决策 B：彻底重置复用 resetFormSilently，而非就地赋空

清空分支没有重复写一遍“清字段 + 清模型 + bump key”，而是直接调用 `resetFormSilently()`。好处是重置（用户主动点）与清空（自动态切换）共用同一条回收链路，避免两套清空逻辑长期漂移。

**经验**：“自动态切换”和“用户主动重置”本质都是回到初始干净态，应该共享同一个回收函数，而不是各写一份。

### 决策 C：子组件示例行为必须由父级“示例模式”标志驱动

`ProcessModelConfig` 内部有多个示例行为（默认选第一个模型、默认选第一个任务类型、接口空时塞样例“双线”），最初有的受 `initial` 控制、有的没受控制，导致重置后部分示例仍泄漏。

**经验**：子组件内凡是“仅用于教学预览”的行为，必须全部挂到同一个由父级下发的示例模式开关上，不能有遗漏，否则重置永远清不干净。这次是逐个排查才补齐的，说明这类开关缺乏集中约束，容易漏。

## 5. 仍待处理 / 后续行动项

| 项 | 说明 | 优先级 |
|---|---|---|
| 登出未清理重放 session | `storeToken` watch 的登出分支只清了 `user_guide_first_login`，未清 `user_guide_replay_active` / `user_guide_replay_shown_v1`。测试时易踩残留坑，也是真实泄漏 bug（重放状态会跨登录保留）。建议补清除。 | 高 |
| 测试方式规范 | 联调时通过“反转 if 分支”模拟首次登录会破坏 `firstLoginResult` 语义一致性，导致误判。建议统一用“接口 mock 返回 true”或“临时强制 isFirst=true（连 firstLoginResult 一起改）”方式，并在测试文档中固化。 | 中 |
| 示例模式开关集中化 | `ProcessModelConfig` 内多个示例分支散落在不同方法，靠人工逐个补 `initial` 守卫。后续可将示例行为收敛为一个 computed 或 mixin，避免新增示例分支时漏挂开关。 | 中 |
| spec 文档补齐 | 设计文档已知限制中提到本 feature 尚无独立 spec，态切换规则、保留字段边界目前散落在代码注释里。建议补一份稳定 spec。 | 中 |
| replay session 步骤级恢复 | 当前 replay 只记录模块是否展示过，不记录步骤级进度，中断后只能从模块头重放。若需要细粒度恢复，可将步骤索引写入 sessionStorage。 | 低 |

## 6. 经验沉淀

1. **“态切换”类需求要穷举中间状态**：keep-alive 缓存 + 多处示例数据注入，会产生“部分清空、部分残留”的中间态。设计与测试时不能只验证“全示例”和“全空”两头，必须覆盖“基本信息已清、流程模型仍残留”这类过渡态。本次四条核心规则中，规则 2 的“示例数据全部清空”之所以反复返工，正是因为中间态清理不彻底。

2. **跨页面会话状态要随生命周期完整清理**：sessionStorage 的重放状态如果不在登出时清除，会跨登录泄漏，制造“不可复现”的测试假象。任何会话级状态都应配套登出/登入的清理与重置点。

3. **判据要面向目标态、行为开关要集中收口**：态切换判据用“是否有真实数据”比“字段值是否等于示例”更稳健；子组件的示例行为必须统一挂到父级下发的示例模式开关，不能散落。

4. **测试时的临时改动要连语义一起改**：为测试反转某个分支时，必须同步检查所有依赖该标志的派生状态（如 `firstLoginResult`），否则会出现“分支走了、守卫却拦住”的自相矛盾，把测试引向错误方向。

5. **自动态切换与用户主动重置应共享回收链路**：避免两套清空逻辑长期漂移，`resetFormSilently` 作为唯一回收出口是本次能快速收敛的关键。

## 7. 涉及代码索引

- 新增活动页主文件：[src/views/workflow/work/insertActivityDetail.vue](../../../src/views/workflow/work/insertActivityDetail.vue)
  - `isSampleMode` 数据标志
  - `hasRealUserData` 计算属性
  - `applySampleDataPolicy` 态切换策略
  - `resetFormSilently` 统一回收函数
- 流程模型配置组件：[src/views/workflow/work/components/ProcessModelConfig.vue](../../../src/views/workflow/work/components/ProcessModelConfig.vue)
  - `initial` prop 驱动的示例行为收口
  - `loadProcessModels` / `loadTaskTypes` 的示例兜底守卫
- 全局用户指引：[src/components/UserGuide/index.vue](../../../src/components/UserGuide/index.vue)
  - `checkGlobalGuide` 首次登录语义
  - `checkModuleGuide` 触发守卫与重放会话判断
  - 登出清理（待补全重放 session）
- 首次登录接口：[src/api/login.js](../../../src/api/login.js)
