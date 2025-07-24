-- SCRIPT DE CRIAÇÃO DE TABELAS
CREATE TABLE Campanha (
    Id_Campanha SERIAL NOT NULL,
    Nome VARCHAR(100) NOT NULL,
    Doenca_alvo VARCHAR(100) NOT NULL,
    Tipo_vacina VARCHAR(30) NOT NULL,
    Data_inicio DATE NOT NULL,
    Data_fim DATE,
    Publico_alvo VARCHAR(100) NOT NULL,
    PRIMARY KEY (Id_Campanha)
);

CREATE TABLE Vacina (
    Id_Vacina SERIAL NOT NULL,
    Nome VARCHAR(100) NOT NULL,
    Doenca_alvo VARCHAR(100) NOT NULL,
    Codigo_Lote VARCHAR(100) NOT NULL,  
    Data_Chegada DATE NOT NULL,
    Data_Validade DATE NOT NULL,
    Qtd_Doses INT NOT NULL,
    PRIMARY KEY (Id_Vacina)
);

CREATE TABLE Local (
    Id_Local SERIAL NOT NULL,
    Nome VARCHAR(100) NOT NULL,
    Rua VARCHAR(100) NOT NULL,
    Bairro VARCHAR(100) NOT NULL,
    Numero INT NOT NULL,
    Cidade VARCHAR(100) NOT NULL,
    Estado VARCHAR(50) NOT NULL,
    Contato VARCHAR(100) NOT NULL,
    Capacidade INT,
    PRIMARY KEY (Id_Local)
);

CREATE TABLE Usuario (
    Nome VARCHAR(100) NOT NULL,
    CPF VARCHAR(20) NOT NULL,
    Telefone VARCHAR(100) NOT NULL,
    PRIMARY KEY (CPF)
);

CREATE TABLE Administrador (
    Local_Trabalho VARCHAR(100) NOT NULL,
    CPF VARCHAR(20) NOT NULL,
    PRIMARY KEY (CPF),
    FOREIGN KEY (CPF) REFERENCES Usuario(CPF) ON DELETE CASCADE
);

CREATE TABLE Cidadao (
    Cartao_Sus VARCHAR(100),
    Rua VARCHAR(100),
    Bairro VARCHAR(100),
    Numero INT,
    Cidade VARCHAR(100),
    Estado VARCHAR(50),
    CPF VARCHAR(20) NOT NULL,
    PRIMARY KEY (CPF),
    FOREIGN KEY (CPF) REFERENCES Usuario(CPF) ON DELETE CASCADE
);

CREATE TABLE Agente_saude (
    Email VARCHAR(100) NOT NULL,
    Posto_Trabalho VARCHAR(100) NOT NULL,
    CPF VARCHAR(20) NOT NULL,
    PRIMARY KEY (CPF),
    FOREIGN KEY (CPF) REFERENCES Usuario(CPF) ON DELETE CASCADE
);

CREATE TABLE Vacinacao (
    Id_Vacinacao SERIAL NOT NULL,
    Contagem INT NOT NULL,
    Data_aplicacao DATE NOT NULL,
    Id_Vacina INTEGER NOT NULL,
    CPF VARCHAR(20) NOT NULL,
    Id_Local INTEGER NOT NULL,    
    Id_Campanha INTEGER NOT NULL, 
    PRIMARY KEY (Id_Vacinacao),
    FOREIGN KEY (Id_Vacina) REFERENCES Vacina(Id_Vacina),
    FOREIGN KEY (CPF) REFERENCES Cidadao(CPF),
    FOREIGN KEY (Id_Local) REFERENCES Local(Id_Local),
    FOREIGN KEY (Id_Campanha) REFERENCES Campanha(Id_Campanha)
);

CREATE TABLE Parente (
    Id_Parentesco SERIAL NOT NULL,
    CPF_Responsavel VARCHAR(20) NOT NULL,
    CPF_Parente VARCHAR(20) NOT NULL,
    PRIMARY KEY (Id_Parentesco),
    FOREIGN KEY (CPF_Responsavel) REFERENCES Cidadao(CPF),
    FOREIGN KEY (CPF_Parente) REFERENCES Cidadao(CPF)
);

CREATE TABLE Agendamento (
    Id_Agendamento SERIAL NOT NULL,
    Data_Agendamento DATE NOT NULL,
    Id_Vacina INTEGER NOT NULL,   
    Id_Local INTEGER NOT NULL, 
    CPF VARCHAR(20) NOT NULL,
    PRIMARY KEY (Id_Agendamento),
    FOREIGN KEY (Id_Vacina) REFERENCES Vacina(Id_Vacina),
    FOREIGN KEY (Id_Local) REFERENCES Local(Id_Local),
    FOREIGN KEY (CPF) REFERENCES Cidadao(CPF)
);

-- POVOAMENTO

