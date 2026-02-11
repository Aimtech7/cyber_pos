import pg8000.native
import sys

# Project and Password
project_ref = "wdlkjjrrdslfpplohmsq"
password = "Cybercafe2026"

region = "gcp-0-eu-west-1"
host = f"{region}.pooler.supabase.com"
port = 6543
user = f"postgres.{project_ref}"
dbname = "postgres"

print(f"Checking {region}...")

try:
    conn = pg8000.native.Connection(
        user=user,
        password=password,
        host=host,
        port=port,
        database=dbname,
        timeout=10
    )
    print("SUCCESS! FOUND IT!")
    conn.close()
except Exception as e:
    print(f"Failed: {e}")
