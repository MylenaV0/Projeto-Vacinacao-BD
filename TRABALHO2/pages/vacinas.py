import panel as pn
import pandas as pd
import sqlalchemy
from datetime import date, datetime

# Importar a conexão do db_config
from db_config import engine

# --- Widgets para Filtragem
filtro_nome_vacina = pn.widgets.TextInput(name="Nome da Vacina", placeholder='Filtrar por nome...')
filtro_doenca_vacina = pn.widgets.TextInput(name="Doença Alvo", placeholder='Filtrar por doença...')

# --- Widgets do Formulário para Inserir/Atualizar 
form_nome_vacina = pn.widgets.TextInput(name="Nome da Vacina*", placeholder="Ex: CoronaVac")
form_doenca_alvo = pn.widgets.TextInput(name="Doença Alvo*", placeholder="Ex: COVID-19")
form_lote = pn.widgets.IntInput(name="Código do Lote*", start=0, value=0) 
form_data_chegada = pn.widgets.DatePicker(name="Data de Chegada*")
form_data_validade = pn.widgets.DatePicker(name="Data de Validade*")
form_qtd_doses = pn.widgets.IntInput(name="Quantidade de Doses*", start=0, value=100)

# --- Botões de Ação
btn_consultar = pn.widgets.Button(name='Aplicar Filtros', button_type='primary')
btn_limpar = pn.widgets.Button(name='Limpar Filtros', button_type='default')
btn_inserir = pn.widgets.Button(name='Inserir Nova Vacina', button_type='success')
btn_atualizar = pn.widgets.Button(name='Atualizar Selecionada', button_type='warning', disabled=True)
btn_excluir = pn.widgets.Button(name='Excluir Selecionada', button_type='danger', disabled=True)

# --- Tabela para exibir Vacinas
tabela_vacinas = pn.widgets.Tabulator(pd.DataFrame(), layout='fit_columns', show_index=False, height=400, page_size=10)

# --- Funções

def formatar_datas_df(df):
    for col in ['data_chegada', 'data_validade']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%Y')
    return df

def carregar_todas_vacinas():
    try:
        query = "SELECT * FROM Vacina ORDER BY Id_Vacina DESC;"
        df = pd.read_sql(query, engine)
        tabela_vacinas.value = formatar_datas_df(df)
    except Exception as e:
        pn.state.notifications.error(f"Erro ao carregar vacinas: {e}")

def on_consultar_vacina(event=None):
    try:
        conditions, params = [], {}
        if filtro_nome_vacina.value:
            conditions.append("Nome ILIKE :nome")
            params["nome"] = f"%{filtro_nome_vacina.value}%"
        if filtro_doenca_vacina.value:
            conditions.append("Doenca_Alvo ILIKE :doenca")
            params["doenca"] = f"%{filtro_doenca_vacina.value}%"

        base_query = "SELECT * FROM Vacina"
        if not conditions:
            carregar_todas_vacinas()
            pn.state.notifications.info("Nenhum filtro aplicado. Mostrando todas as vacinas.")
            return

        query_string = f"{base_query} WHERE {' AND '.join(conditions)} ORDER BY Id_Vacina DESC;"
        with engine.connect() as connection:
            result = connection.execute(sqlalchemy.text(query_string), params)
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        
        tabela_vacinas.value = formatar_datas_df(df)
        pn.state.notifications.success(f"{len(df)} resultados encontrados.") if not df.empty else pn.state.notifications.warning("Nenhuma vacina encontrada.")
    except Exception as e:
        pn.state.notifications.error(f"Erro ao consultar vacinas: {e}")

def on_limpar_filtros(event=None):
    filtro_nome_vacina.value = ''
    filtro_doenca_vacina.value = ''
    carregar_todas_vacinas()
    pn.state.notifications.success("Filtros limpos.")

def on_inserir_vacina(event=None):
    if not all([form_nome_vacina.value, form_doenca_alvo.value, form_lote.value, form_data_chegada.value, form_data_validade.value]):
        pn.state.notifications.warning("Preencha todos os campos obrigatórios (*).")
        return
    if form_data_validade.value <= form_data_chegada.value:
        pn.state.notifications.warning("A Data de Validade deve ser posterior à Data de Chegada.")
        return

    query = sqlalchemy.text("INSERT INTO Vacina (Nome, Doenca_alvo, Codigo_Lote, Data_Chegada, Data_Validade, Qtd_Doses) VALUES (:nome, :doenca, :lote, :chegada, :validade, :qtd)")
    params = {
        "nome": form_nome_vacina.value, "doenca": form_doenca_alvo.value, "lote": form_lote.value,
        "chegada": form_data_chegada.value, "validade": form_data_validade.value, "qtd": form_qtd_doses.value
    }
    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                connection.execute(query, params)
                trans.commit()
                pn.state.notifications.success("Vacina inserida com sucesso!")
                carregar_todas_vacinas()
            except Exception as e:
                trans.rollback()
                pn.state.notifications.error(f"Erro na transação ao inserir: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão ao inserir: {e}")

