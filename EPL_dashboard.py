import streamlit as st
import pandas as pd # For data manipulation and analysis
import requests # For making HTTP requests to fetch the data
import io # For handling in-memory text streams
import matplotlib.pyplot as plt # For data visualization
import urllib.parse # For URL encoding of parameters when making API requests

## Objective: 
# compare EPL with other types of indicators such as  unionization rate, unemployment benefits, etc. 
# I can use the OECD API to fetch data for these indicators and then create visualizations to compare them with the EPL indicators. 
# For example, I can create a line chart that shows the trends of EPL, GDP growth rate, and unemployment rate over time for a selected country. 
# I can also create scatter plots to show the relationship between EPL and these other indicators. 
# Additionally, I can calculate correlation coefficients to quantify the strength of the relationships between EPL and the other indicators.

## This version of the code was reviewed and improved slightly by Claude to include better error handling, input validation, and code organization. The improvements include:
# 1. Added error handling for API requests to manage timeouts and other request exceptions.
# 2. Implemented input validation for the start period to ensure it is a valid year within a reasonable range.
# 3. Added checks to ensure the expected columns are present in the API response before processing the data.
# 4. Organized the code into functions for better readability and maintainability.
# It needs more improvement, especially in the patent option at the end. 

# to run the app locally, use the command in the terminal: py -m streamlit run "~/folderpath/EPL_dashboard.py"

## Indicator options with their corresponding codes, version, and abbreviation for the legend

indicator_options = {
    "EPL for Individual and Collective Dismissals (ICD)": [".EPL_OV", "2", "ICD"],
    "EPL for Collective Dismissals (CD)": [".EPL_CD", "2", "CD"],
    "EPL for Individual Dismissals (ID)": [".EPL_R", "1", "ID"]
}

tech_options = {
    f"ICT (broadband ≥100 Mb/s, % of enterprises)": "ICT",
    f"Patents (applications, EPO)": "patents",
}

indicator_options_explanations = {
    "EPL for Individual and Collective Dismissals (ICD)": 
        "The Employment Protection Legislation index for individual and collective dismissals (ICD) measures the strictness of regulations regarding the dismissal of employees. "
        "It takes into account factors such as the procedures for dismissals, the costs associated with dismissals, and the legal protections for employees. "
        "A higher EPL index indicates stricter employment protection legislation.",
    "EPL for Collective Dismissals (CD)": 
        "The Employment Protection Legislation index for collective dismissals (CD) specifically focuses on the regulations and protections related to the dismissal of groups of employees. "
        "This index considers factors such as the requirements for notifying authorities, consultation processes, and severance pay for collective dismissals. "
        "A higher EPL index for collective dismissals indicates stronger protections for employees in cases of mass layoffs.",
    "EPL for Individual Dismissals (ID)": 
        "The Employment Protection Legislation index for individual dismissals (ID) assesses the strictness of regulations governing the dismissal of individual employees. "
        "This index evaluates factors such as the legal grounds for dismissal, the procedures that employers must follow, and the costs associated with dismissing an employee. "
        "A higher EPL index for individual dismissals signifies more stringent employment protection legislation for individual workers."
}

country_to_region = {
    'DNK': 'Nordic', 'FIN': 'Nordic', 'ISL': 'Nordic', 'NOR': 'Nordic', 'SWE': 'Nordic',
    'AUT': 'Continental', 'BEL': 'Continental', 'DEU': 'Continental', 'FRA': 'Continental',
    'LUX': 'Continental', 'NLD': 'Continental', 'CHE': 'Continental',
    'ESP': 'Southern', 'GRC': 'Southern', 'ITA': 'Southern', 'PRT': 'Southern',
    'BGR': 'Eastern', 'HRV': 'Eastern', 'CZE': 'Eastern', 'EST': 'Eastern',
    'HUN': 'Eastern', 'LVA': 'Eastern', 'LTU': 'Eastern', 'POL': 'Eastern',
    'ROU': 'Eastern', 'SVK': 'Eastern', 'SVN': 'Eastern',
    'GBR': 'Anglo', 'IRL': 'Anglo',
}

