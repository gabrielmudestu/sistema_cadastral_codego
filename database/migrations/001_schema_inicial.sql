-- Schema inicial: Sistema Cadastral CODEGO

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    cpf_cnpj VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,
    telefone VARCHAR(30),
    cargo VARCHAR(100),
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS processos_documentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    protocolo VARCHAR(50) NOT NULL UNIQUE,
    caminho_pdf_preenchido VARCHAR(500),
    caminho_pdf_assinado VARCHAR(500),
    status ENUM('Pendente', 'Assinado', 'Cancelado') NOT NULL DEFAULT 'Pendente',
    texto_recibo TEXT,
    data_geracao DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_upload_assinado DATETIME NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS mensagens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    processo_id INT NULL,
    remetente_nome VARCHAR(255) NOT NULL,
    assunto VARCHAR(255) NOT NULL,
    conteudo TEXT NOT NULL,
    data_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (processo_id) REFERENCES processos_documentos(id)
);

CREATE TABLE IF NOT EXISTS anexos_mensagem (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mensagem_id INT NOT NULL,
    nome_original VARCHAR(255) NOT NULL,
    caminho_storage VARCHAR(500) NOT NULL,
    tamanho_bytes BIGINT NOT NULL,
    tipo_mime VARCHAR(100) NOT NULL,
    FOREIGN KEY (mensagem_id) REFERENCES mensagens(id)
);
