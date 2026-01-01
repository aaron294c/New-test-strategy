# Starting the Application

## Backend
```bash
# Navigate to backend directory and start the Python API
cd backend
python api.py
```

## Frontend
```bash
# In a new terminal, navigate to frontend directory and start the development server
cd frontend
npm start  # or yarn start, depending on your package manager
```

## Using Both Simultaneously
```bash
# Using a single command with background process
cd backend && python api.py & cd ../frontend && npm start
```

Note: Make sure you have all required dependencies installed for both frontend and backend before starting the servers.
