#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import getpass
import hashlib
import json
import math
import os
import re
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape as xml_escape
from xml.etree import ElementTree as ET


XHTML_NS = "http://www.w3.org/1999/xhtml"
OPF_NS = "http://www.idpf.org/2007/opf"
DC_NS = "http://purl.org/dc/elements/1.1/"
CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"
XML_NS = "http://www.w3.org/XML/1998/namespace"

COMMON_FRAGMENT_NS = {
    "epub": "http://www.idpf.org/2007/ops",
    "xlink": "http://www.w3.org/1999/xlink",
    "svg": "http://www.w3.org/2000/svg",
    "mathml": "http://www.w3.org/1998/Math/MathML",
}

CANDIDATE_BLOCK_TAGS = {
    "p",
    "li",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "figcaption",
    "caption",
    "td",
    "th",
    "dt",
    "dd",
    "blockquote",
}


class EpubTranslateError(RuntimeError):
    pass


class OpenAIRequestError(EpubTranslateError):
    pass


def _localname(tag: str) -> str:
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _namespace(tag: str) -> str | None:
    if tag.startswith("{"):
        return tag[1:].split("}", 1)[0]
    return None


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now_slug() -> str:
    return time.strftime("%Y%m%d-%H%M%S", time.localtime())


def _skill_paths() -> tuple[Path, Path]:
    skill_root = Path(__file__).resolve().parents[1]
    # Expected layout: <project_root>/.codex/skills/<skill-name>
    # project_root is three levels above <skill-name>.
    project_root = skill_root.parents[2]
    return skill_root, project_root


def _default_skill_data_dir() -> Path:
    _, project_root = _skill_paths()
    return project_root / ".skills-data" / "epub-translate"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _q(ns: str, tag: str) -> str:
    return f"{{{ns}}}{tag}"


def _parse_xml(path: Path) -> ET.Element:
    try:
        return ET.fromstring(path.read_bytes())
    except ET.ParseError as e:
        raise EpubTranslateError(f"Failed to parse XML: {path}: {e}") from e


def _unzip_epub(epub_path: Path, out_dir: Path) -> None:
    with zipfile.ZipFile(epub_path, "r") as zf:
        zf.extractall(out_dir)


def _get_container_rootfile_paths(container_xml_path: Path) -> list[str]:
    root = _parse_xml(container_xml_path)
    rootfiles = []
    for rootfile in root.findall(f".//{_q(CONTAINER_NS, 'rootfile')}"):
        full_path = rootfile.attrib.get("full-path")
        if full_path:
            rootfiles.append(full_path)
    if not rootfiles:
        raise EpubTranslateError("container.xml has no rootfile full-path entries")
    return rootfiles


@dataclasses.dataclass(frozen=True)
class OpfPackage:
    opf_path: str  # container-relative POSIX path
    opf_dir: str  # container-relative POSIX dir
    manifest: dict[str, dict[str, str]]
    spine: list[str]
    nav_id: str | None


def _parse_opf(opf_fs_path: Path, opf_container_path: str) -> OpfPackage:
    root = _parse_xml(opf_fs_path)

    manifest: dict[str, dict[str, str]] = {}
    for item in root.findall(f".//{_q(OPF_NS, 'manifest')}/{_q(OPF_NS, 'item')}"):
        item_id = item.attrib.get("id")
        href = item.attrib.get("href")
        media_type = item.attrib.get("media-type")
        if not item_id or not href or not media_type:
            continue
        manifest[item_id] = {
            "href": href,
            "media_type": media_type,
            "properties": item.attrib.get("properties", ""),
        }

    spine: list[str] = []
    for itemref in root.findall(f".//{_q(OPF_NS, 'spine')}/{_q(OPF_NS, 'itemref')}"):
        idref = itemref.attrib.get("idref")
        if idref:
            spine.append(idref)

    nav_id: str | None = None
    for item_id, meta in manifest.items():
        props = meta.get("properties", "")
        if "nav" in props.split():
            nav_id = item_id
            break

    opf_dir = str(Path(opf_container_path).parent.as_posix())
    return OpfPackage(
        opf_path=opf_container_path,
        opf_dir="." if opf_dir == "" else opf_dir,
        manifest=manifest,
        spine=spine,
        nav_id=nav_id,
    )


def _iter_xhtml_docs(package: OpfPackage, scope: str, include_nav: bool) -> list[tuple[str, str]]:
    ids: list[str] = []
    if scope == "spine":
        ids.extend(package.spine)
    elif scope == "all-xhtml":
        ids.extend([i for i, meta in package.manifest.items() if meta.get("media_type") == "application/xhtml+xml"])
    else:
        raise EpubTranslateError(f"Unknown scope: {scope}")

    if include_nav and package.nav_id and package.nav_id not in ids:
        ids.append(package.nav_id)

    seen: set[str] = set()
    ordered: list[str] = []
    for item_id in ids:
        if item_id in seen:
            continue
        seen.add(item_id)
        ordered.append(item_id)

    docs: list[tuple[str, str]] = []
    for item_id in ordered:
        meta = package.manifest.get(item_id)
        if not meta:
            continue
        if meta.get("media_type") != "application/xhtml+xml":
            continue
        href = meta.get("href")
        if not href:
            continue
        container_path = str((Path(package.opf_dir) / href).as_posix())
        docs.append((item_id, container_path))
    return docs


