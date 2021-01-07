#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import datetime
import requests
import json
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from urllib.request import urlopen
##from rq import Queue
##from worker import conn
##
##q = Queue(connection=conn)

# In[2]:




# In[3]:



# Fetching GeoJson for all Countries

with urlopen('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json') as response:
    countries = json.load(response)

# Country Codes and Country Names

Country_ISO=pd.read_excel('Country_ISO.xlsx')
List=[x for x in Country_ISO['Codes']]

# Global Daily Dataset for each Country

r=requests.get('https://covidapi.info/api/v1/global/timeseries/2020-01-01/' + datetime.datetime.today().strftime('%Y-%m-%d'))
j=r.json()
frames=[]
for x in List:
    idf=pd.DataFrame(j['result'][x])
    idf['Code']=x
    idf['Country']=[i for i in Country_ISO.loc[Country_ISO.Codes==x,'Country']][0]
    frames.append(idf)
Day_Wise=pd.concat(frames)
Day_Wise['Active']=Day_Wise['confirmed']-Day_Wise['deaths']-Day_Wise['recovered']
Day_Wise.rename(columns={'confirmed':'Confirmed','date':'Date','deaths':'Deaths','recovered':'Recovered'},inplace=True)
Day_Wise=Day_Wise[['Date','Country','Code','Confirmed','Active','Recovered','Deaths']]
Day_Wise['Date']=pd.to_datetime(Day_Wise['Date'])

# Global Daily Dataset

r=requests.get('https://covidapi.info/api/v1/global/count')
j=r.json()
frames2=[]
for x in j['result'].keys():
    id=j['result'][x]
    id['Date']=x
    frames2.append(id)
Day_Wise_Global=pd.DataFrame(frames2)
Day_Wise_Global['Active']=Day_Wise_Global['confirmed']-Day_Wise_Global['deaths']-Day_Wise_Global['recovered']
Day_Wise_Global.rename(columns={'confirmed':'Confirmed','deaths':'Deaths','recovered':'Recovered'},inplace=True)
Day_Wise_Global=Day_Wise_Global[['Date','Confirmed','Active','Recovered','Deaths']]
Day_Wise_Global['Date']=pd.to_datetime(Day_Wise_Global['Date'])

# Global Dataset for the Latest Date

Global=Day_Wise.loc[Day_Wise.Date==Day_Wise['Date'].max()].reset_index().drop('index',axis=1)

# New Cases for the Latest Date

Latest=(Day_Wise.loc[Day_Wise.Date==Day_Wise['Date'].max()]).drop(labels=['Date'],axis=1)
Old=(Day_Wise.loc[Day_Wise.Date==Day_Wise['Date'].max()-datetime.timedelta(days=1)]).drop(labels=['Date'],axis=1)
New_Cases=Latest.set_index(['Country','Code']).subtract(Old.set_index(['Country','Code'])).reset_index().drop(['Code','Confirmed'],axis=1)
New_Cases['Active']=New_Cases.Active.apply(lambda x: 0 if x<0 else x)
New_Cases['Recovered']=New_Cases.Recovered.apply(lambda x: 0 if x<0 else x)
New_Cases['Deaths']=New_Cases.Deaths.apply(lambda x: 0 if x<0 else x)

# Total Global Count

r=requests.get('https://covidapi.info/api/v1/global')
j=r.json()
Global_Count=pd.DataFrame(j['result'],index=[0]).rename(columns={'confirmed':'Confirmed','recovered':'Recovered','deaths':'Deaths'})
Last_Refreshed=j['date']
Global_Count['Active']=Global_Count['Confirmed']-Global_Count['Recovered']-Global_Count['Deaths']
Global_Count=Global_Count[['Confirmed','Active','Recovered','Deaths']]
Global_Count=Global_Count.stack().astype(str).reindex()
Global_Count=pd.DataFrame(Global_Count).reset_index().drop('level_0',axis=1)
Global_Count.columns=['Last Refreshed',Day_Wise['Date'].max().strftime('%d-%m-%y')]

