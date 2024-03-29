import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster
import openpyxl
import requests
from datetime import datetime
import geopandas as gpd
#from pandasai import SmartDataframe
#from pandasai import PandasAI
#from pandasai import PandasAI

#from pandasai.llm.openai import OpenAI
import time
import yaml



st.set_page_config(
    page_title="ISS",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="auto",

)
## Ocultar menu e logo do streamlit
hide_menu="""
<style>
#MainMenu {visibility:hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
<style>

"""
st.markdown(hide_menu,unsafe_allow_html=True)




@st.cache_data
def load_data():
	url = "https://api.whonghub.org/api/v1/data/1129.csv"
	username = st.secrets["iss_username"]
	password = st.secrets["iss_password"]

	response = requests.get(url, auth=(username, password))

	if response.status_code == 200:
	    data = response.content.decode('utf-8')
	    with open('moziss.csv', 'w', encoding='utf-8') as f: 
	        f.write(data)
	        
	    # Convertendo para DataFrame
	    moziss = pd.read_csv('moziss.csv',low_memory=False)
	    print(moziss.head())
	else:
	    print("Erro ao recuperar os dados. Código de status HTTP:", response.status_code)

	moziss["today"]=pd.to_datetime(moziss["today"])
	moziss["mes"]=moziss.today.dt.month
	moziss["ano"]=moziss.today.dt.year
	moziss["week"]=moziss.today.dt.strftime("%U")
	moziss["nome"]=np.where(moziss["verify_person"]=="OTHERS",moziss.verify_person_other,moziss.verify_person)

	moziss["states"]=moziss["states"].str.title()
	moziss["districts"]=moziss["districts"].str.title()
	moziss["nome"]=moziss["nome"].str.title()
	#moziss=moziss.loc[(moziss["ano"]==2024) & (moziss["mes"]==2)]
	#moziss.head(2)



	df=moziss.copy()
	#df = moziss[columns]
	df["ano"]=df["ano"].astype(int)
	df["week"]=df["week"].astype(int)
    

	df = df.dropna(subset=['_gps_beginning_latitude', '_gps_beginning_longitude'])
	df["latitude"]=df['_gps_beginning_latitude']
	df["longitude"]=df['_gps_beginning_longitude']

    
	return df
@st.cache_data
def load_shp():
	shp = gpd.read_file("Distritos_161_j.json")
	#https://github.com/anhambombe/iss/blob/main/Distritos_161_j.json
	#https://raw.githubusercontent.com/anhambombe/iss/main/Distritos_161_j.json

	# Definir o CRS do GeoDataFrame
	shp.crs = "EPSG:4201"

	return shp

@st.cache_data
def load_shpp():
	shpp = gpd.read_file("Provincias2.json")
	#https://github.com/anhambombe/iss/blob/main/Provincias2.json
	#https://raw.githubusercontent.com/anhambombe/iss/main/Distritos_161_j.json

	# Definir o CRS do GeoDataFrame
	shpp.crs = "EPSG:4201"

	return shpp

    #print (df)
df=load_data()
bd=load_shp()
shpp=load_shpp()



with st.container():
	# Configuração da aplicação Streamlit
	st.title("Repositorio de dados de ISS")
with st.container():
	st.write("---")
	
	tab1, tab2, tab3, tab4 = st.tabs(["📋 Listagem", "📊 Grafico","🌍 Mapa 🗺","🤖 IA"])
	#tab1.subheader("Tables")

prov=st.sidebar.multiselect(
    "Provincia",
    df["states"].unique(),df["states"].unique())

anos=st.sidebar.multiselect(
    "Ano",
    df["ano"].unique(),df["ano"].unique()[-1,-2])

df=df.loc[(df["states"].isin(prov)) & (df["ano"].isin(anos))]
bd=bd.loc[bd["Provincia"].isin(prov)]
shpp=shpp.loc[shpp["Provincia"].isin(prov)]