##Functions

@st.cache_data
def load_data_epl(selected_indicator, start_period):
    
      # Validate start_period is a 4-digit year between 1985 and current year
    try:
        year = int(start_period)
        if year < 1985 or year > 2026:
            st.error("Please enter a year between 1985 and 2026.")
            return pd.DataFrame(columns=['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE'])
    except (ValueError, TypeError):
        st.error("Start period must be a valid 4-digit year (e.g., 2004).")
        return pd.DataFrame(columns=['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE'])

    # Validate selected_indicator is a known key
    if selected_indicator not in indicator_options:
        st.error("Invalid indicator selected.")
        return pd.DataFrame(columns=['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE'])

    indicator_code = indicator_options[selected_indicator][0]
    indicator_version = indicator_options[selected_indicator][1]

    # URL-encode the year to be safe
    safe_year = urllib.parse.quote(str(year))

    url = (
        f"https://sdmx.oecd.org/public/rest/data/OECD.ELS.JAI,DSD_EPL@DF_EPL,/"
        f"A.OECD+USA+GBR+CHE+SVN+ESP+SWE+SVK+POL+NOR+NLD+LUX+LTU+LVA+ITA+IRL+"
        f"ISL+HUN+GRC+DEU+FRA+FIN+EST+DNK+CZE+BEL+AUT+HRV+PRT{indicator_code}.."
        f"VERSION{indicator_version}?startPeriod={safe_year}&format=csvfile"
    )

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        st.error("The OECD API took too long to respond. Please try again.")
        return pd.DataFrame(columns=['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE'])
    except requests.exceptions.RequestException:
        st.error("Could not fetch data from the OECD API. Please try again later.")
        return pd.DataFrame(columns=['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE'])

    try:
        df = pd.read_csv(io.StringIO(response.text))
    except (pd.errors.ParserError, pd.errors.EmptyDataError):
        st.error("The data returned by the API could not be read.")
        return pd.DataFrame(columns=['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE'])

    # Check expected columns exist before subsetting
    required_cols = {'REF_AREA', 'TIME_PERIOD', 'OBS_VALUE'}
    if not required_cols.issubset(df.columns):
        st.error("The data format from the API has changed unexpectedly.")
        return pd.DataFrame(columns=['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE'])

    df_clean = df[['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE']].copy()
    df_clean['OBS_VALUE'] = pd.to_numeric(df_clean['OBS_VALUE'], errors='coerce')
    df_clean = df_clean.sort_values(by=['REF_AREA', 'TIME_PERIOD'])
   
    return df_clean


