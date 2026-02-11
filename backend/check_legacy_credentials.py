import pg8000.native
import ssl
import sys

project_ref = "wdlkjjrrdslfpplohmsq"
region = "aws-0-eu-west-1"
pooler_host = f"{region}.pooler.supabase.com"
port_pooler = 6543
dbname = "postgres"

# IPv6 Address from nslookup
ipv6_host = "2a05:d018:135e:1664:bdc6:ad63:7da3:7ed0"
port_direct = 5432

passwords = ["Catejusto7031", "@Catejusto7031"]

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

print("Testing Alternate Connection Methods...")

# 1. Test Short User on Pooler
for pwd in passwords:
    print(f"Testing 'postgres' on Pooler with password '{pwd}'...", end=" ")
    try:
        conn = pg8000.native.Connection(
            user="postgres",
            password=pwd,
            host=pooler_host,
            port=port_pooler,
            database=dbname,
            ssl_context=ssl_context,
            timeout=5
        )
        print("SUCCESS! (Short User)")
        conn.close()
        # Save to .env
        final_pwd = pwd.replace("@", "%40")
        dsn = f"postgresql://postgres:{final_pwd}@{pooler_host}:{port_pooler}/{dbname}"
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
        sys.exit(0)
    except Exception as e:
        print(f"Failed ({e})")

# 2. Test IPv6 Direct
for pwd in passwords:
    print(f"Testing Direct IPv6 with password '{pwd}'...", end=" ")
    try:
        conn = pg8000.native.Connection(
            user="postgres",
            password=pwd,
            host=ipv6_host,
            port=port_direct,
            database=dbname,
            ssl_context=ssl_context,
            timeout=5
        )
        print("SUCCESS! (IPv6)")
        conn.close()
        # Update .env
        final_pwd = pwd.replace("@", "%40")
        dsn = f"postgresql://postgres:{final_pwd}@[{ipv6_host}]:{port_direct}/{dbname}"
        with open(".env", "w") as f:
             f.write(f"DATABASE_URL={dsn}\n")
             # ... (same as above)
        sys.exit(0)
    except Exception as e:
        print(f"Failed ({e})")

print("All alternates failed.")
