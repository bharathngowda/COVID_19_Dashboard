#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import re
from tabula import read_pdf
from tabulate import tabulate


# ## Global Data

# In[2]:


r=requests.get('https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data/csse_covid_19_daily_reports')
soup=BeautifulSoup(r.content)


# In[3]:


data_list={}
for row in soup.findAll('div',attrs={'class':'flex-auto min-width-0 col-md-2 mr-3'}):
    if row.text!='\n.gitignore\n' and row.text!='\nREADME.md\n':
        data_list[re.sub('\\n','',row.text)]=re.sub('/blob','','https://raw.githubusercontent.com'+row.a['href'])


# In[4]:


link_list=pd.DataFrame(data=data_list.values(),
             index=data_list.keys(),
             columns=['Link']).reset_index().rename(columns={'index':'Filename'})
link_list['Date']=link_list['Filename'].apply(lambda x:pd.to_datetime(re.sub('.csv','',x)))
link_list.sort_values(by='Date',inplace=True,ignore_index=True)


# In[5]:


df1=pd.DataFrame()
for i,j in zip(link_list.loc[(link_list.Date>='2020-01-22') & (link_list.Date<='2020-03-21'),['Link']]['Link'],
               link_list.loc[(link_list.Date>='2020-01-22') & (link_list.Date<='2020-03-21'),['Date']]['Date']):
    temp=pd.read_csv(i).fillna(0)
    temp['Date']=j
    df1=pd.concat([df1,temp])
df1=df1[['Date','Country/Region','Confirmed','Deaths','Recovered']].rename(columns={'Country/Region':'Country'})
df1=df1.groupby(['Date','Country']).sum().reset_index().sort_values(by=['Date','Country'])
df1['Active']=df1['Confirmed']-df1['Recovered']-df1['Deaths']
df1.loc[df1['Active']<0,'Active']=0
df1[['Confirmed','Deaths','Recovered','Active']]=df1[['Confirmed','Deaths','Recovered','Active']].astype('int64')
df1['Country']=df1['Country'].str.strip()
df1['Country']=df1.Country.replace(
    to_replace=['Bahamas, The','Bosnia and Herzegovina','Congo (Brazzaville)',
                'Congo (Kinshasa)',"Cote d'Ivoire",'Czech Republic','East Timor','French Guiana','Gambia, The','Greenland','Holy See',
                'Hong Kong','Hong Kong SAR','Iran (Islamic Republic of)','Jersey','Korea, South','Mainland China','North Ireland',
                'North Macedonia','Republic of Ireland','Republic of Korea','Republic of Moldova','Republic of the Congo',
                'Russian Federation','South Korea','Taiwan*','The Bahamas','The Gambia','US','United Arab Emirates','United Kingdom',
                'Vatican City','Viet Nam'],
    value=['Bahamas','Bosnia','Congo','Congo',"Côte d'Ivoire",'Czechia','Timor-Leste','France','Gambia','Denmark',
           'Holy See (Vatican City State)','China','China','Iran','USA','S. Korea','China','Ireland','Macedonia','Ireland',
            'S. Korea','Moldova','Congo','Russia','S. Korea','Taiwan','Bahamas','Gambia','USA','UAE','UK',
           'Holy See (Vatican City State)','Vietnam'])
df1.shape


# In[6]:


df2=pd.DataFrame()
for i,j in zip(link_list.loc[(link_list.Date>='2020-03-22'),['Link']]['Link'],
               link_list.loc[(link_list.Date>='2020-03-22'),['Date']]['Date']):
    temp=pd.read_csv(i).fillna(0)
    temp['Date']=j
    df2=pd.concat([df2,temp])
df2=df2[['Date','Country_Region','Confirmed','Deaths','Recovered','Active']].rename(columns={'Country_Region':'Country'})
df2=df2.groupby(['Date','Country']).sum().reset_index().sort_values(by=['Date','Country'])
df2['Active']=df2['Confirmed']-df2['Recovered']-df2['Deaths']
df2.loc[df2['Active']<0,'Active']=0
df2[['Confirmed','Deaths','Recovered','Active']]=df2[['Confirmed','Deaths','Recovered','Active']].astype('int64')
df2['Country']=df2['Country'].str.strip()
df2['Country']=df2.Country.replace(
    to_replace=['Bosnia and Herzegovina','Congo (Brazzaville)','Congo (Kinshasa)','Holy See','Korea, South','Libya',
                'North Macedonia','Syria','Taiwan*','US','United Arab Emirates','United Kingdom',"Cote d'Ivoire"],
    value=['Bosnia','Congo','Congo','Holy See (Vatican City State)','S. Korea','Libyan Arab Jamahiriya','Macedonia',
            'Syrian Arab Republic','Taiwan','USA','UAE','UK',"Côte d'Ivoire"])
