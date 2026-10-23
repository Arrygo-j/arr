#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图集构建工具：把四方向静态图或占位图，输出成 3x4 的行走图集。

用法：
    python build_atlas.py placeholder <character_id> <appearance_id> <out_png>
    python build_atlas.py from-static <参考图目录> <out_png> [--frame 64x96]

规则（来自人物制作包 V1.1）：
    3 列 x 4 行；行序 down/left/right/up；列序 左脚/中立/右脚；
    每帧同画布；脚底对齐同一基线；透明背景。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

FW, FH = 64, 96
GROUND = FH - 4          # 脚底基线（距画布底部 4px 留白）
DIRS = ["down", "left", "right", "up"]
COL_NAMES = ["left_step", "neutral", "right_step"]

# 占位用配色：hair, skin, cloth, accent
PALETTES = {
    "rudeus":            ("#6b4a2f", "#f0c9a8", "#4a6fa5", "#d8d2c0"),
    "eris":              ("#c0392b", "#f3d0b8", "#8e4a5a", "#e0c070"),
    "roxy":              ("#3f7fd0", "#f2d6c0", "#e8e8f2", "#6a5acd"),
    "sylphie":           ("#4caf6d", "#f5dcc6", "#d9d2c3", "#8fa87a"),
    "player_custom":     ("#2f2f38", "#f0c9a8", "#2e8b57", "#c8b070"),
    "npc_guard":         ("#8a8f98", "#e8c3a4", "#5a6470", "#3f4a56"),
    "npc_merchant":      ("#5a4632", "#eec6a6", "#b5651d", "#8a5a2a"),
    "npc_villager_m":    ("#6a5a44", "#e8c3a4", "#7a6a53", "#9a8a6a"),
    "npc_villager_f":    ("#7a5a3a", "#f0cdb0", "#a05c7a", "#c08a9a"),
}
DEFAULT_PALETTE = ("#555555", "#e8c3a4", "#777777", "#999999")


def _shade(hex_color: str, factor: float) -> tuple[int, int, int, int]:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return (r, g, b, 255)


