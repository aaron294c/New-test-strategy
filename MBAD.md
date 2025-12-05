//@version=6
indicator('MBAD (Mean Reversion + Trend Toggle) - Advanced with Unified Diagnostics', overlay=true)

// === INPUTS ===
src   = input(close, 'Source')
len   = input(256, 'Length')
time_ = input(true , 'Time Weighting', inline = 'w1', group='Weights')
iv    = input(true , 'Inferred Volume Weighting', inline = 'w1', group='Weights')
mode  = input.string("Mean Reversion", options=["Mean Reversion", "Trend Following"], title="Interpretation Mode")

// === VISIBILITY TOGGLES ===
showFadeLabels       = input.bool(true, "Show Fade Labels", group="Visibility")
showDivergenceLabels = input.bool(true, "Show Skew Divergence Labels", group="Visibility")
showMarketPhaseLabels = input.bool(true, "Show Market Phase Labels", group="Visibility") // Renamed to Consensus Labels in UI
showSkewCoCLabels    = input.bool(true, "Show Skew Change of Character Labels", group="Visibility")
showActionSignals    = input.bool(true, "Show Action Signals", group="Visibility")
showAsymmetrySkewLabels = input.bool(true, "Show Asymmetry Skew Labels", group="Visibility")
showDistributionBiasLabels = input.bool(true, "Show Distribution Bias Labels", group="Visibility")


// === FADE SENSITIVITY SETTINGS ===
fade_zscore_thresh     = input.float(1.5, "Fade Z-Score Threshold", step=0.1, group="Fade Settings")
fade_skew_thresh       = input.float(0.8, "Fade Skew Threshold", step=0.1, group="Fade Settings")
fade_asymmetry_thresh  = input.float(1.4, "Fade Asymmetry Threshold", step=0.1, group="Fade Settings")
use_or_logic           = input.bool(false, "Use OR instead of AND for Fade Conditions", group="Fade Settings")

// === DIAGNOSTIC THRESHOLDS ===
group_diag_thresh = "Diagnostic Thresholds"
inner_asymmetry_thresh_high = input.float(1.2, "Inner Asymmetry High Threshold", step=0.05, group=group_diag_thresh)
inner_asymmetry_thresh_low  = input.float(0.8, "Inner Asymmetry Low Threshold", step=0.05, group=group_diag_thresh)
outer_asymmetry_thresh_high = input.float(1.2, "Outer Asymmetry High Threshold", step=0.05, group=group_diag_thresh)
outer_asymmetry_thresh_low  = input.float(0.8, "Outer Asymmetry Low Threshold", step=0.05, group=group_diag_thresh)
outer_inner_ratio_thresh_high = input.float(1.2, "Outer/Inner Ratio High Threshold", step=0.05, group=group_diag_thresh)
outer_inner_ratio_thresh_low  = input.float(0.8, "Outer/Inner Ratio Low Threshold", step=0.05, group=group_diag_thresh)

// === CHANGE LOOKBACK PERIODS ===
lookback_period_15day = input.int(15, "15-Candle Change Lookback", minval=1, group="Change Settings")
lookback_period_5day  = input.int(5, "5-Candle Change Lookback", minval=1, group="Change Settings")
change_pos_thresh = input.float(5.0, "Change Positive Threshold (%)", step=0.1, group="Change Settings")
change_neg_thresh = input.float(-5.0, "Change Negative Threshold (%)", step=0.1, group="Change Settings")
price_change_thresh_perc = input.float(0.5, "Price Change Threshold (%) for Directional Bias", step=0.1, group="Change Settings")

// === MOMENT CALCULATION ===
// Function to calculate weighted moments (mean, standard deviation, skew, kurtosis, etc.)
weighted_moments(data, weights, len) =>
    sum_m1 = 0.0
    sum_m2 = 0.0
    sum_m3 = 0.0
    sum_m4 = 0.0
    sum_m5 = 0.0
    sum_m6 = 0.0
    sum_w  = 0.0
    for i = 0 to len - 1
        datum  = data.get(i)
        weight = weights.get(i)
        sum_w  += weight
        sum_m1 += datum * weight
    mean = sum_m1 / sum_w

    for i = 0 to len - 1
        datum  = data.get(i)
        weight = weights.get(i)
        diff   = datum - mean
        sum_m2 += math.pow(diff, 2) * weight
        sum_m3 += math.pow(diff, 3) * weight
        sum_m4 += math.pow(diff, 4) * weight
        sum_m5 += math.pow(diff, 5) * weight
        sum_m6 += math.pow(diff, 6) * weight

    dev   = math.sqrt(sum_m2 / sum_w)
    skew  = sum_m3 / sum_w / math.pow(dev, 3)
    kurt  = sum_m4 / sum_w / math.pow(dev, 4)
    hskew = sum_m5 / sum_w / math.pow(dev, 5) // Higher skew
    hkurt = sum_m6 / sum_w / math.pow(dev, 6) // Higher kurtosis
    [mean, dev, skew, kurt, hskew, hkurt]

// === DATA & WEIGHTS PREPARATION ===
// Initialize arrays for data and weights
data    = array.new_float(len)
weights = array.new_float(len)

// Populate data and weights arrays
for i = 0 to len - 1
    // Calculate weight based on time weighting and inferred volume weighting
    weight = (time_ ? (len - i) : 1) * (iv ? math.abs(close[i] - open[i]) : 1)
    data.set(i, src[i])
    weights.set(i, weight)

// Calculate moments using the weighted_moments function
[mean, dev, skew, kurt, hskew, hkurt] = weighted_moments(data, weights, len)

// === MBAD LEVELS CALCULATION ===
// Calculate Z-score for the current close price
zscore = (close - mean) / dev

// Calculate various MBAD levels (limits, extensions, deviations, and basis)
lim_lower  = math.round_to_mintick(mean - dev * hkurt + dev * hskew)
ext_lower  = math.round_to_mintick(mean - dev * kurt + dev * skew)
dev_lower  = math.round_to_mintick(mean - dev)
dev_lower2 = math.round_to_mintick(mean - 2*dev)
basis      = math.round_to_mintick(mean)
dev_upper  = math.round_to_mintick(mean + dev)
ext_upper  = math.round_to_mintick(mean + dev * kurt + dev * skew)
lim_upper  = math.round_to_mintick(mean + dev * hkurt + dev * hskew)

// Plot MBAD levels on the chart
plot(lim_lower , 'Lower Limit', color.new(color.red, 0)   , 1, plot.style_stepline)
plot(ext_lower , 'Lower Extension', color.new(color.blue, 0)   , 2, plot.style_stepline)
plot(dev_lower , 'Lower Deviation', color.new(color.gray, 0)   , 1, plot.style_stepline)
plot(dev_lower2, 'Lower Deviation 2', color.new(color.gray, 0)   , 1, plot.style_stepline)
plot(basis     , 'Mean'            , color.new(color.purple, 0), 2, plot.style_stepline)
plot(dev_upper , 'Upper Deviation', color.new(color.gray, 0)   , 1, plot.style_stepline)
plot(ext_upper , 'Upper Extension', color.new(color.red, 0)    , 2, plot.style_stepline)
plot(lim_upper , 'Upper Limit'    , color.new(color.blue, 0)   , 1, plot.style_stepline)