# Top 10 Affected Countries

Top10=Global.sort_values('Active',ascending=False,ignore_index=True)[:10].drop(['Date','Code'],axis=1)


# In[4]:



# Fetching GeoJson for India

India_GeoJson=json.load(open('states_india.geojson','r'))

# Fetching Data for India

r=requests.get('https://api.rootnet.in/covid19-in/stats/history')
j=r.json()

# India and State Wise Dataset for all Days

l=len(pd.DataFrame(j))
States=pd.DataFrame()
India=pd.DataFrame()
for x in range(l):
    regional=pd.DataFrame(j['data'][x]['regional'])
    summary=pd.DataFrame.from_dict(j['data'][x]['summary'],orient='index').T
    regional['Date']=j['data'][x]['day']
    summary['Date']=j['data'][x]['day']
    regional=regional.replace(['Andaman and Nicobar Islands','Arunachal Pradesh','Daman and Diu','Delhi','Dadar Nagar Haveli',
                                     'Dadra and Nagar Haveli and Daman and Diu','Orissa','Jammu and Kashmir','Jharkhand#',
                                    'Madhya Pradesh#','Nagaland#','Telengana','Telangana***','Ladakh','Chandigarh***','Maharashtra***','Punjab***'],
                                    ['Andaman & Nicobar Island','Arunanchal Pradesh','Daman & Diu','NCT of Delhi',
                                     'Dadara & Nagar Havelli','Dadara & Nagar Havelli','Odisha','Jammu & Kashmir','Jharkhand',
                                    'Madhya Pradesh','Nagaland','Telangana','Telangana','Jammu & Kashmir','Chandigarh','Maharashtra','Punjab'])

    States=States.append(regional)
    India=India.append(summary)
India['Date']=pd.to_datetime(India['Date'])
India.reset_index(inplace=True)
India.drop(['index','confirmedButLocationUnidentified'],axis=1,inplace=True)
India.rename(columns={'total':'Confirmed','discharged':'Recovered','deaths':'Deaths'},inplace=True)
India['Active']=India['Confirmed']-India['Recovered']-India['Deaths']
States['Date']=pd.to_datetime(States['Date'])
DateRange=[States['Date'].min()+datetime.timedelta(days=x) for x in range((States['Date'].max()-States['Date'].min()).days+1)]
States=States.groupby(['loc','Date']).mean()
States=States.reindex(pd.MultiIndex.from_product([States.index.get_level_values(0).unique(),DateRange],names=['State','Date'])).fillna(0)
States.reset_index(inplace=True)
for c in States.columns:
    if (c !='Date') and (c !='State'):
        States[c]=States[c].astype(int)

States.rename(columns={'totalConfirmed':'Confirmed','discharged':'Recovered','deaths':'Deaths'},inplace=True)
States['Active']=States['Confirmed']-States['Recovered']-States['Deaths']
State_ID={}
for feature in India_GeoJson['features']:
    feature['id']=feature['properties']['state_code']
    State_ID[feature['properties']['st_nm']]=feature['id']
States['ID']=States.State.apply(lambda x: State_ID[x])


# Top 10 Worst Affected Sates

IndiaTop10=States.loc[States.Date==States.Date.max()]
IndiaTop10=IndiaTop10.sort_values('Active',ascending=False,ignore_index=True)[:10].drop(['Date','confirmedCasesIndian','confirmedCasesForeign','ID'],axis=1)

IndiaTop10=IndiaTop10[['State','Confirmed','Active','Recovered','Deaths']]

# India Count

India_Count=India.loc[India.Date==India.Date.max()].drop(['confirmedCasesIndian','confirmedCasesForeign'],axis=1)
India_Count=India_Count[['Confirmed','Active','Recovered','Deaths']].replace('Date','Last Refreshed')
India_Count=India_Count.stack().astype(str).reindex()
India_Count=pd.DataFrame(India_Count).reset_index().drop('level_0',axis=1)
India_Count.columns=['Last Refreshed',India.Date.max().strftime('%d-%m-%y')]