@st.cache_data
def load_tech_data(indicator_code_tech, start_period):
    """
    Fetch OECD technology data. Currently supports:
        'ICT'     - businesses with broadband >= 100 Mb/s, all firms (S_GE10)
        'patents' - patent applications, EPO, applicant role, ICT + Total tech domains
    """
    
    if indicator_code_tech == "ICT":
        url_tech = ("https://sdmx.oecd.org/public/rest/data/"
                    "OECD.STI.DEP,DSD_ICT_B@DF_BUSINESSES,1.0/"
                    "AUS+AUT+BEL+CAN+COL+CZE+DNK+EST+FIN+FRA+DEU+GRC+HUN+ISL+IRL+ISR+ITA+"
                    "JPN+KOR+LVA+LTU+LUX+MEX+NLD+NZL+NOR+POL+PRT+SVK+SVN+ESP+SWE+CHE+TUR+"
                    "GBR+USA+EU27+EU28+OECD+BRA+BGR+HRV+ROU"
                    ".A.A3E_B.PT_ENT._T.S_GE10"
                    f"?startPeriod={start_period}&endPeriod=2023"
                    "&dimensionAtObservation=AllDimensions&format=csvfile")
        source_label = "ICT"
        
    elif indicator_code_tech == "patents":
        url_tech = ("https://sdmx.oecd.org/public/rest/data/"
                    "OECD.STI.PIE,DSD_PATENTS@DF_PATENTS_OECDSPECIFIC,1.0/"
                    "6F0.A.AP.PATN.APPLICATION."
                    "AUS+AUT+BEL+CAN+CHL+COL+CRI+CZE+DNK+EST+FIN+FRA+DEU+GRC+HUN+ISL+IRL+"
                    "ISR+ITA+JPN+KOR+LVA+LTU+LUX+MEX+NLD+NZL+NOR+POL+PRT+SVK+SVN+ESP+SWE+"
                    "CHE+TUR+GBR+USA+EU27_2020+OECD"
                    "..APPLICANT...ICT+_T"
                    f"?startPeriod={start_period}&endPeriod=2023"
                    "&dimensionAtObservation=AllDimensions&format=csvfile")
        source_label = "patents"
        
    else:
        st.error(f"Unknown technology indicator: {indicator_code_tech}")
        return pd.DataFrame(columns=['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE'])
    
    try:
        response_tech = requests.get(url_tech, timeout=15)
        response_tech.raise_for_status() 
    except requests.exceptions.Timeout:
        st.error(f"The OECD API for {source_label} data took too long to respond. Please try again.")
        return pd.DataFrame(columns=['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE'])
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch {source_label} data from OECD: {e}")
        return pd.DataFrame(columns=['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE'])

    try:
        df_tech = pd.read_csv(io.StringIO(response_tech.text))    
    except pd.errors.EmptyDataError:
        st.error(f"No {source_label} data available for the selected period.")
        return pd.DataFrame(columns=['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE'])

 # Subset columns; patents keeps the technology domain for downstream filtering
    if indicator_code_tech == "patents":
        keep_cols = ['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE', 'OECD_TECHNOLOGY_PATENT']
    else:
        keep_cols = ['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE']
    
    required_cols = {'REF_AREA', 'TIME_PERIOD', 'OBS_VALUE'}
    if indicator_code_tech == "patents":
        required_cols.add('OECD_TECHNOLOGY_PATENT')
    if not required_cols.issubset(df_tech.columns):
        st.error(f"The {source_label} data format from the API has changed unexpectedly.")
        return pd.DataFrame(columns=['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE'])

    df_clean = df_tech[keep_cols].copy()
    df_clean['OBS_VALUE'] = pd.to_numeric(df_clean['OBS_VALUE'], errors='coerce')
    df_clean['TIME_PERIOD'] = pd.to_numeric(df_clean['TIME_PERIOD'], errors='coerce').astype('Int64')
    df_clean = df_clean.sort_values(by=['REF_AREA', 'TIME_PERIOD'])

    return df_clean


# Main Streamlit app
st.title("OECD EPL Dashboard") # Set the title of the Streamlit app

col1, col2 = st.columns(2)


##### MAIN INDICATOR SELECTION AND PLOTTING
with col1: 
    selected_indicator = st.selectbox("Select the indicator:", options=list(indicator_options.keys())) # Create a selectbox widget for indicator selection with options from the indicator_options dictionary
with col2:    
    start_period = st.text_input("Enter the start period for the data (e.g., 2004):", value="2004") # Create a text input widget for the user to enter the start period with a default value of "2015"

df_clean = load_data_epl(selected_indicator, start_period) # Load the data using the selected indicator and start period
countries = df_clean['REF_AREA'].unique() # list of unique countries in the data, to be use for the country selection in the sidebar

country_selection = st.multiselect(
    "Select countries to display:", 
    options=list(countries),    
    default="PRT",
    key="country_selection"
) # Create a multiselect widget for country selection with options from the list of unique countries in the data, and a default selection of "PRT"

