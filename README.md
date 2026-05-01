## OECD EPL Tech Dashboard

Interactive Streamlit dashboard for exploring OECD Employment Protection Legislation (EPL) indicators across European countries, and comparing them with technology indicators such as ICT uptake and patent applications.

This dashboard is thematically connected to my doctoral research on EPL, technological change, and labour market transitions, but uses public OECD data so the project is fully reproducible.

### What it does

- Plots time series of three EPL indicators (individual and collective dismissals, collective dismissals, individual dismissals) across 28 OECD countries
- Generates bar charts for cross-country comparison at a single point in time
- Computes summary statistics (peak, trough, standard deviation) over a user-defined window
- Compares two EPL indicators side by side
- Plots EPL against technology indicators (ICT broadband uptake, EPO patent applications) in a region-coded scatter plot with median quadrant lines

### Data

All data is fetched live from the [OECD SDMX REST API](https://data-explorer.oecd.org/). No data is stored in this repository.

- EPL indicators: OECD Indicators of Employment Protection
- ICT indicator: businesses with broadband ≥100 Mb/s, percentage of enterprises
- Patents: applications filed at the European Patent Office (EPO), ICT and total technology domains

### Running locally

Clone the repository and install the dependencies:

```bash
git clone https://github.com/NadiacmdCosta/EPL-dashboard.git
cd EPL-dashboard
pip install -r requirements.txt
```

Run the app:

```bash
streamlit run EPL_dashboard.py
```

### Tech stack

Python, Streamlit, pandas, requests, matplotlib.

**Live demo:** [epl-tech-dashboard.streamlit.app](https://epl-tech-dashboard-8kvmuvxjpj6m8reggsd6pd.streamlit.app/))

### How this was built

I work with an AI tutor that uses a Socratic approach; that is, it poses guiding questions and prompts reasoning rather than providing ready-made code. I define the project, suggest solutions, challenge the logic, and write the code myself. The AI guides the learning process; it does not command it.

### Connect

[LinkedIn](https://www.linkedin.com/in/nadiacmcosta)