df2.shape


# In[7]:


final_df=pd.concat([df1,df2])
Country_ISO=pd.read_excel('Country_ISO.xlsx')
final_df=final_df.merge(Country_ISO,how='left',on='Country')
final_df=final_df.dropna(how='any',subset='Code')


# In[8]:


final_df['Week']=final_df['Date'].dt.strftime('WK %U-%Y')
final_df['Month']=final_df['Date'].dt.strftime('%b-%Y')
final_df['Year']=final_df['Date'].dt.year


# In[9]:


vaccine=pd.read_csv('https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/vaccinations.csv').fillna(0)


# In[10]:


vaccine['date']=pd.to_datetime(vaccine['date'])


# In[11]:


df=final_df.merge(vaccine[['iso_code','date','total_vaccinations']],
             how='left',
             left_on=['Code','Date'],
             right_on=['iso_code','date']).fillna(0)[['Country','Code', 'Date', 'Confirmed', 'Deaths', 'Recovered', 'Active',
       'Week', 'Month', 'Year','total_vaccinations']]
df.rename(columns={'total_vaccinations':'Total Vaccinations'},inplace=True)    
df['Total Vaccinations']=df['Total Vaccinations'].astype('int64')
df.shape


# In[12]:


df.to_csv('global_covid_raw.csv',index=False)


# ## India Data

# In[13]:


r=requests.get('https://github.com/datameet/covid19/tree/master/downloads/mohfw-backup/data_json')
soup=BeautifulSoup(r.content)


# In[14]:


data_list={}
for row in soup.findAll('div',attrs={'class':'flex-auto min-width-0 col-md-2 mr-3'}):
    if row.text!='\n.gitignore\n' and row.text!='\nREADME.md\n':
        data_list[re.split('T',re.sub('\\n','',row.text))[0]]=re.sub('/blob','','https://raw.githubusercontent.com'+row.a['href'])


# In[15]:


df=pd.DataFrame()
for i,j in zip(data_list.values(),data_list.keys()):
    if j !='2020-07-28.json':
        temp=pd.read_json(i)
        temp['Date']=j
        df=pd.concat([df,temp])
df.drop(['sno','active', 'new_active', 'new_positive', 'new_cured', 'new_death',
       'death_reconsille', 'total', 'actualdeath24hrs'],axis=1,inplace=True)
df.shape


# In[16]:


df['Date'].replace('.json','',inplace=True,regex=True)
df['Date']=pd.to_datetime(df['Date'])
df=df.loc[(df.state_name!='') & (df.state_name!='Ladakh')]
df.shape


# In[17]:


df['state_name'].replace(['Dadra and Nagar Haveli and Daman and Diu', 'Telengana***',
       'Maharashtra***', 'Chandigarh***', 'Punjab***', 'Telangana',
       'Bihar****', 'Madhya Pradesh***', 'Himanchal Pradesh',
       'Karanataka', 'Haryana***', 'Kerala***', 'Punjab****',
       'Maharashtra****', 'Chandigarh****', 'Goa*****', 'Goa****',
       'Uttar Pradesh*****', 'Maharashtra*****', 'Assam****',
       'Karnataka****', 'Goa*', 'Punjab**'],['Dadra and Nagar Haveli','Telengana','Maharashtra','Chandigarh',
                                            'Punjab','Telengana','Bihar','Madhya Pradesh','Himachal Pradesh',
                                            'Karnataka','Haryana','Kerala','Punjab','Maharashtra','Chandigarh',
                                            'Goa','Goa','Uttar Pradesh','Maharashtra','Assam','Karnataka',
                                            'Goa','Punjab'],inplace=True)
df.rename(columns={'state_name':'State','positive':'Confirmed','cured':'Recovered','death':'Deaths','state_code':'State_Code'},inplace=True)
df=df[[ 'Date','State', 'Confirmed', 'Recovered', 'Deaths', 'State_Code']].sort_values(['Date','State'])
df.shape