st.subheader(f"{selected_indicator}") # Set the subtitle of the Streamlit app
with st.expander("About this indicator"):
    st.write(f"This dashboard shows the {selected_indicator} from {start_period} to the most recent available data for the selected country. The data is sourced from the OECD and is updated regularly."
         f"The plot allows you to visualize the trends over time for the selected country.")
    st.write(indicator_options_explanations.get(selected_indicator, "No explanation available for this indicator.")) 

indicator_abbr = indicator_options[selected_indicator][2] # Get the indicator abbreviation from the indicator_options dictionary

## plotting the data
fig, ax = plt.subplots(figsize=(10, 6))
 # Loop through the selected countries
for country in country_selection:
    country_data = df_clean[df_clean['REF_AREA'] == country] # Filter the data for the current country
    ax.plot(country_data['TIME_PERIOD'], 
        country_data['OBS_VALUE'], 
        label=f"{country}"
    ) # Plot TIME_PERIOD vs selected_indicator for the current country on ax

ax.set_xlabel("Time")
ax.set_ylabel("EPL Index")
ax.set_title(f" EPL {indicator_abbr} by Country")
## i dont need the individual and collective dismissals on the legend description, just the country name, so I will change the label to just the country name
for line in ax.lines:
    label = line.get_label()
    country_name = label.split()[0] # Get the country name from the label
    line.set_label(country_name) # Set the label to just the country name 
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
## legend with abbreviations
st.pyplot(fig)

## Specific time period selection for bar chart
st.subheader("Bar chart")

col3, col4 = st.columns(2)

with col3:
    country_selection_2 = st.multiselect(
        "Select countries for bar chart:",
        options=list(countries),
        default="PRT",
        key="country_selection_2"
    )

    ## Single quarter time period selection for bar chart
time_period_options = df_clean['TIME_PERIOD'].unique()
time_period_options = [None] + list(time_period_options)
    ## time period selection, but empty by default, so the user has to select one
with col4:
    time_period_barchart = st.selectbox(
        "Select specific time period:", 
        options=list(time_period_options), 
        index=0, 
        key="time_period_barchart"
    )

if time_period_barchart: # Check if a time period has been selected
    with st.expander("About this bar chart"):
        st.write(f"This bar chart shows the {selected_indicator} for the selected countries in the specific time period of {time_period_barchart}. It allows you to compare the values across countries for that particular quarter.")
        ##in case the selected indicator is ID, I want to add a disclaimer about the comparability of the values with the other indicators, since it uses a different version of the indicator, so I will add a conditional statement to check if the selected indicator is ID and if so, I will add a disclaimer about the comparability of the values with the other indicators, since it uses a different version of the indicator.
    if selected_indicator == "EPL for Individual Dismissals (ID)":  
        st.write(f"Note: be cautious while comparing ID with the remaining indicators, as the values correspond to a different version of the indicator, which may affect the comparability of the values. The ID indicator uses version 1, while the other indicators use version 2, so the values may not be directly comparable due to differences in the underlying data and methodology used for each version.")
        st.write(indicator_options_explanations.get(selected_indicator, "No explanation available for this indicator.")) # Write the explanation for the selected indicator

df_bar = df_clean[(df_clean['TIME_PERIOD'] == time_period_barchart)] # Filter the data for the selected time period
fig, ax2 = plt.subplots(figsize=(12, 6)) # Create a new figure and subplot for the bar chart
        
for country in country_selection_2: # Loop through the selected countries
    country_data = df_bar[df_bar['REF_AREA'] == country] # Filter the data for the current country
    ax2.bar(country_data['REF_AREA'], country_data['OBS_VALUE'], label=f"{country} {selected_indicator}") # Plot REF_AREA vs selected_indicator for the current country as a bar chart

