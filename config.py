<<<<<<< HEAD
"""
Configuration file for MDICI Dashboard
Automatically detects environment and sets appropriate database server
"""

import socket
import os

def get_server_name():
    """
    Automatically detect which SQL Server to use based on environment
    Returns the appropriate server name for the current environment
    """
    hostname = socket.gethostname().upper()
    
    # You can also use environment variable to override
    # Set MDICI_ENV=test or MDICI_ENV=prod in your system
    env = os.environ.get('MDICI_ENV', '').lower()
    
    # Check if we're in test environment
    if 'NZXT' in hostname or env == 'test':
        return "NZXT\\SQLEXPRESS"  # Test environment
    else:
        return "PHX-SQL-117\\SQL2019"  # Production environment

def get_connection_string():
    """
    Get the full connection string for the current environment
    """
    server_name = get_server_name()
    database_name = "mdici"
    
    return (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server_name};"
        f"DATABASE={database_name};"
        "Trusted_Connection=yes;"
    )

def get_sqlalchemy_connection_string():
    """
    Get SQLAlchemy format connection string
    """
    server_name = get_server_name()
    database_name = "mdici"
    
    return f"mssql+pyodbc://{server_name}/{database_name}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"

def is_test_environment():
    """
    Check if we're running in test environment
    """
    hostname = socket.gethostname().upper()
    env = os.environ.get('MDICI_ENV', '').lower()
    return 'NZXT' in hostname or env == 'test'

# Constants for both environments
DATABASE_NAME = "mdici"
TEST_SERVER = "NZXT\\SQLEXPRESS"
PROD_SERVER = "PHX-SQL-117\\SQL2019"

# Current environment settings
CURRENT_SERVER = get_server_name()
CURRENT_CONNECTION_STRING = get_connection_string()
CURRENT_SQLALCHEMY_STRING = get_sqlalchemy_connection_string()
IS_TEST = is_test_environment()

# Print current configuration when imported (helpful for debugging)
if __name__ == "__main__":
    print(f"Current Environment: {'TEST' if IS_TEST else 'PRODUCTION'}")
    print(f"Server: {CURRENT_SERVER}")
    print(f"Database: {DATABASE_NAME}")
=======
"""
Configuration file for MDICI Dashboard
Automatically detects environment and sets appropriate database server
"""

import socket
import os

def get_server_name():
    """
    Automatically detect which SQL Server to use based on environment
    Returns the appropriate server name for the current environment
    """
    hostname = socket.gethostname().upper()
    
    # You can also use environment variable to override
    # Set MDICI_ENV=test or MDICI_ENV=prod in your system
    env = os.environ.get('MDICI_ENV', '').lower()
    
    # Check if we're in test environment
    if 'NZXT' in hostname or env == 'test':
        return "NZXT\\SQLEXPRESS"  # Test environment
    else:
        return "PHX-SQL-117\\SQL2019"  # Production environment

def get_connection_string():
    """
    Get the full connection string for the current environment
    """
    server_name = get_server_name()
    database_name = "mdici"
    
    return (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server_name};"
        f"DATABASE={database_name};"
        "Trusted_Connection=yes;"
    )

def get_sqlalchemy_connection_string():
    """
    Get SQLAlchemy format connection string
    """
    server_name = get_server_name()
    database_name = "mdici"
    
    return f"mssql+pyodbc://{server_name}/{database_name}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"

def is_test_environment():
    """
    Check if we're running in test environment
    """
    hostname = socket.gethostname().upper()
    env = os.environ.get('MDICI_ENV', '').lower()
    return 'NZXT' in hostname or env == 'test'

# Constants for both environments
DATABASE_NAME = "mdici"
TEST_SERVER = "NZXT\\SQLEXPRESS"
PROD_SERVER = "PHX-SQL-117\\SQL2019"

# Current environment settings
CURRENT_SERVER = get_server_name()
CURRENT_CONNECTION_STRING = get_connection_string()
CURRENT_SQLALCHEMY_STRING = get_sqlalchemy_connection_string()
IS_TEST = is_test_environment()

# Print current configuration when imported (helpful for debugging)
if __name__ == "__main__":
    print(f"Current Environment: {'TEST' if IS_TEST else 'PRODUCTION'}")
    print(f"Server: {CURRENT_SERVER}")
    print(f"Database: {DATABASE_NAME}")
>>>>>>> 6585b5e5b5bd2ec6938179fead84924568b060c4
    print(f"Connection String: {CURRENT_CONNECTION_STRING}")