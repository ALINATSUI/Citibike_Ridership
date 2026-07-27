
CREATE TABLE build_dataset AS 
    SELECT * 
    FROM read_csv('data/citibike_weather_daily.csv');
