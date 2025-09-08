"""
Automated Export and Git Deployment Script
Exports data from database, commits to Git, and triggers Streamlit Cloud update
Run this daily/weekly to keep dashboard current
"""

import subprocess
import os
import sys
from datetime import datetime
import shutil

# Configuration
GITHUB_REPO = "addamiano/mdici-dashboard"  # Update this with your actual repo
COMMIT_MESSAGE_PREFIX = "Auto-update MDICI data"

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed: {description}")
            print(f"Error: {result.stderr}")
            return False
        else:
            print(f"✅ Success: {description}")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
    except Exception as e:
        print(f"❌ Exception during {description}: {str(e)}")
        return False

def export_data():
    """Run the export script"""
    print("=" * 60)
    print("STEP 1: EXPORTING DATA FROM DATABASE")
    print("=" * 60)
    
    # Run the export script
    if not run_command("python export_to_csv.py", "Exporting data from database"):
        return False
    
    # Check if files were created
    required_files = [
        "exported_data/mdici_projects_latest.csv",
        "exported_data/mdici_performance_latest.csv"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Required file not found: {file_path}")
            return False
        else:
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            print(f"✅ Found {file_path} ({file_size:.1f} MB)")
    
    # Run the additional chart generation scripts (02 and 04 only)
    print("\n📊 Generating additional charts...")
    chart_scripts = [
        ("02_SQL_current_active_projects.py", "Project State Distribution"),
        ("04_SQL_current_active_by_ce_division.py", "Projects by CE Division")
    ]
    
    for script, description in chart_scripts:
        if os.path.exists(script):
            if not run_command(f"python {script}", f"Generating {description} chart"):
                print(f"⚠️ Warning: Failed to generate {description} chart")
                # Continue even if chart generation fails
        else:
            print(f"⚠️ Chart script not found: {script}")
    
    return True

def setup_git_repo():
    """Initialize or update Git repository"""
    print("\n" + "=" * 60)
    print("STEP 2: SETTING UP GIT REPOSITORY")
    print("=" * 60)
    
    # Check if this is already a git repo
    if not os.path.exists('.git'):
        print("🆕 Initializing new Git repository...")
        if not run_command("git init", "Initializing Git repository"):
            return False
        
        # Set branch to main
        run_command("git branch -M main", "Setting branch to main")
        
        # Add remote if specified
        remote_url = f"https://github.com/{GITHUB_REPO}.git"
        if not run_command(f"git remote add origin {remote_url}", f"Adding remote {remote_url}"):
            return False
    else:
        print("✅ Git repository already exists")
        # Ensure we're on main branch
        run_command("git branch -M main", "Ensuring main branch")
    
    # Configure git if needed
    run_command('git config user.name "MDICI Auto-Deploy"', "Setting Git username")
    run_command('git config user.email "mdici-deploy@company.com"', "Setting Git email")
    
    return True

def prepare_files_for_deployment():
    """Copy and prepare files for deployment"""
    print("\n" + "=" * 60)
    print("STEP 3: PREPARING FILES FOR DEPLOYMENT")
    print("=" * 60)
    
    # Check that streamlit_app.py exists
    if os.path.exists("streamlit_app.py"):
        print("✅ streamlit_app.py found")
    else:
        print("❌ streamlit_app.py not found")
        return False
    
    # Copy CSV files to root directory for easier Streamlit Cloud access
    csv_files = [
        ("exported_data/mdici_projects_latest.csv", "mdici_projects_latest.csv"),
        ("exported_data/mdici_performance_latest.csv", "mdici_performance_latest.csv")
    ]
    
    for src, dst in csv_files:
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"✅ Copied {src} → {dst}")
        else:
            print(f"❌ Source file not found: {src}")
            return False
    
    # Ensure requirements.txt exists
    if not os.path.exists("requirements.txt"):
        requirements_content = """streamlit>=1.29.0
pandas>=2.0.0
plotly>=5.18.0
beautifulsoup4>=4.12.0
xlsxwriter>=3.1.0
"""
        with open("requirements.txt", "w") as f:
            f.write(requirements_content)
        print("✅ Created requirements.txt")
    
    return True

