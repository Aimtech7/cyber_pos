# Railway Deployment Guide

## Database Migrations

The application has been configured to **NOT** run migrations automatically on startup to prevent boot loops if the database isn't ready.

### Option 1: Automatic Migration (Recommended)
The `railway.json` has been updated to run migrations before starting the server:
```json
"startCommand": "python migrate.py && ./start.sh"
```

### Option 2: Manual Migration
If you need to run migrations manually:

1. Connect to the Railway project via CLI
2. Run the migration command:
   ```bash
   python migrate.py
   ```

## Troubleshooting

If the deployment fails:

1. Check the build logs for migration errors
2. If migrations fail, the server will not start
3. You can override the start command in Railway settings to just `./start.sh` to skip migrations and debug
