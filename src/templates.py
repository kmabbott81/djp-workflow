from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception as e:
    raise RuntimeError("PyYAML required. Install with: pip install pyyaml") from e

from docx import Document
from docx.shared import Pt
from jinja2 import BaseLoader, Environment, StrictUndefined, TemplateError

TEMPLATES_DIR = Path("templates")
OUTPUT_DIR = Path("runs/ui/templates")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TemplateDef:
    key: str
    name: str
    description: str
    variables: dict[str, Any] = field(default_factory=dict)
    prompt: str = ""


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def list_templates() -> list[TemplateDef]:
    TEMPLATES_DIR.mkdir(exist_ok=True, parents=True)
    out: list[TemplateDef] = []
    for yml in sorted(TEMPLATES_DIR.glob("*.yaml")):
        data = _load_yaml(yml)
        out.append(
            TemplateDef(
                key=data.get("key") or yml.stem,
                name=data.get("name") or yml.stem,
                description=data.get("description") or "",
                variables=data.get("variables") or {},
                prompt=data.get("prompt") or "",
            )
        )
    return out


def render_template(prompt_src: str, variables: dict[str, Any]) -> str:
    env = Environment(loader=BaseLoader(), undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
    try:
        return env.from_string(prompt_src).render(**variables)
    except TemplateError as e:
        raise RuntimeError(f"Template render error: {e}") from e


def export_markdown(text: str, fname: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    p = OUTPUT_DIR / f"{fname}.md"
    p.write_text(text, encoding="utf-8")
    return p


def export_docx(text: str, fname: str, heading: str = "DJP Output") -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = Document()
    doc.add_heading(heading, level=1)
    for p in doc.paragraphs:
        for run in p.runs:
            run.font.size = Pt(12)
    for line in text.splitlines():
        para = doc.add_paragraph(line)
        for run in para.runs:
            run.font.size = Pt(11)
    p = OUTPUT_DIR / f"{fname}.docx"
    doc.save(p)
    return p
