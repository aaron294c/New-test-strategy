# Project Context - RSI-MA Performance Analytics Dashboard

## Overview
This project is a comprehensive web-based analytics dashboard for visualizing and analyzing the performance characteristics of an RSI-MA (Relative Strength Index with Moving Average) percentile ranking trading strategy. It combines historical backtesting with forward-looking Monte Carlo simulations.

## Project Structure

### Root Directory
```
/workspaces/New-test-strategy/
├── backend/                 # Python FastAPI backend
├── frontend/               # React TypeScript frontend
├── docs/                   # Project documentation
├── tests/                  # Test suites
├── src/                    # Additional source code
├── .codemachine/          # AI agent coordination system
├── .claude-flow/          # Claude Flow swarm coordination
├── .hive-mind/            # Hive mind collaborative intelligence
└── coordination/          # Coordination configuration
```

### Backend Structure (`/backend/`)
**Primary Language**: Python 3.9+
**Framework**: FastAPI

**Core Files**:
- `api.py` - FastAPI REST endpoints (450 lines)
- `enhanced_backtester.py` - D1-D21 backtesting engine (830 lines)
- `monte_carlo_simulator.py` - Monte Carlo simulations (400 lines)
- `requirements.txt` - Python dependencies

**Additional Analysis Scripts**:
- `live_signal_generator.py` - Real-time signal generation
- `percentile_forward_4h.py` - 4-hour timeframe analysis
- `advanced_backtest_runner.py` - Advanced backtesting
- Various test and validation scripts (test_*.py)

**Key Dependencies**:
- FastAPI 0.104.1 - Web framework
- pandas 2.1.3 - Data processing
- numpy 1.26.2 - Numerical computing
- yfinance 0.2.32 - Market data
- scipy 1.11.4 - Statistical analysis
- uvicorn - ASGI server

### Frontend Structure (`/frontend/`)
**Primary Language**: TypeScript/React
**Build Tool**: Vite 5.0

**Core Structure**:
```
frontend/
├── src/
│   ├── components/
│   │   ├── PerformanceMatrixHeatmap.tsx
│   │   ├── ReturnDistributionChart.tsx
│   │   ├── OptimalExitPanel.tsx
│   │   ├── TradingFramework/ (comprehensive trading framework)
│   │   └── GammaScanner/ (gamma wall scanner)
│   ├── api/
│   │   └── client.ts - Type-safe API client
│   ├── types/
│   │   └── index.ts - TypeScript definitions
│   ├── App.tsx - Main application
│   └── main.tsx - Entry point
├── package.json
└── vite.config.ts
```

**Key Dependencies**:
- React 18.2 - UI framework
- Material-UI 5.14 - Component library
- Plotly.js 2.27 - Interactive charts
- TanStack Query 5.8 - Data fetching
- Zustand 4.4 - State management
- Axios 1.6.2 - HTTP client

### Documentation (`/docs/`)
- Multiple implementation guides
- Methodology documents
- Integration reports
- Verification checklists

### Configuration Files
- `package.json` - Root package with @openrouter/sdk dependency
- `.gitignore` - Git ignore patterns (configured for OpenRouter SDK)
- `.env.example` - Environment variable template
- `docker-compose.yml` - Multi-container orchestration
- `.mcp.json` - MCP server configuration

## Core Responsibilities by Directory

### Backend Responsibilities
1. **Data Acquisition**: Fetch historical market data via yfinance
2. **Indicator Calculation**: Compute RSI, MA, and percentile rankings
3. **Backtesting**: Analyze D1-D21 performance across entry thresholds
4. **Monte Carlo Simulation**: Forward-looking probability analysis
5. **API Endpoints**: Serve data to frontend via RESTful API
6. **Caching**: Store and manage backtest results
7. **Statistical Analysis**: Risk metrics, trend testing, optimal exits

### Frontend Responsibilities
1. **User Interface**: Responsive dashboard with Material-UI
2. **Data Visualization**: Interactive heatmaps, charts, and graphs
3. **State Management**: Handle application state with Zustand
4. **API Integration**: Fetch and cache data with TanStack Query
5. **Type Safety**: Enforce TypeScript types throughout
6. **User Interactions**: Handle clicks, hovers, selections
7. **Export Functions**: Allow data export to CSV/Excel

### Trading Framework Components
The frontend includes an advanced trading framework:
- **Current Market State**: Real-time market condition display
- **Index Market State**: Broad market sentiment tracking
- **Swing Trading Framework**: Complete trading strategy dashboard
- **Expectancy Dashboard**: Position expectancy calculations
- **Instrument Ranking**: Multi-ticker performance comparison
- **Regime Indicator**: Market regime classification
- **Position Monitor**: Active position tracking

