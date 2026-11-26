"""
tcc.config — Parâmetros e caminhos do estudo
=============================================

Todas as escolhas metodológicas que aparecem em mais de um módulo ficam aqui,
com a justificativa e a seção do TCC de onde vêm. Mudar um parâmetro neste
arquivo muda o estudo inteiro de forma consistente.

Referências citadas:
    Collins, Maydew e Weiss (1997); Barth, Beaver e Landsman (2001) — relevância informacional.
    Cameron e Miller (2015); MacKinnon, Nielsen e Webb (2023) — inferência com poucos grupos.
"""
from pathlib import Path                                   # caminhos independentes do sistema operacional

# -----------------------------------------------------------------------------
# Caminhos
# -----------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[2]                 # pasta do repositório (python/tcc/config.py -> raiz)
DADOS = RAIZ / "dados"                                     # extratos congelados da coleta (entrada)
REFERENCIA = RAIZ / "referencia"                           # saídas do pacote original (só para conferência)
ROTEIRO = RAIZ / "relatorio" / "roteiro.txt"               # texto do relatório em PDF (compartilhado com o R)
RESULTADOS = RAIZ / "resultados" / "python"                # saídas da versão Python (a R grava em resultados/r)
TABELAS = RESULTADOS / "tabelas_tcc"                       # tabelas no formato do TCC

# -----------------------------------------------------------------------------
# Amostra (TCC, seções "Seleção da amostra" e "Painel")
# -----------------------------------------------------------------------------
ANOS_COLETA = range(2010, 2026)                            # anos de mercado com cotação de dezembro coletada
ANO_INICIO_PRINCIPAL = 2020                                # painel principal: 2020–2025 (maior cobertura entre empresas)
ANO_FIM = 2025                                             # último ano de mercado
ANO_INICIO_HISTORICO = 2010                                # extensão histórica (2010–2011 caem: só uma empresa)
MIN_EXERCICIOS = 4                                         # mínimo de anos por empresa: com efeito fixo, o modelo
                                                           # só aprende com a variação dentro da empresa
MIN_EMPRESAS_ANO = 2                                       # um ano com uma só empresa não tem comparação transversal
PERCENTIS_WINSOR = (0.01, 0.99)                            # winsorização de ROE e alavancagem (Tabela 3, nota)

# -----------------------------------------------------------------------------
# Variáveis do modelo (eq. 7 do TCC): fundamentos do exercício t−1
# -----------------------------------------------------------------------------
FUNDAMENTOS = ["roe_lag", "dl_lag", "size_lag"]           # ROE (eq. 3), AL (eq. 5) e PORTE (eq. 6), em t−1
DEPENDENTE = "ln_mcap"                                     # y = ln(VM), eq. (2): capitalização de dezembro de t

# -----------------------------------------------------------------------------
# Conciliação contábil e acionária (TCC, "Conciliação dos dados contábeis e acionários")
# -----------------------------------------------------------------------------
TOLERANCIA_LUCRO = 1000                                    # R$ 1 mil: diferença aceita entre lucro total e a soma
                                                           # controladora + não controladores
ESCALAS = (1, 1000)                                        # quantidades de ações em unidades ou em milhares
JANELA_EVENTO = "06-30"                                    # eventos aprovados até 30/06 do ano seguinte e já
                                                           # refletidos na DFP são desfeitos
# Raiz antiga do código de negociação quando a empresa mudou de ticker
RAIZ_ANTIGA = {"EGIE": ("TBLE", 2015),                     # Engie Brasil = Tractebel Energia até 2015
               "ENEV": ("MPXE", 2012)}                     # Eneva = MPX Energia até 2012
# Quantidades conferidas em documentos originais (TCC, mesma seção; Apêndice B)
CEMIG_2020 = dict(on=507_670_289, pn=1_011_082_312,        # Cemig (2021): DFs de 2020, nota 26 (6-K na SEC)
                  ton=71, tpn=583_709)                        # tesouraria: 71 ON e 583.709 PN
EDP_2010_2011 = dict(on=158_805_204, pn=0,                 # EDP (2012): DF de 2011, nota 26, p. 26
                     ton=280_225, tpn=0)                      # tesouraria: 280.225 ON

# -----------------------------------------------------------------------------
# Sensibilidades (TCC, "Inferência e verificações de sensibilidade"; Apêndice C)
# -----------------------------------------------------------------------------
# Janelas de eventos societários: venda da CEB-D (2021), reorganização da CESP e incorporação
# da AES Brasil pela Auren (2022 e 2024), recuperação judicial da Light (2023).
TRANSICOES = {"CEBR3": [2021, 2022],                          # CEB: venda da CEB-D (CEB, 2022)
              "AURE3": [2022, 2023, 2024, 2025],              # Auren: CESP e AES Brasil (Auren Energia, 2025)
              "LIGT3": [2023, 2024]}                          # Light: recuperação judicial (Light, 2023)
