import panel as pn
import pandas as pd
import sqlalchemy
from datetime import datetime, date

# Importar a conexão e funções auxiliares do db_config
from db_config import engine, get_cidadaos, get_vacinas, get_locais, get_campanhas_ativas, get_vacinacoes

# --- Widgets para FILTRAGEM ---
filtro_nome_cidadao = pn.widgets.TextInput(name="Nome do Cidadão", placeholder='Filtrar por nome do cidadão...')
filtro_nome_vacina = pn.widgets.TextInput(name="Nome da Vacina", placeholder='Filtrar por nome da vacina...')
filtro_data_inicio = pn.widgets.DatePicker(name='Período - De:')
filtro_data_fim = pn.widgets.DatePicker(name='Período - Até:')

# --- Widgets do FORMULÁRIO para Inserir/Atualizar ---
# ATUALIZAÇÃO: Mudança de Select para TextInput
form_cpf = pn.widgets.TextInput(name="CPF do Cidadão*", placeholder="Digite o CPF para registrar...")
form_id_vacina = pn.widgets.Select(name="Vacina (Lote)*", options={})
form_id_local = pn.widgets.Select(name="Local de Aplicação*", options={})
form_id_campanha = pn.widgets.Select(name="Campanha*", options={})
form_contagem = pn.widgets.IntInput(name="Contagem da Dose*", start=1, value=1)
form_data_aplicacao = pn.widgets.DatePicker(name="Data de Aplicação*", value=date.today())

# --- Botões de AÇÃO ---
btn_consultar = pn.widgets.Button(name='Aplicar Filtros', button_type='primary')
btn_limpar = pn.widgets.Button(name='Limpar Filtros', button_type='default')
btn_inserir = pn.widgets.Button(name="Registrar Vacinação", button_type="success")
btn_atualizar = pn.widgets.Button(name="Atualizar Selecionada", button_type="warning", disabled=True)
btn_excluir = pn.widgets.Button(name="Excluir Selecionada", button_type="danger", disabled=True)

# --- Tabela ---
tabela_vacinacoes = pn.widgets.Tabulator(pd.DataFrame(), layout='fit_columns', show_index=False, height=400, page_size=10)

# --- FUNÇÕES ---

def update_dropdown_options():
    try:
        # ATUALIZAÇÃO: Remoção da busca por cidadãos, pois não é mais um dropdown
        vacinas_df, locais_df, campanhas_df = get_vacinas(), get_locais(), get_campanhas_ativas()
        form_id_vacina.options = {f"{row['nome']} (Lote: {row['codigo_lote']}, Doses: {row['qtd_doses']})": row['id_vacina'] for _, row in vacinas_df.iterrows()} if not vacinas_df.empty else {}
        form_id_local.options = {f"{row['nome']} ({row['cidade']})": row['id_local'] for _, row in locais_df.iterrows()} if not locais_df.empty else {}
        form_id_campanha.options = {f"{row['nome']} (ID: {row['id_campanha']})": row['id_campanha'] for _, row in campanhas_df.iterrows()} if not campanhas_df.empty else {}
    except Exception as e:
        pn.state.notifications.error(f"Erro ao carregar opções dos menus: {e}")

def carregar_todas_vacinacoes():
    try:
        df = get_vacinacoes()
        tabela_vacinacoes.value = df
        format_and_display_df(df)
        update_dropdown_options()
    except Exception as e:
        pn.state.notifications.error(f"Erro ao carregar vacinações: {e}")

def format_and_display_df(df):
    if 'data_aplicacao' in df.columns and not df.empty:
        df_copy = df.copy()
        df_copy['data_aplicacao'] = pd.to_datetime(df_copy['data_aplicacao']).dt.strftime('%d/%m/%Y')
        tabela_vacinacoes.value = df_copy
    else:
        tabela_vacinacoes.value = df

def on_consultar_vacinacao(event=None):
    # ... (Esta função permanece a mesma)
    pass

def on_limpar_filtros(event=None):
    # ... (Esta função permanece a mesma)
    pass

