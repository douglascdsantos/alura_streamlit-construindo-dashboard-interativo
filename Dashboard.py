#%%
import  streamlit       as  st
import  pandas          as  pd
import  plotly.express  as  px
import  requests

st.set_page_config(layout='wide')

#%% funções
def formatar_valor(valor):
    if valor < 1000:
        return f"{valor:,.2f}".replace(",", " ").replace(".", ",")
    elif valor < 1_000_000:
        return f"{valor / 1000:.2f} mil".replace(".", ",")
    elif valor < 1_000_000_000:
        return f"{valor / 1_000_000:.2f} milhões".replace(".", ",")
    else:
        return f"{valor / 1_000_000_000:.2f} bilhões".replace(".", ",")


#%% carregar dados
url = 'https://labdados.com/produtos'
response = requests.get(url)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], dayfirst=True)

#df = pd.DataFrame({"Estado": ["SP", "RJ", "MG", "BA", "RS", "PR"]})

# Dicionário de regiões (como mencionado anteriormente)
regioes = {
    "Norte": ["AC", "AM", "AP", "PA", "RO", "RR", "TO"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Centro-Oeste": ["DF", "GO", "MT", "MS"],
    "Sudeste": ["ES", "MG", "RJ", "SP"],
    "Sul": ["PR", "RS", "SC"]
}
regioes['Todos estados'] = list(regioes.keys())

# Função para obter a região com base no estado
def obter_regiao(estado):
    for regiao, estados_regiao in regioes.items():
        if estado in estados_regiao:
            return regiao
    return None

# Aplicar a função para criar a coluna "Região"
dados["Região"] = dados["Local da compra"].apply(obter_regiao)


#%%
list(regioes.keys())
#%%
st.title('DASHBOARD DE VENDAS :shopping_trolley:')

#%%
regiao = st.sidebar.selectbox('Regiões', regioes)
regiao
estado = st.sidebar.multiselect('Estados', regioes[regiao] if regiao != 'Todos estados' else dados['Local da compra'].unique())

#%% tabelas
filtro_estado = sorted(dados['Local da compra'].unique()) if len(estado) == 0 and regiao == 'Todos estados' else estado
dados_filtrado = dados.query("`Região` in @regioes[@regiao] and `Local da compra` in @estado").copy()
receita_estados = dados_filtrado.groupby('Local da compra')['Preço'].sum().to_frame().merge(
    dados_filtrado[['Local da compra','lat', 'lon']].drop_duplicates(),
    left_index = True,
    right_on = 'Local da compra',
    how = 'left'
).sort_values('Preço', ascending=False)

#%% receita mensal
receita_mensal = dados_filtrado.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()
receita_mensal['Mes/Ano'] = receita_mensal['Mes'].astype(str).str[:3].str.capitalize() +"/" + receita_mensal['Ano'].astype(str).str[:-2]


#%% receita por categorias
receita_categorias = dados_filtrado.groupby('Categoria do Produto')['Preço'].sum().sort_values(ascending=False).reset_index()

#%% tabelas vendedores

vendedores = dados_filtrado.groupby('Vendedor')['Preço'].agg(['sum','count']).reset_index()
vendedores['ticket médio'] = vendedores['sum'] / vendedores['count']

#%% graficos
fig_mapa_receita = px.scatter_geo(receita_estados,
                                  lat = 'lat',
                                  lon = 'lon',
                                  scope = 'south america',
                                  size = 'Preço',
                                  template = 'seaborn',
                                  hover_name = 'Local da compra',
                                  hover_data = {'lat': False, 'lon': False},
                                  title = 'Receita por Estado')


fig_receita_mensal = px.line(receita_mensal,
                             x = 'Mes',
                             y = 'Preço',
                             markers = True,
                             range_y = (0, receita_mensal.max()),
                             color='Ano',
                             line_dash='Ano',
                             title= 'Receita Mensal')
fig_receita_mensal.update_traces(textposition="bottom right")

fig_receita_estados = px.bar(receita_estados.head().sort_values('Preço'),
                             y = 'Local da compra',
                             x = 'Preço',
                             text_auto=True,
                             title='Top estados (receitas)')
fig_receita_estados.update_layout(xaxis_title = 'Receita')

fig_receita_categorias = px.bar(receita_categorias,
                                x = 'Categoria do Produto',
                                y = 'Preço',
                                text_auto = True,
                                title = 'Receita por Produto')
fig_receita_categorias.update_layout(xaxis_title = 'Categorias')

def plot_vendedores(dataframe, column, num):
    df = dataframe.sort_values(column, ascending=False).head(num).sort_values(column).copy()
    return px.bar(df.head(num),
                  x = column,
                  y= 'Vendedor',
                  text_auto=True,
                  title= f'Top {num} vendedores ({column})')

#%% visualização no Streamlit


#regiao
#a = 
#dados.query("`Local da compra` in @regioes[@regiao]")
#%%

abas = st.tabs(['Receita', 'Quantidade de Vendas', 'Vendedores'])

with abas[0]:
    colunas = st.columns(5)
    with colunas[0]:
        st.metric(f'Faturamento ({round(dados_filtrado["Preço"].sum()/dados["Preço"].sum()*100,2)}%)',
                  f'R$ {formatar_valor(dados_filtrado["Preço"].sum())}',
                  help='Valor avaliado a partir da soma da coluna `Preço`')
    with colunas[1]:
        st.metric('Qtde Vendas',
                  f'{formatar_valor(dados_filtrado.shape[0])}')
    with colunas[2]:
        st.metric(f'Ticket médio',
                  f' R$ {formatar_valor(dados_filtrado["Preço"].sum()/dados_filtrado.shape[0])}')
    with colunas[3]:
        st.metric(f'Mês de maior receita: {receita_mensal.sort_values("Preço", ascending=False).head(1)["Mes/Ano"].values[0]}',
                  f'{formatar_valor(float(receita_mensal.sort_values("Preço", ascending=False).head(1)["Preço"].values[0]))}')
    with colunas[4]:
        st.metric(f'Produto Mais vendido: {dados_filtrado["Produto"].value_counts().index[0]}',
                  f'{dados_filtrado["Produto"].value_counts()[0]} Unidades')

    colunas1 = st.columns(2)
    with colunas1[0]:
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_estados, use_container_width=True)
        
    with colunas1[1]:
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categorias, use_container_width=True)
with abas[1]:
    colunas = st.columns(3)
    with colunas[0]:
        st.metric('Faturamento', f'R$ {formatar_valor(dados_filtrado["Preço"].sum())}', help='Valor avaliado a partir da soma da coluna `Preço`')
    with colunas[1]:
        st.metric('Qtde Vendas', f'{formatar_valor(dados_filtrado.shape[0])}')
        
    with colunas[2]:
        st.metric(f'Produto Mais vendido: {dados_filtrado["Produto"].value_counts().index[0]}', f'{dados_filtrado["Produto"].value_counts()[0]} Unidades')
with abas[2]:
    
    colunas = st.columns(3)
    with colunas[0]:
        qtd_vendedores = st.number_input('Quantidade de vendadores:', 2, 10, 5)
        st.metric('Faturamento', f'R$ {formatar_valor(dados_filtrado["Preço"].sum())}', help='Valor avaliado a partir da soma da coluna `Preço`')
        st.plotly_chart(plot_vendedores(vendedores, 'sum', qtd_vendedores), use_container_width=True)
    
    with colunas[1]:
        st.metric('Qtde Vendas', f'{formatar_valor(dados_filtrado.shape[0])}')
        st.plotly_chart(plot_vendedores(vendedores, 'count', qtd_vendedores), use_container_width=True)
    with colunas[2]:
        st.metric(f'Produto Mais vendido: {dados_filtrado["Produto"].value_counts().index[0]}', f'{dados_filtrado["Produto"].value_counts()[0]} Unidades')
        st.plotly_chart(plot_vendedores(vendedores, 'ticket médio', qtd_vendedores), use_container_width=True)
# %%
#plot_vendedores(dados, 'sum', 5)
# %%
#dados.sort_values('sum', ascending=False)#.head(5)
# %%

