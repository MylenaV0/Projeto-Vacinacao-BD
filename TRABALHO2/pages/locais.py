import panel as pn
import pandas as pd
import sqlalchemy
from datetime import date

# Importar a conexão do db_config
from db_config import engine

# --- Widgets para Filtragem
filtro_nome = pn.widgets.TextInput(name="Nome do Local", placeholder='Filtrar por nome...')
filtro_cidade = pn.widgets.TextInput(name="Cidade", placeholder='Filtrar por cidade...')
filtro_bairro = pn.widgets.TextInput(name="Bairro", placeholder='Filtrar por bairro...')

# --- Widgets do Formulário para Inserir/Atualizar
form_nome = pn.widgets.TextInput(name="Nome do Local*", placeholder='Ex: UBS Central')
form_rua = pn.widgets.TextInput(name="Rua*", placeholder='Ex: Rua da Saúde')
form_bairro = pn.widgets.TextInput(name="Bairro*", placeholder='Ex: Centro')
form_numero = pn.widgets.IntInput(name="Número*", start=1, value=1)
form_cidade = pn.widgets.TextInput(name="Cidade*", placeholder='Ex: Quixadá')
form_estado = pn.widgets.TextInput(name="Estado (UF)*", placeholder='Ex: CE', max_length=2)
form_contato = pn.widgets.TextInput(name="Contato*", placeholder='(88) 99999-9999')
form_capacidade = pn.widgets.IntInput(name="Capacidade (Opcional)", start=0, value=0)

# --- Botões de Ação
btn_consultar = pn.widgets.Button(name='Aplicar Filtros', button_type='primary')
btn_limpar = pn.widgets.Button(name='Limpar Filtros', button_type='default')
btn_inserir = pn.widgets.Button(name='Inserir Novo Local', button_type='success')
btn_atualizar = pn.widgets.Button(name='Atualizar Selecionado', button_type='warning', disabled=True)
btn_excluir = pn.widgets.Button(name='Excluir Selecionado', button_type='danger', disabled=True)

# --- Tabela
tabela_locais = pn.widgets.Tabulator(pd.DataFrame(), layout='fit_columns', show_index=False, height=400, page_size=10)

# --- Funções 

def carregar_todos_locais():
    try:
        query = "SELECT * FROM Local ORDER BY Nome;"
        df = pd.read_sql(query, engine)
        tabela_locais.value = df
    except Exception as e:
        pn.state.notifications.error(f"Erro ao carregar locais: {e}")

def on_consultar_local(event=None):
    try:
        conditions, params = [], {}
        if filtro_nome.value:
            conditions.append("Nome ILIKE :nome")
            params["nome"] = f"%{filtro_nome.value}%"
        if filtro_cidade.value:
            conditions.append("Cidade ILIKE :cidade")
            params["cidade"] = f"%{filtro_cidade.value}%"
        if filtro_bairro.value:
            conditions.append("Bairro ILIKE :bairro")
            params["bairro"] = f"%{filtro_bairro.value}%"

        base_query = "SELECT * FROM Local"
        if not conditions:
            carregar_todos_locais()
            pn.state.notifications.info("Nenhum filtro aplicado. Mostrando todos os locais.")
            return

        query_string = f"{base_query} WHERE {' AND '.join(conditions)} ORDER BY Nome;"
        with engine.connect() as connection:
            result = connection.execute(sqlalchemy.text(query_string), params)
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        
        tabela_locais.value = df
        pn.state.notifications.success(f"{len(df)} resultados encontrados.") if not df.empty else pn.state.notifications.warning("Nenhum local encontrado.")
    except Exception as e:
        pn.state.notifications.error(f"Erro ao consultar locais: {e}")

def on_limpar_filtros(event=None):
    filtro_nome.value, filtro_cidade.value, filtro_bairro.value = '', '', ''
    carregar_todos_locais()
    pn.state.notifications.success("Filtros limpos.")

def on_inserir_local(event=None):
    if not all([form_nome.value, form_rua.value, form_bairro.value, form_numero.value, form_cidade.value, form_estado.value, form_contato.value]):
        pn.state.notifications.warning("Preencha todos os campos obrigatórios (*).")
        return

    query = sqlalchemy.text("INSERT INTO Local (Nome, Rua, Bairro, Numero, Cidade, Estado, Contato, Capacidade) VALUES (:nome, :rua, :bairro, :num, :cid, :est, :cont, :cap)")
    params = {
        "nome": form_nome.value, "rua": form_rua.value, "bairro": form_bairro.value, "num": form_numero.value,
        "cid": form_cidade.value, "est": form_estado.value, "cont": form_contato.value, 
        "cap": form_capacidade.value if form_capacidade.value > 0 else None
    }
    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                connection.execute(query, params)
                trans.commit()
                pn.state.notifications.success("Local inserido com sucesso!")
                carregar_todos_locais()
            except Exception as e:
                trans.rollback()
                pn.state.notifications.error(f"Erro na transação ao inserir: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão ao inserir: {e}")

