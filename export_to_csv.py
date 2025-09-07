"""
MDICI Data Export Script
Exports database data to CSV for Streamlit Cloud deployment
Run this daily/weekly to keep exported data current
"""

import pandas as pd
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
from bs4 import BeautifulSoup
import re
import os
import socket
import urllib.parse

def clean_html_content(text):
    """Clean HTML content from text fields while preserving all text and proper spacing"""
    if pd.isna(text) or not isinstance(text, str):
        return text
   
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')
   
    # Replace <br> and </p> tags with newlines before extracting text
    for br in soup.find_all("br"):
        br.replace_with("\n")
    
    for p in soup.find_all("p"):
        # Add newline after each paragraph
        p.append("\n")
   
    # Get all text content, preserving line breaks
    cleaned_text = soup.get_text()
    
    # Clean up the text while preserving structure
    lines = cleaned_text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line:  # Only add non-empty lines
            cleaned_lines.append(line)
    
    # Join lines with single newlines, but add extra spacing between comment entries
    result = '\n'.join(cleaned_lines)
    
    # Add double newlines between different comment entries (timestamp patterns)
    # This will separate each comment block for better readability
    result = re.sub(r'\n(\w+\s+\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', r'\n\n\1', result)
    
    return result.strip()

def calculate_third_friday(kick_off_date):
    """Calculate the third Friday after the kick-off date"""
    if pd.isna(kick_off_date) or not kick_off_date:
        return None
    
    # Convert to date if datetime
    if hasattr(kick_off_date, 'date'):
        current_date = kick_off_date.date()
    else:
        current_date = kick_off_date
    
    friday_count = 0
    
    while friday_count < 3:
        current_date += timedelta(days=1)
        if current_date.weekday() == 4:  # Friday is 4
            friday_count += 1
    
    return current_date

def get_database_connection():
    """Get database connection based on environment"""
    hostname = socket.gethostname().upper()
    
    # Auto-detect environment
    if 'NZXT' in hostname:
        server_name = "NZXT\\SQLEXPRESS"
        print("Using TEST environment")
    else:
        server_name = "PHX-SQL-117\\SQL2019"
        print("Using PRODUCTION environment")
    
    # Create connection string
    params = urllib.parse.quote_plus(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server_name};"
        f"DATABASE=mdici;"
        f"Trusted_Connection=yes;"
    )
    
    connection_string = f"mssql+pyodbc:///?odbc_connect={params}"
    return create_engine(connection_string, fast_executemany=True, pool_pre_ping=True)

def export_all_data():
    """Export all project data to CSV with calculations"""
    print("Connecting to database...")
    engine = get_database_connection()
    
    # Query to get ALL projects
    query = """
        SELECT [Design Engineer], [Defect ID], [Priority], [Service Area],
        Facility, [Project State], [Service Line], [Kick-Off Date],
        OPW, [Number of Devices], [Facility Updates], [ASA Assigned], Comments,
        [Testing Info Sent], [Actual Go-Live Date]
        FROM MDICI.dbo.defects
        ORDER BY 
            CASE 
                WHEN [Kick-Off Date] = '1900-01-01' THEN 0  -- Show placeholder dates first
                ELSE 1 
            END,
            [Kick-Off Date] DESC
    """
    
    print("Loading project data...")
    df = pd.read_sql(query, engine)
    
    print(f"SUCCESS: Loaded {len(df)} projects from database")
    
    # Clean HTML from text columns
    print("Cleaning HTML content...")
    df['Comments'] = df['Comments'].apply(clean_html_content)
    if 'Facility Updates' in df.columns:
        df['Facility Updates'] = df['Facility Updates'].apply(clean_html_content)
    
    # Calculate days since kickoff
    print("Calculating dates...")
    df['Days Since Kickoff'] = df['Kick-Off Date'].apply(
        lambda x: (date.today() - x.date()).days if pd.notna(x) and hasattr(x, 'date') else None
    )
    
    # Calculate expected completion date
    df['Expected DE Completion'] = df['Kick-Off Date'].apply(calculate_third_friday)
    
    # Calculate status based on project state and days
    def get_status(row):
        project_state = row['Project State']
        days = row['Days Since Kickoff']
        
        # Only calculate SLA status for Design projects
        if project_state == 'Design':
            if days is None:
                return "No Kickoff Date"
            elif days <= 14:
                return "On Track"
            elif days <= 21:
                return "Attention Needed"
            else:
                return "Overdue"
        elif project_state == 'Firewall':
            return "Waiting for Firewall"
        elif project_state == 'Testing':
            return "Pending Updates from Site"
        elif project_state == 'Intake':
            return "In Intake Process"
        elif project_state == 'Hold':
            return "On Hold"
        elif project_state in ['Complete', 'Security']:
            return "Completed"
        else:
            return project_state  # Fallback to project state
    
    df['Status'] = df.apply(get_status, axis=1)
    
    # Calculate days until SLA (only for Design projects)
    df['Days Until SLA'] = df.apply(
        lambda row: (row['Expected DE Completion'] - date.today()).days 
        if pd.notna(row['Expected DE Completion']) and row['Project State'] == 'Design'
        else None, axis=1
    )
    
    # Calculate performance metrics for completed designs
    df['Days to Testing Info Sent'] = df.apply(
        lambda row: (row['Testing Info Sent'] - row['Kick-Off Date']).days 
        if pd.notna(row['Testing Info Sent']) and pd.notna(row['Kick-Off Date'])
        else None, axis=1
    )
    
    df['Days to Completion'] = df.apply(
        lambda row: (row['Actual Go-Live Date'] - row['Kick-Off Date']).days 
        if pd.notna(row['Actual Go-Live Date']) and pd.notna(row['Kick-Off Date'])
        else None, axis=1
    )
    
    # Add export metadata
    df['Export Date'] = datetime.now()
    df['Export Source'] = socket.gethostname()
    
    return df

