
# Coronavirus (COVID-19) Dashboard

This dashboard provides insights on the spread of Coronavirus in diffrent countries as well as in different states of India.
There are 2 tabs-
1. Global 
- Which provides insights on the spread of Coronavirus at country level.
- The data is updated with 1 day delay i.e the dashboards has data upto yesterday.

2. India
- Which provides insights on the spread of Coronavirus at state level.
- The data is updated on a daily basis and we have access to current data.

The dashboard provides information on the latest data available on COVID-19, such as new cases, deaths, recovered, and other valuable data to gauge the transmission and response to the pandemic. 



#### Global Tab

![App Screenshot](https://github.com/bharathngowda/COVID_19/blob/master/Screenshots/Figure-6.jpeg)

#### India Tab

![App Screenshot](https://github.com/bharathngowda/COVID_19/blob/master/Screenshots/Figure-7.jpeg)


  
## API Reference

#### Global - Historical Data for all countries in the world daywise

```http
  GET https://corona.lmao.ninja/v2/historical?lastdays=all
```

#### India - Historical Data for all states in India daywise

```http
  GET https://api.rootnet.in/covid19-in/stats/history
```


  
## Programming Language and Packages

The dashboard is built using Python 3.6+.

The main Packages used are - 
- Plotly - to make the charts
- Dash - to build the interactive dashboard
- Requests - to make requests for getting new data
- Pandas & Numpy - to process the data and convert it into a format that is required by the dashboard.


  
## Features

#### Stats
It contains 4 indicators - Confirmed, Active, Recovered, Deaths.
- Confirmed - is the running total of all cases tested and confirmed around the world.
- Active - is the current total active cases as on last refreshed date.
- Recovered - is the total number of patients who have recovered from the infection as on last refreshed date.
- Deaths - is the running total of all COVID-19 releated deaths






  
## Dependencies and Libraries 

Install my-project with npm

```bash
  npm install my-project
  cd my-project
```
    