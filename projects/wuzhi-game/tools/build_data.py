#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据层构建：把人物制作包的 CSV 转换成项目 JSON，并扫描已有图集生成运行时 manifest。

输入（默认）：
    人物制作包_V1.1/06_人物主表.csv
    人物制作包_V1.1/07_外观版本任务.csv
    人物制作包_V1.1/08_通用NPC模板.csv
    人物制作包_V1.1/05_角色资源样例.json   （字段参考）

输出：
    data/characters/characters.json
    data/characters/appearance_tasks.json
    data/characters/npc_templates.json
    data/characters/manifest.json           （运行时用，只收录已有图集的条目）

用法：
    python tools/build_data.py [--package ../../人物制作包_V1.1]
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # projects/wuzhi-game
OUT_DIR = ROOT / "data" / "characters"
ASSETS = ROOT / "assets" / "characters" / "overworld"

CHAR_KEYS = {
    "人物ID": "character_id",
    "中文名": "display_name",
    "来源类型": "source_type",
    "资源级别": "resource_level",
    "开发批次": "batch",
    "优先场景/章节": "primary_scenes",
    "游戏定位": "role",
    "外观识别锚点（待按参考图校对）": "appearance_anchors",
    "地图小人": "needs_overworld",
    "对话立绘": "needs_portrait",
    "战斗资源": "needs_battle",
    "外观阶段": "appearance_stages",
    "制作状态": "status",
    "参考确认": "reference_check",
    "参考网址": "reference_url",
    "备注": "notes",
}

TASK_KEYS = {
    "资源任务ID": "task_id",
    "人物ID": "character_id",
    "人物": "display_name",
    "外观版本": "appearance_id",
    "故事/使用阶段": "stage_label",
    "批次": "batch",
    "目标素材": "target_assets",
    "视觉核对重点": "visual_check",
    "进度": "status",
    "输出路径": "output_path",
    "验收结果": "acceptance",
}

NPC_KEYS = {
    "模板ID": "template_id",
    "模板名称": "display_name",
    "资源级别": "resource_level",
    "开发批次": "batch",
    "优先地区": "regions",
    "外观剪影": "silhouette",
    "可替换部件": "swappable_parts",
    "主要道具": "props",
    "地图小人": "needs_overworld",
    "立绘": "needs_portrait",
    "战斗": "needs_battle",
    "状态": "status",
    "备注": "notes",
}


def read_csv(path: Path, mapping: dict) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for row in rows:
        rec = {}
        for cn, key in mapping.items():
            rec[key] = (row.get(cn) or "").strip()
        if rec.get(list(mapping.values())[0]):
            out.append(rec)
    return out


def scan_atlases() -> dict:
    """扫描 assets/characters/overworld/<cid>/<aid>/walk_4dir_3f.png。"""
    found = {}
    if not ASSETS.exists():
        return found
    for png in ASSETS.glob("*/*/walk_4dir_3f.png"):
        cid, aid = png.parent.parent.name, png.parent.name
        meta_path = png.with_suffix(".meta.json")
        meta = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                meta = {}
        found.setdefault(cid, {})[aid] = {
            "png": png,
            "mode": meta.get("mode", "unknown"),
        }
    return found


def build_manifest(characters: list[dict]) -> dict:
    by_id = {c["character_id"]: c for c in characters}
    atlases = scan_atlases()
    entries: dict = {}
    for cid, appearances in sorted(atlases.items()):
        info = by_id.get(cid, {})
        for aid, data in sorted(appearances.items()):
            rel = data["png"].relative_to(ROOT).as_posix()
            status = "placeholder" if data["mode"] == "placeholder" else "in_review"
            entries.setdefault(cid, {})[aid] = {
                "display_name": info.get("display_name", cid),
                "source_type": info.get("source_type", ""),
                "batch": info.get("batch", ""),
                "status": status,
                "sprite": {
                    "path": "res://" + rel,
                    "frame_size": [64, 96],
                    "columns": 3,
                    "rows": 4,
                    "row_order": ["down", "left", "right", "up"],
                    "col_order": ["left_step", "neutral", "right_step"],
                    "walk_sequence": [1, 0, 1, 2],
                    "fps": 7,
                    "ground_anchor": "foot_baseline",
                    "texture_filter": "nearest",
                },
                "portrait": {
                    "base_path": f"res://assets/characters/portraits/{cid}/{aid}/",
                    "expressions": ["normal", "smile", "angry", "surprised"],
                    "status": "pending",
                },
                "battle": {
                    "base_path": f"res://assets/characters/battle/{cid}/{aid}/",
                    "status": "deferred",
                },
                "quality_gates": [
                    "reference_checked",
                    "same_stage_outfit",
                    "four_directions_consistent",
                    "equal_frame_canvas",
                    "foot_anchor_aligned",
                    "in_godot_tested",
                ],
            }
    return {
        "schema_version": "1.1-static-appearance",
        "generated_by": "tools/build_data.py",
        "time_growth": {
            "enabled": False,
            "auto_age_increase": False,
            "auto_appearance_switch": False,
            "age_based_events": False,
        },
        "characters": entries,
    }


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", default="../../人物制作包_V1.1")
    ns = ap.parse_args()
    pkg = (ROOT / ns.package).resolve()

    characters = read_csv(pkg / "06_人物主表.csv", CHAR_KEYS)
    tasks = read_csv(pkg / "07_外观版本任务.csv", TASK_KEYS)
    npcs = read_csv(pkg / "08_通用NPC模板.csv", NPC_KEYS)

    write_json(OUT_DIR / "characters.json", {
        "schema_version": "1.1",
        "source": "人物制作包_V1.1/06_人物主表.csv",
        "count": len(characters),
        "characters": characters,
    })
    write_json(OUT_DIR / "appearance_tasks.json", {
        "schema_version": "1.1",
        "source": "人物制作包_V1.1/07_外观版本任务.csv",
        "count": len(tasks),
        "tasks": tasks,
    })
    write_json(OUT_DIR / "npc_templates.json", {
        "schema_version": "1.1",
        "source": "人物制作包_V1.1/08_通用NPC模板.csv",
        "count": len(npcs),
        "templates": npcs,
    })
    manifest = build_manifest(characters)
    write_json(OUT_DIR / "manifest.json", manifest)

    built = sum(len(v) for v in manifest["characters"].values())
    print(f"characters={len(characters)} tasks={len(tasks)} npcs={len(npcs)} "
          f"manifest_entries={built}")


if __name__ == "__main__":
    main()
