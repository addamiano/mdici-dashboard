import pyodbc
import pandas as pd
import matplotlib.pyplot as plt

# Database connection details using your provided connection string
conn_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    #"SERVER=NZXT\\SQLExpress;"
    "SERVER=PHX-SQL-117\\SQL2019;"
    "DATABASE=mdici;"
    "Trusted_Connection=yes;"
)

# Establish a connection to the SQL database
conn = pyodbc.connect(conn_string)

# SQL query to fetch the necessary data
query = '''
SELECT [Defect ID], 
       CASE 
           WHEN [Project State] = 'Security' THEN 'Complete' 
           WHEN [Project State] = 'Firewall' THEN 'Design' 
           ELSE [Project State] 
       END AS [Project State], 
       [Service Area], 
       [Priority], 
       [Facility], 
       [Kick-Off Date], 
       [Design Engineer]
FROM dbo.defects
WHERE [Project State] IN ('Testing', 'Design', 'Intake', 'Hold', 'Firewall', 'Security')
--AND [Kick-Off Date] < '2025-08-31'
'''

# Load data from the SQL query into a DataFrame
data = pd.read_sql(query, conn)

# Closing the database connection
conn.close()

# Remove rows where 'Project State' is 'Complete'
data = data[data['Project State'] != 'Complete']

# Filtering and aggregating the data for visualization
filtered_project_state_counts = data['Project State'].value_counts()

# Plot the pie chart
plt.figure(figsize=(35, 25), dpi=300)

# Update colors to include only the relevant project states
colors = {
    'Design': '#6c5ea4',  
    'Hold': '#1c7f40',    
    'Intake': '#00ad8d',  
    'Testing': '#c15289'
}

# Default color for any unknown states (though they should be filtered out)
default_color = '#d3d3d3'

# Assign the colors for the project states, using default_color for unknown states
state_colors = [colors.get(state, default_color) for state in filtered_project_state_counts.index]

fig, ax = plt.subplots(figsize=(35, 25), dpi=300)
wedges, texts, autotexts = ax.pie(filtered_project_state_counts, 
                                  labels=filtered_project_state_counts.index,
                                  autopct=lambda p: '{:.0f}'.format(p * sum(filtered_project_state_counts) / 100),
                                  startangle=90, colors=state_colors,
                                  textprops={'fontsize': 34})

plt.setp(autotexts, size=34, weight="bold")

legend = ax.legend(wedges, filtered_project_state_counts.index,
                   title="Project States",
                   loc="lower right",
                   bbox_to_anchor=(1, 0),
                   fontsize=34,
                   labelspacing=1.2)

plt.setp(legend.get_title(), fontsize=34)

plt.tight_layout()
plt.subplots_adjust(right=0.85, bottom=0.1)

# Save the pie chart
plt.savefig('02_page_2_of_FY_Data.png', bbox_inches='tight', transparent=True, dpi=300, format='png')
