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
    st.title("📋 MDICI Design Project Tracker")
    
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
    
    # Show export info
    if 'Export Date' in df.columns and not df['Export Date'].isna().all():
        export_date = df['Export Date'].max()
        st.info(f"📅 Data last exported: {export_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    st.success(f"✅ Loaded {total_projects:,} total projects ({awaiting_kickoff} awaiting kickoff info)")
    
    # Sidebar filters
    with st.sidebar:
        st.header("Filters")
        
        # Project State filter - now includes all states for historical view
        st.subheader("Project State")
        project_states = sorted(df['Project State'].unique())
        
        # Separate active vs completed for easier selection
        active_states = [s for s in project_states if s in ['Design', 'Firewall', 'Testing', 'Intake', 'Hold']]
        completed_states = [s for s in project_states if s in ['Complete', 'Security']]
        
        # Quick filter buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🎯 Active Only", use_container_width=True):
                st.session_state.selected_states = active_states
        with col2:
            if st.button("⏳ Awaiting Kickoff", use_container_width=True, help="Intake projects awaiting kickoff info"):
                st.session_state.selected_states = ['Intake']
                st.session_state.date_filter = "Awaiting kickoff (1900-01-01)"
        with col3:
            if st.button("📋 All Projects", use_container_width=True):
                st.session_state.selected_states = project_states
                st.session_state.show_placeholders = False
        
        # Initialize session state if not exists
        if 'selected_states' not in st.session_state:
            st.session_state.selected_states = ['Design', 'Firewall']  # Default to active Design/Firewall
        
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
    
    # Apply filters
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
        # Convert to string and search (case insensitive)
        mask = filtered_df['Defect ID'].astype(str).str.contains(defect_search, case=False, na=False)
        filtered_df = filtered_df[mask]
        
        # If exact match found, highlight it in the UI
        if len(filtered_df) == 1:
            st.success(f"✅ Found exact match: Defect ID {defect_search}")
        elif len(filtered_df) > 1:
            st.info(f"🔍 Found {len(filtered_df)} projects matching '{defect_search}'")
        else:
            st.warning(f"❌ No projects found matching '{defect_search}'")
    
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
        st.metric("Overdue Design", overdue_count, help="Design projects past 21-day SLA")
    
    with col5:
        # Only urgent Design projects matter for SLA
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
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Active Projects", "👥 By Engineer", "📝 Detailed View"])
    
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
        
        # Sort options
        col1, col2 = st.columns(2)
        with col1:
            sort_column = st.selectbox(
                "Sort by:",
                options=[col for col in display_columns if col in filtered_df.columns],
                index=5 if 'Days Since Kickoff' in display_columns else 0
            )
        with col2:
            sort_ascending = st.radio("Order:", ["Newest First", "Oldest First"], horizontal=True)
        
        # Sort the dataframe
        sorted_df = filtered_df.sort_values(
            sort_column, 
            ascending=(sort_ascending == "Oldest First"),
            na_position='last'
        )
        
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
        
        # Download and summary section
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            csv = sorted_df[display_columns].to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"MDICI_Projects_{date.today()}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            st.metric("Total Projects", len(sorted_df))
    
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
    
    # Footer
    st.markdown("---")
    if 'Export Date' in df.columns and not df['Export Date'].isna().all():
        export_date = df['Export Date'].max()
        st.caption(f"Data exported: {export_date.strftime('%Y-%m-%d %H:%M:%S')} | Auto-refreshes when new data is uploaded")
    else:
        st.caption("Cloud version - updates when new CSV files are uploaded")

if __name__ == "__main__":
    main()