# tools

制作期脚本。依赖 Python 3 + Pillow（`python -m pip install pillow`）。

## 1. 生成图集

```bash
# 占位图（没有美术资源时用于跑通链路）
python tools/build_atlas.py placeholder rudeus child assets/characters/overworld/rudeus/child/walk_4dir_3f.png

# 由四方向静态参考图合成（正式流程）
python tools/build_atlas.py from-static assets/characters/references/rudeus/child \
    assets/characters/overworld/rudeus/child/walk_4dir_3f.png
```

`from-static` 会读取 `*_down.png`、`*_left.png`、`*_right.png`、`*_up.png` 四张图，
缩放到 64×96 画布、脚底对齐基线，再拼成 3×4 图集。

> 注意：静态图只能得到「待机 + 起伏式占位行走」。正式 12 帧仍需逐帧绘制后替换同名 PNG。

每次生成都会在 PNG 旁写 `walk_4dir_3f.meta.json`，记录来源模式（`placeholder` / `from-static`），
数据层据此把状态标为 `placeholder` 或 `in_review`。

## 2. 重建数据

```bash
python tools/build_data.py
```

读取 `人物制作包_V1.1/06–08` 的 CSV，输出：

| 文件 | 内容 |
|---|---|
| `data/characters/characters.json` | 44 位人物（43 原著 + 1 原创） |
| `data/characters/appearance_tasks.json` | 29 项外观任务（含 7 项暂缓） |
| `data/characters/npc_templates.json` | 12 种通用 NPC 模板 |
| `data/characters/manifest.json` | 运行时清单，只收录已有图集的外观 |

## 3. 校验

```bash
python tools/validate_data.py
```

检查：ID 唯一、任务引用有效、暂缓名单与约定一致、图集存在且为 192×384 RGBA、
每帧非空、行序正确、全库无 `age` / `birth_year` 等禁用字段。
