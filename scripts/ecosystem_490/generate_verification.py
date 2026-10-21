#!/usr/bin/env python3
"""Generate evidence-first VERIFICACION.md files from a GitHub repository inventory.

Input: JSON from GitHub REST/GraphQL, either a list of repositories or an object with
'repositories'/'items'. This script never contacts GitHub, clones code, changes visibility,
sets licenses, deletes files, or claims that checks passed. It creates scaffold files only.

Example:
  python3 scripts/ecosystem_490/generate_verification.py inventory.json --out ./repo-audit
"""
from __future__ import annotations
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TEMPLATE = """# VERIFICACIÓN DEL REPOSITORIO

> Generado como plantilla. Los estados son NOT RUN hasta que exista evidencia.

## Identidad
- Repositorio: {full_name}
- URL: {html_url}
- Rama predeterminada: {default_branch}
- Visibilidad observada: {visibility}
- Archivado observado: {archived}
- Tamaño GitHub reportado (KB): {size}
- Fecha de generación UTC: {date}
- Commit revisado: NOT RUN
- Rol canónico: INCIERTO
- Prioridad: NOT TRIAGED

## Resumen
- Propósito verificado: NOT RUN
- Estado de producto: DESCONOCIDO
- Oportunidad principal: NOT RUN
- Riesgo principal: NOT RUN

## Controles
| Control | Estado | Evidencia |
|---|---|---|
| Procedencia/propiedad | NOT RUN | |
| Backup + restauración | NOT RUN | |
| Licencia y assets | NOT RUN | |
| Secret scanning | NOT RUN | |
| Dependencias/SBOM | NOT RUN | |
| Tests | NOT RUN | |
| Lint/typecheck/build | NOT RUN | |
| Deploy/URL canónica (si aplica) | NOT RUN | |
| Duplicados exactos y semánticos | NOT RUN | |
| Accesibilidad/UI (si aplica) | NOT RUN | |

## Herramientas
- Superpowers: NOT RUN
- Impeccable (solo UI): NOT RUN
- Graphify: NOT RUN
- CodeGraff: BLOCKED pending license/security review

## Evidencia y decisión
| ID | Acción/comando | Resultado | Evidencia |
|---|---|---|---|
| E-001 | Inventario de metadata | Observed | {html_url} |

- Resultado global: NOT RUN
- Bloqueantes: NOT TRIAGED
- Próximo paso: inspección de solo lectura
"""

def load_repos(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        repos = data
    elif isinstance(data, dict):
        repos = data.get("repositories") or data.get("items") or data.get("data") or []
        if isinstance(repos, dict):
            repos = repos.get("repositories") or repos.get("nodes") or []
    else:
        raise ValueError("Formato JSON no reconocido")
    if not isinstance(repos, list):
        raise ValueError("La colección de repositorios no es una lista")
    return [r for r in repos if isinstance(r, dict)]

def slug(full_name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", full_name.replace("/", "__"))
    return safe.strip(".-") or "unknown-repo"

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("inventory", type=Path)
    p.add_argument("--out", type=Path, default=Path("repo-audit"))
    p.add_argument("--limit", type=int, default=0, help="Optional sample limit; 0 means all.")
    args = p.parse_args()
    repos = load_repos(args.inventory)
    if args.limit > 0:
        repos = repos[:args.limit]
    args.out.mkdir(parents=True, exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    manifest = []
    seen = set()
    for r in repos:
        owner = r.get("owner") or {}
        full_name = r.get("full_name") or r.get("repository_full_name")
        if not full_name and isinstance(owner, dict) and r.get("name"):
            full_name = f"{owner.get('login', 'unknown')}/{r['name']}"
        full_name = str(full_name or r.get("name") or "unknown/unknown")
        if full_name in seen:
            continue
        seen.add(full_name)
        url = r.get("html_url") or r.get("display_url") or f"https://github.com/{full_name}"
        visibility = r.get("visibility") or ("private" if r.get("private") else "public" if "private" in r else "unknown")
        archived = r.get("archived", "unknown")
        size = r.get("size", "unknown")
        default_branch = r.get("default_branch") or "unknown"
        folder = args.out / slug(full_name)
        folder.mkdir(parents=True, exist_ok=True)
        safe_url = str(url).replace("|", "%7C")
        content = TEMPLATE.format(full_name=full_name, html_url=safe_url, default_branch=default_branch,
                                  visibility=visibility, archived=archived, size=size, date=date)
        (folder / "VERIFICACION.md").write_text(content, encoding="utf-8")
        manifest.append({"full_name": full_name, "url": url, "folder": folder.name,
                         "visibility": visibility, "archived": archived, "default_branch": default_branch,
                         "status": "NOT RUN"})
    (args.out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Scaffolds creados: {len(manifest)}; estado: NOT RUN; salida: {args.out.resolve()}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
