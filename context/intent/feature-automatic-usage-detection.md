# Feature: Detecção Automática de Usos

## What

Descobrir automaticamente onde os repositórios rastreados são usados em
integrações, dashboards, cartões Lovelace, automações, scripts, cenas, blueprints,
temas e outros recursos do Home Assistant. Apresentar os resultados com evidência,
nível de confiança e possibilidade de confirmação pelo administrador.

## Why

O cadastro manual não escala e pode deixar ocultas dependências importantes. A
detecção automática ajuda o usuário a avaliar o impacto de atualizar, substituir
ou remover um repositório.

## Acceptance Criteria

- [ ] Usos manuais permanecem intactos durante a detecção.
- [ ] Usos detectados têm origem, chave estável, confiança, evidência e última
      observação.
- [ ] O sistema diferencia resultado confirmado, candidato e referência obsoleta.
- [ ] Dashboards, automações e scripts são cobertos no MVP.
- [ ] Uma fonte indisponível não apaga nem obsoleta indevidamente seu histórico.
- [ ] Administradores podem confirmar, ignorar ou converter candidatos em usos
      manuais.
- [ ] O sistema não modifica dashboards, automações, scripts ou configurações.

## Related

- [Project Intent](project-intent.md)
- [Plano da detecção](../../docs/automatic-usage-detection-plan.md)
- [SDD da detecção](../../docs/automatic-usage-detection-sdd.md)
- [Decision: Persistent Registry and Snapshot Synchronization](../decisions/003-persistent-registry-synchronization.md)
- [Decision: Administrator Panel and WebSocket API](../decisions/004-administrator-panel-api.md)
- [Pattern: Ownership-Preserving Synchronization](../knowledge/patterns/ownership-preserving-synchronization.md)
- [Pattern: Registry Domain Operations](../knowledge/patterns/registry-domain-operations.md)

## Status

- **Created**: 2026-10-23 (Phase: Intent)
- **Status**: Proposed (not implemented)