# In[18]:


df['State'].replace(['Andaman and Nicobar Islands','Arunachal Pradesh','Daman and Diu','Dadra and Nagar Haveli',
                         'Delhi','Jammu and Kashmir','Telengana'],
                        ['Andaman & Nicobar Island','Arunanchal Pradesh','Daman & Diu','Dadara & Nagar Havelli',
                         'NCT of Delhi','Jammu & Kashmir','Telangana'],inplace=True)


# In[19]:


df['Active']=df['Confirmed']-df['Recovered']-df['Deaths']
df['Week']=df['Date'].dt.strftime('WK %U-%Y')
df['Month']=df['Date'].dt.strftime('%b-%Y')
df['Year']=df['Date'].dt.year
df.shape


# In[20]:


df.Date.max()


# In[21]:


df.to_csv('india_covid_raw.csv',index=False)


# # India - Vaccination Data

# In[22]:


r=requests.get('https://github.com/datameet/covid19/tree/master/downloads/mohfw-backup/cumulative_vaccination_coverage')
soup=BeautifulSoup(r.content)


# In[23]:


data_list={}
for row in soup.findAll('div',attrs={'class':'flex-auto min-width-0 col-md-2 mr-3'}):
    if row.text!='\n.gitignore\n' and row.text!='\nREADME.md\n':
        data_list[re.split('T',re.sub('\\n','',row.text))[0]]=re.sub('/blob','','https://raw.githubusercontent.com'+row.a['href'])
del data_list['2022-07-2#-at-07-00-AM.pdf']
del data_list['2022-02-17-at-07-00-AM.pdf']
del data_list['2022-02-07-at-08-00-AM.pdf']
del data_list['2022-05-11-at-07-00-AM.pdf']
del data_list['2022-08-01-at-07-00-AM.pdf']


# In[24]:


link_list=pd.DataFrame(data=data_list.values(),index=data_list.keys()).reset_index().rename(columns={'index':'Filename',0:'Link'})


# In[25]:


link_list['Date']=pd.to_datetime(link_list['Filename'].str[:10])


# In[26]:


df1=pd.DataFrame()
for i,j in zip(link_list.loc[link_list.Date=='2021-02-25','Link'],link_list['Date']):
    temp = read_pdf(i,pages="all")[1][1:] 
    temp.columns=['Sl.No','State','Session planned','Session completed','18+ Dose 1','18+ Dose 2', '18+ Total Doses']
    temp['Date']=j
    df1=pd.concat([df1,temp[['Date','State','18+ Dose 1','18+ Dose 2', '18+ Total Doses']]])
df1.shape


# In[27]:


df2=pd.DataFrame()
for i,j in zip(link_list.loc[(link_list.Date>='2021-02-26') & (link_list.Date<='2022-01-03'),['Link']]['Link'],
               link_list.loc[(link_list.Date>='2021-02-26') & (link_list.Date<='2022-01-03'),['Date']]['Date']):
    if j == pd.to_datetime('2021-08-09'):
        temp=read_pdf(i,pages='all')[1]
        temp=temp.loc[temp.iloc[:,0].isin([str(x) for x in range(1,40)]+[float(x) for x in range(1,40)])].dropna(how='all',axis=1)
        temp.columns=['Sl.No','State','18+ Dose 1','18+ Dose 2']
        temp['18+ Total Doses']=temp['18+ Dose 1'].str.replace(',','').astype('int64')+temp['18+ Dose 2'].str.replace(',','').astype('int64')
    elif j == pd.to_datetime('2021-09-11'):
        temp = read_pdf(i,pages="all")[1][1:] 
        temp['Sl.No']=temp['Beneficiaries vaccinatedS. No. State/UT'].apply(lambda x:re.findall('\d+',x)[0])
        temp['State']=temp['Beneficiaries vaccinatedS. No. State/UT'].apply(lambda x:re.split('^\d+',x)[1])
        temp['18+ Dose 2']=temp['Unnamed: 0'].apply(lambda x:re.split(' ',x)[0])
        temp['18+ Total Doses']=temp['Unnamed: 0'].apply(lambda x:re.split(' ',x)[1])
        temp.drop(['Beneficiaries vaccinatedS. No. State/UT','Unnamed: 0'],axis=1,inplace=True)
        temp.columns=['18+ Total Doses','Sl.No','State','18+ Dose 1','18+ Dose 2']
    else:
        temp = read_pdf(i,pages="all")
        if len(temp)==2:
            temp=temp[1]
        elif len(temp)==1:
            temp=temp[0]
        else: 
            temp=temp[2]
        temp=temp.loc[temp.iloc[:,0].isin([str(x) for x in range(1,40)]+[float(x) for x in range(1,40)])].dropna(how='all',axis=1)
        temp.columns=['Sl.No','State','18+ Dose 1','18+ Dose 2', '18+ Total Doses']
        
    temp['Date']=j
    df2=pd.concat([df2,temp[['Date','State','18+ Dose 1','18+ Dose 2', '18+ Total Doses']]])