// Background coloring for extreme price zones
bgcolor(close > ext_upper ? color.new(color.red, 85) : na)
bgcolor(close < ext_lower ? color.new(color.green, 85) : na)

// === LABEL FOR EXTREME EXTENSION ZONE ===
// Label appears when price enters or remains in the extreme extension zone
if close > ext_upper
    label.new(bar_index, high, "Extreme Extension Zone (Upper)", style=label.style_label_down, color=color.new(color.red, 0), textcolor=color.white, size=size.small)
if close < ext_lower
    label.new(bar_index, low, "Extreme Extension Zone (Lower)", style=label.style_label_up, color=color.new(color.green, 0), textcolor=color.white, size=size.small)


// === ASYMMETRY CALCULATION ===
// Calculate distances for inner and outer asymmetry
inner_upper_dist = ext_upper - mean
inner_lower_dist = mean - ext_lower
outer_upper_dist = lim_upper - mean
outer_lower_dist = mean - lim_lower

// Calculate asymmetry ratios
inner_asymmetry_ratio = inner_upper_dist / inner_lower_dist
outer_asymmetry_ratio = outer_upper_dist / outer_lower_dist

// Plot asymmetry ratios as histograms
plot(inner_asymmetry_ratio, "Inner Asymmetry Ratio", color=color.new(color.blue, 0), style=plot.style_histogram, linewidth=2)
plot(outer_asymmetry_ratio, "Outer Asymmetry Ratio", color=color.new(color.purple, 0), style=plot.style_histogram, linewidth=2)

// === LABEL STACKING OFFSETS ===
// Define offsets for vertical stacking of labels
// Increased label_offset_step for better separation and clearer visibility
var float label_offset_step = 0.035 // Increased for more spacing
price_label_pos_base = high * 1.005
price_label_neg_base = low * 0.995

// Positive offsets (above price) - ordered by general priority/frequency
price_label_pos_offset1 = price_label_pos_base + (high * label_offset_step * 0) // Consensus (Positive)
price_label_pos_offset2 = price_label_pos_base + (high * label_offset_step * 1) // Asymmetry Skew (Positive) / Fade Down
price_label_pos_offset3 = price_label_pos_base + (high * label_offset_step * 2) // Distribution Short Bias / Skew Negative / Divergence from Skew (Down)
price_label_pos_offset4 = price_label_pos_base + (high * label_offset_step * 3) // Trend Follow Down

// Negative offsets (below price) - ordered by general priority/frequency
price_label_neg_offset1 = price_label_neg_base - (low * label_offset_step * 0) // Consensus (Negative)
price_label_neg_offset2 = price_label_neg_base - (low * label_offset_step * 1) // Asymmetry Skew (Negative) / Fade Up
price_label_neg_offset3 = price_label_neg_base - (low * label_offset_step * 2) // Distribution Long Bias / Skew Positive/Neutralising / Divergence from Skew (Up)
price_label_neg_offset4 = price_label_neg_base - (low * label_offset_step * 3) // Trend Follow Up


// === ASYMMETRY-BASED SKEW LABELS (from previous version) ===
if showAsymmetrySkewLabels
    if inner_asymmetry_ratio > 1.5
        label.new(bar_index, price_label_pos_offset2, "Moderate Positive Skew", color=color.new(color.blue, 0), textcolor=color.white, size=size.small)
    if inner_asymmetry_ratio < 0.7
        label.new(bar_index, price_label_neg_offset2, "Moderate Negative Skew", color=color.new(color.orange, 0), textcolor=color.white, size=size.small)
    if outer_asymmetry_ratio > 1.5
        label.new(bar_index, price_label_pos_offset2, "Strong Positive Skew", color=color.new(color.green, 0), textcolor=color.white, size=size.small)
    if outer_asymmetry_ratio < 0.7
        label.new(bar_index, price_label_neg_offset2, "Strong Negative Skew", color=color.new(color.red, 0), textcolor=color.white, size=size.small)

// === OSCILLATOR FOR BIAS INDICATION (from previous version) ===
exp_return_proxy = skew * dev
plot(exp_return_proxy, title="Expected Return Proxy", color=color.new(color.fuchsia, 0), linewidth=2)

// === CROSSOVER SIGNAL LABEL: Distribution Flip (from previous version) ===
skew_cross_up = ta.crossover(skew, 0)
skew_cross_down = ta.crossunder(skew, 0)
if showDistributionBiasLabels
    if skew_cross_up
        label.new(bar_index, price_label_neg_offset3, "Distribution → Long Bias", style=label.style_label_up, color=color.new(color.green, 0), textcolor=color.white, size=size.small)
    if skew_cross_down
        label.new(bar_index, price_label_pos_offset3, "Distribution → Short Bias", style=label.style_label_down, color=color.new(color.red, 0), textcolor=color.white, size=size.small)

// === CHANGE OF CHARACTER: SKEW ===
// Smooth skew and calculate skew delta for change of character detection
skew_smooth = ta.sma(skew, 5)
skew_delta = skew_smooth - skew_smooth[1]

// Define conditions for skew change of character
coc_positive     = skew_delta > 0 and skew_smooth[1] < 0 and skew_smooth > 0
coc_neutralising = skew_smooth > skew_smooth[1] and skew_smooth < 0 and skew_smooth > -0.2
coc_negative     = skew_delta < 0 and skew_smooth[1] > 0 and skew_smooth < 0

// Display labels for skew change of character if enabled
if showSkewCoCLabels
    if coc_positive
        label.new(bar_index, price_label_neg_offset4, "Skew → Positive", style=label.style_label_up, color=color.new(color.green, 0), textcolor=color.white, size=size.small)
    if coc_neutralising
        label.new(bar_index, price_label_neg_offset4, "Skew Neutralising", style=label.style_label_up, color=color.new(color.orange, 0), textcolor=color.white, size=size.small)
    if coc_negative
        label.new(bar_index, price_label_pos_offset4, "Skew → Negative", style=label.style_label_down, color=color.new(color.red, 0), textcolor=color.white, size=size.small)

// === DIVERGENCE FROM SKEW (REFINED from previous version) ===
// Note: skew_delta is already calculated above
if showDivergenceLabels
    // Adjusted offsets to prevent overlap with other labels
    if high > high[1] and skew_delta < -0.2
        label.new(bar_index, price_label_pos_offset3, "Divergence from Skew", color=color.new(color.orange, 0), textcolor=color.black, style=label.style_label_down)
    if low < low[1] and skew_delta > 0.2
        label.new(bar_index, price_label_neg_offset3, "Divergence from Skew", color=color.new(color.orange, 0), textcolor=color.black, style=label.style_label_up)