# India New Cases

Latest=(States.loc[States.Date==States['Date'].max()]).drop(labels=['Date'],axis=1)
Old=(States.loc[States.Date==States['Date'].max()-datetime.timedelta(days=1)]).drop(labels=['Date'],axis=1)
IndiaNewCases=Latest.set_index(['State']).subtract(Old.set_index(['State'])).reset_index().drop(['Confirmed'],axis=1)
IndiaNewCases['Active']=IndiaNewCases.Active.apply(lambda x: 0 if x<0 else x)
IndiaNewCases['Recovered']=IndiaNewCases.Recovered.apply(lambda x: 0 if x<0 else x)
IndiaNewCases['Deaths']=IndiaNewCases.Deaths.apply(lambda x: 0 if x<0 else x)

StateList=[x for x in IndiaNewCases['State']]


# In[5]:

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server=app.server

# Styling 

Title={'backgroundColor':'#000000','color':'#FFFFFF','textAlign':'center','font-weight':'bold'}

Tab_Style={'backgroundColor': '#000000','border':'none','padding': '6px','fontWeight': 'bold','color': 'white'}

Tab_Selected_Style={'borderTop': '4px solid #0000FF','borderBottom': '1px solid black','borderLeft': '1px solid black',
    'borderRight': '1px solid black','backgroundColor': '#1F1F1F','color': 'white','padding': '6px'}

Main_Tab={'height': '44px'}

Web_Layout_Style={'backgroundColor':'#000000','margin':'5px'}
Heading={'backgroundColor':'#000000','color':'#FFFFFF','textAlign':'center','font-weight':'bold'}
Page_Background='#000000'
Data_Table_Header_Style={'backgroundColor': 'rgb(30, 30, 30)'}
Data_Table_Cell_Style={'backgroundColor': 'rgb(50, 50, 50)','color': 'white','fontWeight': 'bold','font_family': 'cursive',
                       'font_size': '14px','text_align': 'center'}

Grid_Color='#121212'
Fig_Font=dict(color='white')
Title_Font={'size':14,'color':'white'}
Tick_Font={'color':'white','size':12}
Page_Background='#000000'
Fig_Title_Font=dict(color='white',size=16)


# In[6]:



# Global PLot

fig = px.choropleth_mapbox(Global, geojson=countries, locations='Code', color='Confirmed',
                       color_continuous_scale=['#ff0000','#bf0000','#800000','#400000'],
                       mapbox_style='carto-darkmatter',
                       hover_name='Country',
                       hover_data=['Confirmed','Recovered','Deaths'],
                       zoom=2.5,center = {"lat": 24, "lon": 78},
                       )
fig.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,height=550,margin=dict(l=0, r=0, t=0, b=0))

# Global Trendline

x=[x for x in Day_Wise_Global['Date']]
y1=[x for x in Day_Wise_Global['Active']]
y2=[x for x in Day_Wise_Global['Recovered']]
y3=[x for x in Day_Wise_Global['Deaths']]


fig0=go.Figure([go.Scatter(x=x,y=y1,name='Active',marker_color='yellow'),
              go.Scatter(x=x,y=y2,name='Recovered',marker_color='green'),
              go.Scatter(x=x,y=y3,name='Death',marker_color='red')])
fig0.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font,
                tickformatstops = [
                dict(dtickrange=[None, 1000], value="%H:%M:%S.%L ms"),
                dict(dtickrange=[1000, 60000], value="%H:%M:%S s"),
                dict(dtickrange=[60000, 3600000], value="%H:%M m"),
                dict(dtickrange=[3600000, 86400000], value="%d-%m-%y"),
                dict(dtickrange=[86400000, 604800000], value="%d-%m-%y"),
                dict(dtickrange=[604800000, "M1"], value="%Y-%U W"),
                dict(dtickrange=["M1", "M12"], value="%b '%y"),
                dict(dtickrange=["M12", None], value="%Y Y")
            ],
            rangeselector=dict(bgcolor='black',
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])))
fig0.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font)

