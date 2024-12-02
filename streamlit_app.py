import uuid
import random
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
import streamlit as st

st.set_page_config(page_title="Topo-Schedule", layout="wide")


# Load CSV data
file_path = r"data/Cross-border Physical Flows_202312312300-202412312300.csv"

try:
    # Read the CSV file, specifying that the header is on the first row
    df = pd.read_csv(file_path, header=0)

    # Replace 'n/e' with NaN
    df.replace('n/e', pd.NA, inplace=True)

    # Convert numeric columns to numeric types
    numeric_cols = df.columns.drop('MTU')
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

    # Rename columns: Replace 'DE_50HzT' with '50H'
    df.columns = df.columns.str.replace('DE_50HzT', '50H')

    # Calculate net flows for each border with updated column names
    df['PL Total'] = df['50H -> PL'] - df['PL -> 50H']
    df['CZ Total'] = df['50H -> CZ'] - df['CZ -> 50H']
    df['DK Total'] = df['50H -> DK'] - df['DK -> 50H']

    # Save initial state for reference
    initial_df = df.copy()

except FileNotFoundError:
    st.error("The specified file could not be found.")
    df = pd.DataFrame()
    initial_df = df.copy()
except Exception as e:
    st.error(f"An error occurred while reading the CSV file: {e}")
    df = pd.DataFrame()
    initial_df = df.copy()

# Initialize session state variables if they don't exist
if 'powerflow_run' not in st.session_state:
    st.session_state.powerflow_run = 0

if 'elements_changed' not in st.session_state:
    st.session_state.elements_changed = False

if 'element_tables' not in st.session_state:
    hours = [f'{i:02}:00' for i in range(24)]
    element_types = ["Switch", "Breaker", "Disconnector", "BusbarCoupler"]
    status_options = ['open', 'closed']

    element_tables = {}
    for etype in element_types:
        elements = [f'{etype} {i+1}' for i in range(10)]
        mrid = [f"_{uuid.uuid4()}" for _ in elements]
        data = {
            'ElementName': elements,
            'mRID': mrid,
            'inService': [random.choice(['TRUE', 'FALSE']) for _ in elements],
            'Group': [random.choice(['VIE', 'ROE', 'HH']) for _ in elements]
        }
        for hour in hours:
            data[hour] = [random.choice(status_options) for _ in elements]
        element_tables[etype] = pd.DataFrame(data)
    st.session_state.element_tables = element_tables

current_time = datetime.now().strftime("%H_%M_%S")
current_date = datetime.now().strftime("%Y%m%d")

st.sidebar.write("")
st.sidebar.write("")

######## Main Dashboard ##########
#col1, col2, col3, col4, col5, col6 = st.columns(6)
#with col6:
#	st.image("data/50Hertz.png", use_container_width=True)

# Topo RA Dashboard
st.write("# Topo RA")
# Sidebar
st.sidebar.write(datetime.now().strftime("# %d.%m.%Y | %H:%M:%S"))

st.sidebar.write("")

st.sidebar.write("## Security Analysis")
st.sidebar.write("")


if st.sidebar.button("Results CROSA"):
    st.sidebar.write("Download CGM ... ")
    st.sidebar.success("RemedialActionSchedule.xml imported")
    st.sidebar.code("ID:" f"_{uuid.uuid4()}", language='text')

if st.sidebar.button("LF Report RSA"):
    st.sidebar.write("Download ...")
    st.sidebar.success(f"\\RSA_{current_date}\\LF_{current_time}")

if st.sidebar.button("DifferenceModel"):
    st.sidebar.write("Generating ...")
    st.sidebar.success("DiffModel created dependent on: " f"_{uuid.uuid4()}")
    st.sidebar.code("ID:" f"_{uuid.uuid4()}", language='text')

st.sidebar.markdown("---")  # Separate buttons from top

st.sidebar.write("## Operational Planning")
st.sidebar.write("")

if st.sidebar.button("GET Model Improvements D-1"):
    st.sidebar.success("DACF Topo Changes imported")

if st.sidebar.button("GET ASP 2.0"):
    st.sidebar.success("Ausschaltplanung imported")

st.sidebar.markdown("---")  # Separate buttons from top
st.sidebar.write("## PST")
st.sidebar.write("")

if st.sidebar.button("GET PST Ceps"):
    st.sidebar.write("Connecting to OPDE...")
    st.sidebar.success("PST imported as Group")