### Gamma Scanner Components
Specialized gamma exposure analysis:
- **Gamma Scanner Tab**: Main gamma wall analysis interface
- **Gamma Symbol Table**: Multi-symbol gamma exposure
- **Gamma Settings Sidebar**: Configuration panel

## Key Dependencies and Integration Points

### Backend → Data Sources
- **yfinance**: Yahoo Finance API for OHLCV data
- **5 years lookback**: Historical data depth

### Backend → Frontend
- **REST API**: http://localhost:8000
- **CORS enabled**: Cross-origin requests allowed
- **JSON responses**: Structured data exchange
- **Caching**: 24-hour TTL on backtest results

### Frontend → Backend
- **Axios client**: HTTP requests with interceptors
- **Type-safe**: Full TypeScript coverage
- **Error handling**: Comprehensive error boundaries
- **Retry logic**: Automatic retry on failures

### Development Tooling
- **SPARC Methodology**: Systematic development workflow
- **Claude Flow**: AI swarm coordination (NPM package)
- **MCP Servers**: Multi-agent coordination
- **Git Workflow**: Version control on codemacine/dev branch

## External Dependencies

### Python Backend
```
fastapi==0.104.1
pandas==2.1.3
numpy==1.26.2
yfinance==0.2.32
scipy==1.11.4
uvicorn[standard]
python-multipart
```

### TypeScript Frontend
```
react: ^18.2.0
@mui/material: ^5.14.18
plotly.js: ^2.27.1
@tanstack/react-query: ^5.8.4
axios: ^1.6.2
zustand: ^4.4.7
typescript: ^5.3.2
```

### Root Level
```
@openrouter/sdk: ^0.1.27
```

## Architectural Patterns

### Backend Patterns
- **MVC-style**: Models (data classes), Controllers (API), Views (JSON responses)
- **Caching Layer**: Results cached in `backend/cache/`
- **Async Processing**: Background tasks for long-running operations
- **Error Handling**: Try-catch with detailed error responses

### Frontend Patterns
- **Component-Based**: Reusable React components
- **Container/Presenter**: Smart containers, dumb presenters
- **Custom Hooks**: Reusable logic extraction
- **Type-First**: TypeScript interfaces before implementation

## Current Git State
- **Branch**: codemacine/dev
- **Main Branch**: main
- **Status**: Clean (no uncommitted changes)
- **Recent Activity**: OpenRouter SDK configuration and gitignore updates

## File Size Constraints
- **Modular Design**: Files kept under 500 lines where possible
- **Separation of Concerns**: Clear boundaries between modules
- **Clean Architecture**: Independent, testable components

## Development Environment
- **Platform**: Linux (Azure VM)
- **OS**: Ubuntu (Linux 6.8.0-1030-azure)
- **Working Directory**: /workspaces/New-test-strategy
- **Git Repo**: Yes
- **Current Date**: 2025-12-03

## Testing Infrastructure
- **Backend**: pytest framework (tests in progress)
- **Frontend**: Jest + React Testing Library (configured in package.json)
- **Test Directory**: `/tests/`

## Deployment Configuration
- **Docker Compose**: Multi-container setup ready
- **Environment Variables**: Templated in .env.example
- **Scripts**: `start.sh`, `start-backend.sh`, `start-frontend.sh`
- **Production**: Docker-ready for deployment

## AI Coordination Systems

### Claude Flow Integration
- **Location**: `/claude-flow/` directory
- **Purpose**: Swarm coordination and task orchestration
- **Commands**: Available via `npx claude-flow` (see CLAUDE.md)

### Code Machine
- **Location**: `/.codemachine/` directory
- **Agent Memory**: JSON files for different architect roles
- **Agents Defined**:
  - founder-architect
  - operational-architect
  - structural-data-architect
  - ui-ux-architect
  - behavior-architect
  - file-assembler
  - blueprint-orchestrator
- **Artifacts**: Planning and architecture manifests

### Hive Mind
- **Location**: `/.hive-mind/` directory
- **Purpose**: Collective intelligence coordination

## Known Configuration
- **OpenRouter SDK**: Recently added for AI/LLM integrations
- **MCP Servers**: Configured for multi-agent coordination
- **SPARC Workflow**: Implemented for systematic development

## Project Status
- **Phase**: Phase 1 Complete - MVP Fully Functional
- **Backend**: Operational with comprehensive API
- **Frontend**: Interactive dashboard deployed
- **Documentation**: Comprehensive guides available
- **Testing**: Frameworks in place, tests in progress