# Agrupamento societário conservador para a inferência (12 grupos):
# Elektro é controlada pela Neoenergia; Taesa tem a Cemig como cocontroladora (com a ISA).
GRUPOS_SOCIETARIOS = {"EKTR3": "NEOE3", "TAEE3": "CMIG3"}     # Neoenergia (2025); Taesa (2025)
DIA_MINIMO_COTACAO = 20                                    # filtro de liquidez: último negócio a partir de 20/dez

# -----------------------------------------------------------------------------
# Inferência (TCC, Apêndice B)
# -----------------------------------------------------------------------------
NIVEL = 0.05                                               # referência de significância
BLOCO_WCR = 4096                                           # combinações de sinais processadas por vez (memória)
TOL_EMPATE_WCR = 1e-10                                     # tolerância numérica para |t*| >= |t observado|
DEFASAGENS_DK = (1, 2)                                     # Driscoll–Kraay: Bartlett com uma e duas defasagens

# -----------------------------------------------------------------------------
# Tabelas descritivas do TCC (texto e códigos, sem resultados estimados)
# -----------------------------------------------------------------------------
# Tabela 2 do TCC — etapas de construção e verificação, com o módulo que executa cada uma
ETAPAS_TCC = [("Identificação", "Código CVM, CNPJ e classes de ações", "entradas"),  # (etapa, procedimento, módulo)
              ("Contabilidade", "Exercício corrente, versão, escala e conciliação do lucro", "contabil"),  # (continuação)
              ("Capitalização", "Quantidade por classe, tesouraria e cotação nominal", "capitalizacao"),  # (continuação)
              ("Painel", "Defasagem anual, denominadores válidos e mínimo de quatro anos", "painel"),  # (continuação)
              ("Estimação", "Efeitos fixos de empresa e ano; inferência agrupada, bootstrap e Driscoll–Kraay", "estimacao"),  # (continuação)
              ("Sensibilidade", "Extremos, composição, negociação e extensão histórica", "especificacoes")]  # (fim)
# Tabela 3 do TCC — definição e unidade das variáveis, com a equação e a coluna do painel
VARIAVEIS_TCC = [("Valor de mercado", "Logaritmo da capitalização das classes elegíveis", "ln de reais", "eqs. 1–2", "ln_mcap"),  # (medida, definição, unidade, equação, coluna)
                 ("Rentabilidade", "Lucro / patrimônio da controladora", "Decimal", "eq. 3", "roe_lag"),  # (continuação)
                 ("Alavancagem", "Dívida financeira líquida / EBITDA aproximado", "Vezes", "eqs. 4–5", "dl_lag"),  # (continuação)
                 ("Porte", "Logaritmo do ativo total", "ln de reais", "eq. 6", "size_lag")]  # (fim)
# Apêndice B, Tabela 1 — rubricas da CVM usadas pelos módulos contabil e entradas
RUBRICAS = [("Ativo total", "BPA", "1"),                      # (conta, demonstração, código CVM)
            ("Caixa e equivalentes", "BPA", "1.01.01"),       # (continuação)
            ("Aplicações financeiras (sensibilidade)", "BPA", "1.01.02"),  # (continuação)
            ("Empréstimos e financiamentos de curto prazo", "BPP", "2.01.04"),  # (continuação)
            ("Empréstimos e financiamentos de longo prazo", "BPP", "2.02.01"),  # (continuação)
            ("Patrimônio líquido total", "BPP", "2.03"),     # (continuação)
            ("Participação dos não controladores no patrimônio", "BPP", "2.03.09"),  # (continuação)
            ("Resultado antes do financeiro e dos tributos", "DRE", "3.05"),  # (continuação)
            ("Lucro líquido total", "DRE", "3.11"),          # (continuação)
            ("Lucro atribuível à controladora", "DRE", "3.11.01"),  # (continuação)
            ("Lucro atribuível aos não controladores", "DRE", "3.11.02"),  # (continuação)
            ("Depreciação, amortização e exaustão", "DVA", "7.04.01")]  # (fim)
DEMONSTRACOES = {"BPA": "Balanço Patrimonial Ativo", "BPP": "Balanço Patrimonial Passivo",  # sigla → nome no campo GRUPO_DFP
                 "DRE": "Demonstração do Resultado", "DVA": "Demonstração de Valor Adicionado"}  # (fim)

# Nomes das empresas para tabelas e figura
NOMES_EMPRESAS = {"AURE3": "Auren", "CEBR3": "CEB", "CLSC3": "Celesc", "CMIG3": "Cemig", "CPFE3": "CPFL",  # rótulos das 14 empresas do painel
                  "EGIE3": "Engie", "EKTR3": "Elektro", "ENEV3": "Eneva", "EQTL3": "Equatorial",  # (continuação)
                  "GEPA3": "Rio Paranapanema", "LIGT3": "Light", "NEOE3": "Neoenergia", "REDE3": "Rede",  # (continuação)
                  "TAEE3": "Taesa"}                           # (fim)
