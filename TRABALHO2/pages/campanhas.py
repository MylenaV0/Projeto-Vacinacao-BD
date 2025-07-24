import panel as pn
import pandas as pd
import sqlalchemy
from datetime import date, datetime

# Importar a conexão do db_config
from db_config import engine

# --- Widgets para FILTRAGEM ---
filtro_nome = pn.widgets.TextInput(name="Nome da Campanha", placeholder='Filtrar por nome...')
filtro_doenca = pn.widgets.TextInput(name="Doença Alvo", placeholder='Filtrar por doença...')
filtro_publico = pn.widgets.TextInput(name="Público Alvo", placeholder='Filtrar por público alvo...')

# --- Widgets do FORMULÁRIO para Inserir/Atualizar ---
form_nome = pn.widgets.TextInput(name="Nome da Campanha*", placeholder='Ex: Campanha de Vacinação COVID-19')
form_doenca = pn.widgets.TextInput(name="Doença Alvo*", placeholder='Ex: COVID-19')
form_tipo_vacina = pn.widgets.RadioBoxGroup(name='Tipo da Vacina*', options=['Dose Única', 'Múltiplas Doses'], value='Dose Única')
form_data_inicio = pn.widgets.DatePicker(name='Data de Início*')
form_data_fim = pn.widgets.DatePicker(name='Data de Fim (Opcional)')
form_publico = pn.widgets.TextInput(name="Público Alvo*", placeholder='Ex: Crianças de 0-5 anos')

# --- Botões de AÇÃO ---
btn_consultar = pn.widgets.Button(name='Aplicar Filtros', button_type='primary')
btn_limpar = pn.widgets.Button(name='Limpar Filtros', button_type='default')
btn_inserir = pn.widgets.Button(name='Inserir Nova Campanha', button_type='success')
btn_atualizar = pn.widgets.Button(name='Atualizar Selecionada', button_type='warning', disabled=True)
btn_excluir = pn.widgets.Button(name='Excluir Selecionada', button_type='danger', disabled=True)

# --- Tabela para exibir Campanhas ---
tabela_campanhas = pn.widgets.Tabulator(pd.DataFrame(), layout='fit_columns', show_index=False, height=400, page_size=10)

# --- FUNÇÕES ---

def formatar_datas_df(df):
    for col in ['data_inicio', 'data_fim']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%Y')
    return df

def carregar_todas_campanhas():
    try:
        query = "SELECT * FROM Campanha ORDER BY Id_Campanha DESC;"
        df = pd.read_sql(query, engine)
        tabela_campanhas.value = formatar_datas_df(df)
    except Exception as e:
        pn.state.notifications.error(f"Erro ao carregar campanhas: {e}")

def on_consultar_campanha(event=None):
    try:
        conditions, params = [], {}
        if filtro_nome.value:
            conditions.append("Nome ILIKE :nome")
            params["nome"] = f"%{filtro_nome.value}%"
        if filtro_doenca.value:
            conditions.append("Doenca_Alvo ILIKE :doenca")
            params["doenca"] = f"%{filtro_doenca.value}%"
        if filtro_publico.value:
            conditions.append("Publico_Alvo ILIKE :publico")
            params["publico"] = f"%{filtro_publico.value}%"
        
        base_query = "SELECT * FROM Campanha"
        if not conditions:
            carregar_todas_campanhas()
            return

        query_string = f"{base_query} WHERE {' AND '.join(conditions)} ORDER BY Id_Campanha DESC;"
        
        with engine.connect() as connection:
            result = connection.execute(sqlalchemy.text(query_string), params)
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        
        tabela_campanhas.value = formatar_datas_df(df)
        pn.state.notifications.success(f"{len(df)} resultados.") if not df.empty else pn.state.notifications.warning("Nenhuma campanha encontrada.")
    except Exception as e:
        pn.state.notifications.error(f"Erro ao consultar campanhas: {e}")

def on_limpar_filtros(event=None):
    filtro_nome.value, filtro_doenca.value, filtro_publico.value = '', '', ''
    carregar_todas_campanhas()
    pn.state.notifications.success("Filtros limpos.")

def on_inserir_campanha(event=None):
    if not all([form_nome.value, form_doenca.value, form_data_inicio.value, form_publico.value]):
        pn.state.notifications.warning("Preencha todos os campos obrigatórios (*)."); return
    if form_data_fim.value and form_data_fim.value < form_data_inicio.value:
        pn.state.notifications.error("A Data de Fim não pode ser anterior à Data de Início."); return

    query = sqlalchemy.text("INSERT INTO Campanha(Nome, Doenca_alvo, Tipo_vacina, Data_inicio, Data_fim, Publico_alvo) VALUES (:nome, :doenca, :tipo, :inicio, :fim, :publico)")
    params = {
        "nome": form_nome.value, "doenca": form_doenca.value, "tipo": form_tipo_vacina.value,
        "inicio": form_data_inicio.value, "fim": form_data_fim.value, "publico": form_publico.value
    }
    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                connection.execute(query, params)
                trans.commit()
                pn.state.notifications.success("Campanha inserida com sucesso!")
                carregar_todas_campanhas()
            except Exception as e:
                trans.rollback(); pn.state.notifications.error(f"Erro na transação: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão: {e}")