def on_atualizar_vacina(event=None):
    selecao = tabela_vacinas.selection
    if not selecao:
        pn.state.notifications.warning("Selecione uma vacina na tabela para atualizar.")
        return
    
    id_vacina = int(tabela_vacinas.value.loc[selecao[0], 'id_vacina'])

    if not all([form_nome_vacina.value, form_doenca_alvo.value, form_lote.value, form_data_chegada.value, form_data_validade.value]):
        pn.state.notifications.warning("Preencha todos os campos obrigatórios (*).")
        return
    if form_data_validade.value <= form_data_chegada.value:
        pn.state.notifications.warning("A Data de Validade deve ser posterior à Data de Chegada.")
        return
        
    query = sqlalchemy.text("UPDATE Vacina SET Nome=:nome, Doenca_alvo=:doenca, Codigo_Lote=:lote, Data_Chegada=:chegada, Data_Validade=:validade, Qtd_Doses=:qtd WHERE Id_Vacina = :id_vacina")
    params = {
        "nome": form_nome_vacina.value, "doenca": form_doenca_alvo.value, "lote": form_lote.value,
        "chegada": form_data_chegada.value, "validade": form_data_validade.value, "qtd": form_qtd_doses.value,
        "id_vacina": id_vacina
    }
    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                connection.execute(query, params)
                trans.commit()
                pn.state.notifications.success("Vacina atualizada com sucesso!")
                carregar_todas_vacinas()
            except Exception as e:
                trans.rollback()
                pn.state.notifications.error(f"Erro na transação ao atualizar: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão ao atualizar: {e}")

def on_excluir_vacina(event=None):
    selecao = tabela_vacinas.selection
    if not selecao:
        pn.state.notifications.warning("Selecione uma vacina para excluir.")
        return

    id_vacina = int(tabela_vacinas.value.loc[selecao[0], 'id_vacina'])

    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                check_query = sqlalchemy.text("SELECT 1 FROM Vacinacao WHERE Id_Vacina = :id_vacina")
                em_uso = connection.execute(check_query, {"id_vacina": id_vacina}).scalar()
                
                if em_uso:
                    pn.state.notifications.error("Não é possível excluir: Esta vacina já foi utilizada em registros de vacinação.")
                    trans.rollback()
                    return
                
                delete_query = sqlalchemy.text("DELETE FROM Vacina WHERE Id_Vacina = :id_vacina")
                connection.execute(delete_query, {"id_vacina": id_vacina})
                
                trans.commit()
                pn.state.notifications.success("Vacina excluída com sucesso!")
                carregar_todas_vacinas()
                preencher_formulario_selecao([])
            except Exception as e:
                trans.rollback()
                pn.state.notifications.error(f"Erro na transação ao excluir: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão ao excluir: {e}")

@pn.depends(tabela_vacinas.param.selection, watch=True)
def preencher_formulario_selecao(selection):
    if not selection:
        btn_atualizar.disabled = True
        btn_excluir.disabled = True
        form_nome_vacina.value, form_doenca_alvo.value = '', ''
        form_lote.value = 0 
        form_data_chegada.value, form_data_validade.value = None, None
        form_qtd_doses.value = 0
        return
    
    btn_atualizar.disabled = False
    btn_excluir.disabled = False
    
    row_data = tabela_vacinas.value.loc[selection[0]]
    
    form_nome_vacina.value = row_data.get('nome', '')
    form_doenca_alvo.value = row_data.get('doenca_alvo', '')
    form_lote.value = int(row_data.get('codigo_lote', 0))
    form_qtd_doses.value = int(row_data.get('qtd_doses', 0))
    
    try:
        form_data_chegada.value = pd.to_datetime(row_data.get('data_chegada'), dayfirst=True).date()
        form_data_validade.value = pd.to_datetime(row_data.get('data_validade'), dayfirst=True).date()
    except:
        form_data_chegada.value, form_data_validade.value = None, None

# --- Conexão dos Botões
btn_consultar.on_click(on_consultar_vacina)
btn_limpar.on_click(on_limpar_filtros)
btn_inserir.on_click(on_inserir_vacina)
btn_atualizar.on_click(on_atualizar_vacina)
btn_excluir.on_click(on_excluir_vacina)

carregar_todas_vacinas()

# --- Layout da Página 
filtros_card = pn.Card(
    pn.Column(filtro_nome_vacina, filtro_doenca_vacina),
    pn.Row(btn_consultar, btn_limpar),
    title="🔍 Filtros de Consulta"
)

gerenciamento_card = pn.Card(
    pn.pane.Markdown("Para **Atualizar/Excluir**, selecione uma linha. Para **Inserir**, preencha os campos."),
    form_nome_vacina, form_doenca_alvo, form_lote,
    form_data_chegada, form_data_validade, form_qtd_doses,
    pn.Row(btn_inserir, btn_atualizar, btn_excluir),
    title="📝 Gerenciar Vacinas",
    collapsed=True
)

vacinas_page_layout = pn.Column(
    pn.pane.Markdown("## Gerenciamento de Vacinas", styles={'text-align': 'center'}),
    pn.Row(
        pn.Column(filtros_card, gerenciamento_card, width=400),
        pn.Column(tabela_vacinas, sizing_mode='stretch_width')
    )
)
