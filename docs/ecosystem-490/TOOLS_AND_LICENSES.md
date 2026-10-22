# Herramientas de agentes: selección, licencias y aplicación

Fecha de revisión: 2026-10-22. Las instrucciones de instalación cambian; verificar README y release actual antes de ejecutar.

## 1. Superpowers — metodología de desarrollo

- Origen: https://github.com/obra/superpowers
- Licencia verificada en LICENSE: MIT.
- README oficial leído mediante el conector GitHub. Describe skills y un flujo de trabajo: brainstorming, diseño, worktrees, plan por tareas, TDD, revisión y verificación.
- Instalación: específica del agente/editor. La guía oficial ofrece rutas para Codex, Claude Code, Cursor, Gemini CLI, Copilot CLI y otros; no asumir que un comando sirve para todos.
- Aplicación: activar primero en P1/P2 y en cambios no triviales. En repositorios de archivo o solo documentación, aplicar la parte de planificación/verificación pertinente sin forzar TDD innecesario.
- Instalar la herramienta no significa que el código esté corregido.

## 2. Impeccable — calidad de interfaz

- Origen: https://github.com/pbakaus/impeccable
- Licencia verificada en package.json: Apache-2.0.
- README: npx impeccable install, luego /impeccable init; declara comandos de diseño y reglas deterministas de detección.
- Versión observada en el package.json consultado: 4.7.0. Es una observación de la rama consultada, no una recomendación de fijar esa versión indefinidamente.
- Aplicación: solo en proyectos frontend/UI. Mantener PRODUCT.md y DESIGN.md específicos de cada producto; no compartir identidad visual de Belentani con NoiaCore.
- Antes de usar npx en CI, fijar versión y verificar flags de la versión instalada. No asumir que --ci existe sin comprobar la ayuda actual.

## 3. Graphify — grafo de código y documentación

- Origen: https://github.com/Graphify-Labs/graphify
- README oficial consultado: análisis local con AST/tree-sitter; consultas, rutas entre símbolos y relaciones con etiquetas de confianza. Algunas capacidades de documentos/media pueden depender de backends configurados.
- Uso recomendado: empezar con 3 repositorios representativos y medir utilidad, coste y falsos positivos; después generar grafos por repositorio y agregar solo metadatos/enlaces autorizados.
- No tratar una relación inferida como hecho extraído; preservar la distinción de confianza de la herramienta.
- Verificar licencia y versión en el checkout exacto antes de redistribuir. No enviar código privado a servicios cloud sin una decisión explícita de privacidad.

## 4. CodeGraff / graff — agente terminal

- Origen: https://github.com/justrach/codegraff
- El LICENSE consultado declara AGPL-3.0 modificado y reserva derechos comerciales/cloud a los titulares. No es una licencia estándar que deba tratarse como AGPL simple.
- Recomendación: no incorporarlo como servicio, redistribuirlo ni copiar su código al ecosistema hasta revisar jurídicamente los términos completos. Puede evaluarse en entorno aislado sin acceso a secretos.
- No ejecutar curl | sh sin inspeccionar el script, validar checksum/firma y conocer los cambios que realiza en PATH/configuración.

## Política común

- Fijar versiones y registrar commit/tag + SHA-256 del artefacto descargado.
- Inspeccionar scripts de instalación antes de ejecutarlos.
- Ejecutar agentes en worktree aislado, con permisos mínimos y sin secretos por defecto.
- Prohibir cambios de visibilidad, licencias, borrados, reescritura de historial y despliegues masivos como efecto implícito de una skill.
- Guardar evidencia saneada; no guardar tokens, .env, dumps de datos personales ni resultados que expongan secretos.
