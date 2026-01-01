/**
 * Strategy & Rules Panel Component
 * Displays percentile movement patterns, trend significance analysis, and trade management rules
 */

import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Chip,
  Alert,
  AlertTitle,
  Card,
  CardContent,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Timeline as TimelineIcon,
  ShowChart as ShowChartIcon,
} from '@mui/icons-material';
import {
  PercentileMovements,
  TrendAnalysis,
  TradeManagementRule,
} from '../types';

interface StrategyRulesPanelProps {
  percentileMovements: PercentileMovements;
  trendAnalysis: TrendAnalysis;
  tradeRules: TradeManagementRule[];
  ticker: string;
  threshold: number;
}

const StrategyRulesPanel: React.FC<StrategyRulesPanelProps> = ({
  percentileMovements,
  trendAnalysis,
  tradeRules,
  ticker,
  threshold,
}) => {
  // Get reversion analysis data
  const reversionAnalysis = percentileMovements?.reversion_analysis;

  // Determine reversion risk level
  const getReversionRisk = () => {
    if (!reversionAnalysis) return { level: 'Unknown', color: 'default' };
    const reversionPts = reversionAnalysis.reversion_from_peak;

    if (reversionPts < 5) return { level: 'Low', color: 'success' };
    if (reversionPts < 15) return { level: 'Moderate', color: 'warning' };
    return { level: 'High', color: 'error' };
  };

  const reversionRisk = getReversionRisk();

  // Get trend confidence
  const getTrendConfidence = () => {
    const pValue = trendAnalysis?.trend_p_value || 1;
    if (pValue < 0.01) return { level: 'Very High', color: 'success' };
    if (pValue < 0.05) return { level: 'High', color: 'info' };
    if (pValue < 0.10) return { level: 'Moderate', color: 'warning' };
    return { level: 'Low', color: 'error' };
  };

  const trendConfidence = getTrendConfidence();

  // Categorize rules by confidence
  const highConfidenceRules = tradeRules?.filter(r => r.confidence === 'High') || [];
  const mediumConfidenceRules = tradeRules?.filter(r => r.confidence === 'Medium') || [];

  const getRuleIcon = (type: string) => {
    switch (type) {
      case 'Exit Timing':
        return <TimelineIcon color="primary" />;
      case 'Trend Following':
        return <TrendingUpIcon color="success" />;
      case 'Early Exit Signal':
        return <WarningIcon color="warning" />;
      case 'Reversion Protection':
        return <ShowChartIcon color="error" />;
      default:
        return <InfoIcon />;
    }
  };

  return (
    <Box>
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          📊 Strategy & Rules Analysis - {ticker} (Entry ≤{threshold}%)
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Comprehensive analysis of percentile movements, trend significance, and actionable trade management rules
        </Typography>
      </Paper>

      <Grid container spacing={3}>
        {/* Trend Significance Analysis */}
        <Grid item xs={12} md={6}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ShowChartIcon color="primary" />
                📈 Trend Significance Analysis
              </Typography>

              <Box sx={{ mt: 2 }}>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Trend Direction
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                      {trendAnalysis?.trend_direction === 'Upward' ? (
                        <TrendingUpIcon color="success" />
                      ) : (
                        <TrendingDownIcon color="error" />
                      )}
                      <Typography variant="h6">
                        {trendAnalysis?.trend_direction || 'Unknown'}
                      </Typography>
                    </Box>
                  </Grid>

                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Statistical Confidence
                    </Typography>
                    <Chip
                      label={trendConfidence.level}
                      color={trendConfidence.color as any}
                      size="small"
                      sx={{ mt: 0.5 }}
                    />
                  </Grid>

                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Correlation
                    </Typography>
                    <Typography variant="h6">
                      {trendAnalysis?.trend_correlation?.toFixed(2) || 'N/A'}
                    </Typography>
                  </Grid>

                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      P-Value
                    </Typography>
                    <Typography variant="h6">
                      {trendAnalysis?.trend_p_value?.toFixed(3) || 'N/A'}
                    </Typography>
                  </Grid>

                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Peak Return Day
                    </Typography>
                    <Typography variant="h6">
                      D{trendAnalysis?.peak_day || 'N/A'}
                    </Typography>
                  </Grid>

                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Peak Return
                    </Typography>
                    <Typography variant="h6" color={trendAnalysis?.peak_return > 0 ? 'success.main' : 'error.main'}>
                      {trendAnalysis?.peak_return ? `${trendAnalysis.peak_return > 0 ? '+' : ''}${trendAnalysis.peak_return.toFixed(2)}%` : 'N/A'}
                    </Typography>
                  </Grid>
                </Grid>

                <Divider sx={{ my: 2 }} />

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Exit Timing Strategy
                </Typography>
                <Alert severity={trendAnalysis?.early_vs_late_p_value < 0.05 ? 'info' : 'warning'} sx={{ mt: 1 }}>
                  <AlertTitle>
                    {trendAnalysis?.early_vs_late_significance || 'Unknown'}
                  </AlertTitle>
                  {trendAnalysis?.early_vs_late_p_value < 0.05
                    ? `Later exits (D${Math.floor((trendAnalysis?.peak_day || 21) * 2 / 3)}-D21) significantly outperform early exits (p=${trendAnalysis?.early_vs_late_p_value?.toFixed(3)})`
                    : 'No clear timing advantage between early vs late exits'}
                </Alert>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Percentile Movement Patterns */}
        <Grid item xs={12} md={6}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TimelineIcon color="secondary" />
                🎯 Percentile Movement Patterns
              </Typography>

              {reversionAnalysis && (
                <Box sx={{ mt: 2 }}>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Reversion Risk
                      </Typography>
                      <Chip
                        label={reversionRisk.level}
                        color={reversionRisk.color as any}
                        size="small"
                        sx={{ mt: 0.5 }}
                      />
                    </Grid>

                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Typical Peak Percentile
                      </Typography>
                      <Typography variant="h6">
                        {reversionAnalysis.median_peak_percentile?.toFixed(0)}th
                      </Typography>
                    </Grid>

                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Reversion Magnitude
                      </Typography>
                      <Typography variant="h6" color="warning.main">
                        {reversionAnalysis.reversion_from_peak?.toFixed(0)} points
                      </Typography>
                    </Grid>

                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Final Percentile (Median)
                      </Typography>
                      <Typography variant="h6">
                        {reversionAnalysis.median_final_percentile?.toFixed(0)}th
                      </Typography>
                    </Grid>

                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">
                        Complete Failure Rate
                      </Typography>
                      <Typography variant="h6" color="error.main">
                        {reversionAnalysis.complete_reversion_rate?.toFixed(1)}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        (Percentage of trades falling below 20th percentile)
                      </Typography>
                    </Grid>
                  </Grid>

                  <Divider sx={{ my: 2 }} />

                  <Alert severity="info">
                    <AlertTitle>Peak Signal</AlertTitle>
                    When RSI-MA reaches {reversionAnalysis.median_peak_percentile?.toFixed(0)}th percentile,
                    expect {reversionAnalysis.reversion_from_peak?.toFixed(0)}-point decline toward exit
                  </Alert>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Trade Management Rules */}
        <Grid item xs={12}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CheckCircleIcon color="success" />
                ⚡ Strategic Trade Management
              </Typography>

              {highConfidenceRules.length > 0 && (
                <Box sx={{ mt: 2, mb: 3 }}>
                  <Alert severity="success" sx={{ mb: 2 }}>
                    <AlertTitle>Primary Strategy (High Confidence)</AlertTitle>
                    Based on statistically significant patterns from historical data
                  </Alert>
                  <List>
                    {highConfidenceRules.map((rule, idx) => (
                      <ListItem key={idx} sx={{ bgcolor: 'background.default', mb: 1, borderRadius: 1 }}>
                        <ListItemIcon>
                          {getRuleIcon(rule.type)}
                        </ListItemIcon>
                        <ListItemText
                          primary={rule.type}
                          secondary={rule.rule}
                          primaryTypographyProps={{ fontWeight: 'bold' }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {mediumConfidenceRules.length > 0 && (
                <Box>
                  <Alert severity="info" sx={{ mb: 2 }}>
                    <AlertTitle>Secondary Considerations (Medium Confidence)</AlertTitle>
                    Additional factors to consider in trade management
                  </Alert>
                  <List>
                    {mediumConfidenceRules.map((rule, idx) => (
                      <ListItem key={idx} sx={{ bgcolor: 'background.default', mb: 1, borderRadius: 1 }}>
                        <ListItemIcon>
                          {getRuleIcon(rule.type)}
                        </ListItemIcon>
                        <ListItemText
                          primary={rule.type}
                          secondary={rule.rule}
                          primaryTypographyProps={{ fontWeight: 'bold' }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {tradeRules.length === 0 && (
                <Alert severity="warning">
                  <AlertTitle>Insufficient Data</AlertTitle>
                  Not enough historical events to generate specific trade management rules.
                </Alert>
              )}

              <Divider sx={{ my: 3 }} />

              {/* Overall Strategy Recommendation */}
              <Box>
                <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                  Overall Strategy Recommendation:
                </Typography>
                <Alert
                  severity={
                    reversionRisk.level === 'High' ? 'error' :
                    trendAnalysis?.trend_direction === 'Upward' ? 'success' : 'warning'
                  }
                  sx={{ mt: 1 }}
                >
                  <AlertTitle>
                    {reversionRisk.level === 'High' && reversionAnalysis && trendAnalysis?.peak_day < 10
                      ? 'DEFENSIVE Strategy'
                      : trendAnalysis?.trend_strength > 0.7 && reversionRisk.level === 'Low'
                      ? 'AGGRESSIVE Strategy'
                      : 'MODERATE Strategy'}
                  </AlertTitle>
                  {reversionRisk.level === 'High' && reversionAnalysis && trendAnalysis?.peak_day < 10 ? (
                    <>Returns peak early with high reversion risk - exit at peak (D{trendAnalysis?.peak_day})</>
                  ) : trendAnalysis?.trend_strength > 0.7 && reversionRisk.level === 'Low' ? (
                    <>Strong trend with low reversion risk - use trailing stops and hold through D{trendAnalysis?.peak_day}</>
                  ) : trendAnalysis?.peak_day && reversionAnalysis ? (
                    <>Exit near return peak (D{trendAnalysis?.peak_day}) to avoid {reversionAnalysis.reversion_from_peak?.toFixed(0)}-point decline</>
                  ) : (
                    <>Use systematic profit-taking approach based on percentile targets</>
                  )}
                </Alert>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default StrategyRulesPanel;
