# Catálogo complementario — herramientas para el ecosistema

Revisión web de fuentes oficiales: 2026-10-22. Elegir por riesgo y tipo de proyecto; no instalar cada herramienta en todos los repositorios por defecto.

## Catálogos de skills

- [anthropics/skills](https://github.com/anthropics/skills): ejemplos de skills de desarrollo, creatividad y tareas empresariales. El README advierte que parte del material es demostrativo y que algunas subcarpetas de documentos son source-available, no open source. Revisar la licencia por carpeta antes de redistribuir.
- [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills): colección oficial de skills de Vercel. Usar skills concretas para flujos web/React y verificar la licencia de cada carpeta.
- [obra/superpowers](https://github.com/obra/superpowers): metodología general de ingeniería; MIT verificado. Complementa catálogos, no los reemplaza.

**Regla de selección:** cada skill debe declarar trigger, entradas, permisos, pasos, verificación, fallos conocidos y fuente/licencia. No copiar una colección entera a 490 repositorios; instalar solo las skills relevantes y versionarlas de forma central.

## Seguridad de repositorios y CI

- [gitleaks/gitleaks](https://github.com/gitleaks/gitleaks): escáner de secretos para Git, archivos y directorios; licencia MIT verificada. Complementar escaneo de working tree con escaneo del historial. Cero hallazgos no prueba ausencia absoluta de secretos.
- [trufflesecurity/trufflehog](https://github.com/trufflesecurity/trufflehog): busca y verifica credenciales filtradas; el repositorio declara AGPL-3.0. Revisar términos antes de redistribuir o incorporar como servicio comercial. No imprimir los valores encontrados; rotar las credenciales confirmadas.
- [zizmorcore/zizmor](https://github.com/zizmorcore/zizmor): análisis estático de workflows GitHub Actions; MIT verificado. Útil para permisos excesivos, credenciales persistentes y referencias inseguras de actions. Importante: una salida SARIF puede devolver código cero aunque haya findings; el workflow debe evaluar los hallazgos y bloquear según política, no fiarse solo del check verde.
- [OSV-Scanner](https://github.com/google/osv-scanner): candidato para detectar dependencias afectadas por vulnerabilidades usando manifiestos/lockfiles; validar soporte de ecosistemas y salida antes de estandarizarlo.

## Grafo de código vs agente terminal

| Herramienta | Función principal | Uso recomendado |
|---|---|---|
| Graphify | Grafo de símbolos, imports y documentación; consultas con confianza extraída/inferida | Análisis local en familias con muchos módulos y dependencias |
| CodeGraff / graff | Agente terminal que puede leer/editar archivos y ejecutar comandos | Solo en sandbox, permisos mínimos y revisión legal de licencia modificada |
| Superpowers | Proceso de ingeniería basado en skills | Plan, TDD, debugging, revisión y cierre |
| Impeccable | Calidad de diseño frontend | Solo repos con UI; no aplicar a scripts, APIs sin UI o archivos |

## Política para la flota

1. Versionar herramientas y registrar commit/tag y checksum.
2. Fijar actions externas por SHA cuando se usen en CI.
3. Dar permisos mínimos a workflows y a agentes.
4. No permitir que una skill cambie visibilidad, licencias, secretos, historia Git o producción.
5. Ejecutar primero en tres repositorios representativos y medir falsos positivos, duración y coste.
6. Mantener los resultados por repo con estado PASS/FAIL/NOT RUN y log saneado.
7. Aplicar por familia y riesgo; los 490 repositorios no comparten necesariamente framework ni propósito.
