import os
import panel as pn
import pandas as pd
import sqlalchemy
import psycopg2 # Importar psycopg2 para a conexão
from datetime import datetime, date
from dotenv import load_dotenv

pn.extension('tabulator', notifications=True)

load_dotenv() 
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')

# --- Conexão Banco
con = None  
engine = None

try:
    con = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS 
    )
    engine = sqlalchemy.create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print("Conexão com o banco de dados estabelecida com sucesso!")
    if pn.state:
        pn.state.notifications.success("Conexão com o banco de dados estabelecida!")
except Exception as e:
    con = None
    engine = None
    print(f"Erro ao conectar com o banco de dados: {e}")
    if pn.state:
        pn.state.notifications.error(f"Erro: Conexão com o banco de dados não estabelecida. Detalhes: {e}")


# --- Funções auxiliares para interação com o BD
def fetch_data(query, params=None):
    """
    Busca dados do banco de dados e retorna um DataFrame do Pandas.
    Args:
        query (str): A query SQL para executar.
        params (tuple, optional): Parâmetros para a query. Defaults to None.
    Returns:
        pd.DataFrame: DataFrame contendo os resultados da query, ou um DataFrame vazio em caso de erro.
    """
    if engine is None:
        if pn.state:
            pn.state.notifications.error("Erro: Conexão com o banco de dados não estabelecida para buscar dados.")
        return pd.DataFrame()
    try:
        df = pd.read_sql(query, engine, params=params)
        return df
    except Exception as e:
        if pn.state:
            pn.state.notifications.error(f"Erro ao buscar dados: {e}")
        print(f"DEBUG: Erro ao buscar dados: {e} - Query: {query}")
        return pd.DataFrame()

def execute_query(query, params=None, fetch_result=False):
    """
    Executa uma query no banco de dados (INSERT, UPDATE, DELETE, CREATE TABLE).
    Permite opcionalmente retornar resultados (e.g., para RETURNING Id).
    Args:
        query (str): A query SQL para executar.
        params (tuple, optional): Parâmetros para a query. Defaults to None.
        fetch_result (bool, optional): Se True, tenta retornar os resultados da query.
                                     Útil para instruções RETURNING. Defaults to False.
    Returns:
        Any: True em caso de sucesso (para queries sem retorno), False em caso de erro,
             ou o resultado de cur.fetchall() se fetch_result for True.
    """
    if con is None:
        if pn.state:
            pn.state.notifications.error("Erro: Conexão com o banco de dados não estabelecida para executar query.")
        return False
    try:
        cur = con.cursor()
        cur.execute(query, params)
        if fetch_result:
            result = cur.fetchall()
            con.commit()
            cur.close()
            return result
        else:
            con.commit()
            cur.close()
            return True
    except Exception as e:
        con.rollback()
        if pn.state:
            pn.state.notifications.error(f"Erro ao executar query: {e}")
        print(f"DEBUG: Erro ao executar query: {e} - Query: {query}")
        return False

def table_exists(table_name):
    """
    Verifica se uma tabela específica existe no banco de dados.
    Args:
        table_name (str): O nome da tabela a ser verificada.
    Returns:
        bool: True se a tabela existir, False caso contrário ou em caso de erro.
    """
    if con is None:
        if pn.state:
            pn.state.notifications.error("Erro: Conexão com o banco de dados não estabelecida para verificar tabela.")
        return False
    try:
        cur = con.cursor()
        cur.execute(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name.lower()}');")
        exists = cur.fetchone()[0]
        cur.close()
        return exists
    except Exception as e:
        if pn.state:
            pn.state.notifications.error(f"Erro ao verificar existência da tabela '{table_name}': {e}")
        print(f"DEBUG: Erro ao verificar existência da tabela '{table_name}': {e}")
        return False

# --- Funções para pegar dados

def get_campanhas_ativas():
    query = """
    SELECT Id_Campanha, Nome, Doenca_Alvo, Tipo_Vacina, Data_Inicio, Data_Fim, Publico_Alvo
    FROM Campanha
    WHERE (Data_Fim IS NULL OR Data_Fim >= CURRENT_DATE) AND Data_Inicio <= CURRENT_DATE
    ORDER BY Data_Inicio DESC;
    """
    return fetch_data(query)