// === INTERPRETATION LOGIC ===
// Calculate the ratio of outer to inner asymmetry, and smooth it
asymmetry_ratio_ratio = outer_asymmetry_ratio / inner_asymmetry_ratio
smooth_ratio = ta.sma(asymmetry_ratio_ratio, 5)
plot(smooth_ratio, "Outer/Inner Asymmetry Ratio (Smoothed)", color=color.new(color.fuchsia, 0), linewidth=2)

// Define market phase based on asymmetry ratios and user-defined thresholds
// CORRECTED LOGIC: Using configurable thresholds for clearer distinction and alignment with user's bias
var bool is_trend_confirming_bull = inner_asymmetry_ratio > inner_asymmetry_thresh_high and outer_asymmetry_ratio > outer_asymmetry_thresh_high and (asymmetry_ratio_ratio >= outer_inner_ratio_thresh_low and asymmetry_ratio_ratio <= outer_inner_ratio_thresh_high)
var bool is_trend_confirming_bear = inner_asymmetry_ratio < inner_asymmetry_thresh_low and outer_asymmetry_ratio < outer_asymmetry_thresh_low and (asymmetry_ratio_ratio >= outer_inner_ratio_thresh_low and asymmetry_ratio_ratio <= outer_inner_ratio_thresh_high)

var bool is_tail_risk_building_bull = inner_asymmetry_ratio >= inner_asymmetry_thresh_low and inner_asymmetry_ratio <= inner_asymmetry_thresh_high and outer_asymmetry_ratio > outer_asymmetry_thresh_high and asymmetry_ratio_ratio > outer_inner_ratio_thresh_high
var bool is_tail_risk_building_bear = inner_asymmetry_ratio >= inner_asymmetry_thresh_low and inner_asymmetry_ratio <= inner_asymmetry_thresh_high and outer_asymmetry_ratio < outer_asymmetry_thresh_low and asymmetry_ratio_ratio < outer_inner_ratio_thresh_low

// Adjusted mean-reverting conditions to better capture overextension and bias
// For mean-reverting bear: price is overextended up (high Z-score), and inner asymmetry shows negative bias (or neutral/mild positive)
// and outer asymmetry suggests compression/reversion.
var bool is_mean_reverting_bear_cond = zscore > fade_zscore_thresh and inner_asymmetry_ratio <= inner_asymmetry_thresh_high and outer_asymmetry_ratio < outer_asymmetry_thresh_low and asymmetry_ratio_ratio < outer_inner_ratio_thresh_low
// For mean-reverting bull: price is overextended down (low Z-score), and inner asymmetry shows positive bias (or neutral/mild negative)
// and outer asymmetry suggests expansion/reversion.
var bool is_mean_reverting_bull_cond = zscore < -fade_zscore_thresh and inner_asymmetry_ratio >= inner_asymmetry_thresh_low and outer_asymmetry_ratio > outer_asymmetry_thresh_high and asymmetry_ratio_ratio > outer_inner_ratio_thresh_high


// Adding a general "Strong Bias" category if precise conditions aren't met but overall direction is clear
var bool is_strong_bearish_bias = skew < -0.1 and inner_asymmetry_ratio < inner_asymmetry_thresh_low and outer_asymmetry_ratio < outer_asymmetry_thresh_low
var bool is_strong_bullish_bias = skew > 0.1 and inner_asymmetry_ratio > inner_asymmetry_thresh_high and outer_asymmetry_ratio > outer_asymmetry_thresh_high

// Check for consolidation based on Outer/Inner Ratio
var bool is_consolidating = asymmetry_ratio_ratio >= outer_inner_ratio_thresh_low and asymmetry_ratio_ratio <= outer_inner_ratio_thresh_high


// Assign consensus label and color - ensuring only one is assigned based on priority
var string consensus_label = "– Undefined"
var color consensus_color = color.gray

// Prioritize Mean-Reverting at extremes, then strong trends, then tail risk, then general bias, then consolidation
if is_mean_reverting_bear_cond // Overextended up, and mean-reverting pattern (pullback likely)
    consensus_label := "⬇️ Mean-Reverting (Bear)"
    consensus_color := color.orange
else if is_mean_reverting_bull_cond // Overextended down, and mean-reverting pattern (bounce likely)
    consensus_label := "⬆️ Mean-Reverting (Bull)"
    consensus_color := color.lime
else if is_trend_confirming_bear // Clear bearish trend confirmation
    consensus_label := "🔽 Trend Confirming (Bear)"
    consensus_color := color.red
else if is_trend_confirming_bull // Clear bullish trend confirmation
    consensus_label := "🔼 Trend Confirming (Bull)"
    consensus_color := color.green
else if is_tail_risk_building_bear // Bearish tail risk building
    consensus_label := "⬇️ Tail Risk Building (Bear)"
    consensus_color := color.purple
else if is_tail_risk_building_bull // Bullish tail risk building
    consensus_label := "⬆️ Tail Risk Building (Bull)"
    consensus_color := color.new(color.fuchsia, 0)
else if is_consolidating // Market is consolidating
    consensus_label := "↔️ Consolidating/Indecisive"
    consensus_color := color.gray
else if is_strong_bearish_bias // General strong bearish bias (fallback)
    consensus_label := "⬇️ Strong Bearish Bias"
    consensus_color := color.red // Use red for strong bearish bias
else if is_strong_bullish_bias
    consensus_label := "⬆️ Strong Bullish Bias"
    consensus_color := color.green // Use green for strong bullish bias
else
    consensus_label := "– Undefined"
    consensus_color := color.gray


// === HELPER FUNCTIONS FOR CHANGE CALCULATION AND DESCRIPTION ===
// Function to calculate percentage change, handling NA and division by zero
f_calc_perc_change(current_val, prev_val) =>
    if na(current_val) or na(prev_val) or prev_val == 0
        na(current_val) and na(prev_val) ? na : 0.0 // Return NA if both NA, else 0.0 (no change from zero)
    else
        (current_val - prev_val) / prev_val * 100

// Determine 5-day price direction
var string price_direction_5day = ""
price_change_5day_perc = f_calc_perc_change(close, close[lookback_period_5day])

if price_change_5day_perc > price_change_thresh_perc
    price_direction_5day := "Up"
else if price_change_5day_perc < -price_change_thresh_perc
    price_direction_5day := "Down"
else
    price_direction_5day := "Flat"

// Helper functions for Metric Bias Classification (consistent with threshold inputs)
// These define if a *single value* has a particular bias based on thresholds
f_is_inner_asymmetry_bull_trend_bias(ia_val) => ia_val > inner_asymmetry_thresh_high
f_is_inner_asymmetry_bear_trend_bias(ia_val) => ia_val < inner_asymmetry_thresh_low
f_is_inner_asymmetry_neutral_bias(ia_val) => ia_val >= inner_asymmetry_thresh_low and ia_val <= inner_asymmetry_thresh_high