if st.sidebar.button("GET PST TennetDE"):
    st.sidebar.write("Connecting to OPDE...")
    st.sidebar.success("PST imported as Group")
st.sidebar.markdown("---")  # Separate buttons from top

# Add to the sidebar
st.sidebar.markdown("## Backoffice Data")

st.sidebar.write("")

# Assume you have a list of available dates
date_options = ["2024-11-14", "2024-11-15", "2024-11-16"]
selected_date = st.sidebar.selectbox("Select Date", date_options)

# Add a 'Load' button
if st.sidebar.button("Load"):
    # st.write(f"Loading data for {selected_date}...")
    # Implement your data loading logic here
    # For example:
    data_file = f"/path/to/data/Cross-border Flows_{selected_date}.csv"
    try:
        df = pd.read_csv(data_file)
        st.write(f"Data for {selected_date} loaded successfully.")
        # Update your app with the new data
    except FileNotFoundError:
        st.sidebar.error(f"No data file found for {selected_date}.")

# Search fields
col1, col2, col3, col4 = st.columns(4)
mRID_search = col1.text_input("mRID")
group_RA = col2.text_input("Group")
element_search = col3.text_input("ElementName")
element_type = col4.selectbox("ElementType", ["Switch", "Breaker", "Disconnector", "BusbarCoupler"])

# Select the appropriate table based on element type
selected_table = st.session_state.element_tables[element_type]
filtered_df = selected_table.copy()

# Apply filters
if mRID_search:
    filtered_df = filtered_df[filtered_df['mRID'].str.contains(mRID_search, na=False)]
if group_RA:
    filtered_df = filtered_df[filtered_df['Group'].str.contains(group_RA, na=False)]
if element_search:
    filtered_df = filtered_df[filtered_df['ElementName'].str.contains(element_search, na=False)]

st.session_state['filtered_df'] = filtered_df.copy()

st.markdown("---")

# Element Status Table
st.write("## Element Status Table")

# Display success message if status was updated
if 'status_updated_message' in st.session_state:
    st.success(st.session_state.status_updated_message)
    del st.session_state.status_updated_message

update_col1, update_col2 = st.columns([3, 1])
with update_col1:
    if not st.session_state['filtered_df'].empty:
        # Hide the index column and adjust column widths
        styled_df = st.session_state['filtered_df'].style.hide(axis='index')
        st.dataframe(styled_df, use_container_width=True, height=400)
    else:
        st.info("No elements found with the current search criteria.")

with update_col2:
    if not st.session_state['filtered_df'].empty:
        st.write("**Change Status**")
        # Create a form to prevent immediate re-execution
        with st.form(key='update_status_form'):
            # Select Element and Hour
            element_selected = st.selectbox("Select Element", st.session_state['filtered_df']['ElementName'], key='element_select')
            # Ensure that only the hour columns are available for selection
            hour_columns = [col for col in st.session_state['filtered_df'].columns if col.endswith(":00")]
            hour_selected = st.selectbox("Select Hour", hour_columns, key='hour_select')

            # Check if the element exists in selected_table
            element_row = selected_table.loc[selected_table['ElementName'] == element_selected]

            if not element_row.empty and hour_selected in selected_table.columns:
                current_status = element_row[hour_selected].values[0]
                new_status = st.selectbox(
                    "Select New Status",
                    ["open", "closed"],
                    index=["open", "closed"].index(current_status),
                    key='status_select'
                )

                # Submit button inside the form
                submit_button = st.form_submit_button(label='Update Status')

                if submit_button:
                    if new_status != current_status:
                        selected_table.loc[selected_table['ElementName'] == element_selected, hour_selected] = new_status
                        st.session_state.element_tables[element_type] = selected_table
                        st.session_state.elements_changed = True  # Mark that elements have changed
                        # Set a flag to show success message after rerun
                        st.session_state.status_updated_message = f"Status of {element_selected} at {hour_selected} updated to {new_status}."
                        st.rerun()
                    else:
                        st.info("No changes were made.")
            else:
                st.warning("Selected element not found in the current table.")
    else:
        st.info("No elements available to update.")