fig0.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font)

#Top 10 Countries

x=[x for x in Top10['Country']]

y1=[x for x in Top10['Active']]
y2=[x for x in Top10['Recovered']]
y3=[x for x in Top10['Deaths']]

fig3=go.Figure([go.Bar(x=x,y=y1,name='Active',legendgroup='Active',marker_color='yellow'),
               go.Bar(x=x,y=y2,name='Recovered',legendgroup='Recovered',marker_color='green'),
               go.Bar(x=x,y=y3,name='Deaths',legendgroup='Deaths',marker_color='red')])
fig3.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
fig3.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
fig3.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font)

# Global Count

x=[x for x in Global_Count['Last Refreshed']]
y=[x for x in Global_Count[Global_Count.columns[1]]]


fig4=go.Figure([go.Bar(y=[x[3]],name='Deaths',marker_color='red',showlegend=False,x=[y[3]],width=0.25,orientation='h'),
               go.Bar(y=[x[2]],name='Recovered',marker_color='green',showlegend=False,x=[y[2]],width=0.25,orientation='h'),
               go.Bar(y=[x[1]],name='Active',marker_color='yellow',showlegend=False,x=[y[1]],width=0.25,orientation='h'),
               go.Bar(y=[x[0]],name='Conifrmed',marker_color='blue',showlegend=False,x=[y[0]],width=0.25,orientation='h')])
fig4.update_xaxes(visible=False)
fig4.update_yaxes(visible=False)
fig4.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,height=125,width=260,
                  margin= {'l': 0, 'r': 0, 't': 0, 'b': 0})


# In[7]:



# India Map

Indian_Map=States.loc[States.Date==States.Date.max()]
fig9=px.choropleth_mapbox(Indian_Map,geojson=India_GeoJson,locations='ID',color='Confirmed',mapbox_style='carto-darkmatter',
                        hover_name='State', hover_data=['Confirmed','Recovered','Deaths'],zoom=3.5,center = {"lat": 24, "lon": 78}
                         ,color_continuous_scale=['#ff0000','#bf0000','#800000','#400000'])
fig9.update_geos(fitbounds='locations',visible=False)
fig9.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,height=550,margin=dict(l=0, r=0, t=0, b=0))

# India Trendline

x=[x for x in India['Date']]
y1=[x for x in India['Active']]
y2=[x for x in India['Recovered']]
y3=[x for x in India['Deaths']]


fig5=go.Figure([go.Scatter(x=x,y=y1,name='Active',marker_color='yellow'),
              go.Scatter(x=x,y=y2,name='Recovered',marker_color='green'),
              go.Scatter(x=x,y=y3,name='Death',marker_color='red')])
fig5.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font,
                tickformatstops = [
                dict(dtickrange=[None, 1000], value="%H:%M:%S.%L ms"),
                dict(dtickrange=[1000, 60000], value="%H:%M:%S s"),
                dict(dtickrange=[60000, 3600000], value="%H:%M m"),
                dict(dtickrange=[3600000, 86400000], value="%d-%m-%y"),
                dict(dtickrange=[86400000, 604800000], value="%d-%m-%y"),
                dict(dtickrange=[604800000, "M1"], value="%Y-%U W"),
                dict(dtickrange=["M1", "M12"], value="%b '%y"),
                dict(dtickrange=["M12", None], value="%Y Y")
            ],
            rangeselector=dict(bgcolor='black',
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])))
fig5.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font)

fig5.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font)

# Top 10 Countries

x=[x for x in IndiaTop10['State']]

