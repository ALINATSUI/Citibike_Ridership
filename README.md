# Citibike Ridership #


Using CitiBike and NOAA public datasets hosted on Google BigQuery, this project analyzes how NYC weather affects bike-share ridership, using aggregated daily trip data from 2013–2018.

## Repository Structure ## 

| Folder | Description |
| -------| ------------|
| `code/`  | eda.ipynb, preprocessing.ipynb, model.ipynb
| `data/`  | citibike_weather_daily.csv, citibike.parquet, citibike_complete.parquet | 
| `docs/`  | Supporting documentation (i.e, images)git
| `queries`| build_dataset.sql, load.sql, schema.sql
|`.github/workflows` | For Github Actions workflow

| Files | 
| ------|
| `main.py` | 
| `requirements.txt` |
| `README.md`
|`streamlit.py` ------> Selenium to wakeup Streamlit app through Github Actions workflow
|.github/workflows/wake.yml ----> Wakeup timer configuration
 
      