def commit_and_push():
    """Commit changes and push to GitHub"""
    print("\n" + "=" * 60)
    print("STEP 4: COMMITTING AND PUSHING TO GITHUB")
    print("=" * 60)
    
    # Add files to staging
    files_to_commit = [
        "streamlit_app.py",
        "requirements.txt", 
        "mdici_projects_latest.csv",
        "mdici_performance_latest.csv",
        "02_page_2_of_FY_Data.png",
        "04_page_4_of_FY_Data.png"
    ]
    
    for file_path in files_to_commit:
        if os.path.exists(file_path):
            if not run_command(f"git add {file_path}", f"Staging {file_path}"):
                return False
        else:
            print(f"⚠️ File not found for staging: {file_path}")
    
    # Create commit message with timestamp and stats
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Get project count for commit message
    try:
        import pandas as pd
        df = pd.read_csv("mdici_projects_latest.csv")
        project_count = len(df)
        commit_message = f"{COMMIT_MESSAGE_PREFIX} - {timestamp} ({project_count:,} projects)"
    except:
        commit_message = f"{COMMIT_MESSAGE_PREFIX} - {timestamp}"
    
    # Commit changes
    if not run_command(f'git commit -m "{commit_message}"', "Committing changes"):
        print("ℹ️ No changes to commit (files may be unchanged)")
        return True  # This is OK - no changes needed
    
    # Push to remote 
    # Since GITHUB_REPO is set to "addamiano/mdici-dashboard", we'll push
    print(f"📤 Pushing to GitHub repository: {GITHUB_REPO}")
    
    # Push to main branch
    if not run_command("git push -u origin main", "Pushing to GitHub (main branch)"):
        print("❌ Failed to push to GitHub - you may need to configure authentication")
        print("   Set up a Personal Access Token or SSH key for authentication")
        print("\n   To fix authentication:")
        print("   1. Create a Personal Access Token at https://github.com/settings/tokens")
        print("   2. Run: git remote set-url origin https://USERNAME:TOKEN@github.com/addamiano/mdici-dashboard.git")
        return False
    
    return True

def verify_deployment():
    """Verify the deployment was successful"""
    print("\n" + "=" * 60)
    print("STEP 5: DEPLOYMENT VERIFICATION")
    print("=" * 60)
    
    # Check file sizes and dates
    files_to_check = [
        "streamlit_app.py",
        "mdici_projects_latest.csv",
        "mdici_performance_latest.csv"
    ]
    
    print("📋 Deployment files:")
    for file_path in files_to_check:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            print(f"   ✅ {file_path}: {file_size:,} bytes, modified {file_time.strftime('%H:%M:%S')}")
        else:
            print(f"   ❌ {file_path}: MISSING")
    
    # Show next steps
    print("\n🚀 Next Steps:")
    print("   1. Go to your Streamlit Cloud app dashboard")
    print("   2. Verify the app updates within 2-3 minutes")
    print("   3. Test the dashboard functionality")
    
    print(f"   4. Check GitHub repository: https://github.com/{GITHUB_REPO}")
    print(f"   5. Streamlit Cloud URL: https://share.streamlit.io/addamiano/mdici-dashboard/main/streamlit_app.py")
    
    return True

def main():
    """Main deployment function"""
    print("🚀 MDICI Dashboard Auto-Deploy Started")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: Export data
        if not export_data():
            print("❌ Data export failed - stopping deployment")
            return False
        
        # Step 2: Set up Git
        if not setup_git_repo():
            print("❌ Git setup failed - stopping deployment") 
            return False
        
        # Step 3: Prepare files
        if not prepare_files_for_deployment():
            print("❌ File preparation failed - stopping deployment")
            return False
        
        # Step 4: Commit and push
        if not commit_and_push():
            print("❌ Git operations failed - stopping deployment")
            return False
        
        # Step 5: Verify
        verify_deployment()
        
        print("\n" + "=" * 60)
        print("✅ AUTO-DEPLOY COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("🎉 Your dashboard should update on Streamlit Cloud within 2-3 minutes")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Unexpected error during deployment: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
    
    print("\n💡 To schedule this script:")
    print("   • Windows: Use Task Scheduler")
    print("   • Run daily at 8 AM: python auto_deploy.py")
    print("   • Or manually run whenever you want to update the dashboard")
