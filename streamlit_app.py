"""
MDICI Dashboard - Complete Cloud Version
Full functionality from streamlit_simple.py but reads from CSV files
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from io import BytesIO

# Page configuration
st.set_page_config(
    page_title="MDICI Design Projects",
    page_icon="📋",
    layout="wide"
)

# Custom CSS to reduce padding around info bars
st.markdown("""
<style>
    .stAlert {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
    }
    .stSuccess {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
    }
</style>
""", unsafe_allow_html=True)

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
        ]
        
        df = None
        for file_path in possible_files:
            try:
                df = pd.read_csv(file_path)
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

def create_timeline_chart(df):
    """Create timeline view of projects"""
    if df.empty:
        return None
        
    timeline_df = df[df['Kick-Off Date'].notna()].copy()
    timeline_df = timeline_df.sort_values('Kick-Off Date', ascending=False).head(20)
    
    fig = go.Figure()
    
    # Add kickoff dates
    fig.add_trace(go.Scatter(
        x=timeline_df['Kick-Off Date'],
        y=timeline_df['Defect ID'],
        mode='markers',
        name='Kick-off',
        marker=dict(size=10, color='blue')
    ))
    
    # Add expected completion dates
    completion_df = timeline_df[timeline_df['Expected DE Completion'].notna()]
    fig.add_trace(go.Scatter(
        x=completion_df['Expected DE Completion'],
        y=completion_df['Defect ID'],
        mode='markers',
        name='Expected Completion',
        marker=dict(size=10, color='green', symbol='square')
    ))
    
    # Connect with lines
    for _, row in completion_df.iterrows():
        if pd.notna(row['Expected DE Completion']):
            fig.add_trace(go.Scatter(
                x=[row['Kick-Off Date'], row['Expected DE Completion']],
                y=[row['Defect ID'], row['Defect ID']],
                mode='lines',
                line=dict(color='lightgray', width=1),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    fig.update_layout(
        title="Project Timeline (Recent 20 Projects)",
        xaxis_title="Date",
        yaxis_title="Project ID",
        height=500,
        showlegend=True
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
    st.title("📋 MDICI Project Tracker")
    
    # Show data source info
    st.caption("📊 Cloud Version - Data from CSV exports")
    
    # Load data with progress indicator
    with st.spinner("Loading exported project data..."):
        df = load_project_data()
        performance_df = load_completed_performance()
    
    if df.empty:
        st.error("No data available. Please check your CSV files.")
        st.info("💡 Make sure you've uploaded the exported CSV files to your storage location.")
        return
    
    # Show database summary with correct logic
    total_projects = len(df)
    # Only count "Intake" projects with placeholder dates as "awaiting kickoff info"
    awaiting_kickoff = len(df[(df['Kick-Off Date'] == '1900-01-01') & (df['Project State'] == 'Intake')])
    
    # Compact info bar
    if 'Export Date' in df.columns and not df['Export Date'].isna().all():
        export_date = df['Export Date'].max()
        export_info = f"📅 Last export: {export_date.strftime('%Y-%m-%d %H:%M')} | "
    else:
        export_info = ""
    
    st.info(f"{export_info}✅ {total_projects:,} total projects ({awaiting_kickoff} awaiting kickoff)", icon="📊")
    
    # Performance Metrics from Completed Projects - Enhanced with 6 and 12 month views
    if not performance_df.empty:
        st.subheader("📊 Recent Performance Metrics")
        
        # Calculate 6 month and 12 month metrics
        from datetime import datetime, timedelta
        now = datetime.now()
        six_months_ago = now - timedelta(days=180)
        twelve_months_ago = now - timedelta(days=365)
        
        # Filter data for different time periods using Actual Go-Live Date (when projects completed)
        if 'Actual Go-Live Date' in performance_df.columns:
            performance_df['Actual Go-Live Date'] = pd.to_datetime(performance_df['Actual Go-Live Date'], errors='coerce')
            perf_6m = performance_df[performance_df['Actual Go-Live Date'] >= six_months_ago]
            perf_12m = performance_df[performance_df['Actual Go-Live Date'] >= twelve_months_ago]
        else:
            # Fallback to all data if no date column available
            perf_6m = performance_df
            perf_12m = performance_df
        
        # 6 month metrics
        st.markdown("**Last 6 Months:**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            avg_to_testing_6m = perf_6m['Days_to_Testing'].mean() if len(perf_6m) > 0 else 0
            st.metric("Kickoff → Testing Info", f"{avg_to_testing_6m:.1f} days", 
                     help="Average days from project kickoff to when testing information is sent to the site")
        with col2:
            avg_to_completion_6m = perf_6m['Days_to_Completion'].mean() if len(perf_6m) > 0 else 0
            st.metric("Kickoff → Completion", f"{avg_to_completion_6m:.1f} days",
                     help="Average total project duration from kickoff to go-live date")
        with col3:
            # Calculate Testing Info → Completion (new metric)
            testing_to_completion_6m = perf_6m['Days_to_Completion'] - perf_6m['Days_to_Testing'] 
            avg_testing_to_completion_6m = testing_to_completion_6m.dropna().mean() if len(perf_6m) > 0 else 0
            st.metric("Testing Info → Completion", f"{avg_testing_to_completion_6m:.1f} days",
                     help="Average days from when testing info is sent until project goes live (site testing & implementation phase)")
        with col4:
            sla_met_6m = len(perf_6m[perf_6m['Days_to_Testing'] <= 21]) if len(perf_6m) > 0 else 0
            sla_rate_6m = (sla_met_6m / len(perf_6m) * 100) if len(perf_6m) > 0 else 0
            st.metric("SLA Met Rate (≤21 days)", f"{sla_rate_6m:.1f}%",
                     help="Percentage of projects that met the 21-day SLA from kickoff to testing info sent")
        
        # 12 month metrics  
        st.markdown("**Last 12 Months:**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            avg_to_testing_12m = perf_12m['Days_to_Testing'].mean() if len(perf_12m) > 0 else 0
            st.metric("Kickoff → Testing Info", f"{avg_to_testing_12m:.1f} days",
                     help="Average days from project kickoff to when testing information is sent to the site")
        with col2:
            avg_to_completion_12m = perf_12m['Days_to_Completion'].mean() if len(perf_12m) > 0 else 0
            st.metric("Kickoff → Completion", f"{avg_to_completion_12m:.1f} days",
                     help="Average total project duration from kickoff to go-live date")
        with col3:
            # Calculate Testing Info → Completion (new metric)
            testing_to_completion_12m = perf_12m['Days_to_Completion'] - perf_12m['Days_to_Testing']
            avg_testing_to_completion_12m = testing_to_completion_12m.dropna().mean() if len(perf_12m) > 0 else 0
            st.metric("Testing Info → Completion", f"{avg_testing_to_completion_12m:.1f} days",
                     help="Average days from when testing info is sent until project goes live (site testing & implementation phase)")
        with col4:
            sla_met_12m = len(perf_12m[perf_12m['Days_to_Testing'] <= 21]) if len(perf_12m) > 0 else 0
            sla_rate_12m = (sla_met_12m / len(perf_12m) * 100) if len(perf_12m) > 0 else 0
            st.metric("SLA Met Rate (≤21 days)", f"{sla_rate_12m:.1f}%",
                     help="Percentage of projects that met the 21-day SLA from kickoff to testing info sent")
    
    # Search & Filter section - moved above data grid for better UX
    st.markdown("---")
    st.subheader("🔍 Search & Filter")
    
    # Row 1: Main search inputs
    search_col1, search_col2, search_col3, search_col4 = st.columns(4)
    
    with search_col1:
        defect_search = st.text_input(
            "Defect ID:",
            placeholder="Enter ID...",
            help="Search by Defect ID",
            key="top_defect_search"
        )
    
    with search_col2:
        opw_search = st.text_input(
            "OPW Description:",
            placeholder="Keywords...",
            help="Search in project descriptions",
            key="top_opw_search"
        )
    
    with search_col3:
        ip_search = st.text_input(
            "IP Address:",
            placeholder="IP or partial...",
            help="Find IP addresses in project details",
            key="top_ip_search"
        )
    
    with search_col4:
        if st.button("🧹 Clear All", use_container_width=True, key="top_clear_button"):
            # Clear all session state and rerun
            for key in list(st.session_state.keys()):
                if key.startswith('top_') or key in ['selected_states']:
                    del st.session_state[key]
            st.session_state.selected_states = ['Design', 'Firewall']
            st.rerun()
    
    # Row 2: Additional filters
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
    
    with filter_col1:
        facilities = ['All'] + sorted(df['Facility'].dropna().unique().tolist())
        selected_facility = st.selectbox("Facility:", facilities)
    
    with filter_col2:
        service_lines = ['All'] + sorted(df['Service Line'].dropna().unique().tolist())
        selected_service_line = st.selectbox("Service Line:", service_lines)
    
    with filter_col3:
        asa_options = ['All'] + sorted([
            asa.strip() for asa_list in df['ASA Assigned'].dropna().unique() 
            for asa in str(asa_list).split('/') if asa.strip() and asa.strip() != 'nan'
        ])
        selected_asa = st.selectbox("ASA Assigned:", asa_options)
    
    # Row 3: Project state and other essential filters
    state_col1, state_col2, state_col3, state_col4 = st.columns(4)
    
    with state_col1:
        # Project State filter
        project_states = sorted(df['Project State'].unique())
        if 'selected_states' not in st.session_state:
            st.session_state.selected_states = ['Design', 'Firewall']
        
        selected_states = st.multiselect(
            "Project States:",
            options=project_states,
            default=st.session_state.selected_states
        )
        if selected_states:
            st.session_state.selected_states = selected_states
    
    with state_col2:
        engineers = ['All'] + sorted(df['Design Engineer'].dropna().unique().tolist())
        selected_engineer = st.selectbox("Design Engineer:", engineers)
    
    with state_col3:
        # Quick filter buttons - expanded with saved presets
        st.write("**Quick Filters:**")
        button_col1, button_col2 = st.columns(2)
        with button_col1:
            if st.button("🎯 Active Only", help="Design, Firewall, Testing states", use_container_width=True):
                st.session_state.selected_states = ['Design', 'Firewall', 'Testing']
                st.rerun()
            if st.button("⏳ Intake Only", help="Projects awaiting kickoff", use_container_width=True):
                st.session_state.selected_states = ['Intake']
                st.rerun()
            if st.button("📋 All Projects", help="Show all project states", use_container_width=True):
                project_states = sorted(df['Project State'].unique())
                st.session_state.selected_states = project_states
                st.rerun()
        with button_col2:
            if st.button("🚨 Critical/Overdue", help="Overdue + Attention Needed projects", use_container_width=True):
                # Filter for overdue and attention needed projects
                st.session_state.selected_states = ['Design', 'Firewall', 'Testing']
                st.session_state.filter_critical = True
                st.rerun()
            if st.button("📅 This Week's Kickoffs", help="Projects with kickoffs in next 7 days", use_container_width=True):
                st.session_state.selected_states = ['Design', 'Firewall', 'Testing', 'Intake']
                st.session_state.filter_week_kickoffs = True
                st.rerun()
            if st.button("🔄 Reset Filters", help="Clear all filters", use_container_width=True):
                for key in list(st.session_state.keys()):
                    if key.startswith('filter_') or key.startswith('top_'):
                        del st.session_state[key]
                st.session_state.selected_states = ['Design', 'Firewall']
                st.rerun()
    
    with state_col4:
        # Keep this empty or add something else if needed
        st.write("")  # Placeholder
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_states:
        filtered_df = filtered_df[filtered_df['Project State'].isin(selected_states)]
    
    if selected_engineer != 'All':
        filtered_df = filtered_df[filtered_df['Design Engineer'] == selected_engineer]
    
    
    # Apply special preset filters
    if st.session_state.get('filter_critical', False):
        # Filter for Critical/Overdue projects
        filtered_df = filtered_df[filtered_df['Status'].isin(['Overdue', 'Attention Needed'])]
        st.session_state.filter_critical = False  # Reset after applying
    
    if st.session_state.get('filter_week_kickoffs', False):
        # Filter for this week's kickoffs (next 7 days)
        from datetime import datetime, timedelta
        today = datetime.now().date()
        week_from_now = today + timedelta(days=7)
        
        # Convert Kick-Off Date to datetime
        filtered_df['Kick-Off Date'] = pd.to_datetime(filtered_df['Kick-Off Date'], errors='coerce')
        
        # Filter for kickoffs between today and 7 days from now
        mask = (filtered_df['Kick-Off Date'].dt.date >= today) & (filtered_df['Kick-Off Date'].dt.date <= week_from_now)
        filtered_df = filtered_df[mask]
        st.session_state.filter_week_kickoffs = False  # Reset after applying
    
    # Apply all filters
    if defect_search:
        mask = filtered_df['Defect ID'].astype(str).str.contains(defect_search, case=False, na=False)
        filtered_df = filtered_df[mask]
    
    if selected_facility != 'All':
        filtered_df = filtered_df[filtered_df['Facility'] == selected_facility]
    
    if selected_service_line != 'All':
        filtered_df = filtered_df[filtered_df['Service Line'] == selected_service_line]
    
    if selected_asa != 'All':
        mask = filtered_df['ASA Assigned'].astype(str).str.contains(selected_asa, case=False, na=False)
        filtered_df = filtered_df[mask]
    
    if opw_search:
        mask = filtered_df['OPW'].astype(str).str.contains(opw_search, case=False, na=False)
        filtered_df = filtered_df[mask]
    
    if ip_search:
        opw_mask = filtered_df['OPW'].astype(str).str.contains(ip_search, case=False, na=False)
        comments_mask = filtered_df['Comments'].astype(str).str.contains(ip_search, case=False, na=False)
        combined_mask = opw_mask | comments_mask
        filtered_df = filtered_df[combined_mask]
    
    # Compact active filters summary
    active_filters = []
    if selected_states != sorted(df['Project State'].unique()):
        active_filters.append(f"States: {len(selected_states)}")
    if selected_engineer != 'All':
        active_filters.append(f"Engineer: {selected_engineer}")
    if defect_search:
        active_filters.append(f"ID: {defect_search}")
    if selected_facility != 'All':
        active_filters.append(f"Facility: {selected_facility}")
    if selected_service_line != 'All':
        active_filters.append(f"Service: {selected_service_line}")
    if selected_asa != 'All':
        active_filters.append(f"ASA: {selected_asa}")
    if opw_search:
        active_filters.append(f"OPW: {opw_search}")
    if ip_search:
        active_filters.append(f"IP: {ip_search}")
    
    if active_filters:
        st.success(f"🎯 **{len(filtered_df)} projects** | Filters: {' • '.join(active_filters)}", icon="🔍")
    
    # Visual Alert Box for Critical Projects
    overdue_projects = filtered_df[filtered_df['Status'] == 'Overdue']
    attention_projects = filtered_df[filtered_df['Status'] == 'Attention Needed']
    
    if len(overdue_projects) > 0 or len(attention_projects) > 0:
        alert_col1, alert_col2 = st.columns(2)
        with alert_col1:
            if len(overdue_projects) > 0:
                st.error(f"🚨 **{len(overdue_projects)} OVERDUE PROJECTS** - Immediate attention required!")
        with alert_col2:
            if len(attention_projects) > 0:
                st.warning(f"⚠️ **{len(attention_projects)} projects need attention** - Approaching SLA deadline")
    
    # Key Metrics - Only for Design projects for SLA tracking
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
        # Only count overdue for Design projects (SLA only applies to them)
        overdue_count = len(design_projects[design_projects['Status'] == 'Overdue'])
        # Use red color for overdue metric if > 0
        if overdue_count > 0:
            st.metric("🔴 Overdue Design", overdue_count, help="Design projects past 21-day SLA")
        else:
            st.metric("Overdue Design", overdue_count, help="Design projects past 21-day SLA")
    
    with col5:
        # Only urgent Design projects matter for SLA
        urgent = len(design_projects[(design_projects['Days Until SLA'] <= 3) & 
                                   (design_projects['Days Until SLA'].notna())])
        # Use yellow/orange color for urgent if > 0
        if urgent > 0:
            st.metric("🟡 Urgent Design (<3 days)", urgent, help="Design projects near SLA deadline")
        else:
            st.metric("Urgent Design (<3 days)", urgent, help="Design projects near SLA deadline")
    
    # Tabs for different views - added Executive Summary
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Active Projects", "👥 By Engineer", "📝 Detailed View", "📈 Executive Summary"])
    
    with tab1:
        st.subheader("📋 Project Overview")
        
        # Define columns to display - now customizable
        default_columns = [
            'Defect ID',
            'OPW',
            'Design Engineer', 
            'Project State',
            'Kick-Off Date', 
            'Expected DE Completion',
            'Days Since Kickoff', 
            'Testing Info Sent',
            'Facility Updates'
        ]
        
        # Optional columns users can add
        optional_columns = [
            'Days Until SLA', 'Priority', 'Service Line', 'OPW', 
            'Service Area', 'Facility Updates', 'Comments', 'ASA Assigned', 
            'Number of Devices', 'Actual Go-Live Date'
        ]
        
        # Column selector
        with st.expander("🔧 Customize Columns", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Default Columns** (always shown)")
                for col in default_columns:
                    if col in filtered_df.columns:
                        st.write(f"✅ {col}")
            
            with col2:
                additional_cols = st.multiselect(
                    "**Add Optional Columns**",
                    [col for col in optional_columns if col in filtered_df.columns],
                    help="Select additional columns to display"
                )
        
        # Combine columns
        display_columns = default_columns + additional_cols
        display_columns = [col for col in display_columns if col in filtered_df.columns]
        
        # Sort options with Total Projects
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            sort_options = [col for col in display_columns if col in filtered_df.columns]
            default_index = sort_options.index('Defect ID') if 'Defect ID' in sort_options else 0
            sort_column = st.selectbox(
                "Sort by:",
                options=sort_options,
                index=default_index
            )
        with col2:
            sort_ascending = st.radio("Order:", ["Newest First", "Oldest First"], horizontal=True, index=1)
        
        # Sort the dataframe
        sorted_df = filtered_df.sort_values(
            sort_column, 
            ascending=(sort_ascending == "Oldest First"),
            na_position='last'
        )
        
        # Show total projects in the third column
        with col3:
            st.metric("Total Projects", len(sorted_df))
        
        # Display the main table with selection capability
        selected_rows = st.dataframe(
            sorted_df[display_columns],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                "Kick-Off Date": st.column_config.DateColumn(
                    "Kick-Off Date",
                    format="YYYY-MM-DD"
                ),
                "Expected DE Completion": st.column_config.DateColumn(
                    "Expected Completion", 
                    format="YYYY-MM-DD"
                ),
                "Testing Info Sent": st.column_config.DateColumn(
                    "Testing Info Sent",
                    format="YYYY-MM-DD"
                ),
                "Actual Go-Live Date": st.column_config.DateColumn(
                    "Go-Live Date",
                    format="YYYY-MM-DD"
                ),
                "Days Since Kickoff": st.column_config.NumberColumn(
                    "Days Since Kickoff",
                    format="%d days"
                ),
                "Days Until SLA": st.column_config.NumberColumn(
                    "Days Until SLA",
                    format="%d days",
                    help="Negative = Overdue"
                ),
                "Status": st.column_config.TextColumn(
                    "Status",
                    help="Click row below to see full details"
                )
            }
        )
        
        # Show details of selected row
        if selected_rows and len(selected_rows.selection.rows) > 0:
            selected_index = selected_rows.selection.rows[0]
            selected_project = sorted_df.iloc[selected_index]
            
            st.markdown("---")
            st.markdown("### 📋 **Project Details**")
            
            # Create three columns for project details
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**🔍 Basic Info**")
                st.write(f"**Defect ID:** {selected_project['Defect ID']}")
                st.write(f"**Design Engineer:** {selected_project['Design Engineer']}")
                st.write(f"**Status:** {selected_project['Status']}")
                st.write(f"**Priority:** {selected_project.get('Priority', 'N/A')}")
                st.write(f"**Project State:** {selected_project['Project State']}")
                st.write(f"**Service Area:** {selected_project.get('Service Area', 'N/A')}")
                st.write(f"**Service Line:** {selected_project.get('Service Line', 'N/A')}")
            
            with col2:
                st.markdown("**📅 Timeline**")
                st.write(f"**Kick-Off Date:** {selected_project['Kick-Off Date']}")
                st.write(f"**Expected DE Completion:** {selected_project.get('Expected DE Completion', 'N/A')}")
                st.write(f"**Testing Info Sent:** {selected_project.get('Testing Info Sent', 'Not Sent')}")
                st.write(f"**Go-Live Date:** {selected_project.get('Actual Go-Live Date', 'Not Complete')}")
                st.write(f"**Days Since Kickoff:** {selected_project.get('Days Since Kickoff', 'N/A')}")
                if selected_project.get('Days Until SLA'):
                    sla_days = selected_project['Days Until SLA']
                    sla_color = "🔴" if sla_days < 0 else "🟡" if sla_days <= 3 else "🟢"
                    st.write(f"**Days Until SLA:** {sla_color} {sla_days}")
            
            with col3:
                st.markdown("**🔧 Technical Details**")
                st.write(f"**OPW:** {selected_project.get('OPW', 'N/A')}")
                st.write(f"**Number of Devices:** {selected_project.get('Number of Devices', 'N/A')}")
                st.write(f"**ASA Assigned:** {selected_project.get('ASA Assigned', 'N/A')}")
            
            # Show Facility Updates and Comments in full width
            if pd.notna(selected_project.get('Facility Updates')):
                st.markdown("**🏢 Facility Updates**")
                st.markdown(f"```\n{selected_project['Facility Updates']}\n```")
            
            if pd.notna(selected_project.get('Comments')):
                st.markdown("**💬 Comments History**")
                st.markdown(f"```\n{selected_project['Comments']}\n```")
        else:
            st.info("👆 Click on any row in the table above to see detailed project information")
    
    with tab2:
        st.subheader("Projects by Design Engineer")
        
        # Group by engineer and status
        engineer_summary = filtered_df.groupby(['Design Engineer', 'Status']).size().reset_index(name='Count')
        engineer_pivot = engineer_summary.pivot(index='Design Engineer', columns='Status', values='Count').fillna(0)
        
        # Display summary table
        st.dataframe(engineer_pivot, use_container_width=True)
        
        # Show workload for each engineer
        st.subheader("Engineer Workload Details")
        for engineer in filtered_df['Design Engineer'].dropna().unique():
            eng_df = filtered_df[filtered_df['Design Engineer'] == engineer]
            
            with st.expander(f"{engineer} - {len(eng_df)} projects"):
                # Show urgent projects first
                urgent_eng = eng_df[eng_df['Status'].isin(['Overdue', 'Attention Needed'])]
                if not urgent_eng.empty:
                    st.warning(f"⚠️ {len(urgent_eng)} projects need attention")
                
                st.dataframe(
                    eng_df[['Defect ID', 'Status', 'Days Until SLA', 'Priority', 'Service Area']],
                    use_container_width=True,
                    hide_index=True
                )
    
    with tab3:
        st.subheader("Detailed Project View with Comments")
        
        # Select a specific project to view details
        project_ids = filtered_df['Defect ID'].unique()
        selected_project_id = st.selectbox("Select Project", project_ids)
        
        if selected_project_id:
            project = filtered_df[filtered_df['Defect ID'] == selected_project_id].iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Project Information**")
                st.write(f"**Defect ID:** {project['Defect ID']}")
                st.write(f"**Design Engineer:** {project['Design Engineer']}")
                st.write(f"**Status:** {project['Status']}")
                st.write(f"**Priority:** {project['Priority']}")
                st.write(f"**Project State:** {project['Project State']}")
                st.write(f"**Service Area:** {project['Service Area']}")
                st.write(f"**Service Line:** {project['Service Line']}")
            
            with col2:
                st.markdown("**Timeline**")
                st.write(f"**Kick-Off Date:** {project['Kick-Off Date']}")
                st.write(f"**Expected Completion:** {project['Expected DE Completion']}")
                st.write(f"**Days Since Kickoff:** {project['Days Since Kickoff']}")
                st.write(f"**Days Until SLA:** {project['Days Until SLA']}")
                st.write(f"**OPW:** {project['OPW']}")
                st.write(f"**Number of Devices:** {project['Number of Devices']}")
            
            # Display Facility Updates
            if pd.notna(project['Facility Updates']):
                st.markdown("**Facility Updates**")
                st.markdown(f"```\n{project['Facility Updates']}\n```")
            
            # Display Comments with proper formatting
            if pd.notna(project['Comments']):
                st.markdown("**Comments History**")
                st.markdown(f"```\n{project['Comments']}\n```")
    
    with tab4:
        st.subheader("📈 Executive Summary")
        
        # Overall project distribution
        exec_col1, exec_col2 = st.columns(2)
        
        with exec_col1:
            st.markdown("### 🏢 Active Projects by Service Area")
            # Get active projects only (excluding Complete/Cancelled and Enterprise placeholder)
            active_df = df[
                (~df['Project State'].isin(['Complete', 'Cancelled'])) &
                (df['Service Area'] != 'Enterprise')
            ]
            service_area_counts = active_df['Service Area'].value_counts()
            
            # Display as a bar chart
            import plotly.express as px
            fig_area = px.bar(
                x=service_area_counts.values,
                y=service_area_counts.index,
                orientation='h',
                title=f"Total Active Projects by Service Area ({len(active_df)} total)",
                labels={'x': 'Number of Projects', 'y': 'Service Area'},
                color=service_area_counts.values,
                color_continuous_scale='Blues'
            )
            fig_area.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_area, use_container_width=True)
        
        with exec_col2:
            st.markdown("### 🔬 Active Projects by Service Line")
            service_line_counts = active_df['Service Line'].value_counts()
            
            # Display as a pie chart
            fig_line = px.pie(
                values=service_line_counts.values,
                names=service_line_counts.index,
                title=f"Distribution by Service Line ({len(active_df)} total)",
                hole=0.4
            )
            fig_line.update_traces(textposition='inside', textinfo='percent+label')
            fig_line.update_layout(height=400)
            st.plotly_chart(fig_line, use_container_width=True)
        
        # SLA Compliance Trending
        st.markdown("### 📊 SLA Compliance Trends")
        if not performance_df.empty:
            # Group by month and calculate SLA rate
            performance_df['Actual Go-Live Date'] = pd.to_datetime(performance_df['Actual Go-Live Date'], errors='coerce')
            performance_df['Month'] = performance_df['Actual Go-Live Date'].dt.to_period('M')
            
            monthly_sla = performance_df.groupby('Month').apply(
                lambda x: (len(x[x['Days_to_Testing'] <= 21]) / len(x) * 100) if len(x) > 0 else 0
            ).reset_index(name='SLA_Rate')
            
            # Convert Period to string for display
            monthly_sla['Month'] = monthly_sla['Month'].astype(str)
            
            # Create line chart
            fig_sla = px.line(
                monthly_sla,
                x='Month',
                y='SLA_Rate',
                title="Monthly SLA Compliance Rate (≤21 days)",
                markers=True
            )
            fig_sla.add_hline(y=90, line_dash="dash", line_color="green", annotation_text="Target: 90%")
            fig_sla.update_layout(
                yaxis_title="SLA Compliance %",
                xaxis_title="Month",
                height=350
            )
            st.plotly_chart(fig_sla, use_container_width=True)
        
        # Top Bottlenecks (active_df already excludes Enterprise)
        st.markdown("### ⚠️ Current Bottlenecks")
        st.caption("Excludes Enterprise placeholder projects")
        bottleneck_col1, bottleneck_col2, bottleneck_col3 = st.columns(3)
        
        with bottleneck_col1:
            # Projects stuck in Firewall
            firewall_df = active_df[active_df['Project State'] == 'Firewall']
            st.metric("🔥 Stuck in Firewall", len(firewall_df), 
                     help="Projects waiting for firewall configuration")
        
        with bottleneck_col2:
            # Projects in Testing > 30 days
            testing_df = active_df[active_df['Project State'] == 'Testing']
            if 'Days Since Kickoff' in testing_df.columns:
                long_testing = testing_df[testing_df['Days Since Kickoff'] > 30]
                st.metric("🧪 Long Testing (>30 days)", len(long_testing),
                         help="Projects in testing phase for over 30 days")
            else:
                st.metric("🧪 In Testing", len(testing_df))
        
        with bottleneck_col3:
            # Intake without kickoff
            intake_df = active_df[(active_df['Project State'] == 'Intake') & 
                                 (active_df['Kick-Off Date'] == '1900-01-01')]
            st.metric("📥 Awaiting Kickoff", len(intake_df),
                     help="Intake projects without kickoff date")
        
        # MODULAR SECTION: Engineer Performance Over Time (3-year rolling)
        # This section can be easily removed by deleting/commenting from here to END MODULAR SECTION
        st.markdown("---")
        with st.expander("👥 Engineer Performance Over Time (3-Year Rolling)", expanded=False):
            st.markdown("### Historical Engineer Performance Analysis")
            st.caption("Shows ACTUAL DE performance (Kick-Off to Testing Info Sent) - Excludes Enterprise and No Resource")
            
            # Use main dataset for complete engineer data
            # Filter for last 3 years and completed projects
            from datetime import datetime, timedelta
            three_years_ago = datetime.now() - timedelta(days=365*3)
            
            # Convert dates
            df_analysis = df.copy()
            df_analysis['Actual Go-Live Date'] = pd.to_datetime(df_analysis['Actual Go-Live Date'], errors='coerce')
            df_analysis['Kick-Off Date'] = pd.to_datetime(df_analysis['Kick-Off Date'], errors='coerce')
            
            # Use DE Completion Date if available, otherwise fall back to Testing Info Sent
            if 'DE Completion Date' in df_analysis.columns:
                df_analysis['DE Completion Date'] = pd.to_datetime(df_analysis['DE Completion Date'], errors='coerce')
                actual_completion_col = 'DE Completion Date'
                st.caption("Using ACTUAL DE Completion Date from database - Excludes Enterprise and No Resource")
            else:
                df_analysis['Testing Info Sent'] = pd.to_datetime(df_analysis['Testing Info Sent'], errors='coerce')
                actual_completion_col = 'Testing Info Sent'
                st.caption("Using Testing Info Sent as proxy for DE completion - Excludes Enterprise and No Resource")
            
            # Filter: Last 3 years, completed projects, exclude Enterprise and No Resource
            perf_3yr = df_analysis[
                (df_analysis['Actual Go-Live Date'] >= three_years_ago) &
                (df_analysis['Project State'].isin(['Complete', 'Security'])) &
                (df_analysis['Service Area'] != 'Enterprise') &
                (df_analysis['Design Engineer'] != 'No Resource') &
                (df_analysis['Design Engineer'] != 'Not Applicable') &
                (df_analysis['Design Engineer'].notna())
            ]
            
            if len(perf_3yr) > 0:
                # Calculate ACTUAL Days from Kick-Off to DE Completion
                perf_3yr['Days_to_DE_Completion'] = (perf_3yr[actual_completion_col] - perf_3yr['Kick-Off Date']).dt.days
                
                # Filter out invalid dates and missing completion dates
                perf_3yr = perf_3yr[
                    (perf_3yr['Kick-Off Date'] > '1950-01-01') &
                    (perf_3yr[actual_completion_col].notna())
                ]
                
                if len(perf_3yr) > 0:
                    # Calculate metrics by engineer
                    engineer_metrics = perf_3yr.groupby('Design Engineer').agg({
                        'Days_to_DE_Completion': 'mean',
                        'Days to Completion': lambda x: x.dropna().mean() if len(x.dropna()) > 0 else 0,
                        'Defect ID': 'count'
                    }).reset_index()
                    
                    engineer_metrics.columns = ['Design Engineer', 'Avg Days to DE Completion', 'Avg Days to Project Completion', 'Projects Completed']
                    
                    # Calculate SLA compliance rate per engineer (21 days to DE Completion)
                    sla_compliance = perf_3yr.groupby('Design Engineer').apply(
                        lambda x: (len(x[x['Days_to_DE_Completion'] <= 21]) / len(x) * 100) if len(x) > 0 else 0
                    ).reset_index(name='SLA Compliance %')
                    
                    # Merge metrics
                    engineer_metrics = pd.merge(engineer_metrics, sla_compliance, on='Design Engineer')
                    
                    # Sort by SLA compliance
                    engineer_metrics = engineer_metrics.sort_values('SLA Compliance %', ascending=False)
                    
                    # Display metrics
                    perf_col1, perf_col2 = st.columns(2)
                    
                    with perf_col1:
                        # Bar chart of SLA compliance
                        fig_eng_sla = px.bar(
                            engineer_metrics.head(15),  # Top 15 engineers
                            x='SLA Compliance %',
                            y='Design Engineer',
                            orientation='h',
                            title="SLA Compliance by Engineer (Top 15)",
                            color='SLA Compliance %',
                            color_continuous_scale='RdYlGn',
                            range_color=[0, 100]
                        )
                        fig_eng_sla.add_vline(x=90, line_dash="dash", line_color="green", annotation_text="Target")
                        fig_eng_sla.update_layout(height=400)
                        st.plotly_chart(fig_eng_sla, use_container_width=True)
                    
                    with perf_col2:
                        # Scatter plot of volume vs performance
                        fig_eng_vol = px.scatter(
                            engineer_metrics,
                            x='Projects Completed',
                            y='Avg Days to DE Completion',
                            size='SLA Compliance %',
                            color='SLA Compliance %',
                            hover_data=['Design Engineer'],
                            title="Volume vs DE Performance (3-Year)",
                            color_continuous_scale='RdYlGn',
                            range_color=[0, 100]
                        )
                        fig_eng_vol.add_hline(y=21, line_dash="dash", line_color="red", annotation_text="21-Day SLA")
                        fig_eng_vol.update_layout(
                            height=400,
                            yaxis_title="Avg Days to DE Completion",
                            xaxis_title="Projects Completed"
                        )
                        st.plotly_chart(fig_eng_vol, use_container_width=True)
                    
                    # Detailed table
                    st.markdown("#### Detailed Engineer Metrics (3-Year Rolling)")
                    st.caption("Based on ACTUAL completion dates (Testing Info Sent) - Excludes Enterprise service area and No Resource assignments")
                    st.dataframe(
                        engineer_metrics.round(1),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Avg Days to DE Completion": st.column_config.NumberColumn(format="%.1f days"),
                            "Avg Days to Project Completion": st.column_config.NumberColumn(format="%.1f days"),
                            "SLA Compliance %": st.column_config.ProgressColumn(
                                min_value=0,
                                max_value=100,
                                format="%.1f%%"
                            ),
                            "Projects Completed": st.column_config.NumberColumn(format="%d")
                        }
                    )
                else:
                    st.info("No valid performance data available (excluding placeholder dates)")
            else:
                st.info("No completed projects in the last 3 years (excluding Enterprise and No Resource)")
        # END MODULAR SECTION: Engineer Performance Over Time
    
    # Footer
    st.markdown("---")
    if 'Export Date' in df.columns and not df['Export Date'].isna().all():
        export_date = df['Export Date'].max()
        st.caption(f"Data exported: {export_date.strftime('%Y-%m-%d %H:%M:%S')} | Auto-refreshes when new data is uploaded")
    else:
        st.caption("Cloud version - updates when new CSV files are uploaded")

if __name__ == "__main__":
    main()