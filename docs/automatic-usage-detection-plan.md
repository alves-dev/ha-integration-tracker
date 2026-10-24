# Plano: Detecção Automática de Usos

## Objetivo

Permitir que o Integration Tracker descubra automaticamente onde cada integração,
plugin, tema, blueprint ou outro repositório rastreado é utilizado dentro do Home
Assistant.

A descoberta deve ser somente leitura. Ela não deve alterar automações, scripts,
dashboards ou configurações do usuário. Os resultados devem aparecer como usos
detectados, separados dos usos cadastrados manualmente.

## Princípios

- Usos manuais nunca são sobrescritos ou removidos pela detecção.
- Cada uso detectado deve possuir uma chave estável para evitar duplicidade.
- Toda associação deve apresentar a evidência que levou à detecção.
- Resultados incertos devem ser apresentados como candidatos, não como fatos.
- O desaparecimento de uma referência deve marcar o uso como obsoleto, sem
  apagar seu histórico imediatamente.
- A detecção deve funcionar mesmo quando uma fonte opcional estiver indisponível.

## Tipos de integração e locais de uso

### Integrações Core e customizadas

Detectar config entries, domínios carregados, entidades, dispositivos e serviços
fornecidos pela integração. Depois, procurar referências a esses domínios,
entidades e serviços em automações, scripts, cenas e dashboards.

As associações mais confiáveis são o domínio exato, um serviço fornecido pela
integração ou uma entidade criada por ela. O domínio do componente, os metadados
do Marketplace/HACS e os arquivos instalados devem formar os fingerprints usados
para a associação.

### Cartões e plugins Lovelace

Pesquisar cartões customizados em dashboards, views e configurações Lovelace.
Também detectar recursos JavaScript externos e recursos servidos pelo diretório
do repositório.

Exemplos de evidência:

- `custom:button-card` usado em uma view;
- recurso `/hacsfiles/<plugin>/<plugin>.js`;
- nome ou slug do cartão presente na configuração do dashboard.

### Temas

Detectar temas configurados, temas selecionados e referências a arquivos de tema.
O resultado deve indicar se o tema está apenas disponível, configurado ou ativo.

### Blueprints

Detectar automações e scripts criados a partir de blueprints, além de blueprints
instalados no diretório do repositório. A associação deve informar o blueprint e
as automações ou scripts que o utilizam.

### Python scripts, templates e extensões

**Status: não implementado.**

Detectar chamadas aos serviços, entidades ou ações fornecidos por esses
repositórios. Quando não for possível associar diretamente o arquivo ao
repositório, o resultado deve ser classificado com confiança média ou baixa.

## Locais de uso

### Dashboards e Lovelace

Pesquisar:

- entidades usadas em cartões;
- serviços chamados por cartões;
- cartões customizados;
- recursos JavaScript;
- dashboards armazenados pelo Home Assistant;
- dashboards configurados em YAML;
- views e títulos de dashboards.

Cada resultado deve registrar dashboard, view, cartão ou recurso quando essa
informação estiver disponível.

### Automações

Pesquisar referências em triggers, conditions e actions, incluindo:

- entidades;
- dispositivos;
- eventos;
- chamadas de serviço;
- automações criadas pela UI e automações em YAML.

### Scripts

Pesquisar entidades, dispositivos, serviços e sequências em
scripts criados pela UI ou definidos em YAML.

### Cenas

Pesquisar entidades e serviços utilizados nas cenas e associá-los ao domínio ou
à integração correspondente.

### Configuração de integrações

Registrar config entries, dispositivos, entidades e serviços como usos ou como
evidência de instalação ativa. Essa informação deve ser distinta de uma
referência explícita em automação ou dashboard.

## Confiança da detecção

### Alta

- domínio exato de uma integração customizada;
- serviço fornecido pelo repositório;
- recurso Lovelace cujo caminho identifica o repositório;
- blueprint instalado dentro do repositório;
- cartão customizado identificado diretamente nos metadados do repositório.

### Média

- nome do domínio semelhante ao nome do repositório;
- nome do cartão parcialmente compatível;
- entidade pertencente a uma integração que pode ser associada ao repositório;
- URL do recurso contendo o mesmo slug do repositório.

### Baixa

- correspondência somente por texto ou comentário;
- associação indireta sem domínio, serviço ou recurso identificável.

Resultados de confiança média ou baixa devem exigir confirmação do administrador.

## Fluxo de atualização

1. Sincronizar os repositórios pelos providers existentes.
2. Executar os detectores locais disponíveis.
3. Gerar uma chave estável para cada resultado.
4. Atualizar a data `last_seen_at` dos usos encontrados.
5. Criar novos candidatos como usos detectados não confirmados.
6. Marcar como obsoletos os usos detectados que não apareceram na verificação.
7. Preservar usos manuais e seus dados.
8. Persistir a alteração de forma atômica.

## Entrega recomendada

O MVP deve cobrir, nesta ordem:

1. Integrações backend, entidades e serviços.
2. Dashboards e recursos Lovelace.
3. Automações.
4. Scripts.
5. Blueprints e cenas.
6. Temas e análise indireta de templates/Python.

O painel deve oferecer uma fila de candidatos com as ações confirmar, ignorar,
editar, converter para uso manual e abrir o local encontrado.