def get_vacinas():
    query = """
    SELECT Id_Vacina, Nome, Doenca_Alvo, Codigo_Lote, Qtd_Doses, Data_Validade, Data_Chegada
    FROM Vacina
    WHERE Data_Validade >= CURRENT_DATE
    ORDER BY Nome;
    """
    return fetch_data(query)

def get_locais(): 
    query = """
    SELECT Id_Local, Nome, Rua, Bairro, Numero, Cidade, Estado, Contato, Capacidade
    FROM Local
    ORDER BY Nome;
    """
    return fetch_data(query)

def get_agendamentos():
    query = """
        SELECT 
            a.id_agendamento, a.cpf, u.nome AS nome_cidadao,
            a.id_vacina, v.nome AS nome_vacina,
            c.id_campanha, c.nome AS nome_campanha,
            a.id_local, l.nome AS nome_local,
            a.data_agendamento
        FROM Agendamento a
        LEFT JOIN Usuario u ON a.cpf = u.cpf
        LEFT JOIN Vacina v ON a.id_vacina = v.id_vacina
        LEFT JOIN Local l ON a.id_local = l.id_local
        LEFT JOIN Campanha c ON v.doenca_alvo = c.doenca_alvo 
        ORDER BY a.data_agendamento DESC, u.nome ASC;
    """
    try:
        df = pd.read_sql(query, engine)
        df.columns = [x.lower() for x in df.columns]
        return df
    except Exception as e:
        print(f"ERRO em get_agendamentos: {e}")
        return pd.DataFrame()

def get_usuarios_completo():
    query = """
    SELECT
        U.CPF,
        U.Nome,
        U.Telefone,
        CASE
            WHEN C.CPF IS NOT NULL THEN 'Cidadão'
            WHEN A.CPF IS NOT NULL THEN 'Administrador'
            WHEN S.CPF IS NOT NULL THEN 'Agente de Saúde'
            ELSE 'Usuário Genérico'
        END AS Tipo_Usuario,
        C.Cartao_Sus, C.Rua, C.Bairro, C.Numero, C.Cidade, C.Estado,
        A.Local_Trabalho AS Admin_Local_Trabalho,
        S.Email AS Agente_Email, S.Posto_Trabalho AS Agente_Posto_Trabalho
    FROM Usuario U
    LEFT JOIN Cidadao C ON U.CPF = C.CPF
    LEFT JOIN Administrador A ON U.CPF = A.CPF
    LEFT JOIN Agente_Saude S ON U.CPF = S.CPF
    ORDER BY U.Nome;
    """
    return fetch_data(query)

def get_cidadaos():
    query = """
    SELECT C.CPF, U.Nome, C.Cartao_Sus, C.Rua, C.Bairro, C.Numero, C.Cidade, C.Estado
    FROM Cidadao C
    JOIN Usuario U ON C.CPF = U.CPF
    ORDER BY U.Nome;
    """
    return fetch_data(query)

def get_vacinacoes():
    query = """
    SELECT
        V_APLIC.Id_Vacinacao,
        V_APLIC.Contagem,
        V_APLIC.Data_aplicacao,
        U.Nome AS Nome_Cidadao,
        V.Nome AS Nome_Vacina,
        L.Nome AS Nome_Local,
        C.Nome AS Nome_Campanha,
        V_APLIC.CPF,
        V_APLIC.Id_Vacina,
        V_APLIC.Id_Local,
        V_APLIC.Id_Campanha
    FROM Vacinacao V_APLIC
    JOIN Usuario U ON V_APLIC.CPF = U.CPF
    JOIN Vacina V ON V_APLIC.Id_Vacina = V.Id_Vacina
    JOIN Local L ON V_APLIC.Id_Local = L.Id_Local
    JOIN Campanha C ON V_APLIC.Id_Campanha = C.Id_Campanha
    ORDER BY V_APLIC.Data_aplicacao DESC, U.Nome, V.Nome;
    """
    return fetch_data(query)