with tab1:
	with st.container():
		col1, col2, col3, col4 = st.columns([.25, .25, .25, .25])
	
		with col1:
			# Defina suas métricas
			df['data'] = df['today'].dt.date
			if prov:
				metrica1 = str(df["data"].max())
				delta1="+++"
			# Obter a data e hora atual
			hoje_hora = datetime.now()
			# Extrair o mês atual
			ano_atual = hoje_hora.year
			mes_atual = hoje_hora.month
			nome_mes = hoje_hora.strftime('%B')
			semana_atual = hoje_hora.isocalendar()[1]
			
			metrica2 = len(df)
			delta2=len(df[(df["ano"]==ano_atual) & (df["mes"]==mes_atual) ])-len(
				df[(df["ano"]==ano_atual-1) & (df["mes"]==mes_atual) ])
	
	
			
			metrica3 = len(df[(df["ano"]==ano_atual) & (df["mes"]==mes_atual-1) ])
			delta3=len(df[(df["ano"]==ano_atual) & (df["mes"]==mes_atual-1) ])-len(
				df[(df["ano"]==ano_atual-1) & (df["mes"]==mes_atual-1) ])
			metrica4 = len(df[(df["ano"]==ano_atual) & (df["week"]==semana_atual-1) ])
			delta4=len(df[(df["ano"]==ano_atual) & (df["week"]==semana_atual-1) ])-len(
			df[(df["ano"]==ano_atual-1) & (df["week"]==semana_atual-1) ])
	
			# Layout do aplicativo
			#st.title('KPI Dashboard')
		
			# KPI 1
			st.subheader('Actualização 📆')
			if prov:
				st.metric(label="Data de envio do último formulario", value=metrica1, delta=delta1)
	
		with col2:	
			# KPI 2
			st.subheader('Total ISS 🎨')
			st.metric(label="Total formulários selecionados", value=metrica2, delta=delta2)
	
		with col3:
			# KPI 3
			st.subheader('⏳Total Mês passado')
			st.metric(label=f"Mês {mes_atual-1}", value=metrica3, delta=delta3)
	
		with col4:
			# KPI 4
			st.subheader(f'⌛Total Semana {semana_atual-1}')
			st.metric(label=f"Semana {semana_atual-1}", value=metrica4, delta=delta4)
	st.write("---")
	with st.container():
		try:
		# Exibir o mapa no Streamlit usando st.components.v1.html()
	
			with st.expander("🔎 Veja a tabela de dados aqui "):
				st.write(df)
		except:
			st.write("Sem dados para exibir. Por favor, selecione pelo menos uma provincia")


with tab2:
	try:

		chart_prov = df["states"].value_counts()

		st.bar_chart(chart_prov)#, labels={'index': 'Estado', 'value': 'Quantidade'}

		# Cria um DataFrame com a contagem de valores únicos na coluna "Vacinado"
		chart_distr = df["districts"].value_counts()
		st.bar_chart(chart_distr)#, labels={'index': 'Distrito', 'value': 'Quantidade'}

		# Renomeia a coluna para "Total"
		#resumo.columns = ["Total"]
	except:
		st.write("Sem dados para exibir. Por favor, selecione pelo menos uma provincia")



