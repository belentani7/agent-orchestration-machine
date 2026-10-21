# Gobierno del ecosistema de repositorios (baseline inicial)

**Estado:** propuesta versionada en rama; no implica que se hayan modificado los 487/490 repositorios.  
**Objetivo:** inventariar, verificar y mejorar cada repositorio con evidencia reproducible, conservando los originales y evitando cambios masivos ciegos.

## Principios

1. **Fuente de verdad:** inventario vivo obtenido de GitHub API; no asumir que un inventario anterior sigue actualizado.
2. **No publicar automáticamente:** visibilidad, licencia y archivado requieren revisión de propiedad intelectual y secretos.
3. **No reescribir en masa:** añadir primero inventario, verificación y puntuación; reparar por familia y riesgo.
4. **Evidencia antes de afirmar:** cada control registra comando, fecha, resultado, commit y enlace al log.
5. **Canónico ≠ más nuevo:** elegir canónico según contenido, procedencia, producto y despliegue; no solo por nombre o tamaño.
6. **Originales preservados:** snapshots y variantes se marcan; no se borran ni fusionan sin comparación y backup restaurable.
7. **Herramientas centrales:** mantener las herramientas de agentes una vez en el entorno de desarrollo y distribuir configuración/políticas; no copiar sus fuentes completas a cientos de repositorios sin necesidad.
8. **Cambios aditivos primero:** rama/PR por lote, CI y revisión antes de mergear.

## Estado real de la investigación

- La conexión GitHub autenticada identifica al usuario belentani7.
- El endpoint de listado devolvió una página de hasta 100 repositorios; los intentos de offsets siguientes no devolvieron páginas adicionales. Por tanto, esta conexión no ha verificado todavía los 487/490 completos.
- Se han leído los README/licencias oficiales de Superpowers, Impeccable, Graphify y CodeGraff. Esto es investigación de sus repositorios, no una clonación local.
- No se afirma que se haya ejecutado el análisis completo de código, tests, builds, secretos o despliegues de todos los repositorios.
- Este paquete es el primer cambio de gobierno centralizado. La aplicación repo por repo se hará solo a partir de un inventario exportado y con resultados registrados.

## Flujo por repositorio

1. Capturar metadata y rama predeterminada.
2. Detectar archivos y stack (package manifests, lockfiles, pyproject, go.mod, Dockerfiles, workflows).
3. Identificar secretos sin imprimir sus valores; los escáneres locales deben ejecutarse con salida saneada.
4. Clasificar licencia: presente / ausente / incierta; nunca añadir una licencia por lote sin autorización del titular.
5. Detectar builds y pruebas reales según el proyecto. No tratar un repositorio de documentación, skill o archivo como app web.
6. Detectar candidatos a duplicado por hashes y señales semánticas; confirmar manualmente antes de archivar.
7. Revisar configuración de despliegue y URL canónica cuando corresponda.
8. Crear VERIFICACION.md con estado PASS / FAIL / NOT RUN / BLOCKED y referencias a evidencia.
9. Abrir PR de reparación por lote pequeño; no publicar ni cambiar visibilidad automáticamente.

## Herramientas

- Superpowers: metodología de descubrimiento, planificación, TDD, revisión y verificación.
- Impeccable: auditoría de diseño solo para proyectos con interfaz; no se aplica a CLI, librerías o repositorios de datos como si fueran frontend.
- Graphify: grafo de código/dependencias y consultas de relaciones cuando sea compatible con el stack.
- CodeGraff: agente terminal opcional; su licencia contiene términos AGPL modificados y reservas de derechos comerciales/cloud. No distribuir ni desplegar como servicio del ecosistema antes de una revisión legal.
- Gitleaks / TruffleHog: análisis de secretos local o CI, con salida saneada.
- GitHub Actions: validación por stack y artefactos de logs.
- Vercel: solo para apps web que realmente lo requieran.

## Prioridad inicial

- **P0:** secretos, credenciales, datos personales, despliegue expuesto, integridad de backups.
- **P1:** productos con usuarios/valor comercial y despliegues rotos.
- **P2:** experiencia de marca, apps creativas y proyectos con potencial de portfolio.
- **P3:** labs, pruebas y experimentos.
- **ARCHIVED:** conservar, documentar procedencia y evitar cambios funcionales no necesarios.

## Criterio de finalización

Un repositorio solo se declara verificado cuando todos los controles aplicables tienen estado y evidencia. NOT RUN no es PASS; un build local no prueba despliegue; un despliegue READY no prueba salud funcional; una licencia ausente no se corrige automáticamente.
