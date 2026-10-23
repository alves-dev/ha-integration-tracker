# SDD: Detecção Automática de Usos

## Status

Proposto. Este documento descreve o desenho e as tarefas de implementação. Nenhuma
parte deste SDD implica que a implementação já tenha sido iniciada.

## Problema

O Integration Tracker atualmente registra usos manualmente. Isso exige que o
usuário conheça previamente todos os dashboards, automações, scripts e demais
configurações que dependem de um repositório.

O novo recurso deve descobrir essas referências sem destruir o contexto manual e
sem tratar uma referência incerta como uma associação confirmada.

## Escopo

### Incluído

- modelo persistente para usos detectados;
- detectores para integrações, dashboards, automações e scripts;
- suporte inicial a recursos Lovelace;
- confiança, evidência, confirmação e estado obsoleto;
- sincronização e deduplicação de resultados;
- comandos WebSocket protegidos por administrador;
- visualização e revisão dos candidatos no painel;
- testes unitários e de persistência.

### Posterior ao MVP

- cenas;
- blueprints;
- temas;
- Python scripts e templates com associações indiretas;
- análise de dependências entre automações e scripts;
- relatórios ou sensores de usos obsoletos.

## Modelo de dados proposto

Expandir `Usage` sem alterar o significado dos usos manuais:

```text
id: identificador interno
name: nome apresentado ao usuário
type: dashboard | automation | script | integration | resource | ...
url: caminho Home Assistant ou URL externa opcional
source: manual | detected
detection_key: chave estável para deduplicação
confidence: high | medium | low
confirmed: boolean
stale: boolean
last_seen_at: timestamp opcional
evidence: objeto serializado com local e referência encontrados
```

Campos gerenciados pelo detector só podem ser atualizados para usos com
`source=detected`. Usos `source=manual` continuam sob controle exclusivo do
usuário.

## Chaves e deduplicação

Cada detector deve produzir uma `detection_key` determinística, por exemplo:

```text
automation:<automation_id>:service:<domain.service>
script:<script_id>:entity:<entity_id>
dashboard:<dashboard_id>:resource:<resource_url>
```

A chave deve ser independente do texto exibido no painel. Alterar o nome de uma
automação não deve criar um novo uso se a referência estrutural continuar sendo a
mesma.

## Arquitetura proposta

```text
Home Assistant state/configuration
              ↓
       detector coordinator
              ↓
      normalized detections
              ↓
        matching engine
              ↓
     registry usage reconciliation
              ↓
       WebSocket API + panel
```

Criar um subsistema de detectores com responsabilidades separadas:

```text
usage_detection/
├── base.py
├── coordinator.py
├── models.py
├── matching.py
├── integrations.py
├── dashboards.py
├── automations.py
└── scripts.py
```

Os detectores devem retornar um modelo comum. O registry deve continuar sendo o
único responsável por validação, mutação e persistência.

## Contrato dos detectores

Cada detector deve:

- ser assíncrono quando depender de APIs do Home Assistant;
- retornar uma lista completa dos resultados que consegue observar;
- não modificar configurações do usuário;
- indicar o tipo de local, a referência, a evidência e a confiança;
- tolerar uma fonte indisponível sem apagar o histórico existente;
- distinguir ausência de dados de uma lista vazia confiável.

Uma fonte indisponível não pode marcar todos os usos daquela fonte como obsoletos.

## Detecção por categoria

### Integrações

Implementar um detector que relacione config entries, entidades, dispositivos,
domínios e serviços aos `TrackedItem` conhecidos. Usar os metadados do provider
para gerar fingerprints e manter a associação dentro da fronteira provider/user.

### Dashboards

Implementar adaptadores separados para dashboards Lovelace armazenados e YAML.
Extrair entidades, serviços, cartões customizados e recursos externos. Cada
resultado deve guardar dashboard, view e referência quando possível.

### Automações

Ler automações da UI e YAML, examinando triggers, conditions e actions. Detectar
entidades, dispositivos, eventos, serviços e scripts chamados.

### Scripts

Ler scripts da UI e YAML, examinando sequências, serviços, entidades, dispositivos
e scripts encadeados.

## Reconciliação

Adicionar uma operação de domínio dedicada, por exemplo:

```text
async_reconcile_detected_usages(detections)
```

Essa operação deve:

1. validar os resultados;
2. agrupar por `item_id` e `detection_key`;
3. atualizar usos detectados existentes;
4. criar novos usos não confirmados;
5. marcar como obsoletos os usos detectados ausentes;
6. ignorar ou preservar candidatos explicitamente ignorados;
7. manter usos manuais sem alterações;
8. persistir uma única vez por reconciliação.

## API do painel

Adicionar comandos administrativos como:

| Comando | Objetivo |
| --- | --- |
| `integration_tracker/usage/detect` | Executar uma verificação sob demanda |
| `integration_tracker/usage/confirm` | Confirmar um uso detectado |
| `integration_tracker/usage/ignore` | Ignorar um candidato |
| `integration_tracker/usage/convert` | Converter candidato em uso manual |
| `integration_tracker/usage/refresh` | Atualizar a detecção de um item |