y1=[x for x in IndiaTop10['Active']]
y2=[x for x in IndiaTop10['Recovered']]
y3=[x for x in IndiaTop10['Deaths']]

fig6=go.Figure([go.Bar(x=x,y=y1,name='Active',legendgroup='Active',marker_color='yellow'),
               go.Bar(x=x,y=y2,name='Recovered',legendgroup='Recovered',marker_color='green'),
               go.Bar(x=x,y=y3,name='Deaths',legendgroup='Deaths',marker_color='red')])
fig6.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
fig6.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
fig6.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font)

# India Count

x=[x for x in India_Count['Last Refreshed']]
y=[x for x in India_Count[India_Count.columns[1]]]


fig7=go.Figure([go.Bar(y=[x[3]],name='Deaths',marker_color='red',showlegend=False,x=[y[3]],width=0.25,orientation='h'),
               go.Bar(y=[x[2]],name='Recovered',marker_color='green',showlegend=False,x=[y[2]],width=0.25,orientation='h'),
               go.Bar(y=[x[1]],name='Active',marker_color='yellow',showlegend=False,x=[y[1]],width=0.25,orientation='h'),
               go.Bar(y=[x[0]],name='Conifrmed',marker_color='blue',showlegend=False,x=[y[0]],width=0.25,orientation='h')])
fig7.update_xaxes(visible=False)
fig7.update_yaxes(visible=False)
fig7.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,height=125,width=260,
                  margin= {'l': 0, 'r': 0, 't': 0, 'b': 0})


# In[8]:



#Country Wise Trendline

@app.callback(
Output('CountryWiseTrendline','figure'),
[Input('CountryList','value')])

def Country_Wise(Country):

    x=[x for x in Day_Wise.loc[Day_Wise.Country==Country,'Date']]
    y1=[x for x in Day_Wise.loc[Day_Wise.Country==Country,'Active']]
    y2=[x for x in Day_Wise.loc[Day_Wise.Country==Country,'Recovered']]
    y3=[x for x in Day_Wise.loc[Day_Wise.Country==Country,'Deaths']]


    fig1=go.Figure([go.Scatter(x=x,y=y1,name='Active',marker_color='yellow'),
                  go.Scatter(x=x,y=y2,name='Recovered',marker_color='green'),
                  go.Scatter(x=x,y=y3,name='Death',marker_color='red')])
    fig1.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font,
                    tickformatstops = [
                    dict(dtickrange=[None, 1000], value="%H:%M:%S.%L ms"),
                    dict(dtickrange=[1000, 60000], value="%H:%M:%S s"),
                    dict(dtickrange=[60000, 3600000], value="%H:%M m"),
                    dict(dtickrange=[3600000, 86400000], value="%d-%m-%y"),
                    dict(dtickrange=[86400000, 604800000], value="%d-%m-%y"),
                    dict(dtickrange=[604800000, "M1"], value="%Y-%U W"),
                    dict(dtickrange=["M1", "M12"], value="%b '%y"),
                    dict(dtickrange=["M12", None], value="%Y Y")
                ],
                rangeselector=dict(bgcolor='black',
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])))
    fig1.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font)

    fig1.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font,
                       title='TRENDLINE FOR '+Country.upper(),title_x=0.5,titlefont=Fig_Title_Font)
    return fig1


# In[9]:



#State Wise Trendline

@app.callback(
Output('StateWiseTrendline','figure'),
[Input('StateList','value')])


def State_Wise(State):

    x=[x for x in States.loc[States.State==State,'Date']]
    y1=[x for x in States.loc[States.State==State,'Active']]
    y2=[x for x in States.loc[States.State==State,'Recovered']]
    y3=[x for x in States.loc[States.State==State,'Deaths']]


    fig10=go.Figure([go.Scatter(x=x,y=y1,name='Active',marker_color='yellow'),
                  go.Scatter(x=x,y=y2,name='Recovered',marker_color='green'),
                  go.Scatter(x=x,y=y3,name='Death',marker_color='red')])
    fig10.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font,
                    tickformatstops = [
                    dict(dtickrange=[None, 1000], value="%H:%M:%S.%L ms"),
                    dict(dtickrange=[1000, 60000], value="%H:%M:%S s"),
                    dict(dtickrange=[60000, 3600000], value="%H:%M m"),
                    dict(dtickrange=[3600000, 86400000], value="%d-%m-%y"),
                    dict(dtickrange=[86400000, 604800000], value="%d-%m-%y"),
                    dict(dtickrange=[604800000, "M1"], value="%Y-%U W"),
                    dict(dtickrange=["M1", "M12"], value="%b '%y"),
                    dict(dtickrange=["M12", None], value="%Y Y")
                ],
                rangeselector=dict(bgcolor='black',
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])))
    fig10.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font)

    fig10.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,font=Fig_Font,
                       title='TRENDLINE FOR '+State.upper(),title_x=0.5,titlefont=Fig_Title_Font)
    return fig10


# In[10]:



# New Cases Count

@app.callback(
Output('CountryWiseNewCase','figure'),
[Input('CountryList','value')])

def New_Cases_Country_Wise(Country):
    
    x=['New Case','New Recovered','New Deaths']
    y=[x for x in New_Cases.loc[New_Cases.Country==Country,'Active']]+[x for x in New_Cases.loc[New_Cases.Country==Country,'Recovered']]+[x for x in New_Cases.loc[New_Cases.Country==Country,'Deaths']]

    fig2=go.Figure([go.Bar(x=[x[0]],y=[y[0]],name='Active',marker_color='yellow')
                    ,go.Bar(x=[x[1]],y=[y[1]],name='Recovered',marker_color='green'),
                    go.Bar(x=[x[2]],y=[y[2]],name='Deaths',marker_color='red')])
    fig2.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
    fig2.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
    fig2.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,
                       title='CASES RECORDED ON '+Last_Refreshed+' for '+Country,title_x=0.5,titlefont=Fig_Title_Font,font=Fig_Font)
    return fig2


# In[11]:


# New Cases Count

@app.callback(
Output('StateWiseNewCase','figure'),
[Input('StateList','value')])

def New_Cases_State_Wise(State):
    
    x=['New Case','New Recovered','New Deaths']
    y=[x for x in IndiaNewCases.loc[IndiaNewCases.State==State,'Active']]+[x for x in IndiaNewCases.loc[IndiaNewCases.State==State,'Recovered']]+[x for x in IndiaNewCases.loc[IndiaNewCases.State==State,'Deaths']]

    fig11=go.Figure([go.Bar(x=[x[0]],y=[y[0]],name='Active',marker_color='yellow')
                    ,go.Bar(x=[x[1]],y=[y[1]],name='Recovered',marker_color='green'),
                    go.Bar(x=[x[2]],y=[y[2]],name='Deaths',marker_color='red')])
    fig11.update_xaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
    fig11.update_yaxes(gridcolor=Grid_Color,tickfont=Tick_Font)
    fig11.update_layout(plot_bgcolor=Page_Background,paper_bgcolor=Page_Background,
                       title='CASES RECORDED ON '+India.Date.max().strftime('%Y-%m-%d')+' for '+State,title_x=0.5,titlefont=Fig_Title_Font,font=Fig_Font)
    return fig11


# In[12]:



# Layout

app.layout=html.Div([
    html.Div(html.H1('COVID-19 DASHBOARD',style=Title),className='row'),
    html.Div([
            dcc.Tabs(id='Layout',value='Tab-1',style=Main_Tab,children=[
            dcc.Tab(id='Global',label='GLOBAL',value='Tab-1',style=Tab_Style,selected_style=Tab_Selected_Style,
                   className='custom-tab',selected_className='custom-tab--selected',children=[
                       html.Div([
                           html.Div([
                               html.Div(html.H6('GLOBAL STATS',style=Heading),className='row'),
                               html.Div([
                                   html.Div([dash_table.DataTable(id='GlobalCount',
                                                             columns=[{'name': 'Last Refreshed', 'id': 'Last Refreshed'}, {'name': Day_Wise['Date'].max().strftime('%d-%m-%y'), 'id':Day_Wise['Date'].max().strftime('%d-%m-%y')}],
                                                             data=Global_Count.to_dict('records'),style_table={'overflowY': 'auto'},
                                                             style_header=Data_Table_Header_Style,style_cell=Data_Table_Cell_Style,
                                                             style_cell_conditional=[{'if':{'column_id':'Last Refreshed'},'textAlign':'left'},
                                                                                    {'if':{'column_id':Day_Wise['Date'].max().strftime('%d-%m-%y')},'textAlign':'right'}])
                                            ],className='six columns',style=Web_Layout_Style),
                                   html.Div([
                                       html.Br(),
                                       dcc.Graph(id='GC',figure=fig4,config = {'displayModeBar': False})
                                   ],className='four columns',style=Web_Layout_Style)
                               ],className='row',style=Web_Layout_Style),
                               html.Div(html.H6('TOP 10 AFFECTED COUNTRIES',style=Heading),className='row',style=Web_Layout_Style),
                               html.Div(dash_table.DataTable(id='Top10',columns=[{'name': i, 'id': i} for i in Top10.columns],
                                                           data=Top10.to_dict('records'),style_table={'overflowY': 'auto'},
                                                             sort_action='native',sort_mode='multi',
                                                           style_header=Data_Table_Header_Style,style_cell=Data_Table_Cell_Style,
                                                           style_cell_conditional=[{'if':{'column_id':'Country'},'textAlign':'left'}
                                                                                    ]),className='row',style=Web_Layout_Style)
                           ],className='four columns',style=Web_Layout_Style),
                           html.Div([
                               html.Div(html.H6('GLOBAL CASES',style=Heading),className='row',style=Web_Layout_Style),
                               html.Div(dcc.Graph(id='GlobalMap',figure=fig))
                           ],className='eight columns',style=Web_Layout_Style)],className='row',style=Web_Layout_Style),
                       html.Div(html.H6('GLOBAL TRENDLINE',style=Heading),className='row',style=Web_Layout_Style),
                       html.Div([
                           dcc.Graph(id='GlobalTrendline',figure=fig0)
                       ],className='row',style=Web_Layout_Style),
                       html.Div([
                           html.Div(html.H6('COUNTRY WISE TRENDLINE & LATEST CASE COUNT',style=Heading),className='row',style=Web_Layout_Style),
                           html.Div([
                               html.Div([dcc.Dropdown(id='CountryList',options=[{'label':x,'value':x} for x in Country_ISO['Country']],
                                                     value='USA',multi=False,clearable=False)],className='three columns',style=Web_Layout_Style)],
                               className='row',style=Web_Layout_Style),
                           html.Div([
                               html.Div([
                                   dcc.Graph(id='CountryWiseTrendline',figure=fig)
                               ],className='six columns',style=Web_Layout_Style),
                               html.Div([
                                   dcc.Graph(id='CountryWiseNewCase',figure=fig)
                               ],className='six columns',style=Web_Layout_Style)
                           ],className='row',style=Web_Layout_Style)
                       ],className='row',style=Web_Layout_Style),
                       html.Div(html.H6('TOP 10 COUNTRIES WITH HIGHEST ACTIVE CASES',style=Heading),className='row',style=Web_Layout_Style),
                       html.Div([
                           dcc.Graph(id='Top10Countries',figure=fig3)
                       ],className='row',style=Web_Layout_Style)
                   ]),
            dcc.Tab(id='India',label='INDIA',value='Tab-2',style=Tab_Style,selected_style=Tab_Selected_Style,
                   className='custom-tab',selected_className='custom-tab--selected',children=[
                       html.Div([
                           html.Div([
                               html.Div(html.H6('INDIA STATS',style=Heading),className='row'),
                               html.Div([
                                   html.Div([dash_table.DataTable(id='IndiaCount',
                                                             columns=[{'name': 'Last Refreshed', 'id': 'Last Refreshed'}, {'name': India['Date'].max().strftime('%d-%m-%y'), 'id':India['Date'].max().strftime('%d-%m-%y')}],
                                                             data=India_Count.to_dict('records'),style_table={'overflowY': 'auto'},
                                                             style_header=Data_Table_Header_Style,style_cell=Data_Table_Cell_Style,
                                                             style_cell_conditional=[{'if':{'column_id':'Last Refreshed'},'textAlign':'left'},
                                                                                    {'if':{'column_id':India['Date'].max().strftime('%d-%m-%y')},'textAlign':'right'}])
                                            ],className='six columns',style=Web_Layout_Style),
                                   html.Div([
                                       html.Br(),
                                       dcc.Graph(id='IC',figure=fig7,config = {'displayModeBar': False})
                                   ],className='four columns',style=Web_Layout_Style)
                               ],className='row',style=Web_Layout_Style),
                               html.Div(html.H6('TOP 10 AFFECTED STATES',style=Heading),className='row',style=Web_Layout_Style),
                               html.Div(dash_table.DataTable(id='IndiaTop10',columns=[{'name': i, 'id': i} for i in IndiaTop10.columns],
                                                           data=IndiaTop10.to_dict('records'),style_table={'overflowY': 'auto'},
                                                             sort_action='native',sort_mode='multi',
                                                           style_header=Data_Table_Header_Style,style_cell=Data_Table_Cell_Style,
                                                           style_cell_conditional=[{'if':{'column_id':'State'},'textAlign':'left'}
                                                                                    ]),className='row',style=Web_Layout_Style)
                           ],className='four columns',style=Web_Layout_Style),
                           html.Div([
                               html.Div(html.H6('INDIA CASES',style=Heading),className='row',style=Web_Layout_Style),
                               html.Div(dcc.Graph(id='IndiaMap',figure=fig9))
                           ],className='eight columns',style=Web_Layout_Style)],className='row',style=Web_Layout_Style),
                       html.Div(html.H6('INDIA TRENDLINE',style=Heading),className='row',style=Web_Layout_Style),
                       html.Div([
                           dcc.Graph(id='IndiaTrendline',figure=fig5)
                       ],className='row',style=Web_Layout_Style),
                       html.Div([
                           html.Div(html.H6('STATE WISE TRENDLINE & LATEST CASE COUNT',style=Heading),className='row',style=Web_Layout_Style),
                           html.Div([
                               html.Div([dcc.Dropdown(id='StateList',options=[{'label':x,'value':x} for x in StateList],
                                                     value='Karnataka',multi=False,clearable=False)],className='three columns',style=Web_Layout_Style)],
                               className='row',style=Web_Layout_Style),
                           html.Div([
                               html.Div([
                                   dcc.Graph(id='StateWiseTrendline',figure=fig)
                               ],className='six columns',style=Web_Layout_Style),
                               html.Div([
                                   dcc.Graph(id='StateWiseNewCase',figure=fig)
                               ],className='six columns',style=Web_Layout_Style)
                           ],className='row',style=Web_Layout_Style)
                       ],className='row',style=Web_Layout_Style),
                       html.Div(html.H6('TOP 10 STATES WITH HIGHEST ACTIVE CASES',style=Heading),className='row',style=Web_Layout_Style),
                       html.Div([
                           dcc.Graph(id='IndiaTop10States',figure=fig6)
                       ],className='row',style=Web_Layout_Style)
        ])
            ])
        
    ],className='row')
    ],className='row',style=Web_Layout_Style)                        
                             


# In[13]:


if __name__ == '__main__':
    app.run_server(debug=True,use_reloader=False)