def _inner_xml(element: ET.Element) -> str:
    parts: list[str] = []
    if element.text:
        parts.append(xml_escape(element.text))
    for child in list(element):
        parts.append(ET.tostring(child, encoding="unicode", method="xml"))
    return "".join(parts)


def _markup_tokens_for_children(parent: ET.Element) -> list[list[Any]]:
    tokens: list[list[Any]] = []

    def rec(el: ET.Element) -> None:
        attrs = sorted(el.attrib.items(), key=lambda kv: kv[0])
        tokens.append(["start", el.tag, attrs])
        for child in list(el):
            rec(child)
        tokens.append(["end", el.tag])

    for child in list(parent):
        rec(child)
    return tokens


def _markup_hash_for_children(parent: ET.Element) -> str:
    tokens = _markup_tokens_for_children(parent)
    payload = json.dumps(tokens, ensure_ascii=False, separators=(",", ":"))
    return _sha256(payload)


def _normalized_text(el: ET.Element) -> str:
    text = " ".join("".join(el.itertext()).split())
    return text.strip()


def _xpath_for_element(root: ET.Element, element: ET.Element) -> str:
    parent_map: dict[ET.Element, ET.Element] = {child: parent for parent in root.iter() for child in parent}
    segments: list[str] = []
    current: ET.Element | None = element
    while current is not None:
        parent = parent_map.get(current)
        name = _localname(current.tag)
        if parent is None:
            idx = 1
        else:
            siblings = [c for c in list(parent) if _localname(c.tag) == name and _namespace(c.tag) == _namespace(current.tag)]
            idx = siblings.index(current) + 1
        segments.append(f"{name}[{idx}]")
        current = parent
    segments.reverse()
    return "/" + "/".join(segments)


_XPATH_SEG_RE = re.compile("^(?P<name>[A-Za-z0-9_.:-]+)\\[(?P<idx>\\d+)\\]$")


def _find_by_xpath(root: ET.Element, xpath: str) -> ET.Element:
    if not xpath.startswith("/"):
        raise EpubTranslateError(f"Invalid xpath (must start with /): {xpath}")
    parts = [p for p in xpath.split("/") if p]
    current = root
    for part in parts[1:]:  # skip root segment
        match = _XPATH_SEG_RE.match(part)
        if not match:
            raise EpubTranslateError(f"Invalid xpath segment: {part} in {xpath}")
        name = match.group("name")
        idx = int(match.group("idx"))
        matching = [c for c in list(current) if _namespace(c.tag) == XHTML_NS and _localname(c.tag) == name]
        if idx < 1 or idx > len(matching):
            raise EpubTranslateError(f"xpath not found: {xpath} (missing {name}[{idx}])")
        current = matching[idx - 1]
    return current


def _select_leaf_block_elements(body: ET.Element) -> list[ET.Element]:
    leaf_ids: set[int] = set()

    def has_candidate_desc(el: ET.Element) -> bool:
        found = False
        for child in list(el):
            if has_candidate_desc(child):
                found = True
        is_candidate = _namespace(el.tag) == XHTML_NS and _localname(el.tag) in CANDIDATE_BLOCK_TAGS
        if is_candidate and not found:
            leaf_ids.add(id(el))
            return True
        return found or is_candidate

    has_candidate_desc(body)
    ordered: list[ET.Element] = []
    for el in body.iter():
        if id(el) in leaf_ids:
            ordered.append(el)
    return ordered


def _build_fragment_wrapper(fragment: str) -> str:
    xmlns_bits = [f'xmlns="{XHTML_NS}"']
    for prefix, uri in COMMON_FRAGMENT_NS.items():
        xmlns_bits.append(f'xmlns:{prefix}="{uri}"')
    xmlns = " ".join(xmlns_bits)
    return f"<wrap {xmlns}>{fragment}</wrap>"


def _parse_fragment_children(fragment: str) -> ET.Element:
    wrapper_xml = _build_fragment_wrapper(fragment)
    try:
        return ET.fromstring(wrapper_xml)
    except ET.ParseError as e:
        raise EpubTranslateError(f"Translated fragment is not well-formed XML: {e}") from e


def _apply_fragment_inner_html(target: ET.Element, translated_inner_html: str) -> None:
    wrapper = _parse_fragment_children(translated_inner_html)
    target.text = wrapper.text
    for child in list(target):
        target.remove(child)
    for child in list(wrapper):
        target.append(child)


def _update_xhtml_lang(xhtml_root: ET.Element, target_lang: str) -> None:
    if _namespace(xhtml_root.tag) != XHTML_NS or _localname(xhtml_root.tag) != "html":
        return
    xhtml_root.attrib[f"{{{XML_NS}}}lang"] = target_lang
    xhtml_root.attrib["lang"] = target_lang


