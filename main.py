import os

from dotenv import load_dotenv

load_dotenv()

key_id = os.environ["KEY_ID"]
secret_key = os.environ["SECRET"]

import duckdb
import isort
import pandas as pd
import pyarrow as pa
import streamlit as st
from google.auth.transport.requests import Request
from google.cloud import bigquery
from google.oauth2 import service_account
from st_aggrid import AgGrid, ColumnsAutoSizeMode, GridOptionsBuilder

st.set_page_config(layout="wide")
project_id = os.environ["GCP_PROJECT_ID"]
sa_info = dict(st.secrets["gcp_service_account"])

credentials = service_account.Credentials.from_service_account_info(
    sa_info, scopes=["https://www.googleapis.com/auth/bigquery"]
)
client = bigquery.Client(credentials=credentials)
credentials.refresh(Request())

@st.cache_data()
#Google BigQuery client
def run_query(query): 
    query_job = client.query(query)
    rows_raw = query_job.result()
    rows = [dict(row) for row in rows_raw]
    return rows

@st.cache_resource(ttl=3000)
def get_connection():
    con = duckdb.connect()
    con.sql(f"""
            INSTALL httpfs;
            LOAD httpfs;
            """)
    con.sql(f"""
                CREATE SECRET my_secret (
                TYPE gcs,
                KEY_ID '{key_id}',
                SECRET '{secret_key}'
                )
            """);
   
    con.sql(f"""
            INSTALL bigquery FROM community;
            LOAD bigquery;
            CREATE SECRET bq_secret (
                TYPE bigquery,
               
                ACCESS_TOKEN '{credentials.token}'
            );
            """)
    
    con.sql(f"""
        ATTACH 'project=bigquery-public-data dataset=new_york_citibike billing_project={project_id}'AS bq_citibike (TYPE bigquery, READ_ONLY)
        """)
    con.sql(f"""
        ATTACH 'project=bigquery-public-data dataset=noaa_gsod billing_project={project_id}' AS bq_gsod_stations (TYPE bigquery, READ_ONLY)
        """)
        
    return con

con = get_connection()
                      

# Initially, I used DuckDb to pull Google Cloud Storage parquet file remotely but found that I had better latency speeds by copying parquet file locally, instead of making the remote calls everytime this file is launched.

# result = con.sql(f"""
#           COPY
#                  (SELECT * FROM read_parquet('gs://citibike_gcs/bq-results*'), LIMIT 1000) 
#           TO 
#                  'data/citibike.parquet' (FORMAT parquet)
#           """);

# result = con.sql(f"""
#           COPY
#                 (SELECT * FROM read_parquet('gs://citibike_gcs/bq-results*')) 
#           TO 
#                 'data/citibike_complete.parquet' (FORMAT parquet)
#           """);



@st.cache_data
def get_q1_data(_con):
    return _con.sql("""
        SELECT name,usaf
            FROM bq_gsod_stations.stations
        WHERE name LIKE '%LA GUARDIA%'
               """).df()
result_q1 = get_q1_data(con)

q1 = st.container(
    width='stretch', 
    height='content', 
    border=True,
    autoscroll=True)

q1.header("Question 1: Find Your Weather Station", anchor=None, divider=True)

q1.write("""New York has several weather stations, but the operations team wants the one at LaGuardia Airport — major airport stations keep the most complete records. Query the stations table to find every US station whose name contains 'LA GUARDIA', and record its usaf ID. You will use this ID in Step 7.
 
Tip: There is a SQL keyword for matching text patterns, and % acts as a wildcard on either side of your search text. Station names are stored in ALL CAPS.
         """)

st.dataframe(result_q1, hide_index=True, column_config={
    'name': 'STATION NAME',
    'usaf': 'USAF ID'
})
st.space(size= 'small')
st.image('docs/Question1.png', width='content', caption='SQL query: Question 1')
st.space(size='medium')

q2 = st.container(
        width='stretch', 
      height='content', 
      border=True,
      autoscroll=True)
q2.header("Question 2: Preview the Ride Data")
q2.write("""
         Before analyzing anything, look at what you're working with. Pull the starttime, stoptime, and tripduration for 10 trips from the citibike_trips table.
 
         Tip: Never run SELECT * without LIMIT on a table this size. Previewing first is not just politeness — the sandbox gives you a monthly query quota, and careless full-table scans burn through it.
""")