def on_atualizar_local(event=None):
    selecao = tabela_locais.selection
    if not selecao:
        pn.state.notifications.warning("Selecione um local para atualizar."); return

    id_local = int(tabela_locais.value.loc[selecao[0], 'id_local'])

    if not all([form_nome.value, form_rua.value, form_bairro.value, form_numero.value, form_cidade.value, form_estado.value, form_contato.value]):
        pn.state.notifications.warning("Preencha todos os campos obrigatórios (*)."); return
        
    query = sqlalchemy.text("UPDATE Local SET Nome=:nome, Rua=:rua, Bairro=:bairro, Numero=:num, Cidade=:cid, Estado=:est, Contato=:cont, Capacidade=:cap WHERE Id_Local = :id_local")
    params = {
        "nome": form_nome.value, "rua": form_rua.value, "bairro": form_bairro.value, "num": form_numero.value,
        "cid": form_cidade.value, "est": form_estado.value, "cont": form_contato.value, 
        "cap": form_capacidade.value if form_capacidade.value > 0 else None,
        "id_local": id_local
    }
    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                connection.execute(query, params)
                trans.commit()
                pn.state.notifications.success("Local atualizado com sucesso!")
                carregar_todos_locais()
            except Exception as e:
                trans.rollback()
                pn.state.notifications.error(f"Erro na transação ao atualizar: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão ao atualizar: {e}")

def on_excluir_local(event=None):
    selecao = tabela_locais.selection
    if not selecao:
        pn.state.notifications.warning("Selecione um local para excluir."); return

    id_local = int(tabela_locais.value.loc[selecao[0], 'id_local'])

    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                check_vacinacao = connection.execute(sqlalchemy.text("SELECT 1 FROM Vacinacao WHERE Id_Local = :id"), {"id": id_local}).scalar()
                check_agendamento = connection.execute(sqlalchemy.text("SELECT 1 FROM Agendamento WHERE Id_Local = :id"), {"id": id_local}).scalar()

                if check_vacinacao or check_agendamento:
                    pn.state.notifications.error("Não é possível excluir: Local está associado a vacinações ou agendamentos.")
                    trans.rollback()
                    return
                
                connection.execute(sqlalchemy.text("DELETE FROM Local WHERE Id_Local = :id"), {"id": id_local})
                trans.commit()
                pn.state.notifications.success("Local excluído com sucesso!")
                carregar_todos_locais()
                preencher_formulario_selecao([])
            except Exception as e:
                trans.rollback()
                pn.state.notifications.error(f"Erro na transação ao excluir: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão ao excluir: {e}")

@pn.depends(tabela_locais.param.selection, watch=True)
def preencher_formulario_selecao(selection):
    if not selection:
        btn_atualizar.disabled, btn_excluir.disabled = True, True
        form_nome.value, form_rua.value, form_bairro.value, form_cidade.value, form_estado.value, form_contato.value = '', '', '', '', '', ''
        form_numero.value, form_capacidade.value = 0, 0
        return
    
    btn_atualizar.disabled, btn_excluir.disabled = False, False
    row_data = tabela_locais.value.loc[selection[0]]
    
    form_nome.value = row_data.get('nome', '')
    form_rua.value = row_data.get('rua', '')
    form_bairro.value = row_data.get('bairro', '')
    form_numero.value = int(row_data.get('numero', 0))
    form_cidade.value = row_data.get('cidade', '')
    form_estado.value = row_data.get('estado', '')
    form_contato.value = row_data.get('contato', '')
    form_capacidade.value = int(row_data.get('capacidade', 0)) if pd.notna(row_data.get('capacidade')) else 0

# --- Conexões dos Botões
btn_consultar.on_click(on_consultar_local)
btn_limpar.on_click(on_limpar_filtros)
btn_inserir.on_click(on_inserir_local)
btn_atualizar.on_click(on_atualizar_local)
btn_excluir.on_click(on_excluir_local)

carregar_todos_locais()

# --- Layout da Página 
filtros_card = pn.Card(
    filtro_nome, filtro_cidade, filtro_bairro,
    pn.Row(btn_consultar, btn_limpar),
    title="🔍 Filtros de Consulta"
)

gerenciamento_card = pn.Card(
    pn.pane.Markdown("Para **Atualizar/Excluir**, selecione uma linha. Para **Inserir**, preencha os campos."),
    form_nome, form_rua, form_bairro, form_numero, form_cidade,
    form_estado, form_contato, form_capacidade,
    pn.Row(btn_inserir, btn_atualizar, btn_excluir),
    title="📝 Gerenciar Locais",
    collapsed=True
)

locais_page_layout = pn.Column(
    pn.pane.Markdown("## Gerenciamento de Locais de Vacinação", styles={'text-align': 'center'}),
    pn.Row(
        pn.Column(filtros_card, gerenciamento_card, width=400),
        pn.Column(tabela_locais, sizing_mode='stretch_width')
    )
)