def draw_frame(direction: str, col: int, palette) -> Image.Image:
    """画一帧占位小人。col: 0 左脚, 1 中立, 2 右脚。"""
    hair, skin, cloth, accent = palette
    im = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)

    side = direction in ("left", "right")
    back = direction == "up"
    cx = FW // 2

    head_r = 9
    head_cy = GROUND - 50
    torso_top = head_cy + head_r - 1
    torso_bottom = GROUND - 20
    shoulder = 5 if side else 9

    # 迈步相位：-1 左脚前, 0 中立, +1 右脚前
    phase = [(-1), 0, 1][col]

    # 双腿
    leg_w = 5
    for i, sign in enumerate((-1, 1)):      # sign=-1 左腿, +1 右腿
        dx = cx + sign * 4
        step = -phase * sign                   # 与迈步相位相反
        if side:
            dx += step * 4
            y_bottom = GROUND - (2 if step > 0 else 0)
        else:
            y_bottom = GROUND - (2 if step > 0 else 0)
            dx += step * 1
        dr.rectangle(
            [dx - leg_w // 2, torso_bottom - 4, dx + leg_w // 2, y_bottom],
            fill=_shade(accent, 0.75),
        )
        # 鞋
        dr.rectangle(
            [dx - leg_w // 2 - 1, y_bottom - 3, dx + leg_w // 2 + 1, y_bottom],
            fill=(50, 44, 40, 255),
        )

    # 躯干
    if side:
        dr.rounded_rectangle(
            [cx - 6, torso_top, cx + 6, torso_bottom + 2], radius=3,
            fill=_shade(cloth, 1.0),
        )
    else:
        dr.rounded_rectangle(
            [cx - shoulder, torso_top, cx + shoulder, torso_bottom + 2], radius=3,
            fill=_shade(cloth, 1.0),
        )

    # 手臂（侧视只画近侧一条，方向更易辨认）
    arm_y0 = torso_top + 3
    arm_y1 = torso_bottom - 3
    arm_signs = (1,) if side else (-1, 1)
    for sign in arm_signs:
        ax = cx + sign * (shoulder + 1)
        swing = -phase * sign * (2 if side else 3)
        if side:
            ax += swing
            dr.rectangle([ax - 2, arm_y0, ax + 2, arm_y1], fill=_shade(cloth, 0.8))
        else:
            dr.rectangle([ax - 2, arm_y0 + swing, ax + 2, arm_y1 + swing],
                         fill=_shade(cloth, 0.8))
        # 手
        dr.rectangle([ax - 2, arm_y1 + swing - 1, ax + 2, arm_y1 + swing + 1],
                     fill=skin)

    # 脖子 + 头（侧视时头部略向朝向偏移，剪影更好认）
    hx = cx + (2 if direction == "right" else -2 if direction == "left" else 0)
    dr.rectangle([cx - 3, head_cy + head_r - 3, cx + 3, torso_top + 1], fill=skin)
    dr.ellipse([hx - head_r, head_cy - head_r, hx + head_r, head_cy + head_r],
               fill=skin)

    # 头发
    if back:
        dr.ellipse([hx - head_r, head_cy - head_r, hx + head_r, head_cy + 2],
                   fill=hair)
    elif side:
        dr.ellipse([hx - head_r, head_cy - head_r, hx + head_r, head_cy + 1],
                   fill=hair)
        drift = -2 if direction == "left" else 2
        dr.ellipse([hx - head_r + drift, head_cy - 4, hx + head_r + drift,
                    head_cy + 6], fill=hair)
    else:
        dr.pieslice([hx - head_r, head_cy - head_r, hx + head_r, head_cy + head_r],
                    180, 360, fill=hair)

    # 五官（背影不画）
    if not back:
        eye_y = head_cy
        if side:
            ex = hx + (-3 if direction == "left" else 3)
            dr.rectangle([ex - 1, eye_y - 1, ex + 1, eye_y + 1], fill=(40, 34, 30, 255))
        else:
            for sign in (-1, 1):
                ex = hx + sign * 4
                dr.rectangle([ex - 1, eye_y - 1, ex + 1, eye_y + 1],
                             fill=(40, 34, 30, 255))

    # 洛琪希的帽子（识别点）
    if palette is PALETTES["roxy"]:
        dr.polygon([(hx, head_cy - head_r - 8), (hx - 12, head_cy - 4),
                    (hx + 12, head_cy - 4)], fill=_shade(cloth, 0.9))
        dr.ellipse([hx - 13, head_cy - 7, hx + 13, head_cy + 1], fill=_shade(cloth, 0.9))

    return im


def build_placeholder(character_id: str, appearance_id: str, out_png: Path) -> dict:
    palette = PALETTES.get(character_id, DEFAULT_PALETTE)
    atlas = Image.new("RGBA", (FW * 3, FH * 4), (0, 0, 0, 0))
    for row, d in enumerate(DIRS):
        for col in range(3):
            atlas.paste(draw_frame(d, col, palette), (col * FW, row * FH))
    out_png.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(out_png)
    result = {"mode": "placeholder", "path": str(out_png), "size": atlas.size,
              "character_id": character_id, "appearance_id": appearance_id}
    write_meta(out_png, result)
    return result


def write_meta(out_png: Path, payload: dict) -> None:
    """在 PNG 旁写一份来源元数据，供数据层判断状态是占位还是正式。"""
    meta = dict(payload)
    meta["generated_at"] = __import__("datetime").datetime.now().isoformat(timespec="seconds")
    out_png.with_suffix(".meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def build_from_static(ref_dir: Path, out_png: Path) -> dict:
    """把 down/left/right/up 四张静态图合成 3x4 图集。

    静态图只能做待机 + 占位行走（中立帧上下起伏 1px），
    正式 12 帧仍需逐帧绘制后替换同名文件。
    """
    statics = {}
    for d in DIRS:
        candidates = sorted(ref_dir.glob(f"*_{d}.png"))
        if not candidates:
            raise SystemExit(f"缺少方向 {d} 的参考图：{ref_dir}/*_{d}.png")
        statics[d] = Image.open(candidates[0]).convert("RGBA")

    atlas = Image.new("RGBA", (FW * 3, FH * 4), (0, 0, 0, 0))
    for row, d in enumerate(DIRS):
        src = statics[d]
        scale = min(FW / src.width, FH / src.height)
        w, h = max(1, int(src.width * scale)), max(1, int(src.height * scale))
        resized = src.resize((w, h), Image.LANCZOS)
        # 脚底对齐
        base = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
        base.alpha_composite(resized, ((FW - w) // 2, GROUND - h))
        for col in range(3):
            frame = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
            dy = 0 if col == 1 else -1
            frame.alpha_composite(base, (0, dy))
            atlas.paste(frame, (col * FW, row * FH))
    out_png.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(out_png)
    result = {"mode": "from-static", "path": str(out_png), "size": atlas.size}
    write_meta(out_png, result)
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["placeholder", "from-static"])
    ap.add_argument("args", nargs="+")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    ns = ap.parse_args()

    if ns.mode == "placeholder":
        cid, aid, out = ns.args[0], ns.args[1], Path(ns.args[2])
        result = build_placeholder(cid, aid, out)
    else:
        ref_dir, out = Path(ns.args[0]), Path(ns.args[1])
        result = build_from_static(ref_dir, out)

    if ns.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"ok: {result['path']} {result['size'][0]}x{result['size'][1]}")


if __name__ == "__main__":
    main()
