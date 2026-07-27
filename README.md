# Citibike Ridership #


Using CitiBike and NOAA public datasets hosted on Google BigQuery, this project analyzes how NYC weather affects bike-share ridership, using aggregated daily trip data from 2013–2018.

## Repository Structure ## 

| Folder | Description |
| -------| ------------|
| `code/`  | eda.ipynb, preprocessing.ipynb, model.ipynb
| `data/`  | citibike_weather_daily.csv, citibike.parquet, citibike_complete.parquet | 
| `docs/`  | Supporting documentation (i.e, images)git
| `queries`| build_dataset.sql
|`.github/workflows` | For Github Actions workflow

| Files | 
| ------|
| `main.py` | 
| `requirements.txt` |
| `README.md`
|`streamlit_wakeup.py` ------> Selenium to wakeup Streamlit app through Github Actions workflow
|.github/workflows/wake.yml ----> Wakeup timer configuration
 
## Tech Stack
This project uses DuckDB with the community BigQuery extension to query Google BigQuery's public datasets directly. It also uses the google-cloud-bigquery Python client for a subset of queries. The front end is built with Streamlit that allows for interactive, searchable data tables.   

To prevent the app from spinning down due to inactivity, a GitHub Actions workflow runs every 7 hours via a cron schedule and uses Selenium to ping the app via the GitHub runner, keeping it awake.


## Configuration & Secrets 


This project authenticates to Google BigQuery in two ways:

1. **DuckDB** connects via the community `bigquery` extension using a `TYPE bigquery` secret, authenticated with an `ACCESS_TOKEN` generated from service account credentials.
2. **The `google-cloud-bigquery` Python client** authenticates separately using `service_account.Credentials.from_service_account_info()`.



### Setup

To run this project locally, create a `.streamlit/secrets.toml` file in the project root with your own GCP service account credential. Be sure to provision the appropriate IAM roles for service account accordingly:

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "your-private-key"
client_email = "your-service-account-email"
client_id = "your-client-id"
# ...remaining standard service account fields
```

This file is excluded from version control via `.gitignore` and should never be committed. 

### Streamlit Community Cloud

If you're planning on using the Streamlit Community cloud to share your app, you'll need to implement the Streamlit Secrets Manager when deploying the app. 

You'll need to navigate to the `Advanced Settings` when deploying Streamlit Community Cloud app and populate the environment variables that were configured in `.streamlit/secrets.toml`. 



For more info, refer to: [Streamlit Secrets Manager](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)