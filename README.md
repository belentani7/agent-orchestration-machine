# Máquina de Orquestación de Agentes

Esta entrega contiene el **núcleo local, ejecutable y sin interfaz web** de una plataforma de orquestación de agentes. El propósito es establecer las fronteras, contratos y controles antes de acoplar una API, una consola administrativa, una base de datos distribuida o proveedores externos.

> El proyecto no se presenta como una plataforma certificada ni desplegada. Los módulos de seguridad y cumplimiento son controles arquitectónicos iniciales; las certificaciones y garantías operativas requieren un programa formal, infraestructura y auditorías independientes.

## Alcance construido

| Elemento | Estado | Qué hace |
|---|---:|---|
| Núcleo de orquestación | Construido | Recibe una tarea, crea un plan, ejecuta pasos y conserva su estado. |
| Aislamiento lógico por tenant | Construido | Vincula cada tarea, auditoría y repositorio al identificador del tenant. |
| Máquina de estados | Construido | Impide transiciones no permitidas durante el ciclo de vida de una tarea. |
| Registro de agentes | Construido | Registra capacidades con permisos explícitos. |
| Enrutamiento LLM | Construido | Selecciona proveedores elegibles por presupuesto y usa fallback. |
| Bus de eventos y auditoría | Construido | Publica eventos internos y genera una traza inmutable en memoria. |
| Adaptadores de prueba | Construido | Incluye proveedor LLM determinista y repositorios en memoria. |
| Interfaz web / HTTP | Excluida | Se añadirá solo después de aprobar este núcleo. |
| Infraestructura productiva | Diferida | Las interfaces permiten conectar cola, base de datos, secret manager y observabilidad reales. |

## Ejecución local

El núcleo no depende de servicios externos. Desde la carpeta raíz:

```bash
PYTHONPATH=src python3 -m machine --demo
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Principios no negociables

| Principio | Aplicación en la base |
|---|---|
| Denegar por defecto | Las capacidades deben registrarse y autorizarse explícitamente. |
| Aislamiento primero | `TenantContext` viaja con la tarea y se valida en el repositorio. |
| Estado verificable | Cada transición se comprueba contra una tabla de transiciones permitidas. |
| Efectos auditables | Las decisiones de enrutamiento, pasos y resultados generan eventos de auditoría. |
| Dependencias invertidas | Dominio y aplicación no importan proveedores ni almacenamiento concretos. |
| Fallo controlado | El router intenta alternativas elegibles; si no existen, falla de forma explícita. |
| Evolución sin reescritura | Las abstracciones separan el núcleo de futuras colas, bases de datos y APIs. |

## Próxima decisión de producto

La estructura permite evolucionar por dos rutas, sin modificar el dominio: una **ejecución local monoproceso** para validación y pruebas, o una **ejecución distribuida** con cola, persistencia y workers. La elección se debe tomar después de validar los flujos de negocio prioritarios y sus requisitos de latencia, volumen y retención.

## Extensión comercial controlada

El repositorio incorpora una extensión comercial en `machine.commercial`: acepta contactos con procedencia y base de contacto registradas, suprime de inmediato a quien solicite baja, requiere aprobar propuestas antes de programarlas, limita envíos por día y entrega mediante un adaptador de ensayo o SMTP configurado por secretos de entorno. El detalle de diseño y activación está en [`docs/COMMERCIAL_OPERATING_SYSTEM.md`](docs/COMMERCIAL_OPERATING_SYSTEM.md).