def export_performance_data():
    """Export performance metrics for completed projects"""
    print("Loading performance data...")
    engine = get_database_connection()
    
    query = """
        SELECT [Design Engineer], [Defect ID], [Kick-Off Date], [Testing Info Sent], [Actual Go-Live Date],
        DATEDIFF(day, [Kick-Off Date], [Testing Info Sent]) as Days_to_Testing,
        DATEDIFF(day, [Kick-Off Date], [Actual Go-Live Date]) as Days_to_Completion
        FROM MDICI.dbo.defects
        WHERE [Project State] IN ('Complete', 'Security')
        AND [Kick-Off Date] IS NOT NULL
        AND [Testing Info Sent] IS NOT NULL
        AND [Kick-Off Date] >= DATEADD(month, -6, GETDATE())  -- Last 6 months
    """
    
    df = pd.read_sql(query, engine)
    df['Export Date'] = datetime.now()
    return df

def main():
    """Main export function"""
    try:
        print("Starting MDICI Data Export")
        print("=" * 50)
        
        # Create output directory
        output_dir = "exported_data"
        os.makedirs(output_dir, exist_ok=True)
        
        # Export main project data
        projects_df = export_all_data()
        
        # Export performance data
        performance_df = export_performance_data()
        
        # Generate filenames with timestamps
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        projects_file = f"{output_dir}/mdici_projects_{timestamp}.csv"
        performance_file = f"{output_dir}/mdici_performance_{timestamp}.csv"
        
        # Also create "latest" versions for Streamlit to use
        latest_projects = f"{output_dir}/mdici_projects_latest.csv"
        latest_performance = f"{output_dir}/mdici_performance_latest.csv"
        
        # Save files
        print(f"Saving to {projects_file}...")
        projects_df.to_csv(projects_file, index=False)
        projects_df.to_csv(latest_projects, index=False)
        
        print(f"Saving to {performance_file}...")
        performance_df.to_csv(performance_file, index=False)
        performance_df.to_csv(latest_performance, index=False)
        
        # Print summary
        print("\n" + "=" * 50)
        print("SUCCESS: Export Complete!")
        print(f"Projects exported: {len(projects_df)}")
        print(f"Performance records: {len(performance_df)}")
        print(f"Files created in: {output_dir}/")
        print("\nFiles created:")
        print(f"   - {projects_file}")
        print(f"   - {latest_projects}")
        print(f"   - {performance_file}")
        print(f"   - {latest_performance}")
        
        # Show summary stats
        design_projects = len(projects_df[projects_df['Project State'] == 'Design'])
        awaiting_kickoff = len(projects_df[(projects_df['Kick-Off Date'] == '1900-01-01') & 
                                          (projects_df['Project State'] == 'Intake')])
        
        print(f"\nData Summary:")
        print(f"   - Total projects: {len(projects_df)}")
        print(f"   - Active Design projects: {design_projects}")
        print(f"   - Awaiting kickoff info: {awaiting_kickoff}")
        
        print(f"\nNext Steps:")
        print(f"   1. Upload '{latest_projects}' to your cloud storage")
        print(f"   2. Update Streamlit app to read from CSV instead of database")
        print(f"   3. Deploy to Streamlit Cloud")
        print(f"   4. Schedule this script to run daily/weekly")
        
    except Exception as e:
        print(f"ERROR: Export failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()