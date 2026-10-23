# Wuzhi Game

《无职转生》题材的人生 RPG（Godot 4.7）。当前阶段：**人物系统骨架**。

## 快速开始

```bash
# 用编辑器打开
D:\godot\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64.exe --path projects/wuzhi-game

# 直接运行测试场景
godot --path projects/wuzhi-game
```

测试场景里：**WASD / 方向键**移动，靠近 NPC 按 **E** 交互（控制台输出）。

## 工程结构

```
project.godot
assets/characters/
  overworld/<character_id>/<appearance_id>/walk_4dir_3f.png   # 3x4 行走图集
  references/      # 参考图，不进发行包
  portraits/       # 剧情立绘（待做）
  battle/          # 战斗资源（暂缓）
data/characters/
  characters.json         # 44 位人物主表
  appearance_tasks.json   # 29 项外观任务
  npc_templates.json      # 12 种通用 NPC 模板
  manifest.json           # 运行时外观清单（由工具生成，勿手改）
scenes/
  characters/{player,npc_base}.tscn
  dev_tests/character_motion_test.tscn
scripts/
  core/input_setup.gd          # 运行时补输入映射（WASD + 方向键）
  characters/character_visual.gd  # 从 manifest 构建 SpriteFrames
  characters/character_body.gd    # 玩家移动
  characters/npc_controller.gd    # NPC 朝向与交互
  dev/test_world.gd               # 测试地图（32px 网格）
tests/
  smoke_test.gd      # 无窗口冒烟测试
  capture_frame.gd   # 抓取一帧渲染结果
tools/
  build_atlas.py / build_data.py / validate_data.py
```

## 校验命令

```bash
# 数据与图集校验
python tools/validate_data.py

# 引擎内冒烟测试（83 项检查）
godot --headless --path projects/wuzhi-game --script res://tests/smoke_test.gd

# 抓一帧画面到 .screenshots/motion_test.png
godot --path projects/wuzhi-game --script res://tests/capture_frame.gd
```

## 约定

- 角色只认 `character_id` + `appearance_id`；不写死贴图路径。
- **不实现**年龄/时间驱动的外观变化（`age`、`birth_year` 等字段禁止出现）。
- 每帧脚底对齐同一基线；图集 3 列 × 4 行，行序 down/left/right/up。
- 29 项外观任务里 7 项标「暂缓」，不得自动开工。
- 未做实机验收的条目，状态只能写「待验收」。

## 当前状态

- ✅ Godot 工程骨架、玩家/NPC 场景、测试地图
- ✅ 44 人物 / 29 任务 / 12 NPC 模板数据层 + 校验
- ✅ P0 九个外观的**占位图集**（非正式美术）
- ⬜ 正式人物美术（等待参考图）
- ⬜ 立绘、战斗资源
