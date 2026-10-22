# Puesta en marcha local

## Requisitos

- GitHub CLI autenticado con acceso de lectura a repositorios privados: `gh auth login`
- `jq`, Python 3.10+ y Git
- Ejecutar desde un equipo de confianza. El inventario contiene nombres de repositorios privados y debe permanecer local salvo que decidas compartirlo.

## 1. Exportar el inventario actual

Desde la raíz del repositorio:

```bash
bash scripts/ecosystem_490/export_github_inventory.sh ./github-inventory.json
```

El exportador usa `gh api --paginate`, filtra repositorios propiedad de `belentani7`, genera JSON y SHA-256. No cambia GitHub.

Si quieres cambiar el propietario de forma explícita:

```bash
GITHUB_OWNER=belentani7 bash scripts/ecosystem_490/export_github_inventory.sh ./github-inventory.json
```

## 2. Crear carpetas de auditoría por repo

```bash
python3 scripts/ecosystem_490/generate_verification.py ./github-inventory.json --out ./repo-audit
```

Para comprobar primero una muestra de tres:

```bash
python3 scripts/ecosystem_490/generate_verification.py ./github-inventory.json --out ./repo-audit-sample --limit 3
```

Cada carpeta generada incluye VERIFICACION.md y el directorio raíz contiene manifest.json. Los controles quedan en NOT RUN hasta ejecutarlos con evidencia real.

**Protección de trabajos anteriores:** el generador comprueba todos los nombres y posibles colisiones antes de escribir; si la carpeta contiene ya un manifiesto o algún `VERIFICACION.md`, se detiene sin sobrescribirlo. Para repetir una exportación usa una carpeta `--out` nueva. El interruptor `--overwrite` es **explícito** y solo se debe usar cuando quieras sustituir conscientemente las plantillas ya existentes; no lo uses con verificaciones modificadas a mano. Una ejecución sobre el inventario no certifica que los repositorios compilen ni declara nada publicado.

## 3. Clonar las herramientas para inspección

```bash
bash scripts/ecosystem_490/clone_agent_tools.sh
```

Esto clona las fuentes upstream en `~/.local/share/belentani-tools` y registra commits en CLONES.tsv. No ejecuta scripts de instalación. CodeGraff se deja en `codegraff-review-only` para revisar los términos de licencia y seguridad; no se instala ni ejecuta.

## 4. Instalar/activar en el editor

Después de revisar las fuentes y fijar versiones:
- Superpowers: seguir la sección específica para el agente usado en el README upstream.
- Impeccable: desde la raíz de una app con UI, ejecutar `npx impeccable install`; después ejecutar `/impeccable init` en el agente. No aplicarlo a proyectos sin interfaz.
- Graphify: usar un entorno Python aislado, preferiblemente `uv tool install graphifyy` o `pipx install graphifyy`; después ejecutar `graphify install --project` en repositorios piloto y construir el grafo según la documentación.
- CodeGraff: no instalar hasta completar revisión legal de su LICENSE modificada y revisar permisos/telemetría/ejecución de comandos.

## 5. Piloto y escalado

1. Ejecutar en tres repositorios distintos y no críticos.
2. Verificar falsos positivos, coste, archivos creados, privacidad y reversibilidad.
3. Abrir PRs pequeños para la integración de configuración.
4. Escalar por familia, no por orden alfabético ni a ciegas.
5. Mantener original, branch y backup hasta validar restauración y equivalencia.