def get_parentescos():
    query = """
    SELECT
        P.Id_Parentesco,
        P.CPF_Responsavel,
        UR.Nome AS Nome_Responsavel,
        P.CPF_Parente,
        UP.Nome AS Nome_Parente
    FROM Parente P
    JOIN Cidadao CR ON P.CPF_Responsavel = CR.CPF
    JOIN Usuario UR ON CR.CPF = UR.CPF
    JOIN Cidadao CP ON P.CPF_Parente = CP.CPF
    JOIN Usuario UP ON CP.CPF = UP.CPF
    ORDER BY UR.Nome, UP.Nome;
    """
    return fetch_data(query)

# --- Funções de Validação

def validar_cidadao_aptidao(cpf, campanha_id):
    if engine is None: return False, "Erro: Conexão com o banco de dados não estabelecida."
    try:
        query_campanha = "SELECT Publico_Alvo FROM Campanha WHERE Id_Campanha = %s"
        campanha_info = fetch_data(query_campanha, params=[campanha_id])
        if campanha_info.empty: return False, "Campanha inválida."
        publico_alvo_campanha = campanha_info.iloc[0]['publico_alvo'].lower()

        query_cidadao = "SELECT U.Nome, C.Cidade FROM Cidadao C JOIN Usuario U ON C.CPF = U.CPF WHERE C.CPF = %s"
        cidadao_info = fetch_data(query_cidadao, params=[cpf])
        if cidadao_info.empty: return False, "CPF não cadastrado como cidadão."

        cidadao_cidade = cidadao_info.iloc[0]['cidade'].lower()
        if cidadao_cidade not in publico_alvo_campanha and "geral" not in publico_alvo_campanha:
            return False, f"Cidadão de {cidadao_cidade.capitalize()} não se encaixa no público alvo da campanha ({publico_alvo_campanha})."
        return True, ""
    except Exception as e:
        return False, f"Erro na validação do cidadão: {e}"

def validar_estoque_vacina(id_vacina):
    if engine is None: return False, "Erro: Conexão com o banco de dados não estabelecida."
    query = "SELECT Qtd_Doses FROM Vacina WHERE Id_Vacina = %s"
    df = fetch_data(query, params=[id_vacina])
    if df.empty: return False, "Vacina inválida."
    return (df.iloc[0]['qtd_doses'] > 0), "Vacina sem estoque disponível."

def contar_agendamentos_no_local(local_id, data_agendamento):
    if engine is None: return 0
    query = """
    SELECT COUNT(*) as contagem
    FROM Agendamento
    WHERE Id_Local = %s AND Data_Agendamento = %s;
    """
    df = fetch_data(query, params=[local_id, data_agendamento])
    return df.iloc[0]['contagem'] if not df.empty else 0

def capacidade_local(local_id):
    if engine is None: return 0
    query = "SELECT Capacidade FROM Local WHERE Id_Local = %s"
    df = fetch_data(query, params=[local_id])
    if df.empty or df.iloc[0]['capacidade'] is None: return 0
    return df.iloc[0]['capacidade']

def validar_periodo_campanha(id_campanha, data_agendamento):
    if engine is None: return False, "Erro: Conexão com o banco de dados não estabelecida."
    query = """
    SELECT Data_Inicio, Data_Fim
    FROM Campanha
    WHERE Id_Campanha = %s;
    """
    df = fetch_data(query, params=[id_campanha])
    if df.empty: return False, "Campanha inválida."
    data_inicio = df.iloc[0]['data_inicio']
    data_fim = df.iloc[0]['data_fim'] if pd.notna(df.iloc[0]['data_fim']) else date.max
    if not (data_inicio <= data_agendamento <= data_fim):
        return False, "Data agendada fora do período da campanha."
    return True, ""

def validar_agendamento_duplicado(cpf, id_vacina, data_agendamento):
    if engine is None: return False, "Erro: Conexão com o banco de dados não estabelecida."
    query = """
    SELECT COUNT(*) as contagem
    FROM Agendamento
    WHERE CPF = %s AND Id_Vacina = %s AND Data_Agendamento = %s;
    """
    df = fetch_data(query, params=[cpf, id_vacina, data_agendamento])
    return (df.iloc[0]['contagem'] == 0), ""

def verificar_cidadao_existe(cpf):
    if engine is None: return False
    query = "SELECT CPF FROM Cidadao WHERE CPF = %s;"
    df = fetch_data(query, params=[cpf])
    return not df.empty
