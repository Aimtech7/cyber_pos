import psycopg2
import sys

# Args: region
region = sys.argv[1] if len(sys.argv) > 1 else "aws-0-us-east-1"
password = "%40Catejusto7031" # Encoded
project_ref = "wdlkjjrrdslfpplohmsq"

host = f"{region}.pooler.supabase.com"
port = 5432
dbname = "postgres"
user = f"postgres.{project_ref}"

print(f"Checking {region} ({host})...")

try:
    dsn = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    conn = psycopg2.connect(dsn)
    print(f"SUCCESS! Connected to {region}")
    conn.close()
except psycopg2.OperationalError as e:
    err_msg = str(e).strip()
    if "Tenant or user not found" in err_msg:
        print(f"Not here (Tenant not found in {region})")
    elif "password authentication failed" in err_msg:
            print(f"FOUND REGION: {region} (Password mismatch)")
    elif "could not translate host name" in err_msg:
        print(f"DNS Error for {region}")
    else:
            print(f"Error: {err_msg}")
except Exception as e:
    print(f"Unexpected Error: {e}")
