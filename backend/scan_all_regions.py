import pg8000.native
import ssl
import sys

# Project and Password
project_ref = "wdlkjjrrdslfpplohmsq"
password = "Cybercafe2026"

regions = [
    # AWS
    "aws-0-eu-west-1", # Ireland (Most likely)
    "aws-0-us-east-1", "aws-0-us-east-2", "aws-0-us-west-1", "aws-0-us-west-2",
    "aws-0-eu-central-1", "aws-0-eu-west-2", "aws-0-eu-west-3", "aws-0-eu-north-1",
    "aws-0-ap-southeast-1", "aws-0-ap-southeast-2", "aws-0-ap-northeast-1", "aws-0-ap-northeast-2",
    "aws-0-ap-south-1", "aws-0-sa-east-1", "aws-0-ca-central-1", "aws-0-af-south-1",
    # GCP
    "gcp-0-us-east-1", "gcp-0-eu-west-1", "gcp-0-ap-southeast-1"
]

print(f"Scanning ALL regions for project: {project_ref} (using pg8000)")

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

for region in regions:
    host = f"{region}.pooler.supabase.com"
    port = 6543
    dbname = "postgres"
    user = f"postgres.{project_ref}"
    
    print(f"Checking {region}...", end=" ")
    sys.stdout.flush()
    
    try:
        conn = pg8000.native.Connection(
            user=user,
            password=password,
            host=host,
            port=port,
            database=dbname,
            ssl_context=ssl_context,
            timeout=5
        )
        print("SUCCESS! FOUND IT!")
        conn.close()
        
        # We found it! Update .env
        dsn = f"postgresql://postgres.{project_ref}:{password}@{host}:{port}/{dbname}"
        with open(".env", "w") as f:
             f.write(f"DATABASE_URL={dsn}\n")
             f.write("REDIS_URL=redis://localhost:6379\n") 
             f.write("SECRET_KEY=sb_publishable_6Yr9_gzE64oHgWS6MezZLA_FKYX1Yq-\n")
             f.write("ALGORITHM=HS256\n")
             f.write("ACCESS_TOKEN_EXPIRE_MINUTES=15\n")
             f.write("REFRESH_TOKEN_EXPIRE_DAYS=7\n")
             f.write(f"CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://{project_ref}.supabase.co\n")
             f.write("APP_NAME=CyberCafe POS Pro\n")
             f.write("DEBUG=True\n")
        
        print(f"Updated .env for region: {region}")
        sys.exit(0)
        
    except Exception as e:
        err_msg = str(e).strip()
        if "password authentication failed" in err_msg:
            print("FOUND! (Bad Password)")
            sys.exit(0) # Stop here if we found the region but pass is wrong
        elif "Tenant or user not found" in err_msg:
            print("Not here.")
        elif "gaierror" in err_msg:
             print("DNS Error.")
        else:
            print(f"Error: {err_msg}")

print("\nScan complete. No matches found.")
