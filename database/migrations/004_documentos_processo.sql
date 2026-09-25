-- Migração: documentos que acompanham o requerimento
-- No Anexo III a pessoa marca a documentação que acompanha o pedido; os
-- arquivos são enviados junto com o documento assinado (Etapa 2).
-- (O backend também cria esta tabela ao iniciar, via create_all.)

CREATE TABLE IF NOT EXISTS documentos_processo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    processo_id INT NOT NULL,
    codigo VARCHAR(100) NOT NULL,
    descricao VARCHAR(500) NOT NULL,
    nome_original VARCHAR(255) NOT NULL,
    caminho_storage VARCHAR(500) NOT NULL,
    tamanho_bytes BIGINT NOT NULL,
    tipo_mime VARCHAR(100) NOT NULL,
    data_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (processo_id) REFERENCES processos_documentos(id)
);