df2.shape


# In[28]:


df3=pd.DataFrame()
for i,j in zip(link_list.loc[(link_list.Date>='2022-01-04') & (link_list.Date<='2022-01-10'),['Link']]['Link'],
               link_list.loc[(link_list.Date>='2022-01-04') & (link_list.Date<='2022-01-10'),['Date']]['Date']):
    if j !=pd.to_datetime('2022-01-09'):
        temp = read_pdf(i,pages="all")[1] 
        temp=read_pdf(i,pages='all')[1]
        temp=temp.loc[temp.iloc[:,0].isin([str(x) for x in range(1,40)]+[float(x) for x in range(1,40)])].dropna(how='all',axis=1)
        temp.columns=['Sl.No','State','18+ Dose 1','18+ Dose 2','18+ Total Doses','15-18 Dose 1']
    else:
        temp = read_pdf(i,pages="all")[1] 
        temp=temp.loc[temp.iloc[:,0].isin([str(x) for x in range(1,40)]+[float(x) for x in range(1,40)])].dropna(how='all',axis=1)
        temp['18+ Dose 2']=temp['Beneficiaries Vaccinated'].apply(lambda x:re.split(' ',x)[0])
        temp['18+ Total Doses']=temp['Beneficiaries Vaccinated'].apply(lambda x:re.split(' ',x)[1])
        temp.drop('Beneficiaries Vaccinated',axis=1,inplace=True)
        temp.columns=['Sl.No','State','18+ Dose 1','15-18 Dose 1','18+ Dose 2','18+ Total Doses']
    temp['Date']=j
    df3=pd.concat([df3,temp[['Date','State','18+ Dose 1','18+ Dose 2', '18+ Total Doses','15-18 Dose 1']]])
df3.shape


# In[29]:


df4=pd.DataFrame()
for i,j in zip(link_list.loc[(link_list.Date>='2022-01-11') & (link_list.Date<='2022-01-31'),['Link']]['Link'],
               link_list.loc[(link_list.Date>='2022-01-11') & (link_list.Date<='2022-01-31'),['Date']]['Date']):
    if j not in pd.to_datetime(['2022-01-24','2022-01-27','2022-01-28','2022-01-29','2022-01-31']):    
        temp = read_pdf(i,pages="all")[1] 
        temp=temp.loc[temp.iloc[:,0].isin([str(x) for x in range(1,40)]+[float(x) for x in range(1,40)])].dropna(how='all',axis=1)
        temp['18+ Dose 1']=temp['Beneficiaries Vaccinated'].apply(lambda x:re.split(' ',x)[0])
        temp['18+ Dose 2']=temp['Beneficiaries Vaccinated'].apply(lambda x:re.split(' ',x)[1])
        temp['15-18 Dose 1']=temp['Beneficiaries Vaccinated'].apply(lambda x:re.split(' ',x)[2])
        temp.drop('Beneficiaries Vaccinated',axis=1,inplace=True)
        temp.columns=['Sl.No','State','60+ Booster Dose','Total Doses','18+ Dose 1','18+ Dose 2','15-18 Dose 1']
    else:
        temp = read_pdf(i,pages="all")[1] 
        temp=temp.loc[temp.iloc[:,0].isin([str(x) for x in range(1,40)]+[float(x) for x in range(1,40)])].dropna(how='all',axis=1)
        temp.columns=['Sl.No','State','18+ Dose 1','18+ Dose 2','15-18 Dose 1','60+ Booster Dose','Total Doses']
    temp['18+ Total Doses']=temp['18+ Dose 1'].str.replace(',','').astype('int64')+temp['18+ Dose 2'].str.replace(',','').astype('int64')
    temp['Date']=j
    df4=pd.concat([df4,temp[['Date','State','18+ Dose 1','18+ Dose 2', '18+ Total Doses','15-18 Dose 1','60+ Booster Dose','Total Doses']]])
df4.shape


# In[30]:


df5=pd.DataFrame()
for i,j in zip(link_list.loc[(link_list.Date>='2022-02-01') & (link_list.Date<='2022-03-16'),['Link']]['Link'],
               link_list.loc[(link_list.Date>='2022-02-01') & (link_list.Date<='2022-03-16'),['Date']]['Date']):
    try:
        temp = read_pdf(i,pages="all")[1] 
        temp=temp.loc[temp.iloc[:,0].isin([str(x) for x in range(1,40)]+[float(x) for x in range(1,40)])].dropna(how='all',axis=1)
        temp.columns=['Sl.No','State','18+ Dose 1','18+ Dose 2','15-18 Dose 1','15-18 Dose 2','60+ Booster Dose','Total Doses']
    except:
        try:
            temp = read_pdf(i,pages="all")[1]
            temp=temp.loc[temp.iloc[:,0].isin([str(x) for x in range(1,40)]+[float(x) for x in range(1,40)])].dropna(how='all',axis=1)
            temp['18+ Dose 1']=temp[temp.columns[2]].apply(lambda x:re.split(' ',x)[0])
            temp['18+ Dose 2']=temp[temp.columns[2]].apply(lambda x:re.split(' ',x)[1])
            temp['15-18 Dose 1']=temp['Beneficiaries Vaccinated'].apply(lambda x:re.split(' ',x)[0])
            temp['15-18 Dose 2']=temp['Beneficiaries Vaccinated'].apply(lambda x:re.split(' ',x)[1])
            temp.drop(['Beneficiaries Vaccinated',temp.columns[2]],axis=1,inplace=True)
            temp.columns=['Sl.No','State','60+ Booster Dose','Total Doses','18+ Dose 1','18+ Dose 2','15-18 Dose 1','15-18 Dose 2']
        except:
            temp = read_pdf(i,pages="all")[1] 
            temp=temp.loc[temp.iloc[:,0].isin([str(x) for x in range(1,40)]+[float(x) for x in range(1,40)])].dropna(how='all',axis=1)
            temp['18+ Dose 1']=temp['Unnamed: 2'].apply(lambda x:re.split(' ',x)[0])
            temp['18+ Dose 2']=temp['Unnamed: 2'].apply(lambda x:re.split(' ',x)[1])
            temp['15-18 Dose 1']=temp['Beneficiaries Vaccinated'].apply(lambda x:re.split(' ',x)[0])
            temp['15-18 Dose 2']=temp['Beneficiaries Vaccinated'].apply(lambda x:re.split(' ',x)[1])
            temp.drop(['Beneficiaries Vaccinated','Unnamed: 2'],axis=1,inplace=True)
            temp.columns=['Sl.No','State','60+ Booster Dose','Total Doses','18+ Dose 1','18+ Dose 2','15-18 Dose 1','15-18 Dose 2']
    temp['18+ Total Doses']=temp['18+ Dose 1'].str.replace(',','').astype('int64')+temp['18+ Dose 2'].str.replace(',','').astype('int64')
    temp['15-18 Total Doses']=temp['15-18 Dose 1'].str.replace(',','').astype('int64')+temp['15-18 Dose 2'].str.replace(',','').astype('int64')
    temp['Date']=j
    df5=pd.concat([df5,temp[['Date','State','18+ Dose 1','18+ Dose 2', '18+ Total Doses','15-18 Dose 1','15-18 Dose 2','15-18 Total Doses','60+ Booster Dose','Total Doses']]])
df5.shape


# In[31]:


df6=pd.DataFrame()
for i,j in zip(link_list.loc[(link_list.Date>='2022-03-17') & (link_list.Date<='2022-04-10'),['Link']]['Link'],
               link_list.loc[(link_list.Date>='2022-03-17') & (link_list.Date<='2022-04-10'),['Date']]['Date']):
    try:
        temp = read_pdf(i,pages="all")[1] 
        temp=temp.dropna(how='all',axis=1)
        temp=temp.loc[temp.iloc[:,0].isin([str(x) for x in range(1,40)]+[float(x) for x in range(1,40)])]
        temp.columns=['Sl.No','State','18+ Dose 1','18+ Dose 2','15-18 Dose 1','15-18 Dose 2','12-14 Dose 1','60+ Booster Dose','Total Doses'] 
    except:
        temp = read_pdf(i,pages="all")[1] 
        temp=temp.dropna(how='all',axis=1)
        temp=temp.loc[temp.iloc[:,0].isin([str(x) for x in range(1,40)]+[float(x) for x in range(1,40)])]
        temp['18+ Dose 1']=temp['Unnamed: 2'].apply(lambda x:re.split(' ',x)[0])
        temp['18+ Dose 2']=temp['Unnamed: 2'].apply(lambda x:re.split(' ',x)[1])
        temp['15-18 Dose 1']=temp['Beneficiaries Vaccinated'].apply(lambda x:re.split(' ',x)[0])
        temp['15-18 Dose 2']=temp['Beneficiaries Vaccinated'].apply(lambda x:re.split(' ',x)[1])
        temp.drop(['Beneficiaries Vaccinated','Unnamed: 2'],axis=1,inplace=True)
        temp.columns=['Sl.No','State','12-14 Dose 1','60+ Booster Dose','Total Doses','18+ Dose 1','18+ Dose 2','15-18 Dose 1','15-18 Dose 2']
    temp['18+ Total Doses']=temp['18+ Dose 1'].str.replace(',','').astype('int64')+temp['18+ Dose 2'].str.replace(',','').astype('int64')
    temp['15-18 Total Doses']=temp['15-18 Dose 1'].str.replace(',','').astype('int64')+temp['15-18 Dose 2'].str.replace(',','').astype('int64')
    temp['Date']=j
    df6=pd.concat([df6,temp[['Date','State','18+ Dose 1','18+ Dose 2', '18+ Total Doses','15-18 Dose 1','15-18 Dose 2','15-18 Total Doses','12-14 Dose 1','60+ Booster Dose','Total Doses']]])
df6.shape


# In[32]:


df7=pd.DataFrame()
for i,j in zip(link_list.loc[(link_list.Date>='2022-04-11') & (link_list.Date<='2022-04-13'),['Link']]['Link'],
               link_list.loc[(link_list.Date>='2022-04-11') & (link_list.Date<='2022-04-13'),['Date']]['Date']):
    try:
        temp = read_pdf(i,pages="all")[1] 
        temp=temp.dropna(how='all',axis=1)
        temp=temp.loc[temp.iloc[:,0].isin([str(x) for x in range(1,40)]+[float(x) for x in range(1,40)])]
        temp.columns=['Sl.No','State','18+ Dose 1','18+ Dose 2','15-18 Dose 1','15-18 Dose 2','12-14 Dose 1','18-59 Booster Dose','60+ Booster Dose','Total Doses'] 
    except:
        temp = read_pdf(i,pages="all")[1] 
        temp=temp.dropna(how='all',axis=1)
        temp=temp.loc[temp.iloc[:,0].isin([str(x) for x in range(1,40)]+[float(x) for x in range(1,40)])]
        temp['18+ Dose 1']=temp['Unnamed: 2'].apply(lambda x:re.split(' ',x)[0])
        temp['18+ Dose 2']=temp['Unnamed: 2'].apply(lambda x:re.split(' ',x)[1])
        temp['15-18 Dose 1']=temp['Beneficiaries Vaccinated'].apply(lambda x:re.split(' ',x)[0])
        temp['15-18 Dose 2']=temp['Beneficiaries Vaccinated'].apply(lambda x:re.split(' ',x)[1])
        temp['12-14 Dose 1']=temp['Beneficiaries Vaccinated'].apply(lambda x:re.split(' ',x)[2])
        temp['18-59 Booster Dose']=temp['Unnamed: 3'].apply(lambda x:re.split(' ',x)[0])
        temp['60+ Booster Dose']=temp['Unnamed: 3'].apply(lambda x:re.split(' ',x)[1])
        temp.drop(['Beneficiaries Vaccinated','Unnamed: 2','Unnamed: 3'],axis=1,inplace=True)
        temp.columns=['Sl.No','State','Total Doses','18+ Dose 1','18+ Dose 2','15-18 Dose 1','15-18 Dose 2','12-14 Dose 1','18-59 Booster Dose','60+ Booster Dose']
    temp['18+ Total Doses']=temp['18+ Dose 1'].str.replace(',','').astype('int64')+temp['18+ Dose 2'].str.replace(',','').astype('int64')
    temp['15-18 Total Doses']=temp['15-18 Dose 1'].str.replace(',','').astype('int64')+temp['15-18 Dose 2'].str.replace(',','').astype('int64')
    temp['Booster Total Doses']=temp['18-59 Booster Dose'].str.replace(',','').astype('int64')+temp['60+ Booster Dose'].str.replace(',','').astype('int64')
    temp['Date']=j
    df7=pd.concat([df7,temp[['Date','State','18+ Dose 1','18+ Dose 2', '18+ Total Doses','15-18 Dose 1','15-18 Dose 2','15-18 Total Doses','12-14 Dose 1','18-59 Booster Dose','60+ Booster Dose','Booster Total Doses','Total Doses']]])
df7.shape


# In[33]:


df8=pd.DataFrame()
for i,j in zip(link_list.loc[(link_list.Date>='2022-04-14'),['Link']]['Link'],
               link_list.loc[(link_list.Date>='2022-04-14'),['Date']]['Date']):
    try:
        temp = read_pdf(i,pages="all")[1] 
        temp=temp.dropna(how='all',axis=1)
        temp=temp.loc[temp.iloc[:,0].isin([str(x) for x in range(1,40)]+[float(x) for x in range(1,40)])].fillna('0')
        temp.columns=['Sl.No','State','18+ Dose 1','18+ Dose 2','15-18 Dose 1','15-18 Dose 2','12-14 Dose 1','12-14 Dose 2','18-59 Booster Dose','60+ Booster Dose','Total Doses']
    except:
        try:
            temp = read_pdf(i,pages="all")[1] 
            temp=temp.dropna(how='all',axis=1)
            temp=temp.loc[temp.iloc[:,0].isin([str(x) for x in range(1,40)]+[float(x) for x in range(1,40)])].fillna('0,0,0,0')
            temp['18+ Dose 1']=temp['Unnamed: 2'].apply(lambda x:re.split(' ',x)[0])
            temp['18+ Dose 2']=temp['Unnamed: 2'].apply(lambda x:re.split(' ',x)[1])
            temp['15-18 Dose 1']=temp['Beneficiaries Vaccinated'].apply(lambda x:re.split(' ',x)[0])
            temp['15-18 Dose 2']=temp['Beneficiaries Vaccinated'].apply(lambda x:re.split(' ',x)[1])
            temp['12-14 Dose 1']=temp['Beneficiaries Vaccinated'].apply(lambda x:re.split(' ',x)[2])
            temp['12-14 Dose 2']=temp['Beneficiaries Vaccinated'].apply(lambda x:re.split(' ',x)[3])
            temp['18-59 Booster Dose']=temp['Unnamed: 3'].apply(lambda x:re.split(' ',x)[0])
            temp['60+ Booster Dose']=temp['Unnamed: 3'].apply(lambda x:re.split(' ',x)[1])
            temp.drop(['Beneficiaries Vaccinated','Unnamed: 2','Unnamed: 3'],axis=1,inplace=True)
            temp.columns=['Sl.No','State','Total Doses','18+ Dose 1','18+ Dose 2','15-18 Dose 1','15-18 Dose 2','12-14 Dose 1','12-14 Dose 2','18-59 Booster Dose','60+ Booster Dose']
        except:
            temp = read_pdf(i,pages="all")[1] 
            temp=temp.dropna(how='all',axis=1)
            temp=temp.loc[temp.iloc[:,0].isin([str(x) for x in range(1,38)]+[float(x) for x in range(1,38)])]
            temp=temp.dropna(how='all',axis=1)
            temp.columns=['Sl.No','State','18+ Dose 1','18+ Dose 2','15-18 Dose 1','15-18 Dose 2','12-14 Dose 1','12-14 Dose 2','18-59 Booster Dose','60+ Booster Dose','Total Doses']
    temp['18+ Total Doses']=temp['18+ Dose 1'].str.replace(',','').astype('int64')+temp['18+ Dose 2'].str.replace(',','').astype('int64')
    temp['15-18 Total Doses']=temp['15-18 Dose 1'].str.replace(',','').astype('int64')+temp['15-18 Dose 2'].str.replace(',','').astype('int64')
    temp['12-14 Total Doses']=temp['12-14 Dose 1'].str.replace(',','').astype('int64')+temp['12-14 Dose 2'].str.replace(',','').astype('int64')
    temp['Booster Total Doses']=temp['18-59 Booster Dose'].str.replace(',','').astype('int64')+temp['60+ Booster Dose'].str.replace(',','').astype('int64')
    temp['Date']=j
    df8=pd.concat([df8,temp[['Date','State','18+ Dose 1','18+ Dose 2', '18+ Total Doses','15-18 Dose 1','15-18 Dose 2','15-18 Total Doses','12-14 Dose 1','12-14 Dose 2','12-14 Total Doses','18-59 Booster Dose','60+ Booster Dose','Booster Total Doses','Total Doses']]])
