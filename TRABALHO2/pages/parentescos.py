import panel as pn
import pandas as pd
import sqlalchemy

# Importar a conexão e funções auxiliares do db_config
from db_config import engine, get_cidadaos, get_parentescos

# --- Widgets para FILTRAGEM ---
filtro_cpf = pn.widgets.TextInput(name="Filtrar por CPF", placeholder='Digite o CPF...')
# ADIÇÃO: Novo widget para filtrar por nome
filtro_nome = pn.widgets.TextInput(name="Filtrar por Nome", placeholder='Digite o nome...')

# --- Widgets do FORMULÁRIO para Inserir/Atualizar ---
form_cpf_responsavel = pn.widgets.Select(name="CPF do Responsável*", options={})
form_cpf_parente = pn.widgets.Select(name="CPF do Parente*", options={})

# --- Botões de AÇÃO ---
btn_consultar = pn.widgets.Button(name='Aplicar Filtros', button_type='primary')
btn_limpar = pn.widgets.Button(name='Limpar Filtros', button_type='default')
btn_inserir = pn.widgets.Button(name='Adicionar Parentesco', button_type='success')
btn_atualizar = pn.widgets.Button(name='Atualizar Selecionado', button_type='warning', disabled=True)
btn_excluir = pn.widgets.Button(name='Excluir Selecionado', button_type='danger', disabled=True)

# --- Tabela ---
tabela_parentescos = pn.widgets.Tabulator(pd.DataFrame(), layout='fit_columns', show_index=False, height=400, page_size=10)

# --- FUNÇÕES ---

def update_dropdown_options():
    try:
        cidadaos_df = get_cidadaos()
        if not cidadaos_df.empty:
            cpf_options = {f"{row['nome']} ({row['cpf']})": row['cpf'] for _, row in cidadaos_df.iterrows()}
            form_cpf_responsavel.options = cpf_options
            form_cpf_parente.options = cpf_options
        else:
            form_cpf_responsavel.options, form_cpf_parente.options = {}, {}
    except Exception as e:
        pn.state.notifications.error(f"Erro ao carregar cidadãos para os menus: {e}")

def carregar_todos_parentescos():
    try:
        df = get_parentescos()
        tabela_parentescos.value = df
        update_dropdown_options()
    except Exception as e:
        pn.state.notifications.error(f"Erro ao carregar parentescos: {e}")

def on_consultar_parentesco(event=None):
    try:
        df_completo = get_parentescos()
        df_filtrado = df_completo

        # ATUALIZAÇÃO: Lógica de filtro combinada
        if filtro_cpf.value:
            cpf_filtrar = filtro_cpf.value.strip()
            df_filtrado = df_filtrado[
                (df_filtrado['cpf_responsavel'].str.contains(cpf_filtrar, na=False)) | 
                (df_filtrado['cpf_parente'].str.contains(cpf_filtrar, na=False))
            ]
        
        if filtro_nome.value:
            nome_filtrar = filtro_nome.value.strip()
            df_filtrado = df_filtrado[
                (df_filtrado['nome_responsavel'].str.contains(nome_filtrar, case=False, na=False)) | 
                (df_filtrado['nome_parente'].str.contains(nome_filtrar, case=False, na=False))
            ]
        
        tabela_parentescos.value = df_filtrado
        if not (filtro_cpf.value or filtro_nome.value):
            pn.state.notifications.info("Nenhum filtro aplicado. Mostrando todos os parentescos.")
        else:
            pn.state.notifications.success(f"{len(df_filtrado)} resultados encontrados.")
    except Exception as e:
        pn.state.notifications.error(f"Erro ao consultar parentescos: {e}")

def on_limpar_filtros(event=None):
    # ATUALIZAÇÃO: Limpa também o novo campo de nome
    filtro_cpf.value = ''
    filtro_nome.value = ''
    carregar_todos_parentescos()
    pn.state.notifications.success("Filtros limpos.")