# Powerflow Execution and updated data display
if st.button("Run Powerflow"):
    if st.session_state.elements_changed:
        st.write("LF Calculation started...")
        st.success("Converged ...")
        st.session_state.powerflow_run += 1
        st.session_state.elements_changed = False  # Reset the flag
    else:
        st.warning("No changes to elements. Cross-border flows are not updated.")

st.markdown("---")

# Cross-Border Physical Flows Table and Diagram
st.write("## Cross-Border Flow")

# Determine row ranges based on powerflow_run
if st.session_state.powerflow_run == 0:
    first_range = (0, 24)
    second_range = (24, 48)
else:
    # For each subsequent run, shift the window by 24 rows
    first_range = (0, 24)
    second_range = (24 * (st.session_state.powerflow_run + 1), 24 * (st.session_state.powerflow_run + 2))

# Prepare initial data
initial_data = initial_df.iloc[first_range[0]:first_range[1]].copy()

# Prepare updated data
if st.session_state.powerflow_run > 0:
    start_row = second_range[0]
    end_row = second_range[1]
    if end_row <= len(df):
        updated_data = df.iloc[start_row:end_row].copy()
    else:
        st.warning("No more data available for updated flows. Showing initial data.")
        updated_data = initial_data.copy()
else:
    updated_data = initial_data.copy()

# Function to style the dataframe and format numbers as integers
def style_dataframe(df):
    numeric_cols = df.select_dtypes(include=[float, int]).columns
    styled_df = df.style.hide(axis='index').format({col: "{:.0f}" for col in numeric_cols})
    # Adjust column widths
    styled_df.set_table_styles(
        [{'selector': 'th', 'props': [('max-width', '80px'), ('font-size', '10pt')]},
         {'selector': 'td', 'props': [('max-width', '80px'), ('font-size', '10pt')]}]
    )
    return styled_df

# Display initial and updated cross-border flow tables side by side
col1, col2 = st.columns(2)

with col1:
    st.write("Border Flows (initial)")
    if not initial_data.empty:
        # Hide the index column and ensure all columns are displayed
        st.dataframe(style_dataframe(initial_data), use_container_width=True, height=400)
    else:
        st.info("No initial data available.")

    fig_initial = go.Figure()
    for border in ['PL Total', 'CZ Total', 'DK Total']:
        fig_initial.add_trace(go.Scatter(
            x=initial_data['MTU'],
            y=initial_data[border],
            mode='lines',
            name=border + " (initial)"
        ))
    fig_initial.update_layout(
        title="Border Flows (initial)",
        xaxis_title="MTU",
        yaxis_title="Flow (MW)",
        xaxis=dict(tickformat='%H:%M', automargin=True),
        showlegend=True,
        autosize=True,
        margin=dict(l=40, r=20, t=40, b=40),
    )
    st.plotly_chart(fig_initial, use_container_width=True, key='cross_border_flow_initial')

with col2:
    st.write("Border Flows (updated)")
    if not updated_data.empty:
        # Hide the index column and ensure all columns are displayed
        st.dataframe(style_dataframe(updated_data), use_container_width=True, height=400)
    else:
        st.info("No updated data available.")

    fig_updated = go.Figure()
    for border in ['PL Total', 'CZ Total', 'DK Total']:
        fig_updated.add_trace(go.Scatter(
            x=updated_data['MTU'],
            y=updated_data[border],
            mode='lines',
            name=border + " (updated)"

        ))
    fig_updated.update_layout(
        title="Border Flows (updated)",
        xaxis_title="MTU",
        yaxis_title="Flow (MW)",
        xaxis=dict(tickformat='%H:%M', automargin=True),
        showlegend=True,
        autosize=True,
        margin=dict(l=40, r=20, t=40, b=40),
    )
    st.plotly_chart(fig_updated, use_container_width=True, key='cross_border_flow_updated')

st.markdown("---")

st.write("## Export ##")

st.write("")
st.write("")

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("Validation"):
        st.write("Checking Header, Version, mRID and References")
        st.write("Consistency Check ...")
        st.success("Validation passed (QoDOC 2.2)")
with col2:
    if st.button("Local File Transfer (MFT)"):
        st.code("/TPSchedule/#_7336296309712345", language='text')
with col3:
    if st.button("Export OPDE"):
        st.write("OPDE Export ...")
        st.success("Upload confirmed.")
        st.code("ID: #_7336296309712345", language='text')
with col4:
	st.image("data/50Hertz.png", use_container_width=True)
        
        
        
        
    