plt.xlabel('Country') # Set the x-axis label
plt.xticks(rotation=45)
plt.ylabel(f'{selected_indicator}') # Set the y-axis label   
plt.title(f'OECD {selected_indicator} - {time_period_barchart}') # Set the title for the plot
plt.legend() # Display the legend´
        
    #legend on the bottom of the plot
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3) # Place the legend at the bottom of the plot, centered horizontally, with 3 columns
st.pyplot(fig) # Display the plot in the Streamlit app

st.subheader("Summary statistics")

col5, col6 = st.columns(2)

with col5:
    time_period_summary_start = st.selectbox(
           "From:", 
            options=list(time_period_options), 
            index=0, 
            key="summary_start"
        )
    
with col6:
    time_period_summary_end = st.selectbox(
            "To:", 
            options=list(time_period_options), 
            index=0, 
            key="summary_end"
        )

if time_period_summary_start and time_period_summary_end:
        st.subheader(f"Summary Statistics - {indicator_abbr} ")
        df_summary = df_clean[
        (df_clean['REF_AREA'].isin(country_selection)) &
        (df_clean['TIME_PERIOD'] >= time_period_summary_start) &
        (df_clean['TIME_PERIOD'] <= time_period_summary_end)
        ]
        # Build one row per country
        rows = []
        for country in country_selection:
            df_country = df_summary[df_summary['REF_AREA'] == country].reset_index(drop=True)
            if df_country.empty:
                continue
            max_val = df_country['OBS_VALUE'].max()
            max_date = df_country.loc[df_country['OBS_VALUE'].idxmax(), 'TIME_PERIOD']
            min_val = df_country['OBS_VALUE'].min()
            min_date = df_country.loc[df_country['OBS_VALUE'].idxmin(), 'TIME_PERIOD']
            std_val = df_country['OBS_VALUE'].std().round(2)
            rows.append({
                'Country': country,
                'Peak Value': max_val,
                'Peak Date': max_date,
                'Trough Value': min_val,
                'Trough Date': min_date,
                'Std Dev': std_val
            })

        df_stats = pd.DataFrame(rows).reset_index(drop=True)
        st.dataframe(df_stats)

####### COMPARISON OF THE SELECTED INDICATOR WITH OTHER INDICATORS
checkbox_comparison = st.checkbox("Do you want to compare the selected indicator with another indicator?", key="checkbox_comparison") #
## i want the checkbox to be on the same line as the text, so I will add an empty string as the label for the checkbox and then use CSS to move it to the right of the text