f_is_outer_asymmetry_bull_trend_bias(oa_val) => oa_val > outer_asymmetry_thresh_high
f_is_outer_asymmetry_bear_trend_bias(oa_val) => oa_val < outer_asymmetry_thresh_low
f_is_outer_asymmetry_neutral_bias(oa_val) => oa_val >= outer_asymmetry_thresh_low and oa_val <= outer_asymmetry_thresh_high

f_is_outer_inner_ratio_bull_trend_bias(oir_val) => oir_val > outer_inner_ratio_thresh_high
f_is_outer_inner_ratio_bear_reversion_bias(oir_val) => oir_val < outer_inner_ratio_thresh_low
f_is_outer_inner_ratio_neutral_bias(oir_val) => oir_val >= outer_inner_ratio_thresh_low and oir_val <= outer_inner_ratio_thresh_high

f_is_skew_bull_bias(s_val) => s_val > 0.1
f_is_skew_bear_bias(s_val) => s_val < -0.1
f_is_skew_neutral_bias(s_val) => math.abs(s_val) <= 0.1

f_is_zscore_overbought_bias(zs_val) => zs_val > fade_zscore_thresh
f_is_zscore_oversold_bias(zs_val) => zs_val < -fade_zscore_thresh
f_is_zscore_neutral_bias(zs_val) => math.abs(zs_val) <= fade_zscore_thresh


// Function to get a descriptive string for percentage change, tailored for "next steps" with directional bias
// This function now robustly handles transitions into/out of neutral zones and clarifies trend/reversion states.
f_get_next_step_from_change(current_val, prev_val, change_perc, pos_thresh, neg_thresh, price_dir_5day, metric_type, zscore_current) =>
    string result = "Consolidation / Indecisive"

    // Determine bias of previous and current value for the specific metric
    bool prev_is_bull_trend = false
    bool prev_is_bear_trend = false
    bool prev_is_bull_reversion = false // A state where current value suggests potential for upward reversion
    bool prev_is_bear_reversion = false // A state where current value suggests potential for downward reversion

    bool current_is_bull_trend = false
    bool current_is_bear_trend = false
    bool current_is_bull_reversion = false
    bool current_is_bear_reversion = false
    bool current_is_neutral = false

    if metric_type == "IA"
        prev_is_bull_trend     := f_is_inner_asymmetry_bull_trend_bias(prev_val)
        prev_is_bear_trend     := f_is_inner_asymmetry_bear_trend_bias(prev_val)
        prev_is_bull_reversion := f_is_inner_asymmetry_bear_trend_bias(prev_val) // Low IA can lead to bull reversion
        prev_is_bear_reversion := f_is_inner_asymmetry_bull_trend_bias(prev_val) // High IA can lead to bear reversion
        current_is_bull_trend  := f_is_inner_asymmetry_bull_trend_bias(current_val)
        current_is_bear_trend  := f_is_inner_asymmetry_bear_trend_bias(current_val)
        current_is_bull_reversion := f_is_inner_asymmetry_bear_trend_bias(current_val)
        current_is_bear_reversion := f_is_inner_asymmetry_bull_trend_bias(current_val)
        current_is_neutral     := f_is_inner_asymmetry_neutral_bias(current_val)
    else if metric_type == "OA"
        prev_is_bull_trend     := f_is_outer_asymmetry_bull_trend_bias(prev_val)
        prev_is_bear_trend     := f_is_outer_asymmetry_bear_trend_bias(prev_val)
        prev_is_bull_reversion := f_is_outer_asymmetry_bear_trend_bias(prev_val) // Low OA can lead to bull reversion
        prev_is_bear_reversion := f_is_outer_asymmetry_bull_trend_bias(prev_val) // High OA can lead to bear reversion
        current_is_bull_trend  := f_is_outer_asymmetry_bull_trend_bias(current_val)
        current_is_bear_trend  := f_is_outer_asymmetry_bear_trend_bias(current_val)
        current_is_bull_reversion := f_is_outer_asymmetry_bear_trend_bias(current_val)
        current_is_bear_reversion := f_is_outer_asymmetry_bull_trend_bias(current_val)
        current_is_neutral     := f_is_outer_asymmetry_neutral_bias(current_val)
    else if metric_type == "OIR"
        prev_is_bull_trend     := f_is_outer_inner_ratio_bull_trend_bias(prev_val) // High OIR means bull trend bias
        prev_is_bear_trend     := f_is_outer_inner_ratio_bear_reversion_bias(prev_val) // Low OIR means bear reversion bias (counter-trend)
        prev_is_bull_reversion := f_is_outer_inner_ratio_bear_reversion_bias(prev_val) // Low OIR means potential bull reversion
        prev_is_bear_reversion := f_is_outer_inner_ratio_bull_trend_bias(prev_val) // High OIR means potential bear reversion
        current_is_bull_trend  := f_is_outer_inner_ratio_bull_trend_bias(current_val)
        current_is_bear_trend  := f_is_outer_inner_ratio_bear_reversion_bias(current_val)
        current_is_bull_reversion := f_is_outer_inner_ratio_bear_reversion_bias(current_val)
        current_is_bear_reversion := f_is_outer_inner_ratio_bull_trend_bias(current_val)
        current_is_neutral     := f_is_outer_inner_ratio_neutral_bias(current_val)
    else if metric_type == "Skew"
        prev_is_bull_trend     := f_is_skew_bull_bias(prev_val)
        prev_is_bear_trend     := f_is_skew_bear_bias(prev_val)
        // For skew, reversion depends on zscore context at extreme skew
        prev_is_bull_reversion := f_is_skew_bear_bias(prev_val) and f_is_zscore_oversold_bias(zscore_current)
        prev_is_bear_reversion := f_is_skew_bull_bias(prev_val) and f_is_zscore_overbought_bias(zscore_current)
        current_is_bull_trend  := f_is_skew_bull_bias(current_val)
        current_is_bear_trend  := f_is_skew_bear_bias(current_val)
        current_is_bull_reversion := f_is_skew_bear_bias(current_val) and f_is_zscore_oversold_bias(zscore_current)
        current_is_bear_reversion := f_is_skew_bull_bias(current_val) and f_is_zscore_overbought_bias(zscore_current)
        current_is_neutral     := f_is_skew_neutral_bias(current_val)
    else if metric_type == "ZScore"
        // Z-score is primarily about overextension and reversion
        prev_is_bull_reversion := f_is_zscore_oversold_bias(prev_val)
        prev_is_bear_reversion := f_is_zscore_overbought_bias(prev_val)
        current_is_bull_reversion := f_is_zscore_oversold_bias(current_val)
        current_is_bear_reversion := f_is_zscore_overbought_bias(current_val)
        current_is_neutral     := f_is_zscore_neutral_bias(current_val)
        // Z-score doesn't indicate trend in the same way, so trend flags are generally false for Z-score
        prev_is_bull_trend := false
        prev_is_bear_trend := false
        current_is_bull_trend := false
        current_is_bear_trend := false

    if na(change_perc)
        result := "N/A - Insufficient Data"
    else if current_is_neutral // Metric value is currently in the neutral zone
        if change_perc < neg_thresh // Metric is decreasing into neutral
            if prev_is_bull_trend or prev_is_bull_reversion // Was bullish/reversion-up, now neutralizing downwards
                result := "Neutralizing from Bullish Bias"
            else if prev_is_bear_trend or prev_is_bear_reversion // Was bearish/reversion-down, still neutralizing downwards
                result := "Consolidating, Bearish Decel." // Less specific if already bearish
            else
                result := "Entering Consolidation (Decel.)"
        else if change_perc > pos_thresh // Metric is increasing into neutral
            if prev_is_bear_trend or prev_is_bear_reversion // Was bearish/reversion-down, now neutralizing upwards
                result := "Neutralizing from Bearish Bias"
            else if prev_is_bull_trend or prev_is_bull_reversion // Was bullish/reversion-up, still neutralizing upwards
                result := "Consolidating, Bullish Decel." // Less specific if already bullish
            else
                result := "Entering Consolidation (Accel.)"
        else // Stable in neutral
            result := "Consolidation Confirmed"
    else if change_perc > pos_thresh // Metric is significantly increasing
        if current_is_bull_trend // Current value supports bullish trend, and it's increasing
            result := "Trend Strength Accel. (Up)"
        else if current_is_bear_trend // Current value supports bearish trend, but it's increasing (rare for trend, but could be specific reversals)
            result := "Bearish Trend Weakening (Up)" // E.g., low OA increasing
        else if current_is_bull_reversion // Current value supports upward reversion, and it's increasing
            result := "Mean Rev. Momentum (Up)"
        else if current_is_bear_reversion // Current value supports downward reversion, but it's increasing (less common)
            result := "Mean Rev. Potential (Building)" // E.g., Z-score getting more overbought
        else
            result := "Increasing (Bias Indefinite)"

    else if change_perc < neg_thresh // Metric is significantly decreasing
        if current_is_bear_trend // Current value supports bearish trend, and it's decreasing
            result := "Trend Strength Accel. (Down)"
        else if current_is_bull_trend // Current value supports bullish trend, but it's decreasing
            result := "Bullish Trend Weakening (Down)" // E.g., high IA/OA decreasing
        else if current_is_bear_reversion // Current value supports downward reversion, and it's decreasing
            result := "Mean Rev. Momentum (Down)"
        else if current_is_bull_reversion // Current value supports upward reversion, but it's decreasing
            result := "Mean Rev. Potential (Diminishing)" // E.g., Z-score getting more oversold
        else
            result := "Decreasing (Bias Indefinite)"
    else // Metric is stable/flat AND not in neutral bias (handled above for neutral)
        if current_is_bull_trend
            result := "Bullish Trend Sustained"
        else if current_is_bear_trend
            result := "Bearish Trend Sustained"
        else if current_is_bull_reversion
            result := "Bullish Reversion Sustained"
        else if current_is_bear_reversion
            result := "Bearish Reversion Sustained"
        else
            result := "Stable (Bias Undefined)"

    result

