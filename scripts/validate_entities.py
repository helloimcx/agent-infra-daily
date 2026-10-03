#!/usr/bin/env python3
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "_data" / "kg" / "nodes.json"
SCHEMA_PATH = ROOT / "_data" / "kg" / "entity_schema.json"

nodes = json.loads(NODES_PATH.read_text(encoding="utf-8"))
schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

errors = []
ids = set()
pages = set()

FORBIDDEN_PHRASES = [
    "在本知识库中作为",
    "已有一手证据或显式分析关系",
    "主要归入",
    "当前图谱显示其直接覆盖/关联",
    "当前已有一手证据或显式分析关系把它连接到",
]

def fail(node_id, message):
    errors.append(f"{node_id}: {message}")

def substantial(value, minimum):
    return isinstance(value, str) and len(re.sub(r"\s+", "", value)) >= minimum

for node in nodes:
    node_id = node.get("id", "<missing-id>")
    if node_id in ids:
        fail(node_id, "duplicate id")
    ids.add(node_id)

    page = node.get("page")
    if not page:
        fail(node_id, "missing page")
    elif page in pages:
        fail(node_id, f"duplicate page: {page}")
    else:
        pages.add(page)
        page_file = ROOT / page.lstrip("/") / "index.html"
        if not page_file.exists():
            fail(node_id, f"missing entity page file: {page_file.relative_to(ROOT)}")

    if node.get("content_mode") != "authored":
        fail(node_id, "content_mode must be authored")
    if node.get("content_version") != "v7":
        fail(node_id, "content_version must be v7")

    if "overview" in node:
        fail(node_id, "legacy overview field is forbidden; use explicitly authored intro")

    intro = node.get("intro")
    why = node.get("why_it_matters")
    if not substantial(intro, 45):
        fail(node_id, "intro is missing or too thin")
    if not substantial(why, 35):
        fail(node_id, "why_it_matters is missing or too thin")

    for field_name in ("intro", "why_it_matters"):
        text = node.get(field_name, "")
        for phrase in FORBIDDEN_PHRASES:
            if phrase in text:
                fail(node_id, f"{field_name} contains forbidden templated phrase: {phrase}")

    node_type = node.get("type")
    required = schema.get("types", {}).get(node_type, [])
    for field_name in required:
        value = node.get(field_name)
        if isinstance(value, list):
            if not value:
                fail(node_id, f"required list field is empty: {field_name}")
        elif not substantial(value, 10):
            fail(node_id, f"missing/too-thin required field: {field_name}")

# Detect accidental duplicate prose across different entities.
for field_name in ("intro", "why_it_matters"):
    seen = {}
    for node in nodes:
        text = re.sub(r"\s+", "", node.get(field_name, ""))
        if not text:
            continue
        if text in seen:
            fail(node["id"], f"{field_name} duplicates {seen[text]}")
        else:
            seen[text] = node["id"]

if errors:
    print("Entity content validation FAILED")
    for e in errors:
        print(" -", e)
    sys.exit(1)

print(f"Entity content validation passed: {len(nodes)} authored entities")