def on_atualizar_campanha(event=None):
    selecao = tabela_campanhas.selection
    if not selecao:
        pn.state.notifications.warning("Selecione uma campanha para atualizar."); return

    id_campanha = int(tabela_campanhas.value.loc[selecao[0], 'id_campanha'])

    if not all([form_nome.value, form_doenca.value, form_data_inicio.value, form_publico.value]):
        pn.state.notifications.warning("Preencha todos os campos obrigatórios (*)."); return
    if form_data_fim.value and form_data_fim.value < form_data_inicio.value:
        pn.state.notifications.error("A Data de Fim não pode ser anterior à Data de Início."); return
        
    query = sqlalchemy.text("UPDATE Campanha SET Nome=:nome, Doenca_alvo=:doenca, Tipo_vacina=:tipo, Data_inicio=:inicio, Data_fim=:fim, Publico_alvo=:publico WHERE Id_Campanha = :id_campanha")
    params = {
        "nome": form_nome.value, "doenca": form_doenca.value, "tipo": form_tipo_vacina.value,
        "inicio": form_data_inicio.value, "fim": form_data_fim.value, "publico": form_publico.value,
        "id_campanha": id_campanha
    }
    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                connection.execute(query, params)
                trans.commit()
                pn.state.notifications.success("Campanha atualizada com sucesso!")
                carregar_todas_campanhas()
            except Exception as e:
                trans.rollback(); pn.state.notifications.error(f"Erro na transação ao atualizar: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão ao atualizar: {e}")

def on_excluir_campanha(event=None):
    selecao = tabela_campanhas.selection
    if not selecao:
        pn.state.notifications.warning("Selecione uma campanha para excluir."); return

    id_campanha = int(tabela_campanhas.value.loc[selecao[0], 'id_campanha'])
    
    # Adicionando um print de depuração para ter certeza da conversão
    print(f"Tentando excluir ID: {id_campanha}, Tipo: {type(id_campanha)}")

    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                check_query = sqlalchemy.text("SELECT 1 FROM Vacinacao WHERE Id_Campanha = :id_campanha")
                em_uso = connection.execute(check_query, {"id_campanha": id_campanha}).scalar()
                
                if em_uso:
                    pn.state.notifications.error("Não é possível excluir: Campanha associada a vacinações."); trans.rollback(); return
                
                delete_query = sqlalchemy.text("DELETE FROM Campanha WHERE Id_Campanha = :id_campanha")
                connection.execute(delete_query, {"id_campanha": id_campanha})
                
                trans.commit()
                pn.state.notifications.success("Campanha excluída com sucesso!")
                carregar_todas_campanhas()
                preencher_formulario_selecao([])
            except Exception as e:
                trans.rollback(); pn.state.notifications.error(f"Erro na transação ao excluir: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão ao excluir: {e}")

@pn.depends(tabela_campanhas.param.selection, watch=True)
def preencher_formulario_selecao(selection):
    """Preenche o formulário de edição quando uma linha da tabela é selecionada."""
    if not selection:
        btn_atualizar.disabled = True
        btn_excluir.disabled = True
        # Limpar formulário
        form_nome.value, form_doenca.value, form_publico.value = '', '', ''
        form_tipo_vacina.value = 'Dose Única'
        form_data_inicio.value, form_data_fim.value = None, None
        return
    
    btn_atualizar.disabled = False
    btn_excluir.disabled = False
    
    row_data = tabela_campanhas.value.loc[selection[0]]
    
    form_nome.value = row_data.get('nome', '')
    form_doenca.value = row_data.get('doenca_alvo', '')
    form_publico.value = row_data.get('publico_alvo', '')

    # --- CORREÇÃO APLICADA AQUI ---
    # Verifica se o valor do banco de dados existe nas opções do widget
    tipo_vacina_do_banco = row_data.get('tipo_vacina')
    if tipo_vacina_do_banco in form_tipo_vacina.options:
        form_tipo_vacina.value = tipo_vacina_do_banco
    else:
        # Se não existir, define um valor padrão para evitar o 'None'
        form_tipo_vacina.value = 'Dose Única'
    
    try:
        data_inicio_raw = row_data.get('data_inicio')
        form_data_inicio.value = datetime.strptime(data_inicio_raw, '%d/%m/%Y').date() if data_inicio_raw else None
    except (ValueError, TypeError):
        form_data_inicio.value = pd.to_datetime(data_inicio_raw).date() if pd.notna(data_inicio_raw) else None
        
    try:
        data_fim_raw = row_data.get('data_fim')
        form_data_fim.value = datetime.strptime(data_fim_raw, '%d/%m/%Y').date() if data_fim_raw else None
    except (ValueError, TypeError):
        form_data_fim.value = pd.to_datetime(data_fim_raw).date() if pd.notna(data_fim_raw) else None

# --- Conexões dos Botões e Carga Inicial ---
btn_consultar.on_click(on_consultar_campanha)
btn_limpar.on_click(on_limpar_filtros)
btn_inserir.on_click(on_inserir_campanha)
btn_atualizar.on_click(on_atualizar_campanha)
btn_excluir.on_click(on_excluir_campanha)

carregar_todas_campanhas()

# --- Layout da Página ---
filtros_card = pn.Card(pn.Column(filtro_nome, filtro_doenca, filtro_publico), pn.Row(btn_consultar, btn_limpar), title="🔍 Filtros de Consulta")
gerenciamento_card = pn.Card(pn.pane.Markdown("Para **Atualizar/Excluir**, selecione uma linha. Para **Inserir**, preencha os campos."), form_nome, form_doenca, form_publico, form_tipo_vacina, form_data_inicio, form_data_fim, pn.Row(btn_inserir, btn_atualizar, btn_excluir), title="📝 Gerenciar Campanhas", collapsed=True)

campanhas_page_layout = pn.Column(
    pn.pane.Markdown("## Gerenciamento de Campanhas de Vacinação", styles={'text-align': 'center'}),
    pn.Row(
        pn.Column(filtros_card, gerenciamento_card, width=400),
        pn.Column(tabela_campanhas, sizing_mode='stretch_width')
    )
)