if checkbox_comparison: # Check if the user has checked the box for comparison 
    st.text("Comparison options:") # Add a text element to the sidebar for comparison options
    comparison_indicator = st.selectbox(
    "Select an indicator to compare:", 
        options=list(indicator_options.keys()), 
        index=1, 
        key="comparison_indicator"
    )

    comparison_abbr = indicator_options[comparison_indicator][2] # Get the abbreviations for both indicators in the comparison
    indicator_comparison = [selected_indicator, comparison_indicator]
    indicator_comparison_abbr = [indicator_abbr, comparison_abbr]

    st.subheader(f"{indicator_abbr} vs {comparison_abbr} ") # Set the subtitle of the Streamlit app
    country_selection_3 = st.multiselect(
        "Select countries for bar chart:",
        options=list(countries),
        default="PRT",
        key="country_selection_3"
    )
    with st.expander("About this comparison"):
        st.write(f"This dashboard shows the {indicator_abbr} with {comparison_abbr} from {start_period} to the most recent available data for the selected country. The data is sourced from the OECD and is updated regularly. The plot allows you to visualize the trends over time side by side  with both indicators.")
        st.write(indicator_options_explanations.get(selected_indicator, "No explanation available for this indicator.")) # Write the explanation for the selected indicator
        st.write(indicator_options_explanations.get(comparison_indicator, "No explanation available for this indicator.")) # Write the explanation for the comparison indicator

    dfs=[]
    for indicator in indicator_comparison:
        df_temp = load_data_epl(indicator, start_period)
        df_temp['indicator'] = indicator
        dfs.append(df_temp)
    df_all = pd.concat(dfs, ignore_index=True)
    df_all.sort_values(by=['REF_AREA', 'TIME_PERIOD'], inplace=True) # Sort the combined data by country and time period

    ## plotting the comparison of the two indicators
    fig, ax3 = plt.subplots(figsize=(10, 6))
    for country in country_selection_3: # Loop through the selected countries
        for indicator in indicator_comparison:
            country_data = df_all[(df_all['REF_AREA'] == country) & (df_all['indicator'] == indicator)] # Filter the data for the current country and indicator
            ax3.plot(country_data['TIME_PERIOD'], 
                    country_data['OBS_VALUE'], 
                    label=f"{country} {indicator_options[indicator][2]}") # Plot TIME_PERIOD vs selected_indicator for the current country on ax    
    ax3.set_xlabel("Time")
    ax3.set_ylabel("Index Value")   
    ax3.set_title(f"Comparison of {indicator_abbr} and {comparison_abbr} by Country")    
    ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    #legend and title with country and indicator, but i want country and indicator abbreviated, so I will change the label to just the country name and indicator abbreviation

    for indicator in indicator_comparison_abbr:
        for line in ax3.lines:  
            label = line.get_label()
            country_name = label.split()[0] # Get the country name from the label
        line.set_label(f"{country_name} {indicator}") # Set the label to just the country name and indicator abbreviation
    st.pyplot(fig)

    with st.expander("Note on comparability of indicators"):
        if comparison_indicator == "Individual Dismissals EPL (ID)":  
            st.caption(f"Be cautious while comparing ID with the remaining indicators, as the values correspond to a different version of the indicator, which may affect the comparability of the values."
                f"The ID indicator uses version 1, while the other indicators use version 2, so the values may not be directly comparable due to differences in the underlying data and methodology used for each version.")


# change the same of the indicator for its abbreviation in the summary statistics table, so it is easier to read and compare with the plot, 
# so I will change the label to just the country name and indicator abbreviation
## Also want to include table for indicator comparison summary statistics, with the same columns as above, but for both indicators in the comparison, 
# so I will create a new dataframe for the comparison summary statistics and display it in a table format as well.

## ask first if we want a summary statistics table for the comparison of the two indicators, and if so, then ask for the time period for the summary statistics, and then create the table with the same columns as above, but for both indicators in the comparison, so we can compare the summary statistics of both indicators side by side in a table format, and also include the indicator abbreviation in the table for easier comparison with the plot.
if checkbox_comparison:
    show_comparison_stats = st.checkbox("Do you want to see summary statistics for the comparison of the two indicators?", key="show_comparison_stats")
    if show_comparison_stats:
        st.subheader(f" Summary Statistics - {indicator_abbr} vs {comparison_abbr}")
        rows_comparison = []    
        for country in country_selection:
            df_country = df_all[(df_all['REF_AREA'] == country) & (df_all['indicator'].isin(indicator_comparison)) & (df_all['TIME_PERIOD'] >= time_period_summary_start) & (df_all['TIME_PERIOD'] <= time_period_summary_end)].reset_index(drop=True)
            if df_country.empty:
                continue    
            for indicator in indicator_comparison:
                df_indicator = df_country[df_country['indicator'] == indicator]
                max_val = df_indicator['OBS_VALUE'].max()
                max_date = df_indicator.loc[df_indicator['OBS_VALUE'].idxmax(), 'TIME_PERIOD']
                min_val = df_indicator['OBS_VALUE'].min()
                min_date = df_indicator.loc[df_indicator['OBS_VALUE'].idxmin(), 'TIME_PERIOD']
                std_val = df_indicator['OBS_VALUE'].std().round(2)
                indicator_comparison_abbr = indicator_options[indicator][2]
                rows_comparison.append({
                    'Country': country,
                    'Indicator': indicator_comparison_abbr,
                    'Peak Value': max_val,
                    'Peak Date': max_date,
                    'Trough Value': min_val,
                    'Trough Date': min_date,
                    'Std Dev': std_val
                })
        df_stats_comparison = pd.DataFrame(rows_comparison).reset_index(drop=True)
        st.dataframe(df_stats_comparison)   

