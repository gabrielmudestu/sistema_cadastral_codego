-- Migração: suporte a múltiplos tipos de documento (ex: Anexo VIII-D)

ALTER TABLE processos_documentos
    ADD COLUMN tipo_documento VARCHAR(50) NOT NULL DEFAULT 'anexo_viii_d' AFTER protocolo,
    ADD COLUMN dados_formulario JSON NULL AFTER tipo_documento;
