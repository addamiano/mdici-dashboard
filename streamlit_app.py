"""
MDICI Dashboard - Cloud Version
Uses CSV files instead of direct database connection
Deploy this version to Streamlit Cloud
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from io import BytesIO
import socket

# Page configuration
st.set_page_config(
    page_title="MDICI Design Projects",
    page_icon="📋",
    layout="wide"
)

# No custom theme - using Streamlit defaults for best compatibility

# Data loading functions for CSV-based deployment
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_project_data():
    """Load project data from CSV file"""
    try:
        # Try to load from different possible locations
        possible_files = [
            'mdici_projects_latest.csv',  # Local file
            'exported_data/mdici_projects_latest.csv',  # Local subfolder
            'https://your-storage-url/mdici_projects_latest.csv'  # Cloud storage (update this URL)
        ]
        
        df = None
        for file_path in possible_files:
            try:
                df = pd.read_csv(file_path)
                st.success(f"✅ Data loaded from: {file_path}")
                break
            except:
                continue
        
        if df is None:
            st.error("❌ Could not load project data. Make sure CSV file is available.")
            return pd.DataFrame()
        
        # Convert date columns
        date_columns = ['Kick-Off Date', 'Expected DE Completion', 'Testing Info Sent', 'Actual Go-Live Date', 'Export Date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_completed_performance():
    """Load performance metrics from CSV"""
    try:
        # Try to load performance data
        possible_files = [
            'mdici_performance_latest.csv',
            'exported_data/mdici_performance_latest.csv',
            'https://your-storage-url/mdici_performance_latest.csv'  # Update this URL
        ]
        
        for file_path in possible_files:
            try:
                df = pd.read_csv(file_path)
                
                # Convert date columns
                date_columns = ['Kick-Off Date', 'Testing Info Sent', 'Actual Go-Live Date', 'Export Date']
                for col in date_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                
                return df
            except:
                continue
                
        return pd.DataFrame()  # Return empty if no file found
    
    except Exception as e:
        st.warning(f"Could not load performance metrics: {str(e)}")
        return pd.DataFrame()

def create_status_pie_chart(df):
    """Create status distribution pie chart"""
    if df.empty:
        return None
        
    status_counts = df['Status'].value_counts()
    
    colors = {
        'On Track': '#00cc88',
        'Attention Needed': '#ffa500',
        'Overdue': '#ff4b4b',
        'No Kickoff Date': '#808080',
        'Waiting for Firewall': '#9c88ff',
        'Pending Updates from Site': '#ff9f43',
        'Completed': '#00d4aa',
        'In Intake Process': '#74b9ff',
        'On Hold': '#a29bfe'
    }
    
    fig = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title="Project Status Distribution",
        color=status_counts.index,
        color_discrete_map=colors,
        hole=0.4
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label+value'
    )
    
    return fig

def create_engineer_workload_chart(df):
    """Create horizontal bar chart of engineer workloads"""
    if df.empty:
        return None
        
    engineer_counts = df.groupby(['Design Engineer', 'Status']).size().reset_index(name='count')
    
    # Custom color mapping
    color_map = {
        'On Track': '#00cc88',
        'Attention Needed': '#ffa500',
        'Overdue': '#ff4b4b',
        'No Kickoff Date': '#808080',
        'Waiting for Firewall': '#9c88ff',
        'Pending Updates from Site': '#ff9f43',
        'Completed': '#00d4aa'
    }
    
    fig = px.bar(
        engineer_counts,
        x='count',
        y='Design Engineer',
        color='Status',
        title="Projects by Design Engineer",
        orientation='h',
        color_discrete_map=color_map,
        height=400
    )
    
    fig.update_layout(
        xaxis_title="Number of Projects",
        yaxis_title="Design Engineer",
        legend_title="Status"
    )
    
    return fig

def export_to_excel(df):
    """Create Excel file with formatting"""
    if df.empty:
        return b""
        
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Write dataframe
        df.to_excel(writer, sheet_name='Project Data', index=False)
        
        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Project Data']
        
        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        # Format header row
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Auto-fit columns
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, min(column_width, 50))
    
    return output.getvalue()

# Main app
def main():
    st.title("📋 MDICI Design Project Tracker")
    
    # Show data source info
    st.caption("📊 Cloud Version - Data from CSV exports")
    
    # Load data with progress indicator
    with st.spinner("Loading exported project data..."):
        df = load_project_data()
        performance_df = load_completed_performance()
    
    if df.empty:
        st.error("No data available. Please check your CSV files.")
        st.info("💡 Make sure you've uploaded the exported CSV files to your chosen storage location.")
        return
    
    # Show database summary with correct logic
    total_projects = len(df)
    # Only count "Intake" projects with placeholder dates as "awaiting kickoff info"
    awaiting_kickoff = len(df[(df['Kick-Off Date'] == '1900-01-01') & (df['Project State'] == 'Intake')])
    
    # Show export info
    if 'Export Date' in df.columns and not df['Export Date'].isna().all():
        export_date = df['Export Date'].max()
        st.info(f"📅 Data last exported: {export_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    st.success(f"✅ Loaded {total_projects:,} total projects ({awaiting_kickoff} awaiting kickoff info)")
    
    # Sidebar filters (same as original)
    with st.sidebar:
        st.header("Filters")
        
        # Project State filter
        st.subheader("Project State")
        project_states = sorted(df['Project State'].unique())
        
        # Quick filter buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🎯 Active Only", use_container_width=True):
                st.session_state.selected_states = [s for s in project_states if s in ['Design', 'Firewall', 'Testing', 'Intake', 'Hold']]
        with col2:
            if st.button("⏳ Awaiting Kickoff", use_container_width=True, help="Intake projects awaiting kickoff info"):
                st.session_state.selected_states = ['Intake']
                st.session_state.date_filter = "Awaiting kickoff (1900-01-01)"
        with col3:
            if st.button("📋 All Projects", use_container_width=True):
                st.session_state.selected_states = project_states
        
        # Initialize session state if not exists
        if 'selected_states' not in st.session_state:
            st.session_state.selected_states = ['Design', 'Firewall']
        
        selected_states = st.multiselect(
            "Select Project States",
            options=project_states,
            default=st.session_state.selected_states,
            help="💡 Use quick buttons above or manually select states"
        )
        
        # Update session state
        if selected_states:
            st.session_state.selected_states = selected_states
        
        # Design Engineer filter
        st.subheader("Design Engineer")
        engineers = ['All'] + sorted(df['Design Engineer'].dropna().unique().tolist())
        selected_engineer = st.selectbox("Select Engineer", engineers)
        
        # Status filter
        st.subheader("SLA Status")
        status_options = df['Status'].unique().tolist()
        selected_status = st.multiselect(
            "Select Status",
            status_options,
            default=status_options
        )
        
        # Date filter for kickoff dates
        st.subheader("Kickoff Date Filter")
        date_filter_type = st.radio(
            "Show projects:",
            ["All dates", "Awaiting kickoff (1900-01-01)", "Real kickoff dates only"],
            help="Filter by kickoff date status"
        )
        
        # Quick search by Defect ID
        st.subheader("🔍 Quick Search")
        defect_search = st.text_input(
            "Search by Defect ID:",
            placeholder="Enter Defect ID number...",
            help="Type a Defect ID to quickly find that project"
        )
    
    # Apply filters (same logic as original)
    filtered_df = df.copy()
    
    if selected_states:
        filtered_df = filtered_df[filtered_df['Project State'].isin(selected_states)]
    
    if selected_engineer != 'All':
        filtered_df = filtered_df[filtered_df['Design Engineer'] == selected_engineer]
    
    if selected_status:
        filtered_df = filtered_df[filtered_df['Status'].isin(selected_status)]
    
    # Apply date filter
    if date_filter_type == "Awaiting kickoff (1900-01-01)":
        filtered_df = filtered_df[filtered_df['Kick-Off Date'] == '1900-01-01']
    elif date_filter_type == "Real kickoff dates only":
        filtered_df = filtered_df[filtered_df['Kick-Off Date'] != '1900-01-01']
    
    # Apply Defect ID search filter
    if defect_search:
        mask = filtered_df['Defect ID'].astype(str).str.contains(defect_search, case=False, na=False)
        filtered_df = filtered_df[mask]
        
        if len(filtered_df) == 1:
            st.success(f"✅ Found exact match: Defect ID {defect_search}")
        elif len(filtered_df) > 1:
            st.info(f"🔍 Found {len(filtered_df)} projects matching '{defect_search}'")
        else:
            st.warning(f"❌ No projects found matching '{defect_search}'")
    
    # Key Metrics (same as original)
    design_projects = filtered_df[filtered_df['Project State'] == 'Design']
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        design_count = len(design_projects)
        st.metric("Active Design Projects", design_count, help="Projects requiring DE work")
    
    with col2:
        firewall_count = len(filtered_df[filtered_df['Project State'] == 'Firewall'])
        st.metric("Waiting on Firewall", firewall_count, help="Projects waiting on DE to move to FW team, or FW team to push rules.")
    
    with col3:
        testing_count = len(filtered_df[filtered_df['Project State'] == 'Testing'])
        st.metric("Pending Site Updates", testing_count, help="Projects waiting for site feedback")
    
    with col4:
        overdue_count = len(design_projects[design_projects['Status'] == 'Overdue'])
        st.metric("Overdue Design", overdue_count, help="Design projects past 21-day SLA")
    
    with col5:
        urgent = len(design_projects[(design_projects['Days Until SLA'] <= 3) & 
                                   (design_projects['Days Until SLA'].notna())])
        st.metric("Urgent Design (<3 days)", urgent, help="Design projects near SLA deadline")
    
    # Performance Metrics from Completed Projects
    if not performance_df.empty:
        st.subheader("📊 Recent Performance Metrics (Last 6 months)")
        perf_col1, perf_col2, perf_col3 = st.columns(3)
        
        with perf_col1:
            avg_to_testing = performance_df['Days_to_Testing'].mean()
            st.metric("Avg Days: Kickoff → Testing Info", f"{avg_to_testing:.1f}", 
                     help="Average time from kickoff to sending testing info")
        
        with perf_col2:
            avg_to_completion = performance_df['Days_to_Completion'].mean()
            st.metric("Avg Days: Kickoff → Completion", f"{avg_to_completion:.1f}",
                     help="Average total project time")
        
        with perf_col3:
            sla_met = len(performance_df[performance_df['Days_to_Testing'] <= 21])
            sla_rate = (sla_met / len(performance_df) * 100) if len(performance_df) > 0 else 0
            st.metric("SLA Met Rate (≤21 days)", f"{sla_rate:.1f}%",
                     help="Percentage meeting 21-day SLA")
    
    # Tabs for different views (rest same as original)
    tab1, tab2, tab3 = st.tabs(["📊 Active Projects", "👥 By Engineer", "📝 Detailed View"])
    
    with tab1:
        st.subheader("📋 Project Overview")
        
        # Same table implementation as original...
        # [Rest of the tab content would be identical to streamlit_simple.py]
        # For brevity, showing key differences only
        
        # Main project table with same functionality
        if not filtered_df.empty:
            st.dataframe(filtered_df, use_container_width=True)
            
            # Download options
            col1, col2 = st.columns(2)
            with col1:
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name=f"MDICI_Projects_{date.today()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col2:
                excel_data = export_to_excel(filtered_df)
                st.download_button(
                    label="📥 Download as Excel",
                    data=excel_data,
                    file_name=f"MDICI_Projects_{date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            st.info("No projects match your current filters.")
    
    # Add similar implementation for other tabs...
    
    # Footer
    st.markdown("---")
    if 'Export Date' in df.columns and not df['Export Date'].isna().all():
        export_date = df['Export Date'].max()
        st.caption(f"Data exported: {export_date.strftime('%Y-%m-%d %H:%M:%S')} | Refreshes when new data is uploaded")
    else:
        st.caption("Cloud version - updates when new CSV files are uploaded")

if __name__ == "__main__":
    main()