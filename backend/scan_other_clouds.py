import psycopg2
import sys

project_ref = "wdlkjjrrdslfpplohmsq"
password = "%40Catejusto7031" # Encoded

# Common Non-AWS Supabase Pooler Regions (GCP, Azure, etc.)
# Based on Supabase documentation/common patterns
regions = [
    # GCP
    "gcp-0-us-east-1", 
    "gcp-0-us-west-1",
    "gcp-0-eu-west-1", 
    "gcp-0-ap-southeast-1",
    
    # Azure (less common for poolers but exist)
    # "azure-0-us-west-1" # hypothetical/rare
    
    # Fly.io (older projects sometimes)
    # "fly-0-..."
]

print(f"Scanning GCP/Other regions for project: {project_ref}")

found = False

for region in regions:
    host = f"{region}.pooler.supabase.com"
    port = 6543
    dbname = "postgres"
    user = f"postgres.{project_ref}"
    dsn = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    
    print(f"Checking {region} ({host})...", end=" ")
    sys.stdout.flush()
    
    try:
        conn = psycopg2.connect(dsn, connect_timeout=4)
        print(f"SUCCESS! FOUND {region}")
        found = True
        conn.close()
        break
    except psycopg2.OperationalError as e:
        err_msg = str(e).strip()
        if "Tenant or user not found" in err_msg:
            print("Not here.")
        elif "password authentication failed" in err_msg:
            print(f"FOUND! {region} (Bad Password)")
            found = True
            break
        elif "could not translate host name" in err_msg:
             print("DNS Error (Region likely doesn't exist).")
        else:
            print(f"Error: {err_msg}")
    except Exception as e:
        print(f"Error: {e}")

if not found:
    print("\nScan complete. No matches found.")