def on_inserir_vacinacao(event=None):
    cpf_digitado = form_cpf.value.strip()
    if not all([cpf_digitado, form_id_vacina.value, form_id_local.value, form_id_campanha.value]):
        pn.state.notifications.warning("Todos os campos do formulário são obrigatórios.")
        return

    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                # ATUALIZAÇÃO: Adicionada validação de existência do CPF
                cidadao_existe = connection.execute(sqlalchemy.text("SELECT 1 FROM Cidadao WHERE CPF = :cpf"), {"cpf": cpf_digitado}).scalar()
                if not cidadao_existe:
                    pn.state.notifications.warning(f"CPF '{cpf_digitado}' não encontrado ou não pertence a um cidadão."); trans.rollback(); return

                vacina_info = connection.execute(sqlalchemy.text("SELECT Qtd_Doses FROM Vacina WHERE Id_Vacina = :id"), {"id": form_id_vacina.value}).first()
                if not vacina_info or vacina_info[0] < 1:
                    pn.state.notifications.warning("Estoque insuficiente para a vacina selecionada."); trans.rollback(); return

                query_insert = sqlalchemy.text("INSERT INTO Vacinacao (Contagem, Data_aplicacao, Id_Vacina, CPF, Id_Local, Id_Campanha) VALUES (:c, :d, :iv, :cpf, :il, :ic)")
                connection.execute(query_insert, {"c": form_contagem.value, "d": form_data_aplicacao.value, "iv": form_id_vacina.value, "cpf": cpf_digitado, "il": form_id_local.value, "ic": form_id_campanha.value})
                
                connection.execute(sqlalchemy.text("UPDATE Vacina SET Qtd_Doses = Qtd_Doses - 1 WHERE Id_Vacina = :id"), {"id": form_id_vacina.value})

                trans.commit()
                pn.state.notifications.success("Vacinação registrada e estoque atualizado!")
                carregar_todas_vacinacoes()
            except Exception as e:
                trans.rollback()
                pn.state.notifications.error(f"Erro na transação: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão: {e}")

# ... (Mantenha as funções on_atualizar, on_excluir como estão, elas já pegam o CPF da linha selecionada) ...

@pn.depends(tabela_vacinacoes.param.selection, watch=True)
def preencher_formulario_selecao(selection):
    if not selection:
        btn_atualizar.disabled, btn_excluir.disabled = True, True
        form_contagem.value = 1
        form_data_aplicacao.value = date.today()
        # ATUALIZAÇÃO: Limpa o campo de texto do CPF
        form_cpf.value = ''
        form_id_vacina.value, form_id_local.value, form_id_campanha.value = None, None, None
        return
    
    btn_atualizar.disabled, btn_excluir.disabled = False, False
    row_data = tabela_vacinacoes.value.loc[selection[0]]
    
    # ATUALIZAÇÃO: Preenche o campo de texto do CPF
    form_cpf.value = row_data.get('cpf', '')
    form_contagem.value = int(row_data.get('contagem', 1))
    try:
        form_data_aplicacao.value = pd.to_datetime(row_data.get('data_aplicacao_original', row_data.get('data_aplicacao'))).date()
    except:
        form_data_aplicacao.value = date.today()

    try:
        form_id_vacina.value = int(row_data.get('id_vacina'))
        form_id_local.value = int(row_data.get('id_local'))
        form_id_campanha.value = int(row_data.get('id_campanha'))
    except (ValueError, TypeError) as e:
        pn.state.notifications.error(f"Não foi possível preencher os menus: {e}")

# ... (Mantenha o resto do código, incluindo o layout, como está) ...
# Omitido por brevidade, apenas as funções acima precisam ser alteradas.

# Cole o código completo abaixo para garantir

# --- CÓDIGO COMPLETO PARA SUBSTITUIÇÃO ---
import panel as pn
import pandas as pd
import sqlalchemy
from datetime import datetime, date

from db_config import engine, get_cidadaos, get_vacinas, get_locais, get_campanhas_ativas, get_vacinacoes

filtro_nome_cidadao = pn.widgets.TextInput(name="Nome do Cidadão", placeholder='Filtrar por nome do cidadão...')
filtro_nome_vacina = pn.widgets.TextInput(name="Nome da Vacina", placeholder='Filtrar por nome da vacina...')
filtro_data_inicio = pn.widgets.DatePicker(name='Período - De:')
filtro_data_fim = pn.widgets.DatePicker(name='Período - Até:')