with tab3:

	#####################

	#$$$$$$$$$$$$$$$$$
	# Escreve o DataFrame na tela
	#st.write(resumo)
	if prov:
	################### shpe ####################################
		# Calcular o centroide do shapefile
		latitude_mean = bd.geometry.centroid.y.mean()
		longitude_mean = bd.geometry.centroid.x.mean()
		# Criar o mapa Folium
		m = folium.Map(location=[latitude_mean, longitude_mean], zoom_start=5,tiles=None)
		folium.TileLayer("OpenStreetMap",attr="layer1", name="Ruas").add_to(m)
		folium.TileLayer(tiles="cartodb positron", name="cartodb positron").add_to(m)
		folium.TileLayer(tiles="cartodb voyager", name="cartodb voyager").add_to(m)
		folium.TileLayer(tiles="NASAGIBS Blue Marble", name="NASAGIBS Blue Marble").add_to(m)

		folium.TileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
		                 attr="layer1", name="Floresta").add_to(m)
		folium.TileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
		                 attr="layer1", name="Terreno").add_to(m)
		folium.TileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
		                 attr="layer1", name="Floresta").add_to(m)
		folium.LayerControl(draggable=True).add_to(m)
		
		
		# Adicionar os dados do shapefile ao mapa Folium
		folium.GeoJson(
		    bd,
		    name='Distritos',
		    style_function=lambda feature: {
		        'fillColor': 'white',
		        'color': 'black',
		        'weight': 1,
		        'fillOpacity': 0.01
		    }
		).add_to(m)

		######################### shp ##################################

			################### shpp ####################################
		# Calcular o centroide do shapefile
		latitude_mean = shpp.geometry.centroid.y.mean()
		longitude_mean = shpp.geometry.centroid.x.mean()
		# Criar o mapa Folium
		#m = folium.Map(location=[latitude_mean, longitude_mean], zoom_start=5)
		
		
		# Adicionar os dados do shapefile ao mapa Folium
		folium.GeoJson(
		    shpp,
		    name='Provincias',
		    style_function=lambda feature: {
		        'fillColor': 'white',
		        'color': 'black',
		        'weight': 1,
		        'fillOpacity': 0.01
		    }
		).add_to(m)

		######################### shp ##################################
		# Adicione marcadores de pontos (dot map) coloridos com base na variável "sexo"
		dot_map = folium.FeatureGroup(name="Dot Map")  # Crie uma camada de sobreposição para o dot map
		# Coordenadas para o centro do mapa
		lat = -19.04318
		long = 34.195
		df.dropna(subset="priority_level", inplace=True)
		df["priority_level"] = np.where(df["priority_level"] == "Hi", "Higher", df["priority_level"])
		df["priority_level"] = np.where(df["priority_level"] == "M", "Medium", df["priority_level"])
		df["priority_level"] = np.where(df["priority_level"] == "L", "Low", df["priority_level"])
		df["priority_level"] = np.where(df["priority_level"] == "H", "High", df["priority_level"])
		colors = {
    			'Medium': 'yellow',  # Amarelo
   		 	'Low': 'red',     # Vermelho
   		 	'High': 'green',   # Verde
			'Higher': 'green'   # Verde
			}

		
		latitude_mean=df['_gps_beginning_latitude'].mean()
		longitude_mean=df['_gps_beginning_longitude'].mean()
		#m = folium.Map(location=[lat, long], zoom_start=5)
		for index, row in df.iterrows():

			popup_content = f"<b>Designaçao:</b> {row['designation']}<br>" \
		                    f"<b>Nome:</b> {row['nome']}<br>" \
		                    f"<b>Provincia:</b> {row['states']}<br>" \
		                    f"<b>Distrito:</b> {row['districts']}<br>" \
		                    f"<b>Unidade Sanitária:</b> {row['name_of_facility_visited']}<br>" \
		                    f"<b>Semana:</b> {row['week']}"
				
			
			tooltip_content = f"<b>Designaçao:</b> {row['designation']}<br>" \
		                    f"<b>Nome:</b> {row['nome']}<br>" \
		                    f"<b>Provincia:</b> {row['states']}<br>" \
		                    f"<b>Distrito:</b> {row['districts']}<br>" \
		                    f"<b>Unidade Sanitária:</b> {row['name_of_facility_visited']}<br>" \
		                    f"<b>Semana:</b> {row['week']}"
										
			dot_map.add_child(folium.CircleMarker(
			location=[row['_gps_beginning_latitude'], row['_gps_beginning_longitude']],
			radius=3,
			color=None,
			fill=True,
			fill_color=colors[row['priority_level']],
			fill_opacity=1,
			#popup=row['districts'] 
			popup=popup_content,
			tooltip=tooltip_content,name="ISS"
			))#.add_to(m)
		# Adicione a camada do dot map ao mapa
		m.add_child(dot_map)
		folium.LayerControl(position = 'topleft', collapsed= True, autoZIndex = True,
                    draggable= True).add_to(m)
		#map1.add_to(m1)

		st.components.v1.html(m._repr_html_(), width=1200, height=500, scrolling=True)
	else:
		st.write("Sem dados para exibir. Por favor, selecione pelo menos uma provincia")

with tab4:
	st.write("Em desenvolvimento, até breve!")
	#dt=pd.read_excel("https://docs.google.com/spreadsheets/d/1q9T-43I0xIU9detDR8tOzmMPQMfx2jKj/edit?usp=sharing&ouid=117668420173752402784&rtpof=true&sd=true)
	#def chat(df,prompt):
		#llm = OpenAI(api_token = st.secrets["openai_api_token"])
		#pandas_ai=PandasAI(llm)
		#result=pandas_ai.run(dbf, prompt=prompt, show_code=True, is_conversational_answer=True)
		#return result

	#input_text = st.text_area("Place your questions in the text box below")
	
	#if input_text:
		#if st.button("Send"):
			#st.info(f"You: {input_text}",icon="👨")
			#result=chat(df,input_text)
			#st.success(f"Bot: {result}",icon="🤖")


st.info("Produzido pelo GPEI Moçambique")



