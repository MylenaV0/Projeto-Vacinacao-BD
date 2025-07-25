import panel as pn
import pandas as pd
import sqlalchemy
from datetime import datetime, date

# Importar a conexão e funções auxiliares do db_config
from db_config import engine, get_campanhas_ativas, get_vacinas, get_locais, get_agendamentos

# --- Widgets para FILTRAGEM
filtro_cpf = pn.widgets.TextInput(name="CPF do Cidadão", placeholder='Filtrar por CPF...')
filtro_nome = pn.widgets.TextInput(name="Nome do Cidadão", placeholder='Filtrar por nome...')
filtro_data_inicio = pn.widgets.DatePicker(name='Período - De:')
filtro_data_fim = pn.widgets.DatePicker(name='Período - Até:')


# --- Widgets do Formulário para Inserir/Atualizar
form_cpf = pn.widgets.TextInput(name="CPF do Cidadão*", placeholder="Ex: 12345678901")
form_campanha = pn.widgets.Select(name="Campanha*", options={})
form_vacina = pn.widgets.Select(name="Vacina*", options={})
form_local = pn.widgets.Select(name="Local*", options={})
form_data_agendamento = pn.widgets.DatePicker(name="Data do Agendamento*", value=date.today())

# --- Botões de Ação ---
btn_consultar = pn.widgets.Button(name='Aplicar Filtros', button_type='primary')
btn_limpar = pn.widgets.Button(name='Limpar Filtros', button_type='default')
btn_inserir = pn.widgets.Button(name="Agendar", button_type="success")
btn_atualizar = pn.widgets.Button(name="Atualizar Agendamento", button_type="warning", disabled=True)
btn_excluir = pn.widgets.Button(name="Cancelar Agendamento", button_type="danger", disabled=True)

# --- Tabela ---
tabela_agendamentos = pn.widgets.Tabulator(pd.DataFrame(), layout='fit_columns', show_index=False, height=400, page_size=10)

# --- Funções ---
def update_dropdown_options():
    try:
        campanhas_df, vacinas_df, locais_df = get_campanhas_ativas(), get_vacinas(), get_locais()
        form_campanha.options = {f"{row['nome']}": row['id_campanha'] for _, row in campanhas_df.iterrows()} if not campanhas_df.empty else {}
        form_vacina.options = {f"{row['nome']} (Lote: {row['codigo_lote']})": row['id_vacina'] for _, row in vacinas_df.iterrows()} if not vacinas_df.empty else {}
        form_local.options = {f"{row['nome']} ({row['cidade']})": row['id_local'] for _, row in locais_df.iterrows()} if not locais_df.empty else {}
    except Exception as e:
        pn.state.notifications.error(f"Erro ao carregar opções dos menus: {e}")

def carregar_todos_agendamentos():
    try:
        df = get_agendamentos()
        df['data_agendamento_original'] = pd.to_datetime(df['data_agendamento'])
        tabela_agendamentos.value = df
        format_and_display_df(df)
        update_dropdown_options()
    except Exception as e:
        pn.state.notifications.error(f"Erro ao carregar agendamentos: {e}")

def format_and_display_df(df):
    if 'data_agendamento' in df.columns and not df.empty:
        df_copy = df.copy()
        df_copy['data_agendamento'] = pd.to_datetime(df_copy['data_agendamento']).dt.strftime('%d/%m/%Y')
        tabela_agendamentos.value = df_copy
    else:
        tabela_agendamentos.value = df

def on_consultar_agendamento(event=None):
    try:
        df_completo = get_agendamentos()
        df_filtrado = df_completo
        
        if filtro_cpf.value:
            df_filtrado = df_filtrado[df_filtrado['cpf'].str.contains(filtro_cpf.value, na=False)]
        if filtro_nome.value:
            df_filtrado = df_filtrado[df_filtrado['nome_cidadao'].str.contains(filtro_nome.value, case=False, na=False)]

        df_filtrado['data_agendamento'] = pd.to_datetime(df_filtrado['data_agendamento'])
        if filtro_data_inicio.value:
            data_inicio = pd.to_datetime(filtro_data_inicio.value)
            df_filtrado = df_filtrado[df_filtrado['data_agendamento'] >= data_inicio]
        if filtro_data_fim.value:
            data_fim = pd.to_datetime(filtro_data_fim.value)
            df_filtrado = df_filtrado[df_filtrado['data_agendamento'] <= data_fim]

        format_and_display_df(df_filtrado)
        pn.state.notifications.success(f"{len(df_filtrado)} resultados encontrados.")
    except Exception as e:
        pn.state.notifications.error(f"Erro ao consultar agendamentos: {e}")

def on_limpar_filtros(event=None):
    filtro_cpf.value, filtro_nome.value = '', ''
    filtro_data_inicio.value, filtro_data_fim.value = None, None
    carregar_todos_agendamentos()
    pn.state.notifications.success("Filtros limpos.")

def on_inserir_agendamento(event=None):
    if not all([form_cpf.value, form_campanha.value, form_vacina.value, form_local.value, form_data_agendamento.value]):
        pn.state.notifications.warning("Todos os campos do formulário são obrigatórios.")
        return

    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                query = sqlalchemy.text("INSERT INTO Agendamento (CPF, Id_Vacina, Id_Local, Data_Agendamento) VALUES (:cpf, :iv, :il, :data)")
                params = {"cpf": form_cpf.value.strip(), "iv": form_vacina.value, "il": form_local.value, "data": form_data_agendamento.value}
                connection.execute(query, params)
                trans.commit()
                pn.state.notifications.success("Agendamento realizado com sucesso!")
                carregar_todos_agendamentos()
            except Exception as e:
                trans.rollback()
                pn.state.notifications.error(f"Erro na transação: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão: {e}")

def on_atualizar_agendamento(event=None):
    selecao = tabela_agendamentos.selection
    if not selecao:
        pn.state.notifications.warning("Selecione um agendamento para atualizar."); return
        
    id_agendamento = int(tabela_agendamentos.value.loc[selecao[0], 'id_agendamento'])
    
    if not all([form_cpf.value, form_campanha.value, form_vacina.value, form_local.value, form_data_agendamento.value]):
        pn.state.notifications.warning("Todos os campos do formulário são obrigatórios.")
        return

    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                query = sqlalchemy.text("UPDATE Agendamento SET CPF=:cpf, Id_Vacina=:iv, Id_Local=:il, Data_Agendamento=:data WHERE Id_Agendamento = :id_ag")
                params = {"cpf": form_cpf.value.strip(), "iv": form_vacina.value, "il": form_local.value, "data": form_data_agendamento.value, "id_ag": id_agendamento}
                connection.execute(query, params)
                trans.commit()
                pn.state.notifications.success("Agendamento atualizado com sucesso!")
                carregar_todos_agendamentos()
                preencher_formulario_selecao([])
            except Exception as e:
                trans.rollback()
                pn.state.notifications.error(f"Erro na transação ao atualizar: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão ao atualizar: {e}")

def on_excluir_agendamento(event=None):
    selecao = tabela_agendamentos.selection
    if not selecao:
        pn.state.notifications.warning("Selecione um agendamento para cancelar."); return

    id_agendamento = int(tabela_agendamentos.value.loc[selecao[0], 'id_agendamento'])

    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                connection.execute(sqlalchemy.text("DELETE FROM Agendamento WHERE Id_Agendamento = :id"), {"id": id_agendamento})
                trans.commit()
                pn.state.notifications.success("Agendamento cancelado com sucesso!")
                carregar_todos_agendamentos()
                preencher_formulario_selecao([])
            except Exception as e:
                trans.rollback()
                pn.state.notifications.error(f"Erro na transação ao cancelar: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão ao cancelar: {e}")

@pn.depends(tabela_agendamentos.param.selection, watch=True)
def preencher_formulario_selecao(selection):
    if not selection:
        btn_atualizar.disabled, btn_excluir.disabled = True, True
        form_cpf.value = ''
        form_data_agendamento.value = date.today()
        form_campanha.value, form_vacina.value, form_local.value = None, None, None
        return
    
    btn_atualizar.disabled, btn_excluir.disabled = False, False
    row_data = tabela_agendamentos.value.loc[selection[0]]
    
    form_cpf.value = row_data.get('cpf', '')
    try:
        form_data_agendamento.value = pd.to_datetime(row_data.get('data_agendamento_original', row_data.get('data_agendamento'))).date()
    except:
        form_data_agendamento.value = date.today()
    
    form_campanha.value = int(row_data.get('id_campanha')) if pd.notna(row_data.get('id_campanha')) else None
    form_vacina.value = int(row_data.get('id_vacina')) if pd.notna(row_data.get('id_vacina')) else None
    form_local.value = int(row_data.get('id_local')) if pd.notna(row_data.get('id_local')) else None

# --- Conexões dos Botões
btn_consultar.on_click(on_consultar_agendamento)
btn_limpar.on_click(on_limpar_filtros)
btn_inserir.on_click(on_inserir_agendamento)
btn_atualizar.on_click(on_atualizar_agendamento)
btn_excluir.on_click(on_excluir_agendamento)

carregar_todos_agendamentos()

# --- Layout da Página 
filtros_card = pn.Card(
    pn.Column(filtro_cpf, filtro_nome, filtro_data_inicio, filtro_data_fim),
    pn.Row(btn_consultar, btn_limpar),
    title="🔍 Filtros de Consulta"
)

gerenciamento_card = pn.Card(
    pn.pane.Markdown("Para **Atualizar/Cancelar**, selecione uma linha. Para **Agendar**, preencha os campos."),
    form_cpf, form_campanha, form_vacina, form_local, form_data_agendamento,
    pn.Row(btn_inserir, btn_atualizar, btn_excluir),
    title="📝 Gerenciar Agendamentos",
    collapsed=True
)

agendamento_page_layout = pn.Column(
    pn.pane.Markdown("## Gerenciamento de Agendamentos", styles={'text-align': 'center'}),
    pn.Row(
        pn.Column(filtros_card, gerenciamento_card, width=400),
        pn.Column(tabela_agendamentos, sizing_mode='stretch_width')
    )
)
