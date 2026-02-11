import pg8000.native
import os
import ssl

password = "Catejusto7031" # Plain password for pg8000, it handles encoding internally usually or passing as arg
# Wait, pg8000.native.Connection takes password as arg.

project_ref = "wdlkjjrrdslfpplohmsq"

# Common Supabase Pooler Regions
regions = [
    "aws-0-us-east-1",      # N. Virginia
    "aws-0-us-west-1",      # N. California
    "aws-0-eu-central-1",   # Frankfurt
    "aws-0-eu-west-1",      # Ireland (most common outside US)
    "aws-0-eu-west-2",      # London
    "aws-0-ap-southeast-1", # Singapore
    "aws-0-ap-northeast-1", # Tokyo
    "aws-0-sa-east-1",      # Sao Paulo
    "aws-0-ca-central-1",   # Canada
    "aws-0-ap-south-1",     # Mumbai
]

print(f"🕵️ Detecting Supabase Region for project: {project_ref} (using pg8000)")

found_region = None
ssl_context = ssl.create_default_context()

for region in regions:
    host = f"{region}.pooler.supabase.com"
    port = 6543
    dbname = "postgres"
    user = f"postgres.{project_ref}"
    
    print(f"\nScanning Region: {region} ({host})...")
    
    try:
        conn = pg8000.native.Connection(
            user=user,
            password=password,
            host=host,
            port=port,
            database=dbname,
            ssl_context=ssl_context,
            timeout=3
        )
        print(f"✅ SUCCESS! Connected to {region}")
        found_region = region
        conn.close()
        break
    except Exception as e:
        err_msg = str(e).strip()
        # pg8000 errors might differ in text
        if "Tenant or user not found" in err_msg:
            print(f"❌ Not here (Tenant not found)")
        elif "password authentication failed" in err_msg:
             print(f"⚠️  FOUND REGION: {region} (But password wrong)")
             found_region = region
             break
        elif "gaierror" in err_msg: # DNS error
            print(f"❌ Host not found (DNS)")
        elif "timeout" in err_msg.lower():
            print(f"❌ Timeout")
        else:
             print(f"❌ Error: {err_msg}")

if found_region:
    print(f"\n🎉 Project is located in: {found_region}")
    print(f"Update your .env with host: {found_region}.pooler.supabase.com")
else:
    print("\n❌ Could not detect region. Please check Supabase Dashboard.")