// === CALCULATE 5-CANDLE AND 15-CANDLE CHANGES ===
inner_asymmetry_ratio_prev_15day = inner_asymmetry_ratio[lookback_period_15day]
outer_asymmetry_ratio_prev_15day = outer_asymmetry_ratio[lookback_period_15day]
asymmetry_ratio_ratio_prev_15day = asymmetry_ratio_ratio[lookback_period_15day]

inner_asymmetry_change_15day = f_calc_perc_change(inner_asymmetry_ratio, inner_asymmetry_ratio_prev_15day)
outer_asymmetry_change_15day = f_calc_perc_change(outer_asymmetry_ratio, outer_asymmetry_ratio_prev_15day)
outer_inner_ratio_change_15day = f_calc_perc_change(asymmetry_ratio_ratio, asymmetry_ratio_ratio_prev_15day)

inner_asymmetry_ratio_prev_5day = inner_asymmetry_ratio[lookback_period_5day]
outer_asymmetry_ratio_prev_5day = outer_asymmetry_ratio[lookback_period_5day]
asymmetry_ratio_ratio_prev_5day = asymmetry_ratio_ratio[lookback_period_5day]

inner_asymmetry_change_5day = f_calc_perc_change(inner_asymmetry_ratio, inner_asymmetry_ratio_prev_5day)
outer_asymmetry_change_5day = f_calc_perc_change(outer_asymmetry_ratio, outer_asymmetry_ratio_prev_5day)
outer_inner_ratio_change_5day = f_calc_perc_change(asymmetry_ratio_ratio, asymmetry_ratio_ratio_prev_5day)


// === INDIVIDUAL METRIC INTERPRETATIONS ===
// Skew Interpretation (reflects current state)
f_getSkewInterpretation(s) =>
    if s > 0.5
        "Strong positive skew (bullish distribution)"
    else if s > 0.1
        "Mild positive skew (bullish bias)"
    else if s < -0.5
        "Strong negative skew (bearish distribution)"
    else if s < -0.1
        "Mild negative skew (bearish bias)"
    else
        "Near zero skew (neutral distribution)"

// Z-Score Interpretation (reflects current state)
f_getZScoreInterpretation(zs) =>
    if zs > 2.0
        "Extremely Overbought (High Risk of Pullback)"
    else if zs > 1.0
        "Overextended (Potential for Pullback)"
    else if zs < -2.0
        "Extremely Oversold (High Risk of Bounce)"
    else if zs < -1.0
        "Underextended (Potential for Bounce)"
    else
        "Within 1σ — Neutral Price Range"

// Inner Asymmetry Interpretation (reflects current state)
f_getInnerAsymmetryInterpretation(ia, h_thresh, l_thresh) =>
    if ia > h_thresh
        "Strong upside body bias (indicates positive momentum)"
    else if ia < l_thresh
        "Strong downside body bias (indicates weakness/reversion)"
    else
        "Neutral body skew (consolidation/balance)"

// Outer Asymmetry Interpretation (reflects current state)
f_getOuterAsymmetryInterpretation(oa, h_thresh, l_thresh) =>
    if oa > h_thresh
        "Tails exploding (strong momentum/trend strength)"
    else if oa < l_thresh
        "Tails compressing (strong mean reversion pressure)"
    else
        "Tail bias mild (neutral/indecisive)"

// Outer/Inner Ratio Interpretation (reflects current state)
f_getOuterInnerRatioInterpretation(oir, h_thresh, l_thresh) =>
    if oir > h_thresh
        "Tail > body (strong trend continuation likely)"
    else if oir < l_thresh
        "Body > tail (strong mean reversion likely)"
    else
        "Balanced (consolidation/indecisive)"