-- 1. CAMPANHA
INSERT INTO Campanha (Nome, Doenca_alvo, Tipo_vacina, Data_inicio, Data_fim, Publico_alvo) VALUES
('Campanha Gripe 2025', 'Gripe', 'Inativada', '2025-03-01', '2025-05-30', 'Idosos'),
('Vacinação Escolar', 'Sarampo', 'Ativada', '2025-04-01', '2025-06-01', 'Crianças'),
('Covid Reforço', 'COVID-19', 'mRNA', '2025-01-10', '2025-03-15', 'Adultos'),
('HPV Jovens', 'HPV', 'Recombinante', '2025-02-05', '2025-04-30', 'Adolescentes'),
('Hepatite B', 'Hepatite B', 'Inativada', '2025-03-10', NULL, 'Todos'),
('Tétano Rural', 'Tétano', 'Toxoide', '2025-05-01', '2025-07-01', 'Trabalhadores rurais'),
('BCG Bebês', 'Tuberculose', 'BCG', '2025-02-20', NULL, 'Recém-nascidos'),
('Raiva Animal', 'Raiva', 'Inativada', '2025-06-01', '2025-07-30', 'População rural'),
('Febre Amarela', 'Febre Amarela', 'Ativada', '2025-03-25', '2025-05-25', 'População geral'),
('Meningite C', 'Meningite', 'Conjugada', '2025-04-10', '2025-06-10', 'Jovens');

-- 2. VACINA
INSERT INTO Vacina (Nome, Doenca_alvo, Codigo_Lote, Data_Chegada, Data_Validade, Qtd_Doses) VALUES
('Vacina Gripe', 'Gripe', 1011, '2025-02-01', '2025-08-01', 1000),
('Vacina Sarampo', 'Sarampo', 1022, '2025-03-01', '2026-03-01', 800),
('Vacina COVID-19', 'COVID-19', 1033, '2025-01-05', '2025-12-01', 1500),
('Vacina HPV', 'HPV', 1044, '2025-02-01', '2026-02-01', 700),
('Vacina Hepatite B', 'Hepatite B', 1055, '2025-03-01', '2026-03-01', 1200),
('Vacina Tétano', 'Tétano', 1066, '2025-04-01', '2026-04-01', 600),
('Vacina BCG', 'Tuberculose', 1077, '2025-01-20', '2026-01-20', 500),
('Vacina Raiva', 'Raiva', 1088, '2025-05-01', '2026-05-01', 400),
('Vacina Febre Amarela', 'Febre Amarela', 1099, '2025-02-10', '2026-02-10', 900),
('Vacina Meningite', 'Meningite', 1100, '2025-03-15', '2026-03-15', 950);

-- 3. LOCAL
INSERT INTO Local (Nome, Rua, Bairro, Numero, Cidade, Estado, Contato, Capacidade) VALUES
('UBS Central', 'Rua das Flores', 'Centro', 100, 'São Paulo', 'SP', '(11) 99999-0001', 200),
('UBS Leste', 'Av. Leste', 'Leste', 200, 'São Paulo', 'SP', '(11) 99999-0002', 150),
('Posto Saúde Norte', 'Rua das Palmeiras', 'Norte', 300, 'Rio de Janeiro', 'RJ', '(21) 98888-0003', 180),
('Clínica Oeste', 'Av. Oeste', 'Oeste', 400, 'Rio de Janeiro', 'RJ', '(21) 98888-0004', 160),
('UBS Sul', 'Rua das Árvores', 'Sul', 500, 'Belo Horizonte', 'MG', '(31) 97777-0005', 190),
('Posto Saúde BH', 'Av. Brasil', 'Centro', 600, 'Belo Horizonte', 'MG', '(31) 97777-0006', 170),
('Clínica Zona Rural', 'Estrada Rural', 'Interior', 700, 'Curitiba', 'PR', '(41) 96666-0007', 120),
('UBS Interior', 'Rua Campestre', 'Campestre', 800, 'Curitiba', 'PR', '(41) 96666-0008', 130),
('Posto Infantil', 'Rua Criança Feliz', 'Infantil', 900, 'Fortaleza', 'CE', '(85) 95555-0009', 100),
('UBS Jovem', 'Rua Juventude', 'Juventude', 1000, 'Fortaleza', 'CE', '(85) 95555-0010', 110);

-- 4. USUARIO
INSERT INTO Usuario (Nome, CPF, Telefone) VALUES
('Ana Silva', '11111111111', '(11) 90000-0001'),
('Bruno Souza', '22222222222', '(11) 90000-0002'),
('Carlos Lima', '33333333333', '(21) 90000-0003'),
('Daniela Rocha', '44444444444', '(21) 90000-0004'),
('Eduardo Dias', '55555555555', '(31) 90000-0005'),
('Fernanda Torres', '66666666666', '(31) 90000-0006'),
('Gustavo Nunes', '77777777777', '(41) 90000-0007'),
('Helena Costa', '88888888888', '(41) 90000-0008'),
('Igor Martins', '99999999999', '(85) 90000-0009'),
('Juliana Freitas', '10101010101', '(85) 90000-0010'),
('Larissa Almeida', '12121212121', '(11) 90000-0011'),
('Matheus Castro', '13131313131', '(11) 90000-0012'),
('Natalia Ribeiro', '14141414141', '(21) 90000-0013'),
('Otávio Mendes', '15151515151', '(31) 90000-0014'),
('Patricia Silva', '16161616161', '(41) 90000-0015');

