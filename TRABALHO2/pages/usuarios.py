import panel as pn
import pandas as pd
import sqlalchemy

# Importar a conexão e a função de busca completa do db_config
from db_config import engine, get_usuarios_completo

# --- Widgets para FILTRAGEM ---
filtro_cpf = pn.widgets.TextInput(name="CPF do Usuário", placeholder='Filtrar por CPF...')
filtro_nome = pn.widgets.TextInput(name="Nome do Usuário", placeholder='Filtrar por nome...')

# --- Widgets do FORMULÁRIO para Inserir/Atualizar ---
form_cpf = pn.widgets.TextInput(name="CPF*", placeholder="Ex: 12345678901")
form_nome = pn.widgets.TextInput(name="Nome*", placeholder="Ex: João da Silva")
form_telefone = pn.widgets.TextInput(name="Telefone*", placeholder="Ex: (88) 91234-5678")
form_tipo = pn.widgets.RadioBoxGroup(name='Tipo de Usuário*', options=['Cidadão', 'Administrador', 'Agente de Saúde'], value='Cidadão')
# Campos específicos de cada perfil
form_cartao_sus = pn.widgets.TextInput(name="Cartão SUS (Cidadão)", placeholder="Opcional")
form_rua = pn.widgets.TextInput(name="Rua (Cidadão)", placeholder="Opcional")
form_bairro = pn.widgets.TextInput(name="Bairro (Cidadão)", placeholder="Opcional")
form_numero = pn.widgets.IntInput(name="Número (Cidadão)", start=0, value=0)
form_cidade = pn.widgets.TextInput(name="Cidade (Cidadão)", placeholder="Opcional")
form_estado = pn.widgets.TextInput(name="Estado (Cidadão)", placeholder="Opcional")
form_local_trabalho = pn.widgets.TextInput(name="Local de Trabalho (Admin)", placeholder="Opcional")
form_email = pn.widgets.TextInput(name="Email (Agente)", placeholder="Opcional")
form_posto_trabalho = pn.widgets.TextInput(name="Posto de Trabalho (Agente)", placeholder="Opcional")

# Painéis para agrupar os campos de perfil
cidadao_fields = pn.Column(form_cartao_sus, form_rua, form_bairro, form_numero, form_cidade, form_estado)
admin_fields = pn.Column(form_local_trabalho)
agente_fields = pn.Column(form_email, form_posto_trabalho)

@pn.depends(form_tipo.param.value, watch=True)
def update_user_fields(tipo):
    cidadao_fields.visible = (tipo == 'Cidadão')
    admin_fields.visible = (tipo == 'Administrador')
    agente_fields.visible = (tipo == 'Agente de Saúde')

# --- Botões de AÇÃO ---
btn_consultar = pn.widgets.Button(name='Aplicar Filtros', button_type='primary')
btn_limpar = pn.widgets.Button(name='Limpar Filtros', button_type='default')
btn_inserir = pn.widgets.Button(name='Inserir Novo Usuário', button_type='success')
btn_atualizar = pn.widgets.Button(name='Atualizar Selecionado', button_type='warning', disabled=True)
btn_excluir = pn.widgets.Button(name='Excluir Selecionado', button_type='danger', disabled=True)

# --- Tabela para exibir Usuários ---
tabela_usuarios = pn.widgets.Tabulator(pd.DataFrame(), layout='fit_columns', show_index=False, height=400, page_size=10)

# --- FUNÇÕES ---

def carregar_todos_usuarios():
    try:
        df = get_usuarios_completo()
        tabela_usuarios.value = df
    except Exception as e:
        pn.state.notifications.error(f"Erro ao carregar usuários: {e}")

