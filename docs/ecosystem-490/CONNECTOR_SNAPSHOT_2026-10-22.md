# Estado cruzado de conectores — 2026-10-22

Este documento registra lo que devolvieron las consultas de solo lectura de esta sesión. No sustituye una auditoría completa de código ni un inventario exportado con hash.

## GitHub

- Consulta paginada: `user:belentani7`, páginas 1–5, 100 resultados por página.
- Resultado: **490 repositorios**, **490 IDs únicos**, **490 nombres únicos**.
- Visibilidad observada: **489 privados y 1 público**.
- Archivados: **218**.
- Tamaño agregado reportado: **11.074.606 KB (~10,56 GiB)**.
- Implicación: la cifra 490 sí se confirma en el snapshot actual; no son 490 repositorios publicados. El inventario previo de 487 está obsoleto.
- Siguiente paso: ejecutar el exportador local con `gh api --paginate` y conservar JSON + SHA-256. No subir la lista completa de nombres privados a un repo ni a una herramienta cloud si no hace falta.

## Vercel

- La lista actual devolvió **96 proyectos** en la consulta.
- Coincidencias de nombres entre familias de interés incluyen: `registro-proyectos-2026`, `judas-experience-preview`, `belentani-cv-ai`, `belentani.es`, `noiacore-web`, `aion`, `heyduck`, `opendesign`, `linguaforge`, `lingua-aberta`, `universo-judas`, `judas-web-legacy`, `manos-abiertas`, `lingua-aberta-empresa`, `aion-showcase`.
- La llamada detallada a proyecto devolvió 404 aun con IDs obtenidos de la lista. Por tanto, **no se certifica aquí el estado de los deployments, variables o dominios**; hace falta resolver el contexto/permisos del endpoint y después inspeccionar cada proyecto.
- No asumir que todo repositorio GitHub debe tener deployment Vercel: librerías, skills, datos y archivos no son aplicaciones web.

## Supabase

- Proyectos encontrados: 2; ambos aparecen como **INACTIVE**.
- Regiones: `eu-west-1` y `eu-central-1`; ambos informan PostgreSQL 17.
- El endpoint de advisors de seguridad devolvió lista vacía para ambos. Dado que los proyectos están inactivos, esto **no se considera un PASS de seguridad ni de disponibilidad**.
- Acción: decidir si se reactivan, se conservan como archivo o se eliminan mediante proceso separado y backup; no reactivar automáticamente porque puede afectar facturación/servicios.

## Notion y Dropbox

- Búsqueda de inventario, herramientas y auditoría en Notion: cero resultados.
- Búsqueda de inventario y términos relacionados en Dropbox: cero resultados.
- Esto no demuestra que no existan documentos; solo que esas consultas no encontraron coincidencias en las fuentes conectadas.

## Conectores no disponibles en esta sesión

No se expuso un conector operativo de Google Drive/Gmail ni Linear en el runtime actual. No se atribuyen resultados a esas plataformas. El texto adjunto menciona inventarios y tareas anteriores, pero sus afirmaciones históricas no se tratan como estado vivo hasta volver a comprobarlas.

## Cambios GitHub en esta sesión

### Gobierno central

- Repositorio: `belentani7/agent-orchestration-machine`
- Rama: `feat/ecosystem-490-tooling-governance`
- PR borrador: https://github.com/belentani7/agent-orchestration-machine/pull/18
- Estado: abierto, borrador, sin merge.
- Incluye guía de gobierno, revisión de herramientas/licencias, plantilla VERIFICACION.md, plan de despliegue gradual, exportador de inventario, generador de scaffolds, script de checkout seguro de herramientas y guía local.

### Piloto de verificación en tres repositorios

- Aion: https://github.com/belentani7/aion/pull/8 — baseline marca **NO RELEASE** tal como ya indica el README; pruebas/build/seguridad siguen NOT RUN.
- Belentani.cv-ai: https://github.com/belentani7/Belentani.cv-ai/pull/77 — documenta drift real: README dice Next.js 15 y package.json declara ^16.3.8; tests/build/seguridad siguen NOT RUN.
- LumaQuote: https://github.com/belentani7/lumaquote/pull/1 — package.json declara MIT, pero no se encontró un LICENSE raíz en la consulta; tests/build/seguridad siguen NOT RUN.

Los tres PRs de piloto son borradores, de un solo archivo cada uno y sin cambios de código de aplicación. Ninguno está mergeado. No se han cambiado ramas principales, visibilidad, licencias, secretos, historial Git ni deployments.