def on_inserir_parentesco(event=None):
    cpf_resp, cpf_par = form_cpf_responsavel.value, form_cpf_parente.value
    if not all([cpf_resp, cpf_par]):
        pn.state.notifications.warning("Selecione o Responsável e o Parente."); return
    if cpf_resp == cpf_par:
        pn.state.notifications.warning("Um cidadão não pode ser parente de si mesmo."); return

    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                check_q = sqlalchemy.text("SELECT 1 FROM Parente WHERE CPF_Responsavel = :resp AND CPF_Parente = :par")
                if connection.execute(check_q, {"resp": cpf_resp, "par": cpf_par}).scalar():
                    pn.state.notifications.warning("Este vínculo de parentesco já existe."); trans.rollback(); return

                insert_q = sqlalchemy.text("INSERT INTO Parente (CPF_Responsavel, CPF_Parente) VALUES (:resp, :par)")
                connection.execute(insert_q, {"resp": cpf_resp, "par": cpf_par})
                trans.commit()
                pn.state.notifications.success("Parentesco adicionado com sucesso!")
                carregar_todos_parentescos()
            except Exception as e:
                trans.rollback(); pn.state.notifications.error(f"Erro na transação: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão: {e}")

def on_atualizar_parentesco(event=None):
    selecao = tabela_parentescos.selection
    if not selecao:
        pn.state.notifications.warning("Selecione um parentesco para atualizar."); return

    id_parentesco = int(tabela_parentescos.value.loc[selecao[0], 'id_parentesco'])
    cpf_resp, cpf_par = form_cpf_responsavel.value, form_cpf_parente.value

    if not all([cpf_resp, cpf_par]):
        pn.state.notifications.warning("Selecione o Responsável e o Parente."); return
    if cpf_resp == cpf_par:
        pn.state.notifications.warning("Um cidadão não pode ser parente de si mesmo."); return

    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                update_q = sqlalchemy.text("UPDATE Parente SET CPF_Responsavel = :resp, CPF_Parente = :par WHERE Id_Parentesco = :id")
                connection.execute(update_q, {"resp": cpf_resp, "par": cpf_par, "id": id_parentesco})
                trans.commit()
                pn.state.notifications.success("Parentesco atualizado com sucesso!")
                carregar_todos_parentescos()
            except Exception as e:
                trans.rollback(); pn.state.notifications.error(f"Erro na transação ao atualizar: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão ao atualizar: {e}")

def on_excluir_parentesco(event=None):
    selecao = tabela_parentescos.selection
    if not selecao:
        pn.state.notifications.warning("Selecione um parentesco para excluir."); return

    id_parentesco = int(tabela_parentescos.value.loc[selecao[0], 'id_parentesco'])

    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                connection.execute(sqlalchemy.text("DELETE FROM Parente WHERE Id_Parentesco = :id"), {"id": id_parentesco})
                trans.commit()
                pn.state.notifications.success("Parentesco excluído com sucesso!")
                carregar_todos_parentescos()
                preencher_formulario_selecao([])
            except Exception as e:
                trans.rollback(); pn.state.notifications.error(f"Erro na transação ao excluir: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão ao excluir: {e}")

@pn.depends(tabela_parentescos.param.selection, watch=True)
def preencher_formulario_selecao(selection):
    if not selection:
        btn_atualizar.disabled, btn_excluir.disabled = True, True
        form_cpf_responsavel.value, form_cpf_parente.value = None, None
        return
    
    btn_atualizar.disabled, btn_excluir.disabled = False, False
    row_data = tabela_parentescos.value.loc[selection[0]]
    
    form_cpf_responsavel.value = row_data.get('cpf_responsavel')
    form_cpf_parente.value = row_data.get('cpf_parente')

# --- Conexões dos Botões e Carga Inicial ---
btn_consultar.on_click(on_consultar_parentesco)
btn_limpar.on_click(on_limpar_filtros)
btn_inserir.on_click(on_inserir_parentesco)
btn_atualizar.on_click(on_atualizar_parentesco)
btn_excluir.on_click(on_excluir_parentesco)

carregar_todos_parentescos()

# --- Layout da Página ---
filtros_card = pn.Card(
    # ATUALIZAÇÃO: Adicionado o filtro de nome ao layout
    filtro_cpf,
    filtro_nome,
    pn.Row(btn_consultar, btn_limpar),
    title="🔍 Filtros de Consulta"
)

gerenciamento_card = pn.Card(
    pn.pane.Markdown("Para **Atualizar/Excluir**, selecione uma linha. Para **Adicionar**, selecione os CPFs."),
    form_cpf_responsavel,
    form_cpf_parente,
    pn.Row(btn_inserir, btn_atualizar, btn_excluir),
    title="📝 Gerenciar Parentescos",
    collapsed=True
)

parentescos_page_layout = pn.Column(
    pn.pane.Markdown("## Gerenciamento de Parentescos", styles={'text-align': 'center'}),
    pn.Row(
        pn.Column(filtros_card, gerenciamento_card, width=450),
        pn.Column(tabela_parentescos, sizing_mode='stretch_width')
    )
)