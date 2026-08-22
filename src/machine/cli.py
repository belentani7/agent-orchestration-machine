from __future__ import annotations

import argparse
import json

from machine.bootstrap import build_machine
from machine.domain.models import TaskRequest, TenantContext


def main() -> None:
    parser = argparse.ArgumentParser(description="Núcleo local de orquestación de agentes")
    parser.add_argument("--demo", action="store_true", help="Ejecuta una tarea de inferencia con adaptador local")
    parser.add_argument("--health", action="store_true", help="Ejecuta una verificación del núcleo")
    args = parser.parse_args()
    if not (args.demo or args.health):
        parser.error("Elija --demo o --health")

    orchestrator, audit, _ = build_machine()
    context = TenantContext(tenant_id="tenant-demo", actor_id="operator-demo", roles=frozenset({"operator"}))
    request = TaskRequest(
        capability="health.check" if args.health else "text.infer",
        payload={} if args.health else {"prompt": "Validar la estructura de la máquina."},
        max_budget_usd=0.01,
    )
    task = orchestrator.submit(context, request)
    print(json.dumps({"task": task.snapshot(), "audit": audit.records_for(context.tenant_id, task.id)}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