-- 5. CIDADAO
INSERT INTO Cidadao (Cartao_Sus, Rua, Bairro, Numero, Cidade, Estado, CPF) VALUES
('123456789012345', 'Rua A', 'Centro', 10, 'São Paulo', 'SP', '11111111111'),
('223456789012345', 'Rua B', 'Leste', 20, 'São Paulo', 'SP', '22222222222'),
('323456789012345', 'Rua C', 'Norte', 30, 'Rio de Janeiro', 'RJ', '33333333333'),
('423456789012345', 'Rua D', 'Oeste', 40, 'Rio de Janeiro', 'RJ', '44444444444'),
('523456789012345', 'Rua E', 'Sul', 50, 'Belo Horizonte', 'MG', '55555555555'),
('623456789012345', 'Rua F', 'Centro', 60, 'Belo Horizonte', 'MG', '66666666666'),
('723456789012345', 'Rua G', 'Interior', 70, 'Curitiba', 'PR', '77777777777'),
('823456789012345', 'Rua H', 'Campestre', 80, 'Curitiba', 'PR', '88888888888'),
('923456789012345', 'Rua I', 'Infantil', 90, 'Fortaleza', 'CE', '99999999999'),
('103456789012345', 'Rua J', 'Juventude', 100, 'Fortaleza', 'CE', '10101010101');

-- 6. ADMINISTRADOR
INSERT INTO Administrador (Local_Trabalho, CPF) VALUES
('UBS Central', '11111111111'),
('UBS Leste', '22222222222'),
('Posto Saúde Norte', '33333333333'),
('Clínica Oeste', '44444444444'),
('UBS Sul', '55555555555'),
('Posto Saúde BH', '12121212121'),
('Clínica Zona Rural', '13131313131'),
('UBS Interior', '14141414141'),
('Posto Infantil', '15151515151'),
('UBS Jovem', '16161616161');

-- 7. AGENTE_SAUDE
INSERT INTO Agente_saude (Email, Posto_Trabalho, CPF) VALUES
('agente1@saude.gov.br', 'UBS Central', '66666666666'),
('agente2@saude.gov.br', 'UBS Leste', '77777777777'),
('agente3@saude.gov.br', 'Posto Saúde Norte', '88888888888'),
('agente4@saude.gov.br', 'Clínica Oeste', '99999999999'),
('agente5@saude.gov.br', 'UBS Sul', '10101010101'),
('agente6@saude.gov.br', 'Posto Saúde BH', '12121212121'),
('agente7@saude.gov.br', 'Clínica Zona Rural', '13131313131'),
('agente8@saude.gov.br', 'UBS Interior', '14141414141'),
('agente9@saude.gov.br', 'Posto Infantil', '15151515151'),
('agente10@saude.gov.br', 'UBS Jovem', '16161616161');

-- 8. PARENTE
INSERT INTO Parente (CPF_Responsavel, CPF_Parente) VALUES
('11111111111', '22222222222'),
('33333333333', '44444444444'),
('55555555555', '66666666666'),
('77777777777', '88888888888'),
('99999999999', '10101010101'),
('11111111111', '33333333333'),
('22222222222', '44444444444'),
('33333333333', '55555555555'),
('44444444444', '66666666666'),
('55555555555', '77777777777');

-- 9. AGENDAMENTO
INSERT INTO Agendamento (Data_Agendamento, Id_Vacina, Id_Local, CPF) VALUES
('2025-03-01', 1, 1, '11111111111'),
('2025-03-02', 2, 2, '22222222222'),
('2025-03-03', 3, 3, '33333333333'),
('2025-03-04', 4, 4, '44444444444'),
('2025-03-05', 5, 5, '55555555555'),
('2025-03-06', 6, 6, '66666666666'),
('2025-03-07', 7, 7, '77777777777'),
('2025-03-08', 8, 8, '88888888888'),
('2025-03-09', 9, 9, '99999999999'),
('2025-03-10', 10, 10, '10101010101');

-- 10. VACINACAO
INSERT INTO Vacinacao (Contagem, Data_aplicacao, Id_Vacina, CPF, Id_Local, Id_Campanha) VALUES
(1, '2025-03-01', 1, '11111111111', 1, 1),
(1, '2025-03-02', 2, '22222222222', 2, 2),
(1, '2025-03-03', 3, '33333333333', 3, 3),
(1, '2025-03-04', 4, '44444444444', 4, 4),
(1, '2025-03-05', 5, '55555555555', 5, 5),
(1, '2025-03-06', 6, '66666666666', 6, 6),
(1, '2025-03-07', 7, '77777777777', 7, 7),
(1, '2025-03-08', 8, '88888888888', 8, 8),
(1, '2025-03-09', 9, '99999999999', 9, 9),
(1, '2025-03-10', 10, '10101010101', 10, 10);
