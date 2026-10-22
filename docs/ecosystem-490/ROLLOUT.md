# Despliegue gradual de herramientas y verificaciones

## Fase 0 — inventario completo

Exportar repositorios con paginación real desde GitHub CLI/API y guardar el JSON fuera del repositorio si incluye campos privados. Comprobar:
- número de elementos y páginas;
- repositorios duplicados por ID;
- repositorios archivados, privados y forks;
- fecha del snapshot y hash SHA-256;
- que el inventario no contenga tokens ni variables de entorno.

No usar como inventario definitivo una respuesta parcial del conector: la consulta que se ejecutó durante esta revisión devolvió 100 repositorios y no permitió recuperar páginas posteriores mediante offsets.

## Fase 1 — piloto (3 repos)

Elegir tres perfiles distintos: producto web activo, herramienta/librería y archivo/lab. Ejecutar en modo solo lectura primero. Registrar coste, falsos positivos, tiempo, archivos generados y riesgos. No tocar ramas principales.

## Fase 2 — familias de producto

Agrupar por evidencias: manifiestos, dependencias, rutas/imports, hashes de archivos, historial de commits, assets y finalidad real. Un nombre parecido no demuestra duplicación; un nombre distinto no descarta que sea la misma aplicación.

Para cada familia, documentar:
- canónico propuesto y por qué;
- variantes y diferencias funcionales;
- evidencia de procedencia;
- enlaces de despliegue y dominios;
- decisión de mantener, integrar, redirigir o archivar;
- persona/propietario que aprueba.

## Fase 3 — ejecutar herramientas según pertinencia

| Perfil | Superpowers | Impeccable | Graphify | Seguridad |
|---|---|---|---|---|
| App web / producto | Sí, para cambios | Sí, si hay UI | Sí, si aporta mapa útil | Sí |
| Librería/CLI | Sí, para cambios | No salvo UI | Sí, si compatible | Sí |
| Skill / documentación | Plan y revisión ligera | No | Opcional | Escaneo de links/secretos |
| Archivo/snapshot | Solo lectura | No | Opcional | No modificar contenido sin necesidad |
| Datos sensibles | Solo con sandbox y permisos mínimos | No | Solo local y autorizado | Prioridad P0 |

## Fase 4 — PRs de cambio

- Una familia o lote pequeño por PR.
- TDD y revisión independiente en cambios de lógica.
- No subir grafos que incluyan rutas privadas, nombres de clientes, código fuente o metadatos sensibles a repositorios públicos.
- No publicar automáticamente, no añadir licencias automáticamente, no borrar duplicados, no reescribir historial y no desplegar masivamente.
- Verificar los cambios en el commit exacto del PR y adjuntar logs saneados.

## Métricas de mejora

- % de repos con inventario íntegro.
- % con backup probado, no solo ZIP existente.
- % con licencia revisada.
- % con secret scan completado.
- % con CI real (no jobs vacíos ni tests omitidos).
- % con README que describe el estado real.
- candidatos a duplicado confirmados/rechazados.
- tiempo y coste por repo; fallos/falsos positivos por herramienta.
- canónicos aprobados y variantes con decisión trazable.

El objetivo no es maximizar el número de repos publicados: es maximizar productos claros, mantenibles, seguros y verificables.
