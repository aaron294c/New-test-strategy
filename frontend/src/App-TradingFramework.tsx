import React from 'react';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import TradingFrameworkDashboard from './components/TradingFramework/TradingFrameworkDashboard';

// Create dark theme matching the trading dashboard aesthetic
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#3B82F6',
      dark: '#1E40AF',
    },
    secondary: {
      main: '#8B5CF6',
    },
    success: {
      main: '#10B981',
      dark: '#047857',
    },
    warning: {
      main: '#FBBF24',
      dark: '#D97706',
    },
    error: {
      main: '#EF4444',
      dark: '#B91C1C',
    },
    info: {
      main: '#06B6D4',
      dark: '#0E7490',
    },
    background: {
      default: '#0F172A',
      paper: '#1E293B',
    },
    text: {
      primary: '#F1F5F9',
      secondary: '#94A3B8',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h6: {
      fontWeight: 600,
    },
    subtitle1: {
      fontWeight: 500,
    },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          fontWeight: 600,
          backgroundColor: '#0F172A',
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <TradingFrameworkDashboard />
    </ThemeProvider>
  );
}

export default App;
