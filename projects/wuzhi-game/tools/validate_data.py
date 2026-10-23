#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据与资源校验：在提交前检查 ID 唯一性、引用完整性、图集规格与禁用字段。

用法：
    python tools/validate_data.py

退出码 0 = 全部通过；1 = 有错误（错误逐条打印）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "characters"

FORBIDDEN_FIELDS = ["age", "birth_year", "age_up", "growth_stage", "time_to_appearance",
                    "birthday", "age_to_appearance"]
EXPECTED_SUSPENDED = {
    "rudeus_teen", "rudeus_young_adult", "eris_journey", "eris_swordswoman",
    "sylphie_academy", "sylphie_adult", "roxy_travel",
}

errors: list[str] = []
warnings: list[str] = []


def load(name: str):
    path = DATA / name
    if not path.exists():
        errors.append(f"缺少数据文件：{path.relative_to(ROOT)}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{name} 不是合法 JSON：{exc}")
        return None


def find_forbidden(node, path="") -> list[str]:
    hits = []
    if isinstance(node, dict):
        for k, v in node.items():
            here = f"{path}.{k}" if path else k
            if k in FORBIDDEN_FIELDS:
                hits.append(here)
            hits.extend(find_forbidden(v, here))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            hits.extend(find_forbidden(v, f"{path}[{i}]"))
    return hits


def main() -> int:
    chars_doc = load("characters.json")
    tasks_doc = load("appearance_tasks.json")
    npcs_doc = load("npc_templates.json")
    manifest_doc = load("manifest.json")
    if not all([chars_doc, tasks_doc, npcs_doc, manifest_doc]):
        return report()

    chars = chars_doc["characters"]
    tasks = tasks_doc["tasks"]
    npcs = npcs_doc["templates"]

    # 1. ID 唯一
    for label, rows, key in (("人物", chars, "character_id"),
                             ("外观任务", tasks, "task_id"),
                             ("NPC 模板", npcs, "template_id")):
        ids = [r[key] for r in rows]
        dup = {i for i in ids if ids.count(i) > 1}
        if dup:
            errors.append(f"{label} ID 重复：{sorted(dup)}")
        blank = [i for i in ids if not i]
        if blank:
            errors.append(f"{label} 存在空 ID")

    # 2. 引用完整性
    char_ids = {c["character_id"] for c in chars}
    npc_ids = {n["template_id"] for n in npcs}
    known = char_ids | npc_ids
    for t in tasks:
        if t["character_id"] not in known:
            errors.append(f"外观任务 {t['task_id']} 引用了不存在的人物 {t['character_id']}")

    # 3. 暂缓名单
    suspended = {t["task_id"] for t in tasks if "暂缓" in t["status"]}
    if suspended != EXPECTED_SUSPENDED:
        errors.append(f"暂缓名单与约定不一致：多 {sorted(suspended - EXPECTED_SUSPENDED)}，"
                      f"少 {sorted(EXPECTED_SUSPENDED - suspended)}")

    # 4. P0 覆盖
    p0 = {t["task_id"] for t in tasks if t["batch"] == "P0"}
    if len(p0) != 9:
        warnings.append(f"P0 任务数为 {len(p0)}，约定为 9")

    # 5. manifest 与图集
    built = 0
    for cid, app_map in manifest_doc.get("characters", {}).items():
        for aid, entry in app_map.items():
            built += 1
            sprite = entry.get("sprite", {})
            rel = sprite.get("path", "").replace("res://", "")
            png = ROOT / rel
            if not png.exists():
                errors.append(f"清单指向的图集不存在：{rel}")
                continue
            with Image.open(png) as im:
                if im.size != (192, 384):
                    errors.append(f"{rel} 尺寸 {im.size}，应为 (192, 384)")
                if im.mode != "RGBA":
                    errors.append(f"{rel} 模式 {im.mode}，应为 RGBA")
                if im.size == (192, 384):
                    for r in range(4):
                        for c in range(3):
                            frame = im.crop((c * 64, r * 96, (c + 1) * 64, (r + 1) * 96))
                            if frame.getbbox() is None:
                                errors.append(f"{rel} 帧 ({r},{c}) 全透明")
            if sprite.get("columns") != 3 or sprite.get("rows") != 4:
                errors.append(f"{rel} 图集布局应为 3x4")
            if sprite.get("row_order") != ["down", "left", "right", "up"]:
                errors.append(f"{rel} 行序必须为 down/left/right/up")

    # 6. 禁用字段
    for doc_name, doc in (("characters.json", chars_doc),
                          ("appearance_tasks.json", tasks_doc),
                          ("manifest.json", manifest_doc)):
        hits = find_forbidden(doc)
        if hits:
            errors.append(f"{doc_name} 出现禁用字段：{hits[:5]}")

    print(f"人物 {len(chars)} / 外观任务 {len(tasks)} / NPC 模板 {len(npcs)} / 已建图集 {built}")
    return report()


def report() -> int:
    for w in warnings:
        print(f"[warn] {w}")
    for e in errors:
        print(f"[error] {e}")
    if errors:
        print(f"\n校验失败：{len(errors)} 个错误")
        return 1
    print("\n校验通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
