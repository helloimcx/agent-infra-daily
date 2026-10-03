#!/usr/bin/env python3
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "_data" / "kg" / "nodes.json"
SCHEMA_PATH = ROOT / "_data" / "kg" / "entity_schema.json"
CLAIMS_PATH = ROOT / "_data" / "kg" / "claims.json"
MONOGRAPHS_PATH = ROOT / "_data" / "kg" / "monographs.json"

nodes = json.loads(NODES_PATH.read_text(encoding="utf-8"))
schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
claims = json.loads(CLAIMS_PATH.read_text(encoding="utf-8"))
monographs = json.loads(MONOGRAPHS_PATH.read_text(encoding="utf-8"))

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
    if node.get("content_version") != "v9":
        fail(node_id, "content_version must be v9")

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
        elif isinstance(value, dict):
            if not value:
                fail(node_id, f"required object field is empty: {field_name}")
            else:
                for subkey, subvalue in value.items():
                    if not substantial(subvalue, 10):
                        fail(node_id, f"required object field {field_name}.{subkey} is missing/too thin")
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

claim_ids = set()
node_by_id = {n["id"]: n for n in nodes}
for claim in claims:
    cid = claim.get("id", "<missing-claim-id>")
    if cid in claim_ids:
        errors.append(f"{cid}: duplicate claim id")
    claim_ids.add(cid)
    entity = claim.get("entity")
    if entity not in node_by_id:
        errors.append(f"{cid}: unknown entity {entity}")
    if claim.get("kind") not in ("fact", "analysis", "hypothesis"):
        errors.append(f"{cid}: invalid kind")
    text = claim.get("text")
    if not substantial(text, 20):
        errors.append(f"{cid}: claim text missing or too thin")
    evidence = claim.get("evidence") or []
    if not evidence:
        errors.append(f"{cid}: claim must have evidence")
    for source_id in evidence:
        source = node_by_id.get(source_id)
        if not source:
            errors.append(f"{cid}: unknown evidence {source_id}")
        elif source.get("type") != "Source":
            errors.append(f"{cid}: evidence must reference Source nodes: {source_id}")


# Validate authored technical monographs for every entity.
monograph_by_entity = {}
monograph_paragraphs = {}
minimums = schema.get("monograph", {}).get("minimums", {})

for mono in monographs:
    entity_id = mono.get("entity", "<missing-entity>")
    if entity_id in monograph_by_entity:
        errors.append(f"{entity_id}: duplicate monograph")
    monograph_by_entity[entity_id] = mono

    if entity_id not in node_by_id:
        errors.append(f"{entity_id}: monograph references unknown entity")
        continue

    sections = mono.get("sections") or []
    node_type = node_by_id[entity_id].get("type")
    req = minimums.get(node_type, {})
    min_sections = int(req.get("sections", 3))
    min_chars = int(req.get("characters", 250))

    if len(sections) < min_sections:
        errors.append(f"{entity_id}: monograph has {len(sections)} sections, requires at least {min_sections}")

    section_ids = set()
    total_text = []
    for section in sections:
        sid = section.get("id", "<missing-section-id>")
        if sid in section_ids:
            errors.append(f"{entity_id}: duplicate monograph section id {sid}")
        section_ids.add(sid)

        if not substantial(section.get("title"), 8):
            errors.append(f"{entity_id}/{sid}: section title missing or too thin")

        paragraphs = section.get("paragraphs") or []
        if not paragraphs:
            errors.append(f"{entity_id}/{sid}: no authored paragraphs")
        for idx, paragraph in enumerate(paragraphs):
            if not substantial(paragraph, 25):
                errors.append(f"{entity_id}/{sid}: paragraph {idx+1} too thin")
            normalized = re.sub(r"\s+", "", paragraph)
            total_text.append(normalized)
            previous = monograph_paragraphs.get(normalized)
            if previous:
                errors.append(f"{entity_id}/{sid}: paragraph duplicates {previous}")
            else:
                monograph_paragraphs[normalized] = f"{entity_id}/{sid}"

        for source_id in section.get("evidence") or []:
            source = node_by_id.get(source_id)
            if not source:
                errors.append(f"{entity_id}/{sid}: unknown evidence {source_id}")
            elif source.get("type") != "Source":
                errors.append(f"{entity_id}/{sid}: evidence must reference Source node: {source_id}")

    total_chars = len("".join(total_text))
    if total_chars < min_chars:
        errors.append(f"{entity_id}: monograph too shallow ({total_chars} chars, requires {min_chars})")

for node in nodes:
    if node["id"] not in monograph_by_entity:
        errors.append(f"{node['id']}: missing required technical monograph")

if errors:
    print("Entity content validation FAILED")
    for e in errors:
        print(" -", e)
    sys.exit(1)

print(f"Entity content validation passed: {len(nodes)} authored entities, {len(monographs)} technical monographs")