// === NEXT STEPS / DIAGNOSIS (WITH MULTI-PERIOD CHANGE CONTEXT) ===
// Skew Next Steps
f_getSkewNextSteps(s, prev_s, change_5day_perc, price_dir_5day, zscore_current) =>
    f_get_next_step_from_change(s, prev_s, change_5day_perc, change_pos_thresh, change_neg_thresh, price_dir_5day, "Skew", zscore_current)

// Z-Score Next Steps
f_getZScoreNextSteps(zs, prev_zs, change_5day_perc, price_dir_5day) =>
    f_get_next_step_from_change(zs, prev_zs, change_5day_perc, change_pos_thresh, change_neg_thresh, price_dir_5day, "ZScore", zs)

// Inner Asymmetry Next Steps
f_getInnerAsymmetryNextSteps(ia, prev_ia, change_5day_perc, price_dir_5day, zscore_current) =>
    f_get_next_step_from_change(ia, prev_ia, change_5day_perc, change_pos_thresh, change_neg_thresh, price_dir_5day, "IA", zscore_current)

// Outer Asymmetry Next Steps
f_getOuterAsymmetryNextSteps(oa, prev_oa, change_5day_perc, price_dir_5day, zscore_current) =>
    f_get_next_step_from_change(oa, prev_oa, change_5day_perc, change_pos_thresh, change_neg_thresh, price_dir_5day, "OA", zscore_current)

// Outer/Inner Ratio Next Steps
f_getOuterInnerRatioNextSteps(oir, prev_oir, change_5day_perc, price_dir_5day, zscore_current) =>
    f_get_next_step_from_change(oir, prev_oir, change_5day_perc, change_pos_thresh, change_neg_thresh, price_dir_5day, "OIR", zscore_current)


// Skew Diagnosis (focus on actionable insight for current state)
f_getSkewDiagnosis(s, skew_change_5day_perc, next_steps_skew) =>
    if f_is_skew_bull_bias(s)
        if str.contains(next_steps_skew, "Accel. (Up)") or str.contains(next_steps_skew, "Strengthening")
            "Market bias remains bullish; upside momentum building."
        else if str.contains(next_steps_skew, "Neutralizing") or str.contains(next_steps_skew, "Weakening")
            "Bullish bias weakening; watch for potential consolidation or reversal."
        else
            "Underlying bullish bias is present."
    else if f_is_skew_bear_bias(s)
        if str.contains(next_steps_skew, "Accel. (Down)") or str.contains(next_steps_skew, "Strengthening")
            "Market bias remains bearish; downside momentum building."
        else if str.contains(next_steps_skew, "Neutralizing") or str.contains(next_steps_skew, "Weakening")
            "Bearish bias weakening; watch for potential consolidation or reversal."
        else
            "Underlying bearish bias is present."
    else
        "Skew is neutral; market direction currently lacks strong distribution bias."

// Z-Score Diagnosis (focus on actionable insight for current state)
f_getZScoreDiagnosis(zs, next_steps_zscore) =>
    if f_is_zscore_overbought_bias(zs)
        if str.contains(next_steps_zscore, "Increasing") or str.contains(next_steps_zscore, "Deepening")
            "Price extremely overbought, increasing risk of sharp pullback. Strongly consider short fade."
        else if str.contains(next_steps_zscore, "Mean Rev. Cont. (Downward)")
            "Price pulling back from overbought. Short fade confirmed / manage longs."
        else
            "Price overbought. High probability of pullback. Consider short fade if other metrics align."
    else if f_is_zscore_oversold_bias(zs)
        if str.contains(next_steps_zscore, "Increasing") or str.contains(next_steps_zscore, "Deepening")
            "Price extremely oversold, increasing risk of sharp bounce. Strongly consider long fade."
        else if str.contains(next_steps_zscore, "Mean Rev. Cont. (Upward)")
            "Price bouncing from oversold. Long fade confirmed / manage shorts."
        else
            "Price oversold. High probability of bounce. Consider long fade if other metrics align."
    else
        "Price within normal deviation. Mean reversion less likely from extremes."

// Inner Asymmetry Diagnosis
f_getInnerAsymmetryDiagnosis(ia, next_steps_ia) =>
    if f_is_inner_asymmetry_bull_trend_bias(ia)
        if str.contains(next_steps_ia, "Accel. (Up)")
            "Strong internal bullish momentum. Likely trend continuation."
        else if str.contains(next_steps_ia, "Neutralizing") or str.contains(next_steps_ia, "Weakening")
            "Bullish internal momentum weakening. Watch for consolidation."
        else
            "Internal structure maintains bullish momentum."
    else if f_is_inner_asymmetry_bear_trend_bias(ia)
        if str.contains(next_steps_ia, "Accel. (Down)")
            "Strong internal bearish momentum. Likely trend continuation."
        else if str.contains(next_steps_ia, "Neutralizing") or str.contains(next_steps_ia, "Weakening")
            "Bearish internal momentum weakening. Watch for consolidation."
        else
            "Internal structure maintains bearish momentum."
    else // Neutral bias
        "Internal structure is balanced. Price action is likely consolidating or indecisive."

// Outer Asymmetry Diagnosis
f_getOuterAsymmetryDiagnosis(oa, next_steps_oa) =>
    if f_is_outer_asymmetry_bull_trend_bias(oa)
        if str.contains(next_steps_oa, "Accel. (Up)")
            "Strong external trend momentum. Favor trend-following entries."
        else if str.contains(next_steps_oa, "Neutralizing") or str.contains(next_steps_oa, "Weakening")
            "External trend momentum weakening from bullish. Prepare for consolidation/pullback."
        else
            "External structure confirms bullish trend. Maintain trend bias."
    else if f_is_outer_asymmetry_bear_trend_bias(oa)
        if str.contains(next_steps_oa, "Accel. (Down)")
            "Strong external trend momentum. Favor trend-following entries."
        else if str.contains(next_steps_oa, "Neutralizing") or str.contains(next_steps_oa, "Weakening")
            "External trend momentum weakening from bearish. Prepare for consolidation/bounce."
        else
            "External structure confirms bearish trend. Maintain trend bias."
    else // Neutral bias
        "External structure is balanced. Reversion or new trend initiation possible."

// Outer/Inner Ratio Diagnosis
f_getOuterInnerRatioDiagnosis(oir, next_steps_oir) =>
    if f_is_outer_inner_ratio_bull_trend_bias(oir) // High OIR means trend confirmed
        if str.contains(next_steps_oir, "Accel. (Up)")
            "Trend strength accelerating. High conviction for trend continuation."
        else if str.contains(next_steps_oir, "Neutralizing") or str.contains(next_steps_oir, "Weakening")
            "Trend strength decelerating from bullish confirmation. Risk of consolidation/reversion."
        else
            "Trend strength remains confirmed. Maintain trend-following strategies."
    else if f_is_outer_inner_ratio_bear_reversion_bias(oir) // Low OIR means reversion confirmed
        if str.contains(next_steps_oir, "Accel. (Down)")
            "Reversion strength accelerating. High conviction for mean reversion."
        else if str.contains(next_steps_oir, "Neutralizing") or str.contains(next_steps_oir, "Weakening")
            "Reversion strength decelerating from bearish confirmation. Risk of consolidation/trend."
        else
            "Reversion strength remains confirmed. Maintain fade strategies."
    else // Neutral OIR
        "Consolidation confirmed. Trade ranges or wait for breakout with clear bias."

