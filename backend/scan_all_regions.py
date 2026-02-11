import socket
import ssl
import sys

# Project and Password
project_ref = "wdlkjjrrdslfpplohmsq"
# We don't even need the password to check "Tenant not found" vs "Password authentication failed"
# But we need to send a startup packet.
# We can use a raw socket SSL handshake + startup message, OR just use psycopg2/pg8000.
# Let's use psycopg2 as it's installed and reliable if we don't crash.
# Wait, check_region.py didn't crash on us-east-1. It crashed on output emoji.
# So I can use psycopg2.

import psycopg2

password = "%40Catejusto7031" # Encoded

regions = [
    "aws-0-us-east-1", "aws-0-us-east-2", "aws-0-us-west-1", "aws-0-us-west-2",
    "aws-0-eu-central-1", "aws-0-eu-west-1", "aws-0-eu-west-2", "aws-0-eu-west-3", "aws-0-eu-north-1",
    "aws-0-ap-southeast-1", "aws-0-ap-southeast-2", "aws-0-ap-northeast-1", "aws-0-ap-northeast-2",
    "aws-0-ap-south-1", "aws-0-sa-east-1", "aws-0-ca-central-1"
]

print(f"Scanning ALL regions for project: {project_ref}")

for region in regions:
    host = f"{region}.pooler.supabase.com"
    port = 6543
    dbname = "postgres"
    user = f"postgres.{project_ref}"
    dsn = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    
    print(f"Checking {region}...", end=" ")
    sys.stdout.flush()
    
    try:
        conn = psycopg2.connect(dsn, connect_timeout=3)
        print(f"SUCCESS! FOUND {region}")
        conn.close()
        break
    except psycopg2.OperationalError as e:
        err_msg = str(e).strip()
        if "Tenant or user not found" in err_msg:
            print("Not here.")
        elif "password authentication failed" in err_msg:
            print(f"FOUND! {region} (Bad Password)")
            break
        elif "could not translate host name" in err_msg:
             print("DNS Error.")
        else:
            print(f"Error: {err_msg}")
    except Exception as e:
        print(f"Error: {e}")