@st.cache_data
def get_q2_data(_con):
    return _con.sql("""
        SELECT 
            starttime, stoptime, ROUND((tripduration/60),2) TRIP_DURATION_Minutes,
            EXTRACT(hour FROM starttime) start_time_HOUR, 
            EXTRACT(minute FROM starttime) start_time_MINUTE, 
            EXTRACT(hour FROM stoptime) stop_time_HOUR,
            EXTRACT(minute FROM stoptime) stop_time_MINUTE
                   
        FROM bq_citibike.new_york_citibike.citibike_trips
        WHERE 
            starttime IS NOT NULL
        LIMIT 10
    """).df()
st.image('docs/Question2.png', width='content', caption='SQL query: Question 2')

result_q2 = AgGrid(get_q2_data(con), theme='material', height= 500, show_search=True, show_download_button=True, show_toolbar=True)             

q3 = st.container(
      width='stretch', 
      height='content', 
      border=True,
      autoscroll=True)
q3.header("Question 3: Size Up the Problem")
q3.write("""
         How many trips are in the table, total? Write a query that returns a single number.

         In your submission document, answer in one sentence: why can't we just export this table to a CSV and open it in pandas?

        Tip: One aggregate function, no grouping needed.
""")
st.space(size='large')

@st.cache_data
def get_q3_data(_con):
    return _con.sql("""
        SELECT 
            COUNT(tripduration) TRIP 
        FROM bq_citibike.new_york_citibike.citibike_trips
                  """).df()
result_q3 = get_q3_data(con)
q3_df = st.dataframe(result_q3, hide_index=True, column_config=
                     {'TRIP': 'Total Trips'})            
                      
st.image('docs/Question3.png', width='content', caption='SQL query: Question 3')
q3_summary = st.write("""

        There are limitations due to the size of the Citibike table (more than 53 million trips).  As a test exercise, I was able to export the Google BigQuery query into Google Cloud Storage, then save as a parquet file. 
                      
        Parquet files allows for efficient storage and faster load times when compared to CSV. I then remotely copied the parquet file locally to `data/citibike_complete.parquet` using DuckDB. No need to convert to pandas in this case.   
        """)

q4 = st.container(
      width='stretch', 
      height='content', 
      border=True,
      autoscroll=True)
q4.header("Question 4: Rides Per Day")
q4.write("""
         This is the heart of the assignment. Collapse the trip-level data into one row per day: for each calendar date, count the number of rides. Name the date column ride_date and the count num_rides. Exclude the junk rows where starttime is NULL.

        Checkpoint: Your dates should run from 2013-07-01 (the month Citi Bike launched) to 2018-05-31 (where this public table ends).
         
     Tip: starttime is a TIMESTAMP, but you want to group by calendar day. There is a function that extracts just the date part. And there is a specific SQL phrase for keeping only rows where a value is not absent.

""")
st.space(size='medium')

@st.cache_data
def get_q4_data(_con):
    return _con.sql("""
                    SELECT 
                   starttime::DATE AS ride_date, 
                   COUNT(*) num_rides
FROM bq_citibike.new_york_citibike.citibike_trips
WHERE starttime IS NOT NULL
GROUP BY ride_date

                   """).df()
result_q4 = get_q4_data(con)
st.dataframe(result_q4)

st.space(size='medium')
st.image('docs/Question4.png', width='content', caption='SQL query: Question 4')
st.space(size='medium')
q5 = st.container(
      width='stretch', 
      height='content', 
      border=True,
      autoscroll=True)
q5.header("Question 5: Add Average Trip Duration")
q5.write("""Extend your Step 5 query: for each day, also compute the average trip length in MINUTES, named `avg_duration_min`.
         
 Tip: Check the schema reference for what units `tripduration` is stored in.

         """)

@st.cache_data
def get_q5_data(_con):
    return _con.sql("""
                    SELECT 
starttime ::DATE AS ride_date, COUNT(*) num_rides, ROUND(AVG(tripduration/60),2) avg_duration_min,
FROM bq_citibike.new_york_citibike.citibike_trips
WHERE starttime IS NOT NULL
GROUP BY ride_date
ORDER BY ride_date ASC
                   """).arrow().read_all()

result_q5 = get_q5_data(con)
st.dataframe(result_q5)
st.space(size='medium')
st.image('docs/Question5.png', width='content', caption='SQL query: Question 5')

q6 = st.container(width='content', 
      height='content', 
      border=True,
      autoscroll=True)