def _update_opf_lang(opf_root: ET.Element, target_lang: str) -> None:
    metadata = opf_root.find(f".//{_q(OPF_NS, 'metadata')}")
    if metadata is None:
        return

    langs = metadata.findall(f".//{_q(DC_NS, 'language')}")
    if langs:
        langs[0].text = target_lang
    else:
        dc_lang = ET.Element(_q(DC_NS, "language"))
        dc_lang.text = target_lang
        metadata.append(dc_lang)

    opf_root.attrib[f"{{{XML_NS}}}lang"] = target_lang


def _write_xml(path: Path, root: ET.Element) -> None:
    tree = ET.ElementTree(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True, method="xml")


def _pack_epub(container_dir: Path, out_epub: Path) -> None:
    mimetype_path = container_dir / "mimetype"
    if not mimetype_path.exists():
        raise EpubTranslateError(f"Missing mimetype file at {mimetype_path}")

    mimetype = mimetype_path.read_bytes()
    if mimetype != b"application/epub+zip":
        raise EpubTranslateError("mimetype content must be exactly: application/epub+zip")

    all_files: list[Path] = [p for p in container_dir.rglob("*") if p.is_file()]
    other_files = [p for p in all_files if p.name != "mimetype" and p.relative_to(container_dir).as_posix() != "mimetype"]
    other_files.sort(key=lambda p: p.relative_to(container_dir).as_posix())

    out_epub.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_epub, "w") as zf:
        zi = zipfile.ZipInfo("mimetype")
        zi.compress_type = zipfile.ZIP_STORED
        zi.external_attr = 0o644 << 16
        zf.writestr(zi, mimetype)
        for path in other_files:
            arcname = path.relative_to(container_dir).as_posix()
            zf.write(path, arcname, compress_type=zipfile.ZIP_DEFLATED)


def _validate_epub(epub_path: Path) -> None:
    with zipfile.ZipFile(epub_path, "r") as zf:
        infos = zf.infolist()
        if not infos:
            raise EpubTranslateError("EPUB zip is empty")
        first = infos[0]
        if first.filename != "mimetype":
            raise EpubTranslateError("First zip entry must be 'mimetype'")
        if first.compress_type != zipfile.ZIP_STORED:
            raise EpubTranslateError("'mimetype' must be stored (uncompressed)")
        mimetype = zf.read("mimetype")
        if mimetype != b"application/epub+zip":
            raise EpubTranslateError("mimetype contents must be exactly 'application/epub+zip' (no newline)")
        if "META-INF/container.xml" not in zf.namelist():
            raise EpubTranslateError("Missing META-INF/container.xml")


