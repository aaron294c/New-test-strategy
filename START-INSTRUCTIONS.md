# Starting the Application

## Prerequisites

### Backend Requirements
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Requirements
```bash
cd frontend
npm install  # or yarn install
```

## Running the Application

### Backend (API Server)
```bash
# Navigate to backend directory and start the Python API
cd backend
source venv/bin/activate  # Activate virtual environment first
python api.py
# API will run on http://localhost:8000
```

### Frontend (Development Server)
```bash
# In a new terminal, navigate to frontend directory and start the development server
cd frontend
npm run dev  # Vite uses 'npm run dev', not 'npm start'
# Frontend will run on http://localhost:5173 (Vite default)
# or http://localhost:3000 if configured
```

## Using Both Simultaneously

### Option 1: Separate Terminals (Recommended)
Open two terminal windows and run backend in one, frontend in the other.

### Option 2: Background Process (Unix/Mac/Linux)
```bash
# Start backend in background
cd backend && source venv/bin/activate && python api.py &

# Start frontend
cd ../frontend && npm run dev
```

### Option 3: Docker Compose (Production-like)
```bash
# From project root
docker-compose up
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

## Verification

1. **Backend Health Check**: http://localhost:8000/api/health
2. **API Docs**: http://localhost:8000/docs (FastAPI auto-generated)
3. **Frontend**: http://localhost:5173 or http://localhost:3000

## Environment Variables

### Backend (`backend/.env`)
```env
# Optional: For options data
POLYGON_API_KEY=your_key_here
TRADIER_API_KEY=Bearer your_token

# Cache directory (optional)
CACHE_DIR=./cache
```

### Frontend (`frontend/.env`)
```env
# API endpoint
VITE_API_URL=http://localhost:8000
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -ti:8000 | xargs kill -9  # Unix/Mac/Linux
netstat -ano | findstr :8000   # Windows

# Find process using port 5173/3000
lsof -ti:5173 | xargs kill -9  # Unix/Mac/Linux
```

### Python Virtual Environment Issues
```bash
# Recreate venv
cd backend
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Missing Dependencies
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Notes

- **Vite Dev Server**: Frontend uses Vite, which runs on port 5173 by default (not 3000)
- **API Proxy**: Vite proxy configured to forward `/api/*` requests to backend
- **CORS**: Backend CORS already configured for localhost:3000, localhost:5173, and production domains
- **Cache**: Backend caches backtest results in `backend/cache/` for 24 hours
- **Data Source**: Uses yfinance for market data (free, no API key needed)