form_cpf = pn.widgets.TextInput(name="CPF do Cidadão*", placeholder="Digite o CPF para registrar...")
form_id_vacina = pn.widgets.Select(name="Vacina (Lote)*", options={})
form_id_local = pn.widgets.Select(name="Local de Aplicação*", options={})
form_id_campanha = pn.widgets.Select(name="Campanha*", options={})
form_contagem = pn.widgets.IntInput(name="Contagem da Dose*", start=1, value=1)
form_data_aplicacao = pn.widgets.DatePicker(name="Data de Aplicação*", value=date.today())

btn_consultar = pn.widgets.Button(name='Aplicar Filtros', button_type='primary')
btn_limpar = pn.widgets.Button(name='Limpar Filtros', button_type='default')
btn_inserir = pn.widgets.Button(name="Registrar Vacinação", button_type="success")
btn_atualizar = pn.widgets.Button(name="Atualizar Selecionada", button_type="warning", disabled=True)
btn_excluir = pn.widgets.Button(name="Excluir Selecionada", button_type="danger", disabled=True)

tabela_vacinacoes = pn.widgets.Tabulator(pd.DataFrame(), layout='fit_columns', show_index=False, height=400, page_size=10)

def update_dropdown_options():
    try:
        vacinas_df, locais_df, campanhas_df = get_vacinas(), get_locais(), get_campanhas_ativas()
        form_id_vacina.options = {f"{row['nome']} (Lote: {row['codigo_lote']}, Doses: {row['qtd_doses']})": row['id_vacina'] for _, row in vacinas_df.iterrows()} if not vacinas_df.empty else {}
        form_id_local.options = {f"{row['nome']} ({row['cidade']})": row['id_local'] for _, row in locais_df.iterrows()} if not locais_df.empty else {}
        form_id_campanha.options = {f"{row['nome']} (ID: {row['id_campanha']})": row['id_campanha'] for _, row in campanhas_df.iterrows()} if not campanhas_df.empty else {}
    except Exception as e:
        pn.state.notifications.error(f"Erro ao carregar opções dos menus: {e}")

def carregar_todas_vacinacoes():
    try:
        df = get_vacinacoes()
        tabela_vacinacoes.value = df
        format_and_display_df(df)
        update_dropdown_options()
    except Exception as e:
        pn.state.notifications.error(f"Erro ao carregar vacinações: {e}")

def format_and_display_df(df):
    if 'data_aplicacao' in df.columns and not df.empty:
        df_copy = df.copy()
        df_copy['data_aplicacao'] = pd.to_datetime(df_copy['data_aplicacao']).dt.strftime('%d/%m/%Y')
        tabela_vacinacoes.value = df_copy
    else:
        tabela_vacinacoes.value = df

def on_consultar_vacinacao(event=None):
    try:
        df_completo = get_vacinacoes()
        df_filtrado = df_completo
        
        if filtro_nome_cidadao.value:
            df_filtrado = df_filtrado[df_filtrado['nome_cidadao'].str.contains(filtro_nome_cidadao.value, case=False, na=False)]
        if filtro_nome_vacina.value:
            df_filtrado = df_filtrado[df_filtrado['nome_vacina'].str.contains(filtro_nome_vacina.value, case=False, na=False)]

        df_filtrado['data_aplicacao'] = pd.to_datetime(df_filtrado['data_aplicacao'])
        if filtro_data_inicio.value:
            data_inicio = pd.to_datetime(filtro_data_inicio.value)
            df_filtrado = df_filtrado[df_filtrado['data_aplicacao'] >= data_inicio]
        if filtro_data_fim.value:
            data_fim = pd.to_datetime(filtro_data_fim.value)
            df_filtrado = df_filtrado[df_filtrado['data_aplicacao'] <= data_fim]

        format_and_display_df(df_filtrado)
        pn.state.notifications.success(f"{len(df_filtrado)} resultados encontrados.")
    except Exception as e:
        pn.state.notifications.error(f"Erro ao consultar vacinações: {e}")

def on_limpar_filtros(event=None):
    filtro_nome_cidadao.value, filtro_nome_vacina.value = '', ''
    filtro_data_inicio.value, filtro_data_fim.value = None, None
    carregar_todas_vacinacoes()
    pn.state.notifications.success("Filtros limpos.")