## lets merge tech data with EPL to plot them in a scatterplot, with x - EPL and y - tech indicator, where the dots are countries in year = 2019
st.subheader(" EPL vs Tech indicator")

col7, col8 = st.columns(2)

with col7:
    tech_label = st.selectbox(
        "Choose a technology indicator:",
        list(tech_options.keys()),
    )

tech_code = tech_options[tech_label]

# If patents, ask which technology domain
patents_domain = None
if tech_code == "patents":
    patents_domain_label = st.radio(
        "Patent technology domain:",
        ["ICT only", "Total patents"],
        horizontal=True,
    )
    patents_domain = "ICT" if patents_domain_label == "ICT only" else "_T"

# Per-indicator metadata for axis label and title
tech_meta = {
    "ICT": {
        "y_label": "Businesses with broadband ≥100 Mb/s (% of enterprises)",
        "title_suffix": "ICT usage in businesses",
    },
    "patents": {
        "y_label": "Patent applications (count, EPO)",
        "title_suffix": "Patent applications",
    },
}


## Time series
with col8:
    start_period_tech = st.text_input("Enter the start period for the data (e.g., 2010):", value="2010") # Create a text input widget for the user to enter the start period with a default value of "2015"

df_tech_time = load_tech_data(tech_code, start_period_tech)

country_selection_4 = st.multiselect(
        "Select countries for bar chart:",
        options=list(countries),
        default="PRT",
        key="country_selection_4"
    )

with st.expander("About this indicator"):
    st.write(f"This indicator represents the % of enterprises that uses internet with 100 Mb/s or higher.")


# Load data tech vs epl
df_tech = load_tech_data(tech_code, start_period)
df_epl = load_data_epl(selected_indicator, start_period)

df_epl['TIME_PERIOD'] = df_epl['TIME_PERIOD'].astype(int)
df_tech['TIME_PERIOD'] = df_tech['TIME_PERIOD'].astype(int)

# Filter patents to chosen technology domain (ICT or Total)
if tech_code == "patents":
    if 'OECD_TECHNOLOGY_PATENT' in df_tech.columns:
        df_tech = df_tech[df_tech['OECD_TECHNOLOGY_PATENT'] == patents_domain]
    else:
        st.warning(
            "OECD_TECHNOLOGY_PATENT column not found in patents data; cannot filter ICT vs Total. "
            "Update load_tech_data to retain that column."
        )

## plotting the data
fig, ax = plt.subplots(figsize=(10, 6))
 # Loop through the selected countries
for country in country_selection_4:
    country_data = df_tech_time[df_tech_time['REF_AREA'] == country] # Filter the data for the current country
    ax.plot(country_data['TIME_PERIOD'], 
        country_data['OBS_VALUE'], 
        label=f"{country}"
    ) 
ax.set_xlabel("Time")
ax.set_ylabel(f"{tech_code}")
ax.set_title(f" {tech_code}")
## i dont need the individual and collective dismissals on the legend description, just the country name, so I will change the label to just the country name
for line in ax.lines:
    label = line.get_label()
    country_name = label.split()[0] # Get the country name from the label
    line.set_label(country_name) # Set the label to just the country name 
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
## legend with abbreviations
st.pyplot(fig)


## Scatter plt
scatter_time_period = st.selectbox( 
    "Time period for the scatter plot:",
    options=sorted(df_epl['TIME_PERIOD'].unique()),
    index=sorted(df_epl['TIME_PERIOD'].unique()).index(2019) if 2019 in df_epl['TIME_PERIOD'].unique() else 0,
    key="scatter_time_period"
)