// Consensus Diagnosis (unified report)
f_getConsensusDiagnosis(mp_label, zs, ia, oa, oir, next_steps_zs, next_steps_ia, next_steps_oa, next_steps_oir, current_skew, next_steps_skew) =>
    string interpretation_str = ""
    string action_str = ""
    string summary_message = ""

    // Build the summary message first, following the desired "one directional report" structure
    bool is_price_overextended_up = f_is_zscore_overbought_bias(zs)
    bool is_price_overextended_down = f_is_zscore_oversold_bias(zs)
    bool is_ia_neutralizing = str.contains(next_steps_ia, "Neutralizing")
    bool is_oa_neutralizing = str.contains(next_steps_oa, "Neutralizing")
    bool is_oir_neutralizing = str.contains(next_steps_oir, "Neutralizing")
    bool is_ia_weakening = str.contains(next_steps_ia, "Weakening")
    bool is_oa_weakening = str.contains(next_steps_oa, "Weakening")
    bool is_oir_weakening = str.contains(next_steps_oir, "Weakening")
    bool is_ia_decel = str.contains(next_steps_ia, "Decel.") // For Neutralizing
    bool is_oa_decel = str.contains(next_steps_oa, "Decel.")
    bool is_oir_decel = str.contains(next_steps_oir, "Decel.")
    bool is_some_neutralizing = is_ia_neutralizing or is_oa_neutralizing or is_oir_neutralizing
    bool is_some_weakening = is_ia_weakening or is_oa_weakening or is_oir_weakening
    bool is_some_decel = is_ia_decel or is_oa_decel or is_oir_decel

    if is_price_overextended_up
        summary_message := "Price is currently overextended upwards. "
        action_str := "Highly consider short fade / managing longs. "
    else if is_price_overextended_down
        summary_message := "Price is currently overextended downwards. "
        action_str := "Highly consider long fade / managing shorts. "
    else
        summary_message := "Price is currently within normal deviation. "
        action_str := "Exercise caution. "

    if is_some_neutralizing or is_some_weakening or is_some_decel
        summary_message += "Momentum indicators (IA, OA, OIR) are showing signs of "
        if is_some_neutralizing
            summary_message += "neutralizing "
        if is_some_weakening
            if is_some_neutralizing
                summary_message += "and "
            summary_message += "decelerating "
        summary_message += "from previous biases. "
    else
        summary_message += "Momentum indicators remain consistent. "


    if f_is_skew_bull_bias(current_skew) and not (str.contains(next_steps_skew, "Neutralizing") or str.contains(next_steps_skew, "Weakening"))
        summary_message += "While underlying bullish skew remains, the market is "
        if is_price_overextended_up
            summary_message += "losing upward impetus at extremes. "
            action_str += "Look for pullback or sideways movement. "
        else if is_some_neutralizing or is_some_weakening or is_some_decel
            summary_message += "showing signs of weakening upward impetus. "
            action_str += "Look for consolidation or pullback. "
        else
            summary_message += "maintaining bullish impetus. "
            action_str += "Maintain bullish bias."
    else if f_is_skew_bear_bias(current_skew) and not (str.contains(next_steps_skew, "Neutralizing") or str.contains(next_steps_skew, "Weakening"))
        summary_message += "While underlying bearish skew remains, the market is "
        if is_price_overextended_down
            summary_message += "losing downward impetus at extremes. "
            action_str += "Look for bounce or sideways movement. "
        else if is_some_neutralizing or is_some_weakening or is_some_decel
            summary_message += "showing signs of weakening downward impetus. "
            action_str += "Look for consolidation or bounce. "
        else
            summary_message += "maintaining bearish impetus. "
            action_str += "Maintain bearish bias."
    else // Skew is neutral or neutralizing
        summary_message += "Skew is neutral or neutralizing, indicating indecision. "
        action_str += "Exercise caution. "

    // Final action suggestion based on overall situation
    if is_price_overextended_up and (is_some_neutralizing or is_some_weakening or is_some_decel)
        action_str := "High probability of mean reversion or consolidation. Strongly consider fade/counter-trend strategies. "
    else if is_price_overextended_down and (is_some_neutralizing or is_some_weakening or is_some_decel)
        action_str := "High probability of mean reversion or consolidation. Strongly consider fade/counter-trend strategies. "
    else if mp_label == "↔️ Consolidating/Indecisive" or f_is_outer_inner_ratio_neutral_bias(oir) // Added this to catch explicitly consolidating states by OIR
        action_str := "Consolidation confirmed. Consider range trading or wait for breakout. "
    else if mp_label == "🔼 Trend Confirming (Bull)" or mp_label == "🔽 Trend Confirming (Bear)"
        action_str := "Trend confirmed. Look for trend-following opportunities. "
    else if mp_label == "⬆️ Tail Risk Building (Bull)" or mp_label == "⬇️ Tail Risk Building (Bear)"
        action_str := "Tail risk building. Prepare for sharp directional move. "
    else // Default if specific action not yet set
        action_str := "Review individual metric rows for specifics."

    // Constructing the final interpretation string for the table cell
    interpretation_str := mp_label + ": " + summary_message

    [interpretation_str, action_str]


// === DIAGNOSTIC DASHBOARD TABLE ===
// Create or update the table for diagnostics, positioned at bottom right
var table skewTable = table.new(position.bottom_right, 7, 7, border_width=1) // Corrected rows to 7 (Header + 6 data rows)

// Set table headers
table.cell(skewTable, 0, 0, "Metric", text_color=color.white, bgcolor=color.gray)
table.cell(skewTable, 1, 0, "Value", text_color=color.white, bgcolor=color.gray)
table.cell(skewTable, 2, 0, "5-Candle Change (%)", text_color=color.white, bgcolor=color.gray)
table.cell(skewTable, 3, 0, "15-Candle Change (%)", text_color=color.white, bgcolor=color.gray)
table.cell(skewTable, 4, 0, "Interpretation (Current State)", text_color=color.white, bgcolor=color.gray) // Clarified title
table.cell(skewTable, 5, 0, "Next Steps (5D Momentum)", text_color=color.white, bgcolor=color.gray) // Shorter title
table.cell(skewTable, 6, 0, "Diagnosis / Action Guidance", text_color=color.white, bgcolor=color.gray) // Renamed Diagnosis