df8.shape


# In[34]:


final_df=pd.concat([df8,df1,df2,df3,df4,df5,df6,df7])
final_df.sort_values(['Date','State'],inplace=True)
final_df['State']=final_df['State'].str.strip()
final_df.fillna('0',inplace=True)
final_df=final_df.loc[~final_df.State.isin(['0','Miscellaneous'])]
for i in ['18+ Dose 1', '18+ Dose 2','15-18 Dose 1', '15-18 Dose 2',
          '12-14 Dose 1','12-14 Dose 2', '18-59 Booster Dose','60+ Booster Dose', 'Total Doses']:
    final_df[i]=final_df[i].str.replace(',','').astype('int64')
final_df['18+ Total Doses']=final_df['18+ Dose 1']+final_df['18+ Dose 2']
final_df['15-18 Total Doses']=final_df['15-18 Dose 1']+final_df['15-18 Dose 2']
final_df['12-14 Total Doses']=final_df['12-14 Dose 1']+final_df['12-14 Dose 2']
final_df['Booster Total Doses']=final_df['18-59 Booster Dose']+final_df['60+ Booster Dose']
final_df['Total Doses']=final_df['18+ Total Doses']+final_df['15-18 Total Doses']+final_df['12-14 Total Doses']+final_df['Booster Total Doses']
final_df['State']=final_df.State.replace(to_replace=['A & N Islands', 'Andaman and Nicobar\rIslands', 'Andhra Pradesh',
       'Arunachal\rPradesh', 'Arunachal Pradesh', 'Assam', 'Bihar',
       'Chandigarh', 'Chhattisgarh', 'Chhattisgarh*', 'Dadra & Nagar',
       'Dadra & Nagar\rHaveli', 'Dadra & Nagar Haveli', 'Daman & Diu',
       'Delhi', 'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh',
       'Jammu & Kashmir', 'Jharkhand', 'Karnataka', 'Kerala', 'Ladakh',
       'Lakshadweep', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
       'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Puducherry',
       'Punjab', 'Punjab*', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
       'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand',
       'West Bengal'],value=['Andaman & Nicobar Island','Andaman & Nicobar Island', 'Andhra Pradesh', 'Arunanchal Pradesh','Arunanchal Pradesh',
'Assam', 'Bihar', 'Chandigarh', 'Chhattisgarh', 'Chhattisgarh','Dadara & Nagar Havelli','Dadara & Nagar Havelli',
'Dadara & Nagar Havelli', 'Daman & Diu', 'NCT of Delhi', 'Goa', 'Gujarat',
'Haryana', 'Himachal Pradesh', 'Jammu & Kashmir', 'Jharkhand',
'Karnataka', 'Kerala', 'Ladakh', 'Lakshadweep', 'Madhya Pradesh',
'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 
'Nagaland', 'Odisha', 'Puducherry', 'Punjab','Punjab', 'Rajasthan',
'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh',
'Uttarakhand', 'West Bengal'])
final_df['Week']=final_df['Date'].dt.strftime('WK %U-%Y')
final_df['Month']=final_df['Date'].dt.strftime('%b-%Y')
final_df['Year']=final_df['Date'].dt.year
final_df


# In[35]:


final_df.to_csv('india_vaccine.csv',index=False)

