import pyodbc
import pandas as pd
import matplotlib.pyplot as plt

# Database connection details using your provided connection string
conn_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=NZXT\\SQLExpress;"
    #"SERVER=PHX-SQL-117\\SQL2019;"
    "DATABASE=mdici;"
    "Trusted_Connection=yes;"
)

# Establish a connection to the SQL database
conn = pyodbc.connect(conn_string)

# SQL query with replacements for 'Service Area' and 'Project State' values
query = '''
SELECT 
    CASE
        WHEN [Service Area] = 'Imaging-RAD' THEN 'Imaging'
        WHEN [Service Area] = 'Imaging-Cardio' THEN 'Imaging'
        WHEN [Service Area] = 'Imaging-RadOnc' THEN 'Imaging'
        WHEN [Service Area] = 'Lab-MDI' THEN 'Lab'
        WHEN [Service Area] = 'Lab-POC' THEN 'Lab'
        WHEN [Service Area] = 'BMDI' THEN 'BMDI/Other'
        WHEN [Service Area] = 'Other' THEN 'BMDI/Other'
        ELSE [Service Area]
    END AS [Service Area],
    COUNT(*) AS project_count
FROM dbo.defects
WHERE 
    CASE 
        WHEN [Project State] = 'Security' THEN 'Complete'
        WHEN [Project State] = 'Firewall' THEN 'Design'
        ELSE [Project State]
    END NOT IN ('Complete', 'Cancelled')
    AND [Kick-Off Date] < '2025-08-31'
GROUP BY 
    CASE
        WHEN [Service Area] = 'Imaging-RAD' THEN 'Imaging'
        WHEN [Service Area] = 'Imaging-Cardio' THEN 'Imaging'
        WHEN [Service Area] = 'Imaging-RadOnc' THEN 'Imaging'
        WHEN [Service Area] = 'Lab-MDI' THEN 'Lab'
        WHEN [Service Area] = 'Lab-POC' THEN 'Lab'
        WHEN [Service Area] = 'BMDI' THEN 'BMDI/Other'
        WHEN [Service Area] = 'Other' THEN 'BMDI/Other'
        ELSE [Service Area]
    END
ORDER BY [Service Area]
'''

# Load data from the SQL query into a DataFrame
data = pd.read_sql(query, conn)

# Closing the database connection
conn.close()

# Set 'Service Area' as the index and get project counts
project_counts = data.set_index('Service Area')['project_count']

# Generate the bar chart
plt.figure(figsize=(10, 5), dpi=300)
bars = plt.bar(project_counts.index, project_counts.values, color='#6c5ea4')

# Add the count above each bar
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, yval, int(yval), va='bottom')

# Set the title for the chart
plt.title('Total In-Flight Projects by Market Area')
plt.xticks(rotation=70)
plt.tight_layout()

# Save the final plot without the x-axis label and with a transparent background
output_graph_path = '03_page_3_of_FY_Data.png'
plt.savefig(output_graph_path, transparent=True, bbox_inches='tight')