// Populate table with data, interpretations, and diagnoses
// Row 1: Skew
string next_steps_skew_str = f_getSkewNextSteps(skew, skew[lookback_period_5day], skew_delta * 100, price_direction_5day, zscore)
table.cell(skewTable, 0, 1, "Skew", text_color=color.white, bgcolor=color.black)
table.cell(skewTable, 1, 1, str.tostring(skew, "0.000"), text_color=color.white)
table.cell(skewTable, 2, 1, str.tostring(skew_delta * 100, "0.00") + "%", text_color=color.white) // Show skew delta as proxy for change
table.cell(skewTable, 3, 1, "N/A", text_color=color.gray) // Skew change not directly meaningful as percentage for table, but delta used in next steps
table.cell(skewTable, 4, 1, f_getSkewInterpretation(skew), text_color=color.white)
table.cell(skewTable, 5, 1, next_steps_skew_str, text_color=color.white)
table.cell(skewTable, 6, 1, f_getSkewDiagnosis(skew, skew_delta * 100, next_steps_skew_str), text_color=color.white)

// Row 2: Z-Score
string next_steps_zscore_str = f_getZScoreNextSteps(zscore, zscore[lookback_period_5day], f_calc_perc_change(zscore, zscore[lookback_period_5day]), price_direction_5day)
table.cell(skewTable, 0, 2, "Z-Score", text_color=color.white, bgcolor=color.black)
table.cell(skewTable, 1, 2, str.tostring(zscore, "0.00"), text_color=color.white)
table.cell(skewTable, 2, 2, str.tostring(f_calc_perc_change(zscore, zscore[lookback_period_5day]), "0.00") + "%", text_color=color.white)
table.cell(skewTable, 3, 2, str.tostring(f_calc_perc_change(zscore, zscore[lookback_period_15day]), "0.00") + "%", text_color=color.white)
table.cell(skewTable, 4, 2, f_getZScoreInterpretation(zscore), text_color=color.white)
table.cell(skewTable, 5, 2, next_steps_zscore_str, text_color=color.white)
table.cell(skewTable, 6, 2, f_getZScoreDiagnosis(zscore, next_steps_zscore_str), text_color=color.white)

// Row 3: Inner Asymmetry
string next_steps_ia_str = f_getInnerAsymmetryNextSteps(inner_asymmetry_ratio, inner_asymmetry_ratio_prev_5day, inner_asymmetry_change_5day, price_direction_5day, zscore)
table.cell(skewTable, 0, 3, "Inner Asymmetry", text_color=color.white, bgcolor=color.black)
table.cell(skewTable, 1, 3, str.tostring(inner_asymmetry_ratio, "0.00"), text_color=color.white)
table.cell(skewTable, 2, 3, str.tostring(inner_asymmetry_change_5day, "0.00") + "%", text_color=color.white)
table.cell(skewTable, 3, 3, str.tostring(inner_asymmetry_change_15day, "0.00") + "%", text_color=color.white)
table.cell(skewTable, 4, 3, f_getInnerAsymmetryInterpretation(inner_asymmetry_ratio, inner_asymmetry_thresh_high, inner_asymmetry_thresh_low), text_color=color.white)
table.cell(skewTable, 5, 3, next_steps_ia_str, text_color=color.white)
table.cell(skewTable, 6, 3, f_getInnerAsymmetryDiagnosis(inner_asymmetry_ratio, next_steps_ia_str), text_color=color.white)

// Row 4: Outer Asymmetry
string next_steps_oa_str = f_getOuterAsymmetryNextSteps(outer_asymmetry_ratio, outer_asymmetry_ratio_prev_5day, outer_asymmetry_change_5day, price_direction_5day, zscore)
table.cell(skewTable, 0, 4, "Outer Asymmetry", text_color=color.white, bgcolor=color.black)
table.cell(skewTable, 1, 4, str.tostring(outer_asymmetry_ratio, "0.00"), text_color=color.white)
table.cell(skewTable, 2, 4, str.tostring(outer_asymmetry_change_5day, "0.00") + "%", text_color=color.white)
table.cell(skewTable, 3, 4, str.tostring(outer_asymmetry_change_15day, "0.00") + "%", text_color=color.white)
table.cell(skewTable, 4, 4, f_getOuterAsymmetryInterpretation(outer_asymmetry_ratio, outer_asymmetry_thresh_high, outer_asymmetry_thresh_low), text_color=color.white)
table.cell(skewTable, 5, 4, next_steps_oa_str, text_color=color.white)
table.cell(skewTable, 6, 4, f_getOuterAsymmetryDiagnosis(outer_asymmetry_ratio, next_steps_oa_str), text_color=color.white)

// Row 5: Outer/Inner Ratio
string next_steps_oir_str = f_getOuterInnerRatioNextSteps(asymmetry_ratio_ratio, asymmetry_ratio_ratio_prev_5day, outer_inner_ratio_change_5day, price_direction_5day, zscore)
table.cell(skewTable, 0, 5, "Outer/Inner Ratio", text_color=color.white, bgcolor=color.black)
table.cell(skewTable, 1, 5, str.tostring(asymmetry_ratio_ratio, "0.00"), text_color=color.white)
table.cell(skewTable, 2, 5, str.tostring(outer_inner_ratio_change_5day, "0.00") + "%", text_color=color.white)
table.cell(skewTable, 3, 5, str.tostring(outer_inner_ratio_change_15day, "0.00") + "%", text_color=color.white)
table.cell(skewTable, 4, 5, f_getOuterInnerRatioInterpretation(asymmetry_ratio_ratio, outer_inner_ratio_thresh_high, outer_inner_ratio_thresh_low), text_color=color.white)
table.cell(skewTable, 5, 5, next_steps_oir_str, text_color=color.white)
table.cell(skewTable, 6, 5, f_getOuterInnerRatioDiagnosis(asymmetry_ratio_ratio, next_steps_oir_str), text_color=color.white)

// Row 6: Consensus (Market Phase)
[consensus_interpretation, consensus_action] = f_getConsensusDiagnosis(consensus_label, zscore, inner_asymmetry_ratio, outer_asymmetry_ratio, asymmetry_ratio_ratio, next_steps_zscore_str, next_steps_ia_str, next_steps_oa_str, next_steps_oir_str, skew, next_steps_skew_str)

table.cell(skewTable, 0, 6, "Consensus", text_color=color.white, bgcolor=color.black)
table.cell(skewTable, 1, 6, consensus_label, text_color=consensus_color)
table.cell(skewTable, 2, 6, "N/A", text_color=color.gray)
table.cell(skewTable, 3, 6, "N/A", text_color=color.gray)
table.cell(skewTable, 4, 6, consensus_interpretation, text_color=color.white)
table.cell(skewTable, 5, 6, "See Action Column", text_color=color.gray) // Simplified as its action is in the next column
table.cell(skewTable, 6, 6, consensus_action, text_color=color.white)