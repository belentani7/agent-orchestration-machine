# Contrato de publicación — Octubre 2026

Aplicar **por producto existente**, no crear nuevos repositorios por cada idea. Preservar historias y archivos; distinguir núcleo, módulo, experimento, copia de seguridad y contenido privado antes de hacer cambios.

## Release gates comprobables

1. **Propósito y límites**: audiencia, problema, uso, diferenciación y promesas exactas del producto. Si su valor no se justifica, conservarlo como experimento en lugar de fabricar una identidad comercial.
2. **Contenido verdadero**: una escuela publica el temario, todas las lecciones prometidas, actividades y evaluaciones coherentes; una herramienta entrega resultados realmente funcionales. No convertir placeholders en claims comerciales.
3. **Experiencia**: home/landing real, navegación funcional, responsive y estados vacíos, errores, loading; dirección visual premium adecuada a **cada identidad**, no una plantilla universal.
4. **Accesibilidad**: WCAG 2.2 AA según aplicabilidad: teclado, foco visible, nombres accesibles, semántica, contraste, reduced motion, formularios y feedback.
5. **Ingeniería**: respetar stack y arquitectura existentes. No imponer Next.js ni migración masiva. Dependencias fijadas; separación de secretos, validación, control de acceso, CSP cuando proceda, protección CSRF/XSS/SSRF, límites y auditoría.
6. **Pruebas**: instalación reproducible, lint/types/build, tests unit/integration/E2E de cada promesa, regresión, análisis de dependencias, secretos y rutas críticas.
7. **Indexabilidad** (solo páginas destinadas a ser públicas): URL y HTTP accesibles, canonical, title/description, enlazado HTML, contenido rastreable, sitemap, idiomas/hreflang cuando exista contenido traducido, robots coherente y JSON-LD que describa lo que la página muestra. La vista previa, la documentación privada o el staging **no deben indexarse**.
8. **Operaciones**: preview con pruebas, smoke tests públicos, logs, monitoreo, rollback, privacidad/consentimiento y licencias de contenido verificadas.
9. **Promoción**: obligatoriamente evidencia de CI verde, revisión de secretos/datos personales y URL real funcional. No cambiar visibilidad GitHub automáticamente. No publicar música/fotografías/licencias de terceros sin derechos comprobados.

## Cambios frente al protocolo de ejecución adjunto

- No lanzar un agente como root; no loops infinitos sin presupuesto; no `git add -A && git push` automático.
- GitHub Actions `schedule` solo se ejecuta cuando el workflow está en rama por defecto; su runner puede quedar en cola.
- `Google-Extended` es un control de uso del contenido para ciertos productos de IA de Google, **no** una forma de mejorar indexación ni un crawler independiente.
- `llms.txt` es opcional para sistemas que lo utilizan; Google Search aclaró en junio de 2026 que no mejora ni empeora el posicionamiento.
- Datos estructurados no garantizan aparición en resultados.
- No inventar umbrales universales de Lighthouse que sustituyan pruebas funcionales.
- Un README, tests mínimos y una landing no convierten automáticamente un producto en terminado.

## Priorización

Trabajar en lotes de hasta tres con lease y tope de coste cuando existan workers aislados. Actualmente el inventariador es deliberadamente **solo lectura**. Un registro de tareas no equivale a ejecución autónoma y un resultado de pruebas no equivale a producto terminado.