df_tech_filtered = df_tech[df_tech['TIME_PERIOD'] == scatter_time_period]
df_epl_filtered = df_epl[df_epl['TIME_PERIOD'] == scatter_time_period]

df_scatter = pd.merge(
    df_epl_filtered,
    df_tech_filtered,
    on=['REF_AREA', 'TIME_PERIOD'],
    how='inner',
    suffixes=('_EPL', '_TECH'),
)

# Drop Germany
df_scatter = df_scatter[df_scatter['REF_AREA'] != 'DEU']

df_scatter['Region'] = df_scatter['REF_AREA'].map(country_to_region)
df_scatter = df_scatter.dropna(subset=['Region'])  # drop non-European countries

if df_scatter.empty:
    st.warning(f"No overlapping data between EPL and {tech_label} for {scatter_time_period}.")
else:
    region_colors = {
        'Nordic': '#1f77b4',
        'Continental': '#2ca02c',
        'Southern': '#d62728',
        'Eastern': '#ff7f0e',
        'Anglo': '#9467bd',
    }
    with st.expander("Interpretation of this scatter plot"):
        st.caption(
        f"This scatter plot shows the relationship between the EPL index and {tech_label} "
        f"for the selected countries in 2019. Each point represents a country: x-axis is the "
        f"EPL index, y-axis is the chosen technology indicator. Data sourced from the OECD."
        )

    fig_scatter, ax_scatter = plt.subplots(figsize=(10, 6))
    for region, color in region_colors.items():
        df_region = df_scatter[df_scatter['Region'] == region]
        if df_region.empty:
            continue
        ax_scatter.scatter(
            df_region['OBS_VALUE_EPL'],
            df_region['OBS_VALUE_TECH'],
            color=color,
            label=region,
            s=60,
            alpha=0.8,
            edgecolors='white',
            linewidths=0.8,
        )
        for _, row in df_region.iterrows():
            ax_scatter.text(
                row['OBS_VALUE_EPL'] + 0.02,
                row['OBS_VALUE_TECH'],
                row['REF_AREA'],
                fontsize=8,
            )

    # Quadrant lines at medians
    epl_median = df_scatter['OBS_VALUE_EPL'].median()
    tech_median = df_scatter['OBS_VALUE_TECH'].median()

    ax_scatter.axvline(epl_median, color='gray', linestyle='--', linewidth=1, alpha=0.7)
    ax_scatter.axhline(tech_median, color='gray', linestyle='--', linewidth=1, alpha=0.7)

    # Light shading on the predicted quadrant (low EPL, high tech, top-left)
    xmin, xmax = ax_scatter.get_xlim()
    ymin, ymax = ax_scatter.get_ylim()
    ax_scatter.axvspan(
        xmin, epl_median,
        ymin=(tech_median - ymin) / (ymax - ymin),
        ymax=1,
        color='green', alpha=0.05,
    )

    # Adapt title to selected patents domain
    if tech_code == "patents":
        domain_for_title = "ICT" if patents_domain == "ICT" else "Total"
        title_suffix = f"Patent applications ({domain_for_title})"
    else:
        title_suffix = tech_meta[tech_code]['title_suffix']

    ax_scatter.set_xlabel(f'{selected_indicator}')
    ax_scatter.set_ylabel(tech_meta[tech_code]['y_label'])
    ax_scatter.set_title(f"EPL vs {title_suffix}, {scatter_time_period}")
    ax_scatter.legend(title='Region', loc='best')
    st.pyplot(fig_scatter)

    with st.expander("Note on comparability of indicators"):
        st.caption(
        "Note: Germany is excluded from this analysis. The PhD research that motivates this dashboard "
        "uses EU-SILC longitudinal microdata, where Germany is not available in the longitudinal sample. "
        "To keep this dashboard consistent with the underlying study, Germany is dropped here as well."
        )
