# CyberCafe POS Pro

A production-ready, always-online cyber café management system with dual interfaces: a front-desk POS for attendants and a remote admin dashboard for managers.

## Features

### Core Functionality
- **Dual Interface**: Separate POS and Admin dashboards
- **Computer Session Management**: Track PC usage with automatic billing
- **Services & Pricing**: Flexible pricing modes (per page, per minute, per job, bundles)
- **Payment Processing**: Cash and M-Pesa with transaction codes
- **Shift Management**: Cash reconciliation and shift reports
- **Inventory Tracking**: Auto-deduct stock with low-stock alerts
- **Expense Tracking**: Record and categorize business expenses
- **Comprehensive Reports**: Sales, profit, service performance, and more
- **Role-Based Access Control**: Admin, Manager, and Attendant roles
- **Audit Logging**: Track all sensitive operations
- **Receipt Printing**: PDF and thermal printer support

### Technical Stack
- **Backend**: Python FastAPI + PostgreSQL + Redis
- **Frontend**: React TypeScript + Vite
- **Real-time**: WebSocket for live updates
- **Authentication**: JWT with httpOnly cookies
- **Deployment**: Docker-ready

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Seed initial data**:
   ```bash
   python -m app.seed
   ```

7. **Start the server**:
   ```bash
   uvicorn app.main:app --reload
   ```

   API will be available at `http://localhost:8000`
   API docs at `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API URL
   ```

4. **Start development server**:
   ```bash
   npm run dev
   ```

   Frontend will be available at `http://localhost:5173`

## Default Login Credentials

After seeding the database, use these credentials:

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Manager | `manager` | `manager123` |
| Attendant | `attendant` | `attendant123` |

**⚠️ IMPORTANT**: Change these passwords immediately in production!

## Docker Deployment

### Using Docker Compose

1. **Create `.env` file** in project root:
   ```env
   DB_PASSWORD=your_secure_password
   SECRET_KEY=your_secret_key_min_32_chars
   CORS_ORIGINS=https://your-frontend-domain.com
   API_URL=https://your-backend-domain.com
   WS_URL=wss://your-backend-domain.com
   ```

2. **Start all services**:
   ```bash
   docker-compose up -d
   ```

3. **Run migrations and seed**:
   ```bash
   docker-compose exec backend alembic upgrade head
   docker-compose exec backend python -m app.seed
   ```

## Deployment to Render

### Backend Deployment

1. **Create PostgreSQL database** on Render
2. **Create Redis instance** on Render
3. **Create Web Service** for backend:
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**:
     - `DATABASE_URL`: (from Render PostgreSQL)
     - `REDIS_URL`: (from Render Redis)
     - `SECRET_KEY`: (generate secure random string)
     - `CORS_ORIGINS`: (your frontend URL)

### Frontend Deployment

1. **Create Static Site** on Render:
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/dist`
   - **Environment Variables**:
     - `VITE_API_URL`: (your backend URL)
     - `VITE_WS_URL`: (your backend WebSocket URL)

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Project Structure

```
cybercafe-pos-pro/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Security, permissions, audit
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── utils/        # Utilities (calculations, receipts)
│   │   ├── config.py     # Configuration
│   │   ├── database.py   # Database connection
│   │   ├── main.py       # FastAPI app
│   │   └── seed.py       # Database seeding
│   ├── alembic/          # Database migrations
│   ├── tests/            # Test files
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/          # API client
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── hooks/        # Custom hooks
│   │   ├── context/      # React context
│   │   └── types/        # TypeScript types
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

## Key Features Explained

### Session Management
- Start/stop computer sessions with automatic timer
- Calculate charges based on duration and rate
- Link sessions to transactions

### Shift System
- Attendants must open a shift before making sales
- Track opening cash, expected cash, and counted cash
- Calculate cash differences (short/over)

### Inventory Management
- Auto-deduct stock when services are sold
- Track stock movements (purchase, usage, adjustment)
- Low stock alerts

### Receipt Printing
- Generate PDF receipts for download/print
- ESC/POS thermal printer support (requires local print server)

### Real-time Updates
- Live computer status updates
- Active session timers
- Dashboard notifications

## Security Features

- JWT authentication with refresh tokens
- Role-based access control (RBAC)
- Password hashing with bcrypt
- Input validation on all endpoints
- Rate limiting on authentication
- Audit logging for sensitive operations
- CORS protection

## Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running
- Check DATABASE_URL in `.env`
- Ensure database exists

### CORS Errors
- Verify CORS_ORIGINS includes your frontend URL
- Check that cookies are enabled

### Receipt Printing
- PDF receipts work in all browsers
- Thermal printing requires ESC/POS compatible printer
- Consider using a local print server for thermal printers

## License

Proprietary - All rights reserved

## Support

For issues or questions, contact: support@cybercafe.com