Os comandos devem seguir o padrão existente de WebSocket: autenticação de
administrador, schema validado, handlers finos e erros de domínio.

## Alterações no painel

No detalhe do repositório, separar:

- usos confirmados;
- candidatos encontrados;
- usos obsoletos;
- evidência da detecção;
- nível de confiança;
- data da última observação.

Cada candidato deve permitir confirmar, ignorar, editar, converter para manual e
abrir o local correspondente.

## Execução

Inicialmente, a detecção deve ser acionada:

- após uma sincronização bem-sucedida;
- pelo botão de verificação manual;
- opcionalmente na inicialização, depois que as fontes estiverem carregadas.

Uma configuração futura pode controlar a detecção automática. O primeiro MVP não
deve criar um agendador independente sem necessidade comprovada.

## Tasks de implementação

### Fase 0 — Contratos e decisão

- [ ] Confirmar os campos finais de `Usage`.
- [ ] Definir a política para candidatos ignorados e usos obsoletos.
- [ ] Definir os tipos de uso suportados no MVP.
- [ ] Definir as fontes oficiais para dashboards UI, dashboards YAML,
      automações e scripts.
- [ ] Registrar a decisão arquitetural antes de alterar o código.

### Fase 1 — Modelo e registry

- [x] Evoluir `Usage` para suportar origem manual/detectada.
- [x] Adicionar confiança, evidência, `detection_key` e `last_seen_at`.
- [x] Implementar serialização compatível com registros existentes.
- [x] Implementar reconciliação de detecções no registry.
- [x] Preservar usos manuais durante todas as reconciliações.
- [x] Definir a transição de usos detectados ausentes para obsoletos.
- [x] Criar testes de reload, deduplicação e migração de dados.

### Fase 2 — Matching de integrações

- [x] Extrair fingerprints de `ProviderItem` e das integrações carregadas.
- [x] Mapear domínios, serviços e entidades.
- [ ] Mapear dispositivos e áreas.
- [x] Implementar associação de alta confiança.
- [x] Implementar classificação média/baixa sem confirmação automática.
- [x] Criar testes com integrações Core e customizadas.

### Fase 3 — Detector de dashboards

- [x] Implementar leitura do dashboard Lovelace armazenado.
- [x] Implementar leitura de dashboard YAML.
- [x] Extrair entidades e serviços usados por cartões.
- [x] Extrair cartões customizados.
- [x] Extrair recursos JavaScript externos.
- [x] Gerar links ou evidências de dashboard, view e cartão.
- [x] Criar testes para os dois formatos de dashboard.

### Fase 4 — Detectores de automações e scripts

- [x] Implementar leitura das automações da UI.
- [x] Implementar leitura das automações YAML.
- [x] Implementar leitura dos scripts da UI.
- [x] Implementar leitura dos scripts YAML.
- [x] Extrair entidades e serviços.
- [ ] Extrair dispositivos, áreas e eventos.
- [ ] Detectar chamadas entre automações e scripts como dependências próprias.
- [x] Criar testes para estruturas aninhadas e ações múltiplas.

### Fase 5 — Coordinator e ciclo de sincronização

- [ ] Criar o coordinator dos detectores.
- [ ] Diferenciar snapshot vazio de fonte indisponível.
- [ ] Integrar a reconciliação após sincronização bem-sucedida.
- [ ] Adicionar execução manual pelo WebSocket.
- [ ] Garantir que falha de um detector não corrompa os demais resultados.
- [ ] Registrar logs úteis sem expor conteúdo sensível das configurações.

### Fase 6 — WebSocket e painel

- [ ] Adicionar schemas e handlers para candidatos detectados.
- [ ] Adicionar confirmação, ignorar e conversão para manual.
- [ ] Exibir confiança, evidência, estado obsoleto e última detecção.
- [ ] Adicionar estado de carregamento e erros parciais.
- [ ] Adicionar filtro por origem e estado do uso.
- [ ] Testar acesso somente de administradores.

### Fase 7 — Qualidade e documentação

- [ ] Atualizar `docs/api.md`.
- [ ] Atualizar `docs/architecture.md` após a implementação.
- [ ] Atualizar README com o comportamento da feature.
- [ ] Adicionar testes de regressão para usos manuais.
- [ ] Executar Ruff, pytest, cobertura e validação estrutural.
- [ ] Atualizar intent, decisão e changelog do Context Mesh.

## Critérios de aceite

- Um uso manual permanece intacto após qualquer detecção.
- A mesma referência não aparece duplicada após várias verificações.
- Uma fonte indisponível não transforma seus usos em obsoletos.
- Um novo candidato mostra local, referência, confiança e evidência.
- O administrador consegue confirmar ou ignorar um candidato.
- O painel diferencia uso confirmado, candidato e uso obsoleto.
- A detecção não altera automações, scripts, dashboards ou arquivos de configuração.
- Registros antigos continuam carregando normalmente.
