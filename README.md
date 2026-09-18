# Radar Concurso

Sistema de monitoramento automatizado de concursos públicos.

## Objetivo

Monitorar diariamente fontes oficiais e portais especializados, identificar oportunidades de concursos e notificar o usuário por e-mail e push.

## Arquitetura de nichos

O projeto será organizado por **nichos** e **subnichos**, permitindo expansão sem alteração estrutural do núcleo do sistema.

### Nichos planejados

- Administrativo
  - Contabilidade
  - Fiscal
  - Finanças
  - Gestão
  - Auditoria
  - Departamento Pessoal
  - Recursos Humanos
- Saúde
  - Enfermagem
  - Técnico em Enfermagem
  - Medicina
  - Radiologia
  - Fisioterapia
- Segurança Pública
  - Polícia Militar
  - Polícia Civil
  - Polícia Rodoviária Federal
  - Outros subnichos

## Princípios

- Fonte oficial como referência definitiva.
- Separação entre coleta, filtragem, classificação e notificação.
- Controle de duplicidades.
- Configuração de nichos fora do código principal.
- Segredos e credenciais somente por variáveis de ambiente.
- Execução independente do ChatGPT.

## Status

Fase 1 — Estrutura inicial do projeto.