q6.header("Question 6: One Station, Six Years of Weather")
q6.write("""Now the weather side. From the gsod20* wildcard tables, pull the daily observations for your LaGuardia station for 2013 through 2018. Your query should return: a proper DATE column named obs_date, plus temp, `max`, `min`, wdsp, and prcp — renamed to temp_f, max_temp_f, min_temp_f, wind_speed_knots, and precip_in.
         
Two puzzles to solve here. First: year, mo, and da are three separate STRING columns, and you need one real DATE. Second: you must limit the wildcard to the right years.

Tip: CONCAT the three string columns with '-' separators, then PARSE_DATE('%Y-%m-%d', ...) the result. Filter the wildcard with _TABLE_SUFFIX BETWEEN '13' AND '18'. And remember the backticks on `max` and `min` — they are reserved words.

""")
st.space(size='small')

q6_query = run_query("""
        SELECT 
            # CONCAT(year,'-',mo,'-',da) concat_date,
            PARSE_DATE("%Y-%m-%d",CONCAT(year,'-',mo,'-',da)) obs_date, 
            temp temp_f,  
            `min` min_temp_f, 
            `max` max_temp_f,
            wdsp wind_speed_knots, 
            prcp precip_in, 
        FROM `bigquery-public-data.noaa_gsod.gsod20*`
            WHERE stn = '725030'AND _TABLE_SUFFIX BETWEEN '13' AND '18'
            ORDER BY obs_date ASC
         """)

q6_query_df = pd.DataFrame(q6_query)
q6_query_df['obs_date'] = pd.to_datetime(q6_query_df['obs_date']).dt.strftime('%Y-%m-%d')


st.dataframe(q6_query_df)
st.space(size='small')
st.image('docs/Question6.png', width='content', caption= 'SQL query: Question 6')

q7 = st.container(
        width='content', 
      height='content', 
      border=True,
      autoscroll=True
)

q7.header("Question 7: The Join -- Your Final Query")
q7.write("""
         Assemble the final table. Using WITH, define your Step 6 query as a CTE named daily_rides and your Step 7 query as a CTE named daily_weather. Then INNER JOIN them on the date, and add two more columns computed from ride_date: day_of_week (the day's name, e.g. 'Monday') and month (a number 1–12). Order by ride_date.

Final column list: ride_date, num_rides, avg_duration_min, temp_f, max_temp_f, min_temp_f, wind_speed_knots, precip_in, day_of_week, month.
Checkpoint: Approximately 1,610 rows.
         
In your submission document, answer: the weather CTE alone had 2,191 rows, but the joined table has ~1,610. Where did the other days go? (Think about what an INNER JOIN keeps, and which of the two sides is missing days.)

Tip: FORMAT_DATE('%A', …) gives you the weekday name; EXTRACT(MONTH FROM …) gives you the month number.

""")
st.space(size='small')


q7_query = run_query("""
WITH 

  daily_rides AS (
    SELECT 
      EXTRACT(DATE FROM starttime) ride_date, FORMAT_DATE("%A", (EXTRACT(DATE FROM starttime))) day_of_week, 
      EXTRACT(month FROM starttime) month, COUNT(*) num_rides, ROUND(AVG(tripduration/ 60), 2) avg_duration_min,
    FROM bq_citibike.new_york_citibike.citibike_trips
      WHERE starttime IS NOT NULL
      GROUP BY ride_date, day_of_week,  month
      ORDER BY ride_date 
      
), 

  daily_weather AS (
    SELECT CONCAT(year,'-',mo,'-',da) concat_date,
      PARSE_DATE("%Y-%m-%d",CONCAT(year,'-',mo,'-',da)) obs_date, 
      temp temp_f,  `min` min_temp_f, `max` max_temp_f,wdsp wind_speed_knots, prcp precip_in, 

    FROM `bigquery-public-data.noaa_gsod.gsod20*` 
      WHERE stn = '725030'AND _TABLE_SUFFIX BETWEEN '13' AND '18'
      ORDER BY obs_date ASC
)

SELECT DR.ride_date,
DR.day_of_week,
DR.month,
DR.avg_duration_min,
DR.num_rides,
DW.temp_f,
DW.max_temp_f,
DW.wind_speed_knots,
DW.precip_in
  
FROM daily_rides DR
INNER JOIN daily_weather DW ON DR.ride_date = DW.obs_date
""")


st.dataframe(q7_query, hide_index=False)
st.space(size='small')

st.image('docs/Question7.png', width='content', caption='SQL query: Question 7')



# ** Creating .sql file **

# sql_file = con.sql("""CREATE TABLE build_dataset AS 
#                    SELECT * 
#                    FROM read_csv('data/citibike_weather_daily.csv');
# """)
# con.sql("EXPORT DATABASE 'queries/' (FORMAT csv)")