_ENV_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _is_tty() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _parse_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    env: dict[str, str] = {}
    for raw in _read_text(path).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not _ENV_KEY_RE.match(key):
            continue
        if len(value) >= 2 and ((value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")):
            value = value[1:-1]
        env[key] = value
    return env


def _dotenv_path(skill_data_dir: Path) -> Path:
    return skill_data_dir / ".env"


def _load_skill_env(skill_data_dir: Path) -> dict[str, str]:
    env_path = _dotenv_path(skill_data_dir)
    return _parse_dotenv(env_path)


def _write_skill_env(skill_data_dir: Path, updates: dict[str, str]) -> Path:
    env_path = _dotenv_path(skill_data_dir)
    current = _parse_dotenv(env_path)
    current.update({k: v for k, v in updates.items() if v is not None})

    ordered_keys = [
        "SKILL_ROOT",
        "SKILL_NAME",
        "SKILL_DATA_ROOT",
        "SKILL_DATA_DIR",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "OPENAI_BASE_URL",
        "OPENAI_REASONING_EFFORT",
    ]
    keys = ordered_keys + sorted([k for k in current.keys() if k not in ordered_keys])
    lines: list[str] = ["# epub-translate local config (auto-generated)\n"]
    for key in keys:
        if key not in current:
            continue
        value = current[key]
        # Quote values that contain spaces to keep parsing simple.
        if any(ch.isspace() for ch in value) or value == "":
            value = json.dumps(value, ensure_ascii=False)
        lines.append(f"{key}={value}\n")

    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text("".join(lines), encoding="utf-8")
    try:
        os.chmod(env_path, 0o600)
    except OSError:
        pass
    return env_path


def _prompt_model(default_model: str) -> str:
    if not _is_tty():
        return default_model
    prompt = (
        "Select default OpenAI model:\n"
        "  1) gpt-5-mini\n"
        "  2) gpt-5.1\n"
        f"Press Enter for default ({default_model}), or type a custom model id:\n> "
    )
    choice = input(prompt).strip()
    if choice == "":
        return default_model
    if choice == "1":
        return "gpt-5-mini"
    if choice == "2":
        return "gpt-5.1"
    return choice


def _prompt_api_key() -> str:
    if not _is_tty():
        raise EpubTranslateError("OPENAI_API_KEY is missing and no TTY is available; run `epub-translate setup` first")
    key = getpass.getpass("Enter OPENAI_API_KEY (will be saved to .skills-data/epub-translate/.env): ").strip()
    if not key:
        raise EpubTranslateError("OPENAI_API_KEY is required")
    return key


def _openai_post_json(*, base_url: str, api_key: str, payload: dict[str, Any], timeout_secs: int) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/responses"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=timeout_secs) as resp:
            body = resp.read()
    except HTTPError as e:
        body = e.read()
        detail = body.decode("utf-8", errors="replace")
        raise OpenAIRequestError(f"OpenAI HTTP {e.code}: {detail}") from e
    except URLError as e:
        raise OpenAIRequestError(f"OpenAI request failed: {e}") from e

    try:
        obj = json.loads(body)
    except json.JSONDecodeError as e:
        raise OpenAIRequestError(f"OpenAI returned non-JSON response: {body[:200]!r}") from e
    if not isinstance(obj, dict):
        raise OpenAIRequestError("OpenAI returned unexpected JSON (not an object)")
    return obj


def _response_output_text(response_obj: dict[str, Any]) -> str:
    texts: list[str] = []
    for out in response_obj.get("output", []) or []:
        if not isinstance(out, dict):
            continue
        if out.get("type") != "message":
            continue
        for content in out.get("content", []) or []:
            if not isinstance(content, dict):
                continue
            if content.get("type") == "output_text":
                text = content.get("text")
                if isinstance(text, str):
                    texts.append(text)
    return "".join(texts)


def _strip_code_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        lines = t.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        t = "\n".join(lines).strip()
    return t


def _parse_translation_json(text: str) -> dict[str, Any]:
    cleaned = _strip_code_fences(text)
    cleaned = cleaned.strip()
    # Heuristic: if extra text slipped in, try to isolate the outermost JSON object.
    if "{" in cleaned and "}" in cleaned:
        cleaned = cleaned[cleaned.find("{") : cleaned.rfind("}") + 1]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Common failure observed: `"id:3"` instead of `"id":3`.
        cleaned2 = cleaned.replace('"id:', '"id":')
        try:
            return json.loads(cleaned2)
        except json.JSONDecodeError as e:
            raise OpenAIRequestError(f"Model returned invalid JSON: {e}") from e


def _cmd_extract(args: argparse.Namespace) -> int:
    epub_path = Path(args.epub).expanduser().resolve()
    if not epub_path.exists():
        raise EpubTranslateError(f"Input EPUB not found: {epub_path}")

    skill_data_dir = Path(os.environ.get("SKILL_DATA_DIR", str(_default_skill_data_dir()))).expanduser().resolve()
    job_dir = Path(args.job_dir).expanduser().resolve() if args.job_dir else (skill_data_dir / "tmp" / f"{_now_slug()}-{os.getpid()}")
    unpacked_dir = job_dir / "unpacked"
    _ensure_dir(unpacked_dir)

    shutil.copy2(epub_path, job_dir / "source.epub")
    _unzip_epub(epub_path, unpacked_dir)

    container_xml = unpacked_dir / "META-INF" / "container.xml"
    if not container_xml.exists():
        raise EpubTranslateError("Missing META-INF/container.xml in EPUB")

    rootfiles = _get_container_rootfile_paths(container_xml)
    opf_container_path = rootfiles[0]
    opf_fs_path = unpacked_dir / Path(opf_container_path)
    if not opf_fs_path.exists():
        raise EpubTranslateError(f"Package document not found: {opf_container_path}")

    package = _parse_opf(opf_fs_path, opf_container_path)
    xhtml_docs = _iter_xhtml_docs(package, scope=args.scope, include_nav=not args.no_include_nav)

    units_path = Path(args.out).expanduser().resolve() if args.out else (job_dir / "units.jsonl")
    count = 0

    with units_path.open("w", encoding="utf-8") as f:
        if args.include_opf_title:
            opf_root = _parse_xml(opf_fs_path)
            metadata = opf_root.find(f".//{_q(OPF_NS, 'metadata')}")
            if metadata is not None:
                title_el = metadata.find(f".//{_q(DC_NS, 'title')}")
                if title_el is not None:
                    src_inner = _inner_xml(title_el)
                    src_text = _normalized_text(title_el)
                    if len(src_text) >= args.min_text_chars and len(src_inner) <= args.max_unit_chars:
                        count += 1
                        unit = {
                            "id": count,
                            "kind": "opf-dc-title",
                            "doc_path": opf_container_path,
                            "xpath": _xpath_for_element(opf_root, title_el),
                            "tag": "dc:title",
                            "source_inner_html": src_inner,
                            "source_text": src_text,
                            "source_text_hash": _sha256(src_text),
                            "source_markup_hash": _markup_hash_for_children(title_el),
                            "source_inner_html_hash": _sha256(src_inner),
                        }
                        f.write(json.dumps(unit, ensure_ascii=False) + "\n")

        for _, doc_path in xhtml_docs:
            xhtml_fs_path = unpacked_dir / Path(doc_path)
            if not xhtml_fs_path.exists():
                continue
            xhtml_root = _parse_xml(xhtml_fs_path)

            title_el = xhtml_root.find(f".//{_q(XHTML_NS, 'head')}/{_q(XHTML_NS, 'title')}")
            if title_el is not None:
                src_inner = _inner_xml(title_el)
                src_text = _normalized_text(title_el)
                if len(src_text) >= args.min_text_chars and len(src_inner) <= args.max_unit_chars:
                    count += 1
                    unit = {
                        "id": count,
                        "kind": "xhtml-fragment",
                        "doc_path": doc_path,
                        "xpath": _xpath_for_element(xhtml_root, title_el),
                        "tag": "title",
                        "source_inner_html": src_inner,
                        "source_text": src_text,
                        "source_text_hash": _sha256(src_text),
                        "source_markup_hash": _markup_hash_for_children(title_el),
                        "source_inner_html_hash": _sha256(src_inner),
                    }
                    f.write(json.dumps(unit, ensure_ascii=False) + "\n")

            body = xhtml_root.find(f".//{_q(XHTML_NS, 'body')}")
            if body is None:
                continue

            leaf_blocks = _select_leaf_block_elements(body)
            for el in leaf_blocks:
                src_inner = _inner_xml(el)
                src_text = _normalized_text(el)
                if len(src_text) < args.min_text_chars:
                    continue
                if len(src_inner) > args.max_unit_chars:
                    continue

                count += 1
                unit = {
                    "id": count,
                    "kind": "xhtml-fragment",
                    "doc_path": doc_path,
                    "xpath": _xpath_for_element(xhtml_root, el),
                    "tag": _localname(el.tag),
                    "source_inner_html": src_inner,
                    "source_text": src_text,
                    "source_text_hash": _sha256(src_text),
                    "source_markup_hash": _markup_hash_for_children(el),
                    "source_inner_html_hash": _sha256(src_inner),
                }
                f.write(json.dumps(unit, ensure_ascii=False) + "\n")

    job = {
        "source_epub": str(epub_path),
        "job_dir": str(job_dir),
        "unpacked_dir": "unpacked",
        "opf_path": opf_container_path,
        "units_path": str(units_path),
        "scope": args.scope,
        "include_nav": not args.no_include_nav,
        "unit_count": count,
    }
    _write_text(job_dir / "job.json", json.dumps(job, ensure_ascii=False, indent=2) + "\n")

    print(str(job_dir))
    print(f"Wrote {count} units to {units_path}")
    return 0


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                raise EpubTranslateError(f"Invalid JSON on line {line_no} of {path}: {e}") from e
            if not isinstance(rec, dict):
                raise EpubTranslateError(f"Expected JSON object on line {line_no} of {path}")
            records.append(rec)
    return records


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                raise EpubTranslateError(f"Invalid JSON on line {line_no} of {path}: {e}") from e
            if not isinstance(rec, dict):
                raise EpubTranslateError(f"Expected JSON object on line {line_no} of {path}")
            yield rec


def _cmd_setup(args: argparse.Namespace) -> int:
    skill_root, project_root = _skill_paths()
    skill_name = "epub-translate"
    skill_data_root = Path(os.environ.get("SKILL_DATA_ROOT", str(project_root / ".skills-data"))).expanduser().resolve()
    skill_data_dir = Path(os.environ.get("SKILL_DATA_DIR", str(skill_data_root / skill_name))).expanduser().resolve()
    _ensure_dir(skill_data_dir)

    existing = _load_skill_env(skill_data_dir)
    base_url = args.base_url or existing.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    default_model = args.model or existing.get("OPENAI_MODEL") or "gpt-5-mini"
    model = _prompt_model(default_model) if not args.no_prompt else default_model

    api_key = os.environ.get("OPENAI_API_KEY") or existing.get("OPENAI_API_KEY")
    if not api_key:
        if args.no_prompt:
            raise EpubTranslateError("OPENAI_API_KEY is missing; run setup without --no-prompt or set OPENAI_API_KEY in the environment")
        api_key = _prompt_api_key()

    reasoning_effort = args.reasoning_effort or existing.get("OPENAI_REASONING_EFFORT") or "low"

    env_path = _write_skill_env(
        skill_data_dir,
        {
            "SKILL_ROOT": str(skill_root),
            "SKILL_NAME": skill_name,
            "SKILL_DATA_ROOT": str(skill_data_root),
            "SKILL_DATA_DIR": str(skill_data_dir),
            "OPENAI_API_KEY": api_key,
            "OPENAI_MODEL": model,
            "OPENAI_BASE_URL": base_url,
            "OPENAI_REASONING_EFFORT": reasoning_effort,
        },
    )

    print(f"Wrote {env_path}")
    return 0


def _load_done_translation_ids(path: Path) -> set[int]:
    done: set[int] = set()
    if not path.exists():
        return done
    for rec in _iter_jsonl(path):
        if "id" not in rec:
            continue
        try:
            done.add(int(rec["id"]))
        except (TypeError, ValueError):
            continue
    return done


def _translate_batch_via_openai(
    *,
    api_key: str,
    base_url: str,
    model: str,
    reasoning_effort: str | None,
    target_lang: str,
    batch: list[dict[str, Any]],
    timeout_secs: int,
    temperature: float | None,
) -> list[dict[str, Any]]:
    prompt = (
        f'Translate these EPUB XHTML fragments from English to the target language "{target_lang}".\n\n'
        "Rules:\n"
        "- Translate ONLY the human-readable text.\n"
        "- Do NOT add/remove/reorder any tags.\n"
        "- Do NOT change any tag names, prefixes, attribute names, or attribute values (including xmlns:* declarations).\n"
        "- Keep punctuation, numbers, and bracketed references exactly (e.g. [1]).\n"
        "- Keep entities/character references as-is (e.g. &amp;, &#160;).\n"
        "- Preserve existing line breaks (\\n) where they appear.\n\n"
        "Output:\n"
        "- Return ONLY valid JSON (no markdown, no commentary).\n"
        '- JSON must be an object: {"translations": [{"id": integer, "translated_inner_html": string}, ...]}\n'
        "- Include exactly one output object per input item, with the same id.\n"
        "- Preserve the original order.\n\n"
        "Input items (JSON array):\n"
        + json.dumps(batch, ensure_ascii=False, indent=2)
    )

    payload: dict[str, Any] = {
        "model": model,
        "input": prompt,
    }
    if reasoning_effort:
        payload["reasoning"] = {"effort": reasoning_effort}
    if temperature is not None:
        payload["temperature"] = temperature

    response_obj = _openai_post_json(base_url=base_url, api_key=api_key, payload=payload, timeout_secs=timeout_secs)
    out_text = _response_output_text(response_obj).strip()
    if not out_text:
        raise OpenAIRequestError("OpenAI response contained no output_text")
    parsed = _parse_translation_json(out_text)
    if not isinstance(parsed, dict) or "translations" not in parsed or not isinstance(parsed["translations"], list):
        raise OpenAIRequestError("Model output did not match expected JSON shape")

    translations = parsed["translations"]
    if len(translations) != len(batch):
        raise OpenAIRequestError(f"Expected {len(batch)} translations, got {len(translations)}")

    normalized: list[dict[str, Any]] = []
    for expected, got in zip(batch, translations, strict=True):
        if not isinstance(got, dict):
            raise OpenAIRequestError("Translation item is not an object")
        exp_id = int(expected["id"])
        got_id = int(got.get("id"))
        if got_id != exp_id:
            raise OpenAIRequestError(f"Translation id mismatch: expected {exp_id}, got {got_id}")
        if "translated_inner_html" not in got:
            raise OpenAIRequestError(f"Missing translated_inner_html for id {exp_id}")
        normalized.append({"id": exp_id, "translated_inner_html": str(got["translated_inner_html"])})
    return normalized


def _cmd_translate(args: argparse.Namespace) -> int:
    job_dir = Path(args.job_dir).expanduser().resolve()
    job_path = job_dir / "job.json"
    if not job_path.exists():
        raise EpubTranslateError(f"Missing job.json in {job_dir} (run extract first)")
    job = json.loads(_read_text(job_path))
    units_path = Path(job.get("units_path", "")).expanduser().resolve()
    if not units_path.exists():
        raise EpubTranslateError(f"Missing units.jsonl at {units_path}")

    skill_data_dir = Path(os.environ.get("SKILL_DATA_DIR", str(_default_skill_data_dir()))).expanduser().resolve()
    skill_env = _load_skill_env(skill_data_dir)

    api_key = os.environ.get("OPENAI_API_KEY") or skill_env.get("OPENAI_API_KEY")
    model = args.model or os.environ.get("OPENAI_MODEL") or skill_env.get("OPENAI_MODEL") or "gpt-5-mini"
    base_url = os.environ.get("OPENAI_BASE_URL") or skill_env.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    reasoning_effort = os.environ.get("OPENAI_REASONING_EFFORT") or skill_env.get("OPENAI_REASONING_EFFORT") or "low"

    out_path = Path(args.out).expanduser().resolve() if args.out else (job_dir / "translations.jsonl")
    done_ids = _load_done_translation_ids(out_path) if args.resume else set()

    limit: int | None = args.max_units
    if args.fraction is not None:
        if args.fraction <= 0 or args.fraction > 1:
            raise EpubTranslateError("--fraction must be > 0 and <= 1")
        try:
            unit_count = int(job.get("unit_count", 0))
        except (TypeError, ValueError):
            unit_count = 0
        if unit_count <= 0:
            raise EpubTranslateError("job.json missing valid unit_count; re-run extract")
        frac_limit = int(math.ceil(unit_count * float(args.fraction)))
        limit = frac_limit if limit is None else min(limit, frac_limit)

    pending: list[dict[str, Any]] = []
    for unit in _iter_jsonl(units_path):
        unit_id = int(unit["id"])
        if limit is not None and unit_id > limit:
            break
        if unit_id in done_ids:
            continue
        pending.append({"id": unit_id, "source_inner_html": unit.get("source_inner_html", "")})

    if not pending:
        print("Nothing to translate (all units already present in translations.jsonl)")
        return 0

    logs_dir = job_dir / "logs"
    _ensure_dir(logs_dir)
    log_path = logs_dir / "openai_translate.log"

    if args.dry_run:
        print(f"Would translate {len(pending)} units → {out_path}")
        return 0

    if not api_key:
        api_key = _prompt_api_key()
        skill_root, project_root = _skill_paths()
        skill_name = "epub-translate"
        skill_data_root = Path(os.environ.get("SKILL_DATA_ROOT", str(project_root / ".skills-data"))).expanduser().resolve()
        _write_skill_env(
            skill_data_dir,
            {
                "SKILL_ROOT": str(skill_root),
                "SKILL_NAME": skill_name,
                "SKILL_DATA_ROOT": str(skill_data_root),
                "SKILL_DATA_DIR": str(skill_data_dir),
                "OPENAI_API_KEY": api_key,
                "OPENAI_MODEL": model,
                "OPENAI_BASE_URL": base_url,
                "OPENAI_REASONING_EFFORT": reasoning_effort,
            },
        )

    batch_size = int(args.batch_size)
    if batch_size <= 0:
        raise EpubTranslateError("--batch-size must be > 0")
    timeout_secs = int(args.timeout_secs)
    max_retries = int(args.max_retries)
    temperature = float(args.temperature) if args.temperature is not None else None

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as out_f, log_path.open("a", encoding="utf-8") as log_f:
        for i in range(0, len(pending), batch_size):
            batch = pending[i : i + batch_size]
            attempt = 0
            while True:
                attempt += 1
                try:
                    translations = _translate_batch_via_openai(
                        api_key=api_key,
                        base_url=base_url,
                        model=model,
                        reasoning_effort=reasoning_effort,
                        target_lang=args.target_lang,
                        batch=batch,
                        timeout_secs=timeout_secs,
                        temperature=temperature,
                    )
                    break
                except OpenAIRequestError as e:
                    log_f.write(f"batch_start_id={batch[0]['id']} attempt={attempt} error={e}\n")
                    log_f.flush()
                    if attempt >= max_retries:
                        raise
                    sleep_s = min(30, 2 ** (attempt - 1))
                    time.sleep(sleep_s)

            for rec in translations:
                out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                done_ids.add(int(rec["id"]))
            out_f.flush()
            log_f.write(f"translated {batch[0]['id']}..{batch[-1]['id']} ok\n")
            log_f.flush()

    print(f"Wrote {out_path}")
    return 0


def _cmd_apply(args: argparse.Namespace) -> int:
    job_dir = Path(args.job_dir).expanduser().resolve()
    job_path = job_dir / "job.json"
    if not job_path.exists():
        raise EpubTranslateError(f"Missing job.json in {job_dir} (run extract first)")
    job = json.loads(_read_text(job_path))
    unpacked_dir = job_dir / job.get("unpacked_dir", "unpacked")
    opf_path = job.get("opf_path")
    if not opf_path:
        raise EpubTranslateError("job.json missing opf_path")

    translations_path = Path(args.translations).expanduser().resolve()
    translations = _load_jsonl(translations_path)
    by_id: dict[int, dict[str, Any]] = {}
    for rec in translations:
        if "id" not in rec or "translated_inner_html" not in rec:
            continue
        try:
            rec_id = int(rec["id"])
        except (TypeError, ValueError):
            continue
        by_id[rec_id] = rec

    units_path = Path(job.get("units_path")).expanduser().resolve()
    units = _load_jsonl(units_path)

    opf_title_unit: dict[str, Any] | None = None
    opf_title_translation: str | None = None
    per_doc: dict[str, list[dict[str, Any]]] = {}
    for unit in units:
        kind = unit.get("kind", "xhtml-fragment")
        unit_id = int(unit["id"])
        translated = by_id.get(unit_id)
        if not translated:
            continue
        if kind == "opf-dc-title":
            opf_title_unit = unit
            opf_title_translation = str(translated["translated_inner_html"])
            continue

        doc_path = unit["doc_path"]
        per_doc.setdefault(doc_path, []).append(
            {
                "unit": unit,
                "translated_inner_html": translated["translated_inner_html"],
            }
        )

    for doc_path, items in per_doc.items():
        xhtml_fs_path = unpacked_dir / Path(doc_path)
        if not xhtml_fs_path.exists():
            continue
        xhtml_root = _parse_xml(xhtml_fs_path)

        for item in items:
            unit = item["unit"]
            xpath = unit["xpath"]
            target = _find_by_xpath(xhtml_root, xpath)

            current_text = _normalized_text(target)
            current_text_hash = _sha256(current_text)
            if current_text_hash != unit.get("source_text_hash") and not args.force:
                raise EpubTranslateError(
                    f"Source mismatch for unit {unit['id']} at {doc_path} {xpath}: text changed since extract (use --force to override)"
                )

            current_markup_hash = _markup_hash_for_children(target)
            if current_markup_hash != unit.get("source_markup_hash") and not args.force:
                raise EpubTranslateError(
                    f"Source mismatch for unit {unit['id']} at {doc_path} {xpath}: markup changed since extract (use --force to override)"
                )

            translated_inner_html = item["translated_inner_html"]
            if unit.get("tag") == "title" and len(list(target)) == 0:
                target.text = str(translated_inner_html)
            else:
                translated_wrapper = _parse_fragment_children(str(translated_inner_html))
                translated_markup_hash = _markup_hash_for_children(translated_wrapper)
                if translated_markup_hash != unit.get("source_markup_hash"):
                    raise EpubTranslateError(
                        f"Markup mismatch for unit {unit['id']} at {doc_path} {xpath}: translated fragment changed tags/attrs"
                    )

                _apply_fragment_inner_html(target, str(translated_inner_html))

        _update_xhtml_lang(xhtml_root, args.target_lang)
        _write_xml(xhtml_fs_path, xhtml_root)

    opf_fs_path = unpacked_dir / Path(opf_path)
    opf_root = _parse_xml(opf_fs_path)
    _update_opf_lang(opf_root, args.target_lang)

    if opf_title_unit and opf_title_translation is not None:
        metadata = opf_root.find(f".//{_q(OPF_NS, 'metadata')}")
        if metadata is not None:
            dc_title = metadata.find(f".//{_q(DC_NS, 'title')}")
            if dc_title is not None:
                current_title = " ".join("".join(dc_title.itertext()).split()).strip()
                current_title_hash = _sha256(current_title)
                if current_title_hash != opf_title_unit.get("source_text_hash") and not args.force:
                    raise EpubTranslateError(
                        "OPF dc:title changed since extract (use --force to override)"
                    )
                dc_title.text = opf_title_translation

    _write_xml(opf_fs_path, opf_root)

    out_epub = Path(args.out_epub).expanduser().resolve()
    _pack_epub(unpacked_dir, out_epub)
    _validate_epub(out_epub)

    print(f"Wrote {out_epub}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    epub_path = Path(args.epub).expanduser().resolve()
    _validate_epub(epub_path)
    print("OK")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="epub-translate")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_setup = sub.add_parser("setup", help="Create/update .skills-data/epub-translate/.env with OpenAI config")
    p_setup.add_argument("--model", help="Default OpenAI model id (e.g., gpt-5.1, gpt-5-mini)")
    p_setup.add_argument("--base-url", help="OpenAI API base URL (default: https://api.openai.com/v1)")
    p_setup.add_argument(
        "--reasoning-effort",
        choices=["minimal", "low", "medium", "high", "xhigh"],
        help="Reasoning effort (GPT-5 models; default: low)",
    )
    p_setup.add_argument("--no-prompt", action="store_true", help="Do not prompt; error if required values are missing")
    p_setup.set_defaults(func=_cmd_setup)

    p_extract = sub.add_parser("extract", help="Extract XHTML fragments into units.jsonl")
    p_extract.add_argument("--epub", required=True, help="Path to input .epub")
    p_extract.add_argument("--job-dir", help="Job directory (default: .skills-data/epub-translate/tmp/<timestamp>-<pid>)")
    p_extract.add_argument("--out", help="Output units.jsonl path (default: <job-dir>/units.jsonl)")
    p_extract.add_argument("--scope", choices=["spine", "all-xhtml"], default="spine", help="Which XHTML docs to extract")
    p_extract.add_argument("--no-include-nav", action="store_true", help="Do not force-include the nav document")
    p_extract.add_argument("--include-opf-title", action="store_true", help="Also extract OPF dc:title as a translation unit")
    p_extract.add_argument("--min-text-chars", type=int, default=1, help="Skip units with less text than this")
    p_extract.add_argument("--max-unit-chars", type=int, default=8000, help="Skip units with source_inner_html longer than this")
    p_extract.set_defaults(func=_cmd_extract)

    p_apply = sub.add_parser("apply", help="Apply translations.jsonl, update lang, and repack EPUB")
    p_apply.add_argument("--job-dir", required=True, help="Job directory printed by extract")
    p_apply.add_argument("--translations", required=True, help="Path to translations.jsonl")
    p_apply.add_argument("--target-lang", required=True, help="BCP-47 language tag to write into OPF/XHTML (e.g., es, fr-CA)")
    p_apply.add_argument("--out-epub", required=True, help="Path to output .epub")
    p_apply.add_argument("--force", action="store_true", help="Apply even if source text/markup changed since extract")
    p_apply.set_defaults(func=_cmd_apply)

    p_translate = sub.add_parser("translate", help="Translate units.jsonl via OpenAI API into translations.jsonl")
    p_translate.add_argument("--job-dir", required=True, help="Job directory printed by extract")
    p_translate.add_argument("--target-lang", required=True, help="Target language (e.g., uk, fr, es)")
    p_translate.add_argument("--out", help="Output translations.jsonl path (default: <job-dir>/translations.jsonl)")
    p_translate.add_argument("--model", help="OpenAI model id override (default: OPENAI_MODEL from .env)")
    p_translate.add_argument("--batch-size", type=int, default=50, help="Number of units per API call (default: 50)")
    p_translate.add_argument("--max-units", type=int, help="Translate only the first N units (by id)")
    p_translate.add_argument("--fraction", type=float, help="Translate only the first fraction of units (0-1)")
    p_translate.add_argument("--no-resume", dest="resume", action="store_false", default=True, help="Do not resume; re-translate all selected units")
    p_translate.add_argument("--timeout-secs", type=int, default=120, help="HTTP timeout in seconds (default: 120)")
    p_translate.add_argument("--max-retries", type=int, default=3, help="Max retries per batch (default: 3)")
    p_translate.add_argument("--temperature", type=float, help="Temperature override (default: omit)")
    p_translate.add_argument("--dry-run", action="store_true", help="Do not call OpenAI; just report what would be done")
    p_translate.set_defaults(func=_cmd_translate)

    p_validate = sub.add_parser("validate", help="Validate basic EPUB container invariants")
    p_validate.add_argument("--epub", required=True, help="Path to .epub to validate")
    p_validate.set_defaults(func=_cmd_validate)

    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except EpubTranslateError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
