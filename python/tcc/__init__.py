"""
tcc — Reprodução do TCC "Fundamentos contábeis e capitalização de mercado de empresas elétricas brasileiras"
===============================================================================================

Rodrigo Pereira Fontes; orientador: Prof. Marco Antonio Alves de Souza Junior (Esalq/USP).
Trabalho de Conclusão de Curso, especialização (MBA) em Finanças e Controladoria, USP/Esalq, 2026.

Módulos, na ordem do pipeline:
    config          parâmetros e caminhos
    entradas        leitura dos extratos congelados (CVM, B3, documentos)
    capitalizacao   eq. (1): capitalização por classe, conciliando DFP, FRE e B3
    contabil        eqs. (3)–(6): ROE, EBITDA, alavancagem e porte
    painel          eq. (2), defasagem, elegibilidade, mínimo de quatro anos, winsorização
    estimacao       eq. (7): MQO com efeitos fixos, CR1, WCR, Holm, Driscoll–Kraay, R², VIF, FWL
    especificacoes  variáveis alternativas e catálogo de 44 modelos
    tabelas         Tabelas 1, 4–8, Apêndice C e Figura 1
    valores         chave → número formatado como no TCC
    conferencia     pacote original, statsmodels/linearmodels e texto do TCC
    relatorio       relatório explicado em PDF
"""
__version__ = "1.0.0"