def on_consultar_usuario(event=None):
    try:
        df_completo = get_usuarios_completo()
        df_filtrado = df_completo
        
        if filtro_cpf.value:
            df_filtrado = df_filtrado[df_filtrado['cpf'].str.contains(filtro_cpf.value, case=False, na=False)]
        if filtro_nome.value:
            df_filtrado = df_filtrado[df_filtrado['nome'].str.contains(filtro_nome.value, case=False, na=False)]

        tabela_usuarios.value = df_filtrado
        if df_filtrado.empty and (filtro_cpf.value or filtro_nome.value):
             pn.state.notifications.warning("Nenhum usuário encontrado.")
        else:
            pn.state.notifications.success(f"{len(df_filtrado)} resultado(s) encontrado(s).")
    except Exception as e:
        pn.state.notifications.error(f"Erro ao consultar usuários: {e}")

def on_limpar_filtros(event=None):
    filtro_cpf.value, filtro_nome.value = '', ''
    carregar_todos_usuarios()
    pn.state.notifications.success("Filtros limpos.")

def on_inserir_usuario(event=None):
    cpf = form_cpf.value.strip()
    if not all([cpf, form_nome.value, form_telefone.value]):
        pn.state.notifications.warning("CPF, Nome e Telefone são obrigatórios.")
        return

    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                if connection.execute(sqlalchemy.text("SELECT 1 FROM Usuario WHERE CPF = :cpf"), {"cpf": cpf}).scalar():
                    pn.state.notifications.warning(f"CPF {cpf} já cadastrado.")
                    trans.rollback(); return
                
                connection.execute(sqlalchemy.text("INSERT INTO Usuario (CPF, Nome, Telefone) VALUES (:cpf, :nome, :tel)"), {"cpf": cpf, "nome": form_nome.value, "tel": form_telefone.value})

                if form_tipo.value == 'Cidadão':
                    connection.execute(sqlalchemy.text("INSERT INTO Cidadao (CPF, Cartao_Sus, Rua, Bairro, Numero, Cidade, Estado) VALUES (:cpf, :sus, :rua, :bairro, :num, :cid, :est)"),
                                       {"cpf": cpf, "sus": form_cartao_sus.value, "rua": form_rua.value, "bairro": form_bairro.value, "num": form_numero.value, "cid": form_cidade.value, "est": form_estado.value})
                elif form_tipo.value == 'Administrador':
                    connection.execute(sqlalchemy.text("INSERT INTO Administrador (CPF, Local_Trabalho) VALUES (:cpf, :local)"), {"cpf": cpf, "local": form_local_trabalho.value})
                elif form_tipo.value == 'Agente de Saúde':
                    connection.execute(sqlalchemy.text("INSERT INTO Agente_Saude (CPF, Email, Posto_Trabalho) VALUES (:cpf, :email, :posto)"), {"cpf": cpf, "email": form_email.value, "posto": form_posto_trabalho.value})
                
                trans.commit()
                pn.state.notifications.success("Usuário inserido com sucesso!")
                carregar_todos_usuarios()
                preencher_formulario_selecao([])
            except Exception as e:
                trans.rollback()
                pn.state.notifications.error(f"Erro na transação ao inserir: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão ao inserir: {e}")

def on_atualizar_usuario(event=None):
    selecao = tabela_usuarios.selection
    if not selecao:
        pn.state.notifications.warning("Selecione um usuário para atualizar.")
        return
        
    cpf_original = tabela_usuarios.value.loc[selecao[0], 'cpf']
    tipo_original = tabela_usuarios.value.loc[selecao[0], 'tipo_usuario']
    novo_tipo = form_tipo.value
    
    if form_cpf.value.strip() != cpf_original:
        pn.state.notifications.error("O CPF não pode ser alterado.")
        form_cpf.value = cpf_original
        return

    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                # 1. Atualiza a tabela principal
                connection.execute(sqlalchemy.text("UPDATE Usuario SET Nome=:nome, Telefone=:tel WHERE CPF=:cpf"), 
                                   {"nome": form_nome.value, "tel": form_telefone.value, "cpf": cpf_original})

                # 2. Lida com a lógica de perfis
                if novo_tipo != tipo_original:
                    # Se o tipo mudou, apaga o perfil antigo
                    if tipo_original == 'Cidadão':
                        connection.execute(sqlalchemy.text("DELETE FROM Cidadao WHERE CPF = :cpf"), {"cpf": cpf_original})
                    elif tipo_original == 'Administrador':
                        connection.execute(sqlalchemy.text("DELETE FROM Administrador WHERE CPF = :cpf"), {"cpf": cpf_original})
                    elif tipo_original == 'Agente de Saúde':
                        connection.execute(sqlalchemy.text("DELETE FROM Agente_Saude WHERE CPF = :cpf"), {"cpf": cpf_original})

                    # E insere o novo perfil
                    if novo_tipo == 'Cidadão':
                        connection.execute(sqlalchemy.text("INSERT INTO Cidadao (CPF, Cartao_Sus, Rua, Bairro, Numero, Cidade, Estado) VALUES (:cpf, :sus, :rua, :bairro, :num, :cid, :est)"),
                                           {"cpf": cpf_original, "sus": form_cartao_sus.value, "rua": form_rua.value, "bairro": form_bairro.value, "num": form_numero.value, "cid": form_cidade.value, "est": form_estado.value})
                    elif novo_tipo == 'Administrador':
                        connection.execute(sqlalchemy.text("INSERT INTO Administrador (CPF, Local_Trabalho) VALUES (:cpf, :local)"), {"cpf": cpf_original, "local": form_local_trabalho.value})
                    elif novo_tipo == 'Agente de Saúde':
                        connection.execute(sqlalchemy.text("INSERT INTO Agente_Saude (CPF, Email, Posto_Trabalho) VALUES (:cpf, :email, :posto)"), {"cpf": cpf_original, "email": form_email.value, "posto": form_posto_trabalho.value})
                else:
                    # Se o tipo não mudou, apenas atualiza o perfil existente
                    if novo_tipo == 'Cidadão':
                        connection.execute(sqlalchemy.text("UPDATE Cidadao SET Cartao_Sus=:sus, Rua=:rua, Bairro=:bairro, Numero=:num, Cidade=:cid, Estado=:est WHERE CPF=:cpf"),
                                           {"sus": form_cartao_sus.value, "rua": form_rua.value, "bairro": form_bairro.value, "num": form_numero.value, "cid": form_cidade.value, "est": form_estado.value, "cpf": cpf_original})
                    elif novo_tipo == 'Administrador':
                        connection.execute(sqlalchemy.text("UPDATE Administrador SET Local_Trabalho=:local WHERE CPF=:cpf"), {"local": form_local_trabalho.value, "cpf": cpf_original})
                    elif novo_tipo == 'Agente de Saúde':
                        connection.execute(sqlalchemy.text("UPDATE Agente_Saude SET Email=:email, Posto_Trabalho=:posto WHERE CPF=:cpf"), {"email": form_email.value, "posto": form_posto_trabalho.value, "cpf": cpf_original})

                trans.commit()
                pn.state.notifications.success("Usuário atualizado com sucesso!")
                carregar_todos_usuarios()
                preencher_formulario_selecao([])

            except Exception as e:
                trans.rollback()
                pn.state.notifications.error(f"Erro na transação ao atualizar: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão ao atualizar: {e}")

def on_excluir_usuario(event=None):
    selecao = tabela_usuarios.selection
    if not selecao:
        pn.state.notifications.warning("Selecione um usuário para excluir.")
        return

    cpf_para_excluir = tabela_usuarios.value.loc[selecao[0], 'cpf']
    
    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                if connection.execute(sqlalchemy.text("SELECT 1 FROM Vacinacao WHERE CPF = :cpf"), {"cpf": cpf_para_excluir}).scalar():
                    pn.state.notifications.error("Não é possível excluir: Usuário possui registros de vacinação.")
                    trans.rollback(); return
                
                connection.execute(sqlalchemy.text("DELETE FROM Cidadao WHERE CPF = :cpf"), {"cpf": cpf_para_excluir})
                connection.execute(sqlalchemy.text("DELETE FROM Administrador WHERE CPF = :cpf"), {"cpf": cpf_para_excluir})
                connection.execute(sqlalchemy.text("DELETE FROM Agente_Saude WHERE CPF = :cpf"), {"cpf": cpf_para_excluir})
                connection.execute(sqlalchemy.text("DELETE FROM Usuario WHERE CPF = :cpf"), {"cpf": cpf_para_excluir})
                
                trans.commit()
                pn.state.notifications.success("Usuário excluído com sucesso!")
                carregar_todos_usuarios()
                preencher_formulario_selecao([])
            except Exception as e:
                trans.rollback()
                pn.state.notifications.error(f"Erro na transação ao excluir: {e}")
    except Exception as e:
        pn.state.notifications.error(f"Erro de conexão ao excluir: {e}")

@pn.depends(tabela_usuarios.param.selection, watch=True)
def preencher_formulario_selecao(selection):
    if not selection:
        btn_atualizar.disabled, btn_excluir.disabled = True, True
        form_cpf.value, form_nome.value, form_telefone.value, form_cartao_sus.value = '', '', '', ''
        form_rua.value, form_bairro.value, form_cidade.value, form_estado.value = '', '', '', ''
        form_local_trabalho.value, form_email.value, form_posto_trabalho.value = '', '', ''
        form_numero.value = 0
        form_tipo.value = 'Cidadão'
        return
    
    btn_atualizar.disabled, btn_excluir.disabled = False, False
    row_data = tabela_usuarios.value.loc[selection[0]]
    
    form_cpf.value = row_data.get('cpf', '')
    form_nome.value = row_data.get('nome', '')
    form_telefone.value = row_data.get('telefone', '')
    form_tipo.value = row_data.get('tipo_usuario', 'Cidadão')
    form_cartao_sus.value = str(row_data.get('cartao_sus', ''))
    form_rua.value = str(row_data.get('rua', ''))
    form_bairro.value = str(row_data.get('bairro', ''))
    form_numero.value = int(row_data.get('numero', 0)) if pd.notna(row_data.get('numero')) else 0
    form_cidade.value = str(row_data.get('cidade', ''))
    form_estado.value = str(row_data.get('estado', ''))
    form_local_trabalho.value = str(row_data.get('admin_local_trabalho', ''))
    form_email.value = str(row_data.get('agente_email', ''))
    form_posto_trabalho.value = str(row_data.get('agente_posto_trabalho', ''))

# --- Conexões dos Botões e Carga Inicial ---
btn_consultar.on_click(on_consultar_usuario)
btn_limpar.on_click(on_limpar_filtros)
btn_inserir.on_click(on_inserir_usuario)
btn_atualizar.on_click(on_atualizar_usuario)
btn_excluir.on_click(on_excluir_usuario)

carregar_todos_usuarios()
update_user_fields(form_tipo.value)

# --- Layout da Página ---
filtros_card = pn.Card(
    pn.Column(filtro_cpf, filtro_nome),
    pn.Row(btn_consultar, btn_limpar),
    title="🔍 Filtros de Consulta"
)

gerenciamento_card = pn.Card(
    pn.pane.Markdown("Para **Atualizar/Excluir**, selecione uma linha. Para **Inserir**, preencha os campos."),
    form_cpf, form_nome, form_telefone, form_tipo,
    pn.Column(cidadao_fields, admin_fields, agente_fields),
    pn.Row(btn_inserir, btn_atualizar, btn_excluir),
    title="📝 Gerenciar Usuários",
    collapsed=True
)

usuarios_page_layout = pn.Column(
    pn.pane.Markdown("## Gerenciamento de Usuários", styles={'text-align': 'center'}),
    pn.Row(
        pn.Column(filtros_card, gerenciamento_card, width=400),
        pn.Column(tabela_usuarios, sizing_mode='stretch_width')
    )
)