# BELENTANI Factory — motor Python persistente

**Estado:** ejecutable y probado localmente; **no** es un agente generativo, ni un
desplegador automático, ni un sistema que certifique productos terminados.
Esta herramienta complementa el orquestador existente y no crea repositorios.

## Por qué aquí y no en otro repositorio

`agent-orchestration-machine` es el núcleo canónico y mantiene tareas, permisos
y políticas. `agent-linux` aporta el entorno de ejecución; `safe-exec`
puede evaluar código no confiable; `system-one-local-python-openclaw` sirve
decisiones tipadas, y `contexto-repos` conserva contexto histórico.
**No se han fusionado estos proyectos ni se ha instalado código entre ellos.**

## Operaciones implementadas

- Importar inventario JSON previamente autorizado con ID de GitHub estable.
- Preservar 490 entradas del inventario histórico sin convertirlas en 490 lanzamientos.
- Mantener una cola SQLite WAL persistente y privada; documentos y archivos
  archivados no obtienen trabajo activo.
- Reservar hasta tres tareas por ejecución (máximo permitido: diez), sin
  doble asignación entre trabajadores.
- Tokens únicos de lease: un trabajador con lease vencido no puede escribir
  el resultado de otro.
- Retrys acotados, bloqueo explícito al agotar intentos, eventos locales.
- Comprobar API GitHub con **GET exclusivamente**, identidad exacta de repositorio,
  listado raíz, README y pistas de estructura.
- Exportar métricas por defecto sin nombres de repositorios privados.
- Evaluar evidencia de una release como **candidata a revisión**, nunca como
  aprobación de publicación.

## Inicio — Python 3.11+ sin dependencias adicionales

Desde la raíz del repositorio:

```bash
export PYTHONPATH=src
# Importación local, sin red y sin cambiar GitHub:
python3 -m machine.factory_engine --db ~/.local/state/belentani-factory/factory.db \
  seed data/portfolio-repositories-2026-10-21.json

python3 -m machine.factory_engine status
python3 -m unittest discover -s tests -p 'test_factory_engine.py' -v
```

Para usar la misma base entre comandos, conserva la opción `--db`:

```bash
db="$HOME/.local/state/belentani-factory/factory.db"
python3 -m machine.factory_engine --db "$db" status
python3 -m machine.factory_engine --db "$db" export --output "$HOME/factory-aggregate.json"
```

### GitHub autenticado (opt-in, exclusivamente lectura)

Configura en el **servidor autorizado**, por un almacén de secretos y no en
el código, `PORTFOLIO_AUDIT_TOKEN`. Debe tener acceso de lectura a la
metadata y el contenido de los repositorios privados seleccionados.

```bash
# No pegues el valor del token en la terminal o historial de comandos.
python3 -m machine.factory_engine --db "$db" scan --limit 3
```

La comprobación realiza lecturas GitHub GET, **no clona ni ejecuta** los
repositorios. `checked` significa **revisión superficial del repositorio**.
No significa QA, contenido completo, build correcto, CI verde o producción.
Si falta el token, el comando falla sin marcar trabajos como comprobados.

## Garantía de que no publica datos privados

La SQLite se crea en el directorio local con permisos restrictivos (en POSIX).
Nunca subas `factory.db`, WAL, SHM, JSON de inventario completo ni tokens a
GitHub, Vercel, Google, a un hosting público ni a los logs de producción.
`export` sin parámetros adicionales solamente emite contadores. La bandera
`--include-names` está reservada a informes privados en un directorio seguro.

## Integración deliberada con otros agentes

| Componente existente | Posible responsabilidad | Integrado ahora |
|---|---|---|
| agent-linux | Invocar periódicamente `scan --limit 3` como usuario sin root | No: falta máquina vinculada |
| system-one-local-python-openclaw | Clasificar decisiones tipadas con confianza y escalado | No, no se simula su API |
| safe-exec | Evaluar artefactos y ejecutar código en aislamiento | No: requiere infraestructura y política revisada |
| Aider / OpenCode | Editar código solo en worktrees autorizados | No: sin credenciales ni sandbox persistente |
| Vercel | Preview y despliegue de commits exactos | No: conexión y comprobación de permisos pendientes |

**No** ejecutes modelos o agentes de terceros como `root`, no añadas
un ciclo infinito y no concedas `gh repo edit --visibility public`
ni `git push --force` a trabajadores.

## Criterio senior de entrega

`gate` recibe un JSON con: `purpose_verified`, `homepage_verified`,
`features_verified`, `content_verified`, `security_verified`,
`accessibility_verified`, `tests_verified`, `licenses_verified`,
`deployment_checked_from_exact_sha`, `rollback_tested`, `commit_sha`,
`production_url`. Devuelve evidencias faltantes y **siempre**
`release_authorized=false`. Los valores JSON son afirmaciones del
proveedor de evidencia, no pruebas criptográficas; una verificación externa
e independiente sigue siendo obligatoria.

## Mantenimiento y límites

No hace falta `uv` ni `pip` para ejecutar este motor. Si el resto del
repositorio adopta `uv`, usa `uv sync --locked` con un `uv.lock` revisado
en vez de instalaciones no reproducibles. Añade Ruff y un escáner de secretos
como comprobaciones CI de desarrollo, no a la ruta de ejecución privada.
El inventario histórico nunca se llama estado «live» sin acceso GitHub real.

El backlog sólo pasa de `queued` a `checked` tras una lectura autenticada.
Un worker que falle vuelve a `retry` con retraso, y acaba en `blocked` tras
agotar intentos. Para un nuevo ciclo de auditoría, se requiere una política
de reencolado explícita (no implementada en esta primera entrega).
