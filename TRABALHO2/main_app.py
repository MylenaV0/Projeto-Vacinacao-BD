# main_app.py
import panel as pn

# Importar os layouts de cada página da pasta 'pages'
from pages.campanhas import campanhas_page_layout
from pages.agendamentos import agendamento_page_layout
from pages.vacinas import vacinas_page_layout
from pages.usuarios import usuarios_page_layout
from pages.vacinacoes import vacinacoes_page_layout
from pages.parentescos import parentescos_page_layout
from pages.locais import locais_page_layout # <-- Nova importação para Locais


pn.extension('tabulator', notifications=True)

# Montagem do Layout da Interface com Abas
app_tabs = pn.Tabs(
    ('Campanhas', campanhas_page_layout),
    ('Agendamentos', agendamento_page_layout),
    ('Vacinas', vacinas_page_layout),
    ('Usuários', usuarios_page_layout),
    ('Vacinações', vacinacoes_page_layout),
    ('Parentescos', parentescos_page_layout),
    ('Locais', locais_page_layout), # <-- Nova aba para Locais
    active=0, # Define a aba inicial (0 para Campanhas, 1 para Agendamentos, etc.)
    sizing_mode='stretch_both'
)

# Crie o template com tema de saúde
template = pn.template.FastListTemplate(
    title="Sistema de Gerenciamento de Saúde Pública",
    sidebar=[
        pn.pane.Markdown("## **Navegação**"),
        pn.pane.Markdown("---"),
        pn.pane.Markdown("Utilize as abas para navegar entre os módulos de **Campanhas**, **Agendamentos**, **Vacinas**, **Usuários**, **Vacinações**, **Parentescos** e **Locais**."), # Texto atualizado
        pn.pane.Markdown("---"),
        pn.pane.Markdown("Desenvolvido com Panel e PostgreSQL.")
    ],
    main=[app_tabs],
    header_background="#4CAF50",
    header_color="white",
    accent_base_color="#4CAF50",
)

# Servir a aplicação através do template
template.servable()

# Mensagem no console para indicar que a aplicação está rodando (opcional, mas útil para debug)
if __name__ == '__main__':
    print("\n-------------------------------------------")
    print("Sistema de Gerenciamento de Saúde Pública iniciado.")
    print(f"Acesse em: http://localhost:5006/main_app")
    print("-------------------------------------------\n")