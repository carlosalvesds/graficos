import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Dashboard de Análise de Dados", layout="wide")
st.title("📊 Dashboard de Análise de Dados")

uploaded_file = st.file_uploader("Faça upload de um arquivo Excel", type=["xlsx", "xls"])

with st.sidebar:
    st.header("Filtros")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    col_empresa = "Empresas"
    col_mes = "Mês"
    col_receita = "Tipo_Serviço"
    col_valor = "Imposto"
    col_tipo = "Regime"
    col_receita_valor = "Receita"

    meses = df[col_mes].unique()
    mes_sel = st.sidebar.multiselect("Selecione o(s) mês(es)", options=meses, default=meses)
    empresas = df[col_empresa].unique()
    empresa_sel = st.sidebar.multiselect("Selecione a(s) empresa(s)", options=empresas, default=empresas)
    receitas = df[col_receita].unique()
    receita_sel = st.sidebar.multiselect("Selecione o(s) tipo(s) de serviço", options=receitas, default=receitas)
    regimes = df[col_tipo].unique()
    regime_sel = st.sidebar.radio("Regime tributário", options=["Ambos"] + list(regimes), index=0)
    niveis = {
        "Por empresa": col_empresa,
        "Por mês": col_mes,
        "Por tipo de serviço": col_receita
    }
    nivel_analise = st.sidebar.selectbox("Nível de análise", options=list(niveis.keys()), index=0)
    col_agrup = niveis[nivel_analise]

    df_filtrado = df[
        (df[col_mes].isin(mes_sel)) &
        (df[col_empresa].isin(empresa_sel)) &
        (df[col_receita].isin(receita_sel))
    ]
    if regime_sel != "Ambos":
        df_filtrado = df_filtrado[df_filtrado[col_tipo] == regime_sel]

    st.markdown("---")
    st.subheader(f"Comparação de Impostos ({'ISS vs ICMS' if regime_sel == 'Ambos' else regime_sel}) - {nivel_analise}")

# ...existing code...

    # Gráfico de barras lado a lado (comparação ISS vs ICMS)
    if regime_sel == "Ambos":
        pivot = df_filtrado.pivot_table(
            index=col_agrup,
            columns=col_tipo,
            values=col_valor,
            aggfunc="sum",
            fill_value=0
        )
        for regime in ["ISS", "ICMS"]:
            if regime not in pivot.columns:
                pivot[regime] = 0.0
        pivot = pivot[["ISS", "ICMS"]]
        pivot = pivot.reset_index()

        # Formata valores para R$ para hover e rótulo
        pivot["ISS_fmt"] = pivot["ISS"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        pivot["ICMS_fmt"] = pivot["ICMS"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        fig = px.bar(
            pivot,
            x=col_agrup,
            y=["ISS", "ICMS"],
            barmode="group",
            labels={"value": "Imposto (R$)", "variable": "Regime"},
        )
        fig.update_traces(
            selector=dict(name="ISS"),
            text=pivot["ISS_fmt"],
            texttemplate='%{text}',
            textposition='outside',
            hovertemplate=f"{col_agrup}: %{{x}}<br>ISS: <b>%{{text}}</b><extra></extra>"
        )
        fig.update_traces(
            selector=dict(name="ICMS"),
            text=pivot["ICMS_fmt"],
            texttemplate='%{text}',
            textposition='outside',
            hovertemplate=f"{col_agrup}: %{{x}}<br>ICMS: <b>%{{text}}</b><extra></extra>"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        pivot = df_filtrado.groupby(col_agrup)[col_valor].sum().reset_index()
        pivot[col_valor + "_fmt"] = pivot[col_valor].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        fig = px.bar(
            pivot,
            x=col_agrup,
            y=col_valor,
            labels={col_valor: "Imposto (R$)", col_agrup: nivel_analise.split()[-1]},
            title=f"Total de {regime_sel} por {nivel_analise.split()[-1]}"
        )
        fig.update_traces(
            text=pivot[col_valor + "_fmt"],
            texttemplate='%{text}',
            textposition='outside',
            hovertemplate=f"{col_agrup}: %{{x}}<br>Imposto: <b>%{{text}}</b><extra></extra>"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Evolução temporal (linha)
    st.subheader("Evolução Temporal da Diferença (ICMS – ISS)")
    if regime_sel == "Ambos":
        ordem_meses = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
        ]
        # Filtra apenas os meses presentes nos dados filtrados
        meses_presentes = [m for m in ordem_meses if m in df_filtrado[col_mes].unique()]
        if not meses_presentes:
            st.info("Não há dados para exibir a evolução temporal.")
        else:
            # Garante que todos os meses presentes estejam no DataFrame, mesmo que não haja valor (preenche com zero)
            pivot_mes = df_filtrado.pivot_table(
                index=col_mes,
                columns=col_tipo,
                values=col_valor,
                aggfunc="sum",
                fill_value=0
            ).reindex(meses_presentes).reset_index()
            if "ICMS" not in pivot_mes.columns:
                pivot_mes["ICMS"] = 0.0
            if "ISS" not in pivot_mes.columns:
                pivot_mes["ISS"] = 0.0
            pivot_mes["Diferença"] = pivot_mes["ICMS"] - pivot_mes["ISS"]
            pivot_mes["Diferença_fmt"] = pivot_mes["Diferença"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            fig3 = px.line(
                pivot_mes,
                x=col_mes,
                y="Diferença",
                labels={"Diferença": "Diferença (ICMS - ISS) (R$)", col_mes: "Mês"},
            )
            fig3.update_traces(
                text=pivot_mes["Diferença_fmt"],
                textposition="top center",
                mode="lines+markers+text",
                hovertemplate=f"Mês: %{{x}}<br>Diferença: <b>%{{text}}</b><extra></extra>"
            )
            st.plotly_chart(fig3, use_container_width=True)

    # Distribuição por tipo de serviço
    st.subheader("Distribuição por Tipo de Serviço")
    if regime_sel == "Ambos":
        pivot_serv = df_filtrado.pivot_table(
            index=col_receita,
            columns=col_tipo,
            values=col_valor,
            aggfunc="sum",
            fill_value=0
        ).reset_index()
        if "ISS" in pivot_serv.columns and "ICMS" in pivot_serv.columns:
            pivot_serv["ISS_fmt"] = pivot_serv["ISS"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            pivot_serv["ICMS_fmt"] = pivot_serv["ICMS"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            fig4 = px.bar(
                pivot_serv,
                x=col_receita,
                y=["ISS", "ICMS"],
                barmode="group",
                labels={"value": "Imposto (R$)", "variable": "Regime", col_receita: "Tipo de Serviço"},
            )
            fig4.update_traces(
                selector=dict(name="ISS"),
                text=pivot_serv["ISS_fmt"],
                texttemplate='%{text}',
                textposition='outside',
                hovertemplate=f"{col_receita}: %{{x}}<br>ISS: <b>%{{text}}</b><extra></extra>"
            )
            fig4.update_traces(
                selector=dict(name="ICMS"),
                text=pivot_serv["ICMS_fmt"],
                texttemplate='%{text}',
                textposition='outside',
                hovertemplate=f"{col_receita}: %{{x}}<br>ICMS: <b>%{{text}}</b><extra></extra>"
            )
            st.plotly_chart(fig4, use_container_width=True)
    else:
        pivot_serv = df_filtrado.groupby(col_receita)[col_valor].sum().reset_index()
        pivot_serv[col_valor + "_fmt"] = pivot_serv[col_valor].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        fig4 = px.bar(
            pivot_serv,
            x=col_receita,
            y=col_valor,
            labels={col_valor: "Imposto (R$)", col_receita: "Tipo de Serviço"},
            title=f"Distribuição de {regime_sel} por Tipo de Serviço"
        )
        fig4.update_traces(
            text=pivot_serv[col_valor + "_fmt"],
            texttemplate='%{text}',
            textposition='outside',
            hovertemplate=f"{col_receita}: %{{x}}<br>Imposto: <b>%{{text}}</b><extra></extra>"
        )
        st.plotly_chart(fig4, use_container_width=True)

    # --- RESUMO FINAL POR EMPRESA E TOTAL GERAL ---
    st.markdown("### Resumo Final por Empresa e Total Geral")
    if not df_filtrado.empty:
        resumo = df_filtrado.pivot_table(
            index=col_empresa,
            values=[col_receita_valor, col_valor],
            columns=col_tipo,
            aggfunc="sum",
            fill_value=0
        )
        resumo.columns = [f"{v}_{k}" if k else v for v, k in resumo.columns]
        cols = []
        if f"{col_receita_valor}_ISS" in resumo.columns:
            cols.append(f"{col_receita_valor}_ISS")
        if f"{col_valor}_ISS" in resumo.columns:
            cols.append(f"{col_valor}_ISS")
        if f"{col_valor}_ICMS" in resumo.columns:
            cols.append(f"{col_valor}_ICMS")
        renomear = {
            f"{col_receita_valor}_ISS": "Receita",
            f"{col_valor}_ISS": "ISS",
            f"{col_valor}_ICMS": "ICMS"
        }
        resumo_exibir = resumo[cols].rename(columns=renomear)
        if "ICMS" in resumo_exibir.columns and "ISS" in resumo_exibir.columns:
            resumo_exibir["Diferença (ICMS - ISS)"] = resumo_exibir["ICMS"] - resumo_exibir["ISS"]
        else:
            resumo_exibir["Diferença (ICMS - ISS)"] = np.nan
        if "Receita" in resumo_exibir.columns:
            resumo_exibir = resumo_exibir.sort_values("Receita", ascending=False)
        resumo_float = resumo_exibir.copy()
        for col in ["Receita", "ISS", "ICMS", "Diferença (ICMS - ISS)"]:
            if col in resumo_float.columns:
                resumo_float[col] = resumo_float[col].replace(
                    {"R\$": "", "\.": "", ",": "."}, regex=True
                ).astype(float)
        total_geral = pd.DataFrame(resumo_float.sum(axis=0)).T
        total_geral.index = ["Total Geral"]
        for col in total_geral.columns:
            total_geral[col] = total_geral[col].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        for col in ["Receita", "ISS", "ICMS", "Diferença (ICMS - ISS)"]:
            if col in resumo_exibir.columns:
                resumo_exibir[col] = resumo_exibir[col].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        resumo_exibir = pd.concat([resumo_exibir, total_geral])
        st.dataframe(resumo_exibir, use_container_width=True)
    else:
        st.info("Não há dados para exibir o resumo final.")

    # --- INSIGHTS EXPLICATIVOS ---
    st.markdown("### 💡 Interpretação dos Resultados e Insights Fiscais")
    with st.expander("Ver explicações e interpretações dos dados"):
        st.markdown("""
- **Impacto direto da alíquota:**  
  O ISS está fixado em **3% sobre a receita**.  
  O ICMS tem **19%**, mas aplicado sobre uma base reduzida (~36,84% da receita).  
  Isso significa que nem sempre o ICMS é 6x maior que o ISS, pois depende da redução da base de cálculo.

- **Comparação empresa a empresa:**  
  Empresas com receitas altas em serviços de alimentação/pontuação tendem a sofrer mais impacto no ICMS, porque mesmo com a redução da base, o imposto final ultrapassa muito o ISS.  
  Já empresas menores podem ter um peso proporcional menor, mas ainda assim pagam quase 4x mais ICMS do que ISS.

- **Tipo de serviço:**  
  Serviços com maior receita bruta sofrem proporcionalmente maior impacto da migração ISS → ICMS.  
  Ao separar por tipo de serviço, é possível identificar quais linhas são mais penalizadas.

- **Comparação direta ISS x ICMS:**  
  A diferença absoluta (**ICMS – ISS**) e a diferença percentual (**% de aumento da carga tributária**) para cada empresa, serviço ou mês mostram claramente quem vai pagar mais e quanto mais.
    
    Mas temos que considerar as seguintes observações; 

    - A Empresa VILLAS nos meses de Janeiro a Julho de 2025, deixou de aproveitar um valor de crédito de ICMS no total de: R$ 29.889,72
    - A Empresa EXCLUSIVE nos meses de Janeiro a Julho de 2025, deixou de aproveitar um valor de crédito de ICMS no total de: xxxxxxxxx

    ➡️ Se o crédito fosse aproveitado, o aumento da carga tributária seria R$ xxxxxxxxxx menor, refletindo diretamente margem de lucro.

    Por outro lado as empresas listadas a baixo sofreram um pouco mais a mudança devido ao credito de ICMS ser menor que os débitos, portando a mudança
    vai aferar consideravelmente.
           
  DESTACAR QUAIS EMPRESAS TEM POUCO APROVEITAMENTO DE CREDITO: FIORI, JARDINS ACQUA PARK, SPLASH?           
                    

- **Quem será mais afetado?**  
  Empresas com alto faturamento e poucos créditos de ICMS tendem a ser mais afetadas.  
  Empresas menores podem até não sentir tanto, mas o percentual de aumento ainda será grande.
        """)