def on_inserir_vacinacao(event=None):
    cpf_digitado = form_cpf.value.strip()
    if not all([cpf_digitado, form_id_vacina.value, form_id_local.value, form_id_campanha.value]):
        pn.state.notifications.warning("Todos os campos do formulário são obrigatórios.")
        return

    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                cidadao_existe = connection.execute(sqlalchemy.text("SELECT 1 FROM Cidadao WHERE CPF = :cpf"), {"cpf": cpf_digitado}).scalar()
                if not cidadao_existe:
                    pn.state.notifications.warning(f"CPF '{cpf_digitado}' não encontrado ou não pertence a um cidadão."); trans.rollback(); return

                vacina_info = connection.execute(sqlalchemy.text("SELECT Qtd_Doses FROM Vacina WHERE Id_Vacina = :id"), {"id": form_id_vacina.value}).first()
                if not vacina_info or vacina_info[0] < 1:
                    pn.state.notifications.warning("Estoque insuficiente para a vacina selecionada."); trans.rollback(); return

                query_insert = sqlalchemy.text("INSERT INTO Vacinacao (Contagem, Data_aplicacao, Id_Vacina, CPF, Id_Local, Id_Campanha) VALUES (:c, :d, :iv, :cpf, :il, :ic)")
                connection.execute(query_insert, {"c": form_contagem.value, "d": form_data_aplicacao.value, "iv": form_id_vacina.value, "cpf": cpf_digitado, "il": form_id_local.value, "ic": form_id_campanha.value})
                
                connection.execute(sqlalchemy.text("UPDATE Vacina SET Qtd_Doses = Qtd_Doses - 1 WHERE Id_Vacina = :id"), {"id": form_id_vacina.value})

                trans.commit()
                pn.state.notifications.success("Vacinação registrada e estoque atualizado!")
                carregar_todas_vacinacoes()
            except Exception as e:
                trans.rollback()
                pn.state.notifications.error(f"Erro na transação: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão: {e}")

def on_atualizar_vacinacao(event=None):
    selecao = tabela_vacinacoes.selection
    if not selecao:
        pn.state.notifications.warning("Selecione um registro para atualizar."); return
        
    id_vacinacao = int(tabela_vacinacoes.value.loc[selecao[0], 'id_vacinacao'])
    id_vacina_original = int(tabela_vacinacoes.value.loc[selecao[0], 'id_vacina'])
    id_vacina_nova = form_id_vacina.value
    cpf_novo = form_cpf.value.strip()

    if not cpf_novo:
        pn.state.notifications.warning("O campo CPF não pode estar vazio para atualizar."); return

    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                cidadao_existe = connection.execute(sqlalchemy.text("SELECT 1 FROM Cidadao WHERE CPF = :cpf"), {"cpf": cpf_novo}).scalar()
                if not cidadao_existe:
                    pn.state.notifications.warning(f"CPF '{cpf_novo}' não encontrado ou não pertence a um cidadão."); trans.rollback(); return

                if id_vacina_nova != id_vacina_original:
                    connection.execute(sqlalchemy.text("UPDATE Vacina SET Qtd_Doses = Qtd_Doses + 1 WHERE Id_Vacina = :id"), {"id": id_vacina_original})
                    nova_vacina_info = connection.execute(sqlalchemy.text("SELECT Qtd_Doses FROM Vacina WHERE Id_Vacina = :id"), {"id": id_vacina_nova}).first()
                    if not nova_vacina_info or nova_vacina_info[0] < 1:
                        pn.state.notifications.warning("Estoque insuficiente para a nova vacina. Atualização cancelada."); trans.rollback(); return
                    connection.execute(sqlalchemy.text("UPDATE Vacina SET Qtd_Doses = Qtd_Doses - 1 WHERE Id_Vacina = :id"), {"id": id_vacina_nova})

                q_update = sqlalchemy.text("UPDATE Vacinacao SET Contagem=:c, Data_aplicacao=:d, Id_Vacina=:iv, CPF=:cpf, Id_Local=:il, Id_Campanha=:ic WHERE Id_Vacinacao = :id_v")
                params = {"c": form_contagem.value, "d": form_data_aplicacao.value, "iv": id_vacina_nova, "cpf": cpf_novo, "il": form_id_local.value, "ic": form_id_campanha.value, "id_v": id_vacinacao}
                connection.execute(q_update, params)
                
                trans.commit()
                pn.state.notifications.success("Vacinação atualizada e estoque ajustado!")
                carregar_todas_vacinacoes()
            except Exception as e:
                trans.rollback()
                pn.state.notifications.error(f"Erro na transação ao atualizar: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão ao atualizar: {e}")

def on_excluir_vacinacao(event=None):
    selecao = tabela_vacinacoes.selection
    if not selecao:
        pn.state.notifications.warning("Selecione um registro para excluir."); return
    
    id_vacinacao = int(tabela_vacinacoes.value.loc[selecao[0], 'id_vacinacao'])
    id_vacina_afetada = int(tabela_vacinacoes.value.loc[selecao[0], 'id_vacina'])
        
    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                connection.execute(sqlalchemy.text("DELETE FROM Vacinacao WHERE Id_Vacinacao = :id"), {"id": id_vacinacao})
                connection.execute(sqlalchemy.text("UPDATE Vacina SET Qtd_Doses = Qtd_Doses + 1 WHERE Id_Vacina = :id"), {"id": id_vacina_afetada})
                trans.commit()
                pn.state.notifications.success("Vacinação excluída e estoque restaurado!")
                carregar_todas_vacinacoes()
                preencher_formulario_selecao([])
            except Exception as e:
                trans.rollback()
                pn.state.notifications.error(f"Erro na transação ao excluir: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão ao excluir: {e}")

@pn.depends(tabela_vacinacoes.param.selection, watch=True)
def preencher_formulario_selecao(selection):
    if not selection:
        btn_atualizar.disabled, btn_excluir.disabled = True, True
        form_contagem.value = 1
        form_data_aplicacao.value = date.today()
        form_cpf.value = ''
        form_id_vacina.value, form_id_local.value, form_id_campanha.value = None, None, None
        return
    
    btn_atualizar.disabled, btn_excluir.disabled = False, False
    row_data = tabela_vacinacoes.value.loc[selection[0]]
    
    form_cpf.value = row_data.get('cpf', '')
    form_contagem.value = int(row_data.get('contagem', 1))
    try:
        form_data_aplicacao.value = pd.to_datetime(row_data.get('data_aplicacao_original', row_data.get('data_aplicacao'))).date()
    except:
        form_data_aplicacao.value = date.today()

    try:
        form_id_vacina.value = int(row_data.get('id_vacina'))
        form_id_local.value = int(row_data.get('id_local'))
        form_id_campanha.value = int(row_data.get('id_campanha'))
    except (ValueError, TypeError) as e:
        pn.state.notifications.error(f"Não foi possível preencher os menus: {e}")

btn_consultar.on_click(on_consultar_vacinacao)
btn_limpar.on_click(on_limpar_filtros)
btn_inserir.on_click(on_inserir_vacinacao)
btn_atualizar.on_click(on_atualizar_vacinacao)
btn_excluir.on_click(on_excluir_vacinacao)

carregar_todas_vacinacoes()

filtros_card = pn.Card(
    filtro_nome_cidadao, filtro_nome_vacina,
    filtro_data_inicio, filtro_data_fim,
    pn.Row(btn_consultar, btn_limpar),
    title="🔍 Filtros de Consulta"
)

gerenciamento_card = pn.Card(
    pn.pane.Markdown("Para **Atualizar/Excluir**, selecione uma linha. Para **Registrar**, preencha os campos."),
    form_cpf, form_id_vacina, form_id_campanha, form_id_local,
    form_data_aplicacao, form_contagem,
    pn.Row(btn_inserir, btn_atualizar, btn_excluir),
    title="📝 Gerenciar Vacinações",
    collapsed=True
)

vacinacoes_page_layout = pn.Column(
    pn.pane.Markdown("## Gerenciamento de Registros de Vacinação", styles={'text-align': 'center'}),
    pn.Row(
        pn.Column(filtros_card, gerenciamento_card, width=400),
        pn.Column(tabela_vacinacoes, sizing_mode='stretch_width')
    )
)