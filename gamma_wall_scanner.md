// @version=6
indicator("Enhanced Gamma Wall Scanner v8.0 - Max Pain Integration", "EGWS_v8", overlay=true, max_labels_count=500, max_lines_count=500, max_boxes_count=100)

// ========================================================================
// ENHANCED GAMMA WALL SCANNER v8.0 - MAX PAIN INTEGRATION
// ========================================================================
// Features: Dynamic data parsing, per-timeframe IVs, real gamma flip display, MAX PAIN ANALYSIS
// Wall Strength: concentration * 45 + log10(absolute_exposure) * 8
// Max Pain: Theoretical price where option writers experience least pain
// Works with Python data generator - no hardcoded data limitations
// Supports unlimited symbols, shows different IV per timeframe
// ========================================================================

// === ENHANCED CONFIGURATION ===
group_display = "Wall Display"
group_walls = "Wall Configuration" 
group_regime = "Market Regime"
group_zones = "IV Zone Settings"
group_maxpain = "Max Pain Settings"
group_alerts = "Alert Settings"
group_visual = "Visual Settings"
group_colors = "Colors"
group_performance = "Performance"

// Wall Display Controls
show_swing_walls = input.bool(true, "Show Swing Walls (14D)", group=group_display)
show_long_walls = input.bool(true, "Show Long Walls (30D)", group=group_display) 
show_quarterly_walls = input.bool(true, "Show Quarterly Walls (90D)", group=group_display)
show_all_timeframes = input.bool(false, "Show All Timeframes Simultaneously", group=group_display)
show_info_table = input.bool(true, "Show Information Table", group=group_display)
show_wall_labels = input.bool(true, "Show Wall Labels", group=group_display)

// IV-Based Zone Configuration
use_iv_zones = input.bool(true, "Use IV-Based Zone Sizing", group=group_zones)
iv_zone_multiplier = input.float(0.6, "IV Zone Multiplier", minval=0.1, maxval=2.0, step=0.1, group=group_zones)
fallback_zone_pct = input.float(1.8, "Fallback Zone % (when IV unavailable)", minval=0.5, maxval=5.0, step=0.1, group=group_zones)
time_decay_factor = input.bool(true, "Apply Time Decay to Zones", group=group_zones)
show_iv_info = input.bool(true, "Show IV Information", group=group_zones)
show_gamma_flip = input.bool(true, "Show Gamma Flip Level", group=group_zones)

// Max Pain Settings
enable_max_pain = input.bool(true, "Enable Max Pain Analysis", group=group_maxpain)
show_max_pain_line = input.bool(true, "Show Max Pain Line", group=group_maxpain)
show_pin_zone = input.bool(true, "Show Pin Risk Zone", group=group_maxpain)
use_dynamic_pin_zone = input.bool(true, "Use Dynamic Pin Zone (IV-Based)", group=group_maxpain)
static_pin_zone_pct = input.float(2.0, "Static Pin Zone %", minval=0.5, maxval=5.0, step=0.5, group=group_maxpain)
max_pain_strikes = input.int(35, "Max Pain Strike Count", minval=15, maxval=75, group=group_maxpain)
use_gamma_weighted_oi = input.bool(true, "Use Gamma-Weighted OI", group=group_maxpain)
strike_spacing = input.float(1.0, "Strike Spacing $", minval=0.25, maxval=5.0, step=0.25, group=group_maxpain)
expiry_type = input.string("Auto-Detect", "Expiry Type", options=["Auto-Detect", "Weekly Friday", "Monthly (3rd Fri)", "Manual Days"], group=group_maxpain)
manual_days_to_expiry = input.int(7, "Manual Days to Expiry", minval=1, maxval=60, group=group_maxpain)
only_high_confidence_expiries = input.bool(true, "Only High-Confidence Expiries", group=group_maxpain)
dealer_bias_factor = input.float(0.65, "Dealer Short Bias", minval=0.1, maxval=1.5, step=0.05, group=group_maxpain)
confidence_threshold = input.float(0.7, "Min Confidence Level", minval=0.1, maxval=1.0, step=0.1, group=group_maxpain)
enable_max_pain_alerts = input.bool(false, "Max Pain Approach Alerts", group=group_maxpain)

// Market Regime Detection
enable_regime_detection = input.bool(true, "Enable Market Regime Detection", group=group_regime)
regime_display_position = input.string("Top Right", "Regime Display Position", options=["Top Left", "Top Right", "Bottom Left", "Bottom Right"], group=group_regime)
adjust_walls_by_regime = input.bool(true, "Adjust Wall Strength by Regime", group=group_regime)
vix_high_threshold = input.float(25.0, "VIX High Volatility Threshold", minval=15.0, maxval=40.0, group=group_regime)
vix_low_threshold = input.float(15.0, "VIX Low Volatility Threshold", minval=10.0, maxval=25.0, group=group_regime)
show_regime_background = input.bool(true, "Show Regime Background Color", group=group_regime)

// Enhanced Wall Filtering
min_strength = input.int(20, "Minimum Wall Strength", minval=0, maxval=100, group=group_walls)
strength_based_opacity = input.bool(true, "Strength-Based Opacity", group=group_walls)
hide_weak_walls = input.bool(false, "Hide Walls Below 40 Strength", group=group_walls)
regime_strength_boost = input.float(1.2, "High Vol Regime Strength Boost", minval=0.8, maxval=2.0, group=group_walls)

// Alert Configuration
enable_wall_breach_alerts = input.bool(true, "Wall Breach Alerts", group=group_alerts)
enable_approach_alerts = input.bool(false, "Wall Approach Alerts", group=group_alerts)
alert_distance_pct = input.float(2.0, "Alert Distance %", minval=0.5, maxval=5.0, group=group_alerts)
enable_regime_change_alerts = input.bool(false, "Regime Change Alerts", group=group_alerts)
enable_gamma_flip_alerts = input.bool(false, "Gamma Flip Cross Alerts", group=group_alerts)

// Enhanced Visual Settings
wall_extension_method = input.string("Fixed", "Wall Extension", options=["Fixed", "To Current Bar", "Infinite"], group=group_visual)
extension_bars = input.int(30, "Extension Bars", minval=10, maxval=100, group=group_visual)
show_wall_zones = input.bool(true, "Show Wall Zones", group=group_visual)
use_gradient_colors = input.bool(true, "Use Gradient Colors by Strength", group=group_visual)
label_size = input.string("Small", "Label Size", options=["Tiny", "Small", "Normal", "Large"], group=group_visual)

// Enhanced Color Scheme
swing_put_color = input.color(#FF4444, "Swing Put Wall", group=group_colors)
swing_call_color = input.color(#44FF44, "Swing Call Wall", group=group_colors)
long_put_color = input.color(#FF8844, "Long Put Wall", group=group_colors) 
long_call_color = input.color(#4488FF, "Long Call Wall", group=group_colors)
quarterly_put_color = input.color(#BB44FF, "Quarterly Put Wall", group=group_colors)
quarterly_call_color = input.color(#FFBB44, "Quarterly Call Wall", group=group_colors)
gamma_flip_color = input.color(#FF8800, "Gamma Flip Level", group=group_colors)
max_pain_color = input.color(#FF0080, "Max Pain Level", group=group_colors)
pin_zone_color = input.color(#FF0080, "Pin Risk Zone", group=group_colors)

// Regime Colors
high_vol_bg_color = input.color(color.new(#FF6B6B, 95), "High Volatility Background", group=group_colors)
low_vol_bg_color = input.color(color.new(#4ECDC4, 95), "Low Volatility Background", group=group_colors)
normal_vol_bg_color = input.color(color.new(#45B7D1, 95), "Normal Volatility Background", group=group_colors)

// Performance and Debug
max_historical_walls = input.int(5, "Max Historical Wall Sets", minval=1, maxval=10, group=group_performance)
show_debug_info = input.bool(false, "Show Debug Information", group=group_performance)
data_refresh_interval = input.int(10, "Data Refresh Interval (bars)", minval=1, maxval=50, group=group_performance)

// === GLOBAL VARIABLES ===
var string current_regime = "Normal Volatility"
var color regime_bg_color = normal_vol_bg_color
var float regime_vix = 15.5
var bool data_validation_passed = false
var int last_data_update = 0
var string parsing_error = ""
var float current_gamma_flip = na

// Max Pain Variables
var float current_max_pain = na
var float max_pain_distance_pct = 0.0
var string pin_risk_level = "LOW"
var color pin_risk_color = color.green
var float max_pain_confidence = 0.0
var float dynamic_pin_zone_pct = 2.0
var int current_expiry_bar = 0
var int days_to_expiry = 7
var bool is_expiry_valid = false
var string expiry_info = ""
var string actual_expiry_method = "Unknown"
var array<float> max_pain_strike_prices = array.new<float>()
var array<float> max_pain_call_oi = array.new<float>()
var array<float> max_pain_put_oi = array.new<float>()
var array<float> max_pain_weights = array.new<float>()

// Enhanced storage arrays for better wall management
var array<line> active_swing_put_lines = array.new<line>()
var array<line> active_swing_call_lines = array.new<line>()
var array<line> active_long_put_lines = array.new<line>()
var array<line> active_long_call_lines = array.new<line>()
var array<line> active_quarterly_put_lines = array.new<line>()
var array<line> active_quarterly_call_lines = array.new<line>()
var array<line> active_gamma_flip_lines = array.new<line>()
var array<line> active_max_pain_lines = array.new<line>()

var array<box> active_swing_put_zones = array.new<box>()
var array<box> active_swing_call_zones = array.new<box>()
var array<box> active_long_put_zones = array.new<box>()
var array<box> active_long_call_zones = array.new<box>()
var array<box> active_quarterly_put_zones = array.new<box>()
var array<box> active_quarterly_call_zones = array.new<box>()
var array<box> active_pin_zones = array.new<box>()

// === DYNAMIC DATA SOURCES ===
// These will be dynamically updated by the Python script


var string level_data1 = "SPX:7000.0,7000.0,6450.0,7400.0,6369.50,6999.00,7000.00,7000.00,5724.09,25.0,1.1,0.0,3.0,7000.00,7000.00,6212.12,7156.38,6054.74,7313.76,6470.00,7210.00,66.7,70.6,86.6,80.0,63.7,65.9,13,30,83,-150.4,157.2,-0.2,0.0,-11.1,8.4;"
var string level_data2 = "QQQ(NDX):600.0,600.0,600.0,655.0,570.30,635.27,600.00,600.00,260.80,28.6,1.0,0.0,3.0,600.00,600.00,554.06,651.51,537.82,667.75,620.00,630.00,68.6,67.2,55.6,50.6,48.6,54.6,13,27,83,-410.0,244.5,-14.4,9.2,-0.9,1.5;"
var string level_data3 = "AAPL:270.0,280.0,270.0,285.0,253.27,289.64,270.00,280.00,216.77,35.5,1.1,0.0,3.0,270.00,280.00,244.18,298.73,235.08,307.83,220.00,255.00,63.1,63.5,57.0,63.7,62.4,67.6,13,27,104,-38.4,116.9,-2.6,7.3,-7.6,32.6;"
var string level_data4 = "NVDA:180.0,180.0,180.0,190.0,156.32,206.62,180.00,180.00,5.00,73.4,1.1,0.0,3.0,180.00,180.00,143.75,219.19,131.18,231.76,150.00,210.00,64.8,69.3,58.8,55.3,56.9,59.8,13,27,104,-111.0,188.9,-7.3,7.8,-22.0,26.5;"
var string level_data5 = "MSFT:500.0,515.0,525.0,540.0,461.03,529.97,500.00,515.00,512.52,36.9,1.1,0.0,3.0,500.00,515.00,443.79,547.21,426.55,564.45,500.00,600.00,59.4,65.3,74.4,53.9,49.9,61.0,13,27,104,-39.5,45.6,-9.5,4.0,-5.6,11.8;"
var string level_data6 = "CVX:155.0,165.0,145.0,165.0,144.49,166.89,155.00,165.00,152.83,38.1,1.1,0.0,3.0,155.00,165.00,138.89,172.49,133.29,178.10,145.00,165.00,61.7,72.7,56.3,63.9,58.7,57.0,13,27,104,-8.5,34.4,-0.3,0.5,-1.6,2.8;"
var string level_data7 = "XOM:115.0,120.0,109.0,118.0,109.32,125.29,115.00,120.00,65.00,36.1,1.1,0.0,3.0,115.00,120.00,105.33,129.28,101.33,133.28,110.00,125.00,68.2,77.4,45.7,68.4,55.8,68.0,13,27,104,-10.4,53.0,-0.2,1.5,-1.3,4.3;"
var string level_data8 = "TSLA:400.0,500.0,385.0,480.0,371.34,488.88,400.00,500.00,330.60,72.4,1.2,0.0,3.0,400.00,500.00,341.96,518.26,312.57,547.65,420.00,500.00,58.2,60.2,46.5,86.9,55.0,48.9,13,27,104,-47.3,65.8,-2.4,11.3,-5.5,6.4;"
var string level_data9 = "META:600.0,700.0,600.0,660.0,541.34,667.92,600.00,700.00,200.00,55.5,1.1,0.0,3.0,600.00,700.00,509.69,699.57,478.04,731.22,650.00,600.00,55.4,56.1,49.9,49.8,50.5,62.1,13,27,104,-25.2,18.0,-6.0,4.4,-5.2,8.4;"
var string level_data10 = "AMZN:230.0,250.0,235.0,270.0,217.96,263.28,230.00,250.00,95.00,49.9,1.1,0.0,3.0,230.00,250.00,206.63,274.61,195.30,285.94,230.00,220.00,58.8,66.0,56.0,56.7,55.0,70.3,13,27,104,-37.0,98.2,-3.9,5.5,-9.0,23.1;"
var string level_data11 = "DIS:100.0,120.0,112.0,120.0,99.54,121.97,100.00,120.00,60.00,53.7,1.1,0.0,3.0,100.00,120.00,93.93,127.58,88.32,133.19,105.00,120.00,58.3,70.0,53.8,48.7,53.7,69.3,13,27,104,-12.6,13.2,-0.2,0.4,-0.6,1.2;"
var string level_data12 = "BAC:50.0,56.0,54.0,55.0,48.00,58.37,50.00,56.00,40.82,51.7,1.1,0.0,3.0,50.00,56.00,45.41,60.96,42.81,63.56,47.00,55.00,62.7,69.9,53.7,76.3,61.0,58.4,13,27,104,-30.4,105.9,-0.7,3.6,-4.3,7.9;"
var string level_data13 = "JPM:300.0,325.0,310.0,310.0,284.14,340.65,300.00,325.00,249.64,47.9,1.0,0.0,3.0,300.00,325.00,270.01,354.78,255.89,368.90,300.00,310.00,55.1,59.0,69.1,50.2,46.9,52.6,13,27,104,-7.7,19.5,-0.4,0.4,-1.4,2.1;"
var string level_data14 = "ADBE:340.0,340.0,325.0,360.0,298.81,355.35,340.00,340.00,344.34,45.8,1.2,0.0,3.0,340.00,340.00,284.67,369.49,270.54,383.62,295.00,410.00,54.1,53.9,51.5,64.5,45.5,48.1,13,27,104,-9.5,4.4,-0.4,0.3,-1.3,1.2;"
var string level_data15 = "AMD:220.0,260.0,235.0,255.0,193.16,260.64,220.00,260.00,151.48,78.8,1.2,0.0,3.0,220.00,260.00,176.28,277.52,159.41,294.39,200.00,300.00,58.3,59.4,52.9,48.6,50.5,56.7,13,27,104,-19.3,26.0,-2.2,1.8,-3.2,6.6;"

var string last_update = "nov 07, 03:42pm"
var string market_regime = "Normal Volatility"
var float current_vix = 20.8
var bool regime_adjustment_enabled = true

// === ENHANCED MARKET REGIME DETECTION SYSTEM ===
get_enhanced_market_regime() =>
    var float cached_vix = 15.5
    var string cached_regime = "Normal Volatility"
    var int last_regime_check = 0
    
    // Update regime periodically for performance
    if barstate.islast and (bar_index - last_regime_check) > data_refresh_interval
        var float vix_value = request.security("VIX", "1D", close[1], lookahead=barmerge.lookahead_off)
        
        if not na(vix_value) and vix_value > 5 and vix_value < 100
            cached_vix := vix_value
            last_regime_check := bar_index
            
            if vix_value >= vix_high_threshold
                cached_regime := "High Volatility"
            else if vix_value <= vix_low_threshold
                cached_regime := "Low Volatility"
            else
                cached_regime := "Normal Volatility"
        else
            // Enhanced fallback using multiple indicators
            price_volatility = ta.stdev(ta.change(close), 20) / close * 100
            rsi_divergence = math.abs(ta.rsi(close, 14) - 50) / 50
            atr_norm = ta.atr(14) / close * 100
            
            volatility_score = price_volatility + (rsi_divergence * 8) + (atr_norm * 15)
            
            if volatility_score > 8.0
                cached_regime := "High Volatility (Est.)"
            else if volatility_score < 3.0
                cached_regime := "Low Volatility (Est.)"
            else
                cached_regime := "Normal Volatility (Est.)"
    
    var color regime_bg = normal_vol_bg_color
    
    if str.contains(cached_regime, "High Volatility")
        regime_bg := high_vol_bg_color
    else if str.contains(cached_regime, "Low Volatility")
        regime_bg := low_vol_bg_color
    else
        regime_bg := normal_vol_bg_color
    
    [cached_regime, cached_vix, regime_bg]

// Update global regime state
if barstate.islast
    [regime_result, vix_result, bg_result] = get_enhanced_market_regime()
    current_regime := regime_result
    regime_vix := vix_result
    regime_bg_color := bg_result

// Apply regime background
bgcolor(enable_regime_detection and show_regime_background ? regime_bg_color : na, title="Market Regime Background")

// === ENHANCED DYNAMIC DATA PARSING ===
parse_dynamic_gamma_data(target_symbol) =>
    // Initialize all return values
    st_put_wall = float(na), st_call_wall = float(na)
    lt_put_wall = float(na), lt_call_wall = float(na) 
    quarterly_put_wall = float(na), quarterly_call_wall = float(na)
    st_put_strength = 0.0, st_call_strength = 0.0
    lt_put_strength = 0.0, lt_call_strength = 0.0
    q_put_strength = 0.0, q_call_strength = 0.0
    lower_1sd = float(na), upper_1sd = float(na), gamma_flip = close
    swing_iv = 25.0, long_iv = 25.0, quarterly_iv = 25.0
    cp_ratio = 2.0, activity_score = 3.0, trend = 0.0
    swing_dte = 15.0, long_dte = 30.0, quarterly_dte = 90.0
    st_put_gex = 0.0, st_call_gex = 0.0, lt_put_gex = 0.0
    lt_call_gex = 0.0, q_put_gex = 0.0, q_call_gex = 0.0
    lower_1_5sd = float(na), upper_1_5sd = float(na)
    lower_2sd = float(na), upper_2sd = float(na)
    parse_error = ""
    
    // Create array of all possible data sources
    data_sources = array.new<string>()
    array.push(data_sources, level_data1)
    array.push(data_sources, level_data2)
    array.push(data_sources, level_data3)
    array.push(data_sources, level_data4)
    array.push(data_sources, level_data5)
    array.push(data_sources, level_data6)
    array.push(data_sources, level_data7)
    array.push(data_sources, level_data8)
    array.push(data_sources, level_data9)
    array.push(data_sources, level_data10)
    array.push(data_sources, level_data11)
    array.push(data_sources, level_data12)
    array.push(data_sources, level_data13)
    array.push(data_sources, level_data14)
    array.push(data_sources, level_data15)
    
    // Enhanced symbol search with robust error handling
    symbol_found = false
    for i = 0 to array.size(data_sources) - 1
        if symbol_found
            break
            
        data_string = array.get(data_sources, i)
        
        // Skip empty data sources
        if str.length(data_string) < 10
            continue
            
        symbol_start = str.pos(data_string, target_symbol + ":")
        
        if symbol_start >= 0
            remaining = str.substring(data_string, symbol_start + str.length(target_symbol) + 1)
            symbol_end = str.pos(remaining, ";")
            
            if symbol_end >= 0
                symbol_data = str.substring(remaining, 0, symbol_end)
                fields = str.split(symbol_data, ",")
                
                // Enhanced field validation - require exactly 36 fields
                if array.size(fields) >= 36
                    // Core wall data with enhanced validation
                    st_put_wall := math.max(0, na(str.tonumber(array.get(fields, 0))) ? 0 : str.tonumber(array.get(fields, 0)))
                    st_call_wall := math.max(0, na(str.tonumber(array.get(fields, 1))) ? 0 : str.tonumber(array.get(fields, 1)))
                    lt_put_wall := math.max(0, na(str.tonumber(array.get(fields, 2))) ? 0 : str.tonumber(array.get(fields, 2)))
                    lt_call_wall := math.max(0, na(str.tonumber(array.get(fields, 3))) ? 0 : str.tonumber(array.get(fields, 3)))
                    
                    // Standard deviation ranges
                    lower_1sd := na(str.tonumber(array.get(fields, 4))) ? close * 0.95 : str.tonumber(array.get(fields, 4))
                    upper_1sd := na(str.tonumber(array.get(fields, 5))) ? close * 1.05 : str.tonumber(array.get(fields, 5))
                    
                    // Gamma flip point (field 8)
                    gamma_flip := na(str.tonumber(array.get(fields, 8))) ? close : str.tonumber(array.get(fields, 8))
                    
                    // Market metrics with validation
                    swing_iv := math.max(5.0, math.min(300.0, na(str.tonumber(array.get(fields, 9))) ? 25.0 : str.tonumber(array.get(fields, 9))))
                    cp_ratio := math.max(0.1, math.min(10.0, na(str.tonumber(array.get(fields, 10))) ? 2.0 : str.tonumber(array.get(fields, 10))))
                    trend := math.max(-5.0, math.min(5.0, na(str.tonumber(array.get(fields, 11))) ? 0.0 : str.tonumber(array.get(fields, 11))))
                    activity_score := math.max(0.0, math.min(5.0, na(str.tonumber(array.get(fields, 12))) ? 3.0 : str.tonumber(array.get(fields, 12))))
                    
                    // Extended standard deviations
                    lower_1_5sd := na(str.tonumber(array.get(fields, 15))) ? close * 0.92 : str.tonumber(array.get(fields, 15))
                    upper_1_5sd := na(str.tonumber(array.get(fields, 16))) ? close * 1.08 : str.tonumber(array.get(fields, 16))
                    lower_2sd := na(str.tonumber(array.get(fields, 17))) ? close * 0.90 : str.tonumber(array.get(fields, 17))
                    upper_2sd := na(str.tonumber(array.get(fields, 18))) ? close * 1.10 : str.tonumber(array.get(fields, 18))
                    
                    // Quarterly walls
                    quarterly_put_wall := math.max(0, na(str.tonumber(array.get(fields, 19))) ? 0 : str.tonumber(array.get(fields, 19)))
                    quarterly_call_wall := math.max(0, na(str.tonumber(array.get(fields, 20))) ? 0 : str.tonumber(array.get(fields, 20)))
                    
                    // Wall strengths with bounds checking
                    st_put_strength := math.max(0, math.min(100, na(str.tonumber(array.get(fields, 21))) ? 0 : str.tonumber(array.get(fields, 21))))
                    st_call_strength := math.max(0, math.min(100, na(str.tonumber(array.get(fields, 22))) ? 0 : str.tonumber(array.get(fields, 22))))
                    lt_put_strength := math.max(0, math.min(100, na(str.tonumber(array.get(fields, 23))) ? 0 : str.tonumber(array.get(fields, 23))))
                    lt_call_strength := math.max(0, math.min(100, na(str.tonumber(array.get(fields, 24))) ? 0 : str.tonumber(array.get(fields, 24))))
                    q_put_strength := math.max(0, math.min(100, na(str.tonumber(array.get(fields, 25))) ? 0 : str.tonumber(array.get(fields, 25))))
                    q_call_strength := math.max(0, math.min(100, na(str.tonumber(array.get(fields, 26))) ? 0 : str.tonumber(array.get(fields, 26))))
                    
                    // Days to expiration
                    swing_dte := math.max(1, math.min(365, na(str.tonumber(array.get(fields, 27))) ? 15 : str.tonumber(array.get(fields, 27))))
                    long_dte := math.max(1, math.min(365, na(str.tonumber(array.get(fields, 28))) ? 30 : str.tonumber(array.get(fields, 28))))
                    quarterly_dte := math.max(1, math.min(365, na(str.tonumber(array.get(fields, 29))) ? 90 : str.tonumber(array.get(fields, 29))))
                    
                    // GEX values with bounds checking
                    st_put_gex := math.max(-100, math.min(100, na(str.tonumber(array.get(fields, 30))) ? 0 : str.tonumber(array.get(fields, 30))))
                    st_call_gex := math.max(-100, math.min(100, na(str.tonumber(array.get(fields, 31))) ? 0 : str.tonumber(array.get(fields, 31))))
                    lt_put_gex := math.max(-100, math.min(100, na(str.tonumber(array.get(fields, 32))) ? 0 : str.tonumber(array.get(fields, 32))))
                    lt_call_gex := math.max(-100, math.min(100, na(str.tonumber(array.get(fields, 33))) ? 0 : str.tonumber(array.get(fields, 33))))
                    q_put_gex := math.max(-100, math.min(100, na(str.tonumber(array.get(fields, 34))) ? 0 : str.tonumber(array.get(fields, 34))))
                    q_call_gex := math.max(-100, math.min(100, na(str.tonumber(array.get(fields, 35))) ? 0 : str.tonumber(array.get(fields, 35))))
                    
                    // Calculate timeframe-specific IVs based on DTE and base IV
                    // This simulates different IVs for different timeframes
                    long_iv := swing_iv * (1.0 + (long_dte - swing_dte) * 0.01)
                    quarterly_iv := swing_iv * (1.0 + (quarterly_dte - swing_dte) * 0.005)
                    
                    symbol_found := true
                    
                else
                    parse_error := "Invalid field count: " + str.tostring(array.size(fields))
            else
                parse_error := "Data terminator not found"
    
    if not symbol_found
        parse_error := "Symbol " + target_symbol + " not found in data sources"
    
    // Return comprehensive data
    [st_put_wall, st_call_wall, lt_put_wall, lt_call_wall, quarterly_put_wall, quarterly_call_wall,
     st_put_strength, st_call_strength, lt_put_strength, lt_call_strength, q_put_strength, q_call_strength,
     lower_1sd, upper_1sd, lower_1_5sd, upper_1_5sd, lower_2sd, upper_2sd,
     gamma_flip, swing_iv, long_iv, quarterly_iv, cp_ratio, activity_score, trend,
     swing_dte, long_dte, quarterly_dte,
     st_put_gex, st_call_gex, lt_put_gex, lt_call_gex, q_put_gex, q_call_gex, parse_error]

// === EXPIRY DATE CALCULATION SYSTEM ===
get_third_friday_of_month(year_val, month_val) =>
    // Calculate 3rd Friday of given month/year
    first_day = timestamp(year_val, month_val, 1, 0, 0, 0)
    first_weekday = dayofweek(first_day)
    
    // Days to first Friday (5 = Friday)
    days_to_first_friday = first_weekday <= 5 ? 5 - first_weekday : 7 - first_weekday + 5
    first_friday_day = 1 + days_to_first_friday
    third_friday_day = first_friday_day + 14  // Add 2 weeks
    
    // Validate day exists in month
    if third_friday_day <= 31  // Simplified validation
        third_friday_day
    else
        21  // Fallback to 21st

calculate_expiry_details() =>
    current_time = time
    current_year = year(current_time)
    current_month = month(current_time)
    current_day = dayofmonth(current_time)
    current_weekday = dayofweek(current_time)
    current_hour = hour(current_time, "America/New_York")  // ET timezone
    
    symbol_prefix = str.substring(syminfo.ticker, 0, 3)
    is_major_etf = symbol_prefix == "SPY" or symbol_prefix == "QQQ" or symbol_prefix == "SPX" or symbol_prefix == "NDX"
    
    // Initialize variables at function scope
    days_remaining = 0
    expiry_bar = 0
    valid_expiry = false
    info_text = ""
    method_used = ""
    
    if expiry_type == "Manual Days"
        days_remaining := manual_days_to_expiry
        expiry_bar := bar_index + days_remaining
        valid_expiry := true
        info_text := "Manual: " + str.tostring(days_remaining) + "D"
        method_used := "Manual Override"
    else
        // Find next Friday
        days_to_next_friday = if current_weekday <= 5
            5 - current_weekday
        else
            7 - current_weekday + 5
        
        // If it's Friday after 4pm ET, move to next Friday
        if current_weekday == 6 and current_hour >= 16
            days_to_next_friday := 7
        
        next_friday_day = current_day + days_to_next_friday
        
        // Calculate 3rd Friday of current month
        third_friday_current = get_third_friday_of_month(current_year, current_month)
        
        // Calculate 3rd Friday of next month
        next_month = current_month < 12 ? current_month + 1 : 1
        next_year = current_month < 12 ? current_year : current_year + 1
        third_friday_next = get_third_friday_of_month(next_year, next_month)
        
        // Determine which expiry to use
        if expiry_type == "Weekly Friday"
            days_remaining := days_to_next_friday
            valid_expiry := not only_high_confidence_expiries or is_major_etf
            info_text := "Weekly: " + str.tostring(days_remaining) + "D"
            method_used := "Weekly Friday"
        else if expiry_type == "Monthly (3rd Fri)"
            if current_day <= third_friday_current
                days_remaining := third_friday_current - current_day
                info_text := "Monthly: " + str.tostring(days_remaining) + "D"
                method_used := "Monthly Current"
            else
                days_remaining := (third_friday_next - current_day) + (next_month == current_month + 1 ? 0 : 31)
                info_text := "Next Monthly: " + str.tostring(days_remaining) + "D"
                method_used := "Monthly Next"
            valid_expiry := true
        else  // Auto-Detect
            // For major ETFs, prefer weekly; for others, prefer monthly
            if is_major_etf
                days_remaining := days_to_next_friday
                info_text := "Auto-Weekly: " + str.tostring(days_remaining) + "D"
                valid_expiry := true
                method_used := "Auto (Weekly)"
            else
                if current_day <= third_friday_current
                    days_remaining := third_friday_current - current_day
                    info_text := "Auto-Monthly: " + str.tostring(days_remaining) + "D"
                    method_used := "Auto (Monthly Current)"
                else
                    days_remaining := (third_friday_next - current_day) + (next_month == current_month + 1 ? 0 : 31)
                    info_text := "Auto-Next: " + str.tostring(days_remaining) + "D"
                    method_used := "Auto (Monthly Next)"
                valid_expiry := not only_high_confidence_expiries or days_remaining <= 7
        
        // Calculate expiry bar (approximate)
        expiry_bar := bar_index + days_remaining
        
        // Validate expiry timing
        if days_remaining <= 0
            valid_expiry := false
            info_text := "Expired"
            method_used := "Invalid (Expired)"
        else if days_remaining > 30
            valid_expiry := false
            info_text := "Too Far"
            method_used := "Invalid (Too Far)"
    
    [days_remaining, expiry_bar, valid_expiry, info_text, method_used]

get_expiry_time_decay(days_remaining) =>
    if days_remaining <= 0
        0.0  // Expired - no effect
    else if days_remaining <= 1
        2.0  // Expiry day - maximum pinning effect
    else if days_remaining <= 3
        1.5  // Last 3 days - strong effect  
    else if days_remaining <= 5
        1.2  // Last week - building effect
    else if days_remaining <= 7
        1.0  // Week before - normal effect
    else
        0.7  // Further out - reduced effect

// === ENHANCED MAX PAIN CALCULATION SYSTEM ===
round_strike_enhanced(strike_price, current_price) =>
    // Dynamic rounding based on price level and volatility
    if current_price >= 500
        math.round(strike_price / 10) * 10  // $10 increments for high-priced stocks
    else if current_price >= 100
        math.round(strike_price / 5) * 5   // $5 increments
    else if current_price >= 20
        math.round(strike_price / 2.5) * 2.5  // $2.50 increments
    else
        math.round(strike_price)           // $1 increments for low-priced stocks

calculate_dynamic_pin_zone(iv_percent, days_remaining, current_price, confidence_level, current_regime_param) =>
    if use_dynamic_pin_zone and not na(iv_percent) and iv_percent > 0
        // Base calculation: 1-day move expectation
        daily_move_pct = (iv_percent / 100) / math.sqrt(365)
        
        // Enhanced time decay factor using expiry-aware calculation
        time_factor = get_expiry_time_decay(days_remaining)
        
        // Confidence adjustment: lower confidence = wider zones
        confidence_factor = 1.0 + (1.0 - confidence_level) * 0.5
        
        // Market regime adjustment
        regime_factor = str.contains(current_regime_param, "High Volatility") ? 1.4 :
                       str.contains(current_regime_param, "Low Volatility") ? 0.7 : 1.0
        
        // Calculate dynamic zone
        zone_pct = daily_move_pct * time_factor * confidence_factor * regime_factor * 100
        
        // Bounds checking
        math.max(0.5, math.min(zone_pct, 8.0))
    else
        static_pin_zone_pct

estimate_enhanced_open_interest(strike_price, current_price, is_call, gamma_wall_data, base_volume, days_remaining) =>
    distance_pct = math.abs(strike_price - current_price) / current_price
    
    // Enhanced decay function with volatility clustering
    base_factor = 1 / (1 + distance_pct * 8)
    volatility_factor = math.pow(0.75, distance_pct * 15)
    
    // Integration with gamma wall data - check if strike is near a wall
    wall_proximity_boost = 1.0
    if use_gamma_weighted_oi and not na(gamma_wall_data)
        wall_distance = math.abs(strike_price - gamma_wall_data) / current_price
        if wall_distance < 0.02  // Within 2% of a gamma wall
            wall_proximity_boost := 2.5  // Significantly higher OI near walls
        else if wall_distance < 0.05  // Within 5%
            wall_proximity_boost := 1.6
    
    base_oi = base_volume * base_factor * volatility_factor * wall_proximity_boost * 0.025
    
    // Dealer positioning bias - dealers often short gamma
    dealer_adjustment = if is_call
        1.0 / dealer_bias_factor  // Calls: dealers more likely short
    else
        dealer_bias_factor        // Puts: dealers more likely long
    
    // Put/call volume bias with time decay using passed days_remaining parameter
    time_bias = if days_remaining <= 7
        is_call ? 0.9 : 1.4  // Near expiry: put bias stronger
    else
        is_call ? 1.0 : 1.2  // Further out: moderate put bias
    
    final_oi = base_oi * dealer_adjustment * time_bias
    
    math.max(150, final_oi)

generate_enhanced_strikes(current_price, strike_count, spacing, wall_put, wall_call, wall_lt_put, wall_lt_call, iv_level) =>
    array.clear(max_pain_strike_prices)
    array.clear(max_pain_weights)
    
    // Dynamic range based on volatility (use default if IV not available)
    iv_to_use = na(iv_level) ? 25.0 : iv_level
    vol_factor = iv_to_use > 40 ? 0.20 : iv_to_use > 25 ? 0.15 : 0.12
    strike_range = current_price * vol_factor
    
    min_strike = current_price - strike_range
    max_strike = current_price + strike_range
    
    // Generate base strikes with enhanced spacing
    step_size = (max_strike - min_strike) / strike_count
    
    i = 0
    while i < strike_count
        raw_strike = min_strike + (i * step_size)
        rounded_strike = round_strike_enhanced(raw_strike, current_price)
        
        // Calculate weight based on various factors
        distance_factor = math.abs(rounded_strike - current_price) / current_price
        weight = math.exp(-distance_factor * 5)  // Exponential decay
        
        // Boost weight if near existing gamma walls
        wall_boost = 1.0
        if not na(wall_put) and math.abs(rounded_strike - wall_put) / current_price < 0.03
            wall_boost := 1.8
        else if not na(wall_call) and math.abs(rounded_strike - wall_call) / current_price < 0.03
            wall_boost := 1.8
        else if not na(wall_lt_put) and math.abs(rounded_strike - wall_lt_put) / current_price < 0.03
            wall_boost := 1.5
        else if not na(wall_lt_call) and math.abs(rounded_strike - wall_lt_call) / current_price < 0.03
            wall_boost := 1.5
        
        weight := weight * wall_boost
        
        // Avoid duplicates
        if array.size(max_pain_strike_prices) == 0 or rounded_strike != array.get(max_pain_strike_prices, array.size(max_pain_strike_prices) - 1)
            array.push(max_pain_strike_prices, rounded_strike)
            array.push(max_pain_weights, weight)
        
        i += 1
    
    // Add strikes near significant gamma walls if not already included
    wall_values = array.new<float>()
    if not na(wall_put) and wall_put > 0
        array.push(wall_values, wall_put)
    if not na(wall_call) and wall_call > 0
        array.push(wall_values, wall_call)
    if not na(wall_lt_put) and wall_lt_put > 0
        array.push(wall_values, wall_lt_put)
    if not na(wall_lt_call) and wall_lt_call > 0
        array.push(wall_values, wall_lt_call)
    
    j = 0
    while j < array.size(wall_values) and array.size(max_pain_strike_prices) < strike_count + 10
        wall_strike = array.get(wall_values, j)
        rounded_wall = round_strike_enhanced(wall_strike, current_price)
        
        // Check if already included
        already_included = false
        k = 0
        while k < array.size(max_pain_strike_prices) and not already_included
            if math.abs(array.get(max_pain_strike_prices, k) - rounded_wall) < 0.01
                already_included := true
            k += 1
        
        if not already_included and rounded_wall >= min_strike and rounded_wall <= max_strike
            array.push(max_pain_strike_prices, rounded_wall)
            array.push(max_pain_weights, 2.0)  // High weight for wall strikes
        j += 1

populate_enhanced_oi_data(current_price, activity_level, wall_put, wall_call, days_remaining) =>
    array.clear(max_pain_call_oi)
    array.clear(max_pain_put_oi)
    
    // Enhanced base volume estimation
    activity_to_use = na(activity_level) ? 3.0 : activity_level
    base_volume = if activity_to_use >= 4
        800000  // High activity
    else if activity_to_use >= 2.5
        600000  // Medium activity  
    else
        400000  // Low activity
    
    strike_count = array.size(max_pain_strike_prices)
    i = 0
    while i < strike_count
        strike = array.get(max_pain_strike_prices, i)
        
        // Use gamma wall data for better estimation
        relevant_wall = if not na(wall_put) and not na(wall_call)
            if math.abs(strike - wall_put) < math.abs(strike - wall_call)
                wall_put
            else
                wall_call
        else if not na(wall_put)
            wall_put
        else if not na(wall_call)
            wall_call
        else
            strike  // Use strike itself if no walls available
        
        call_oi = estimate_enhanced_open_interest(strike, current_price, true, relevant_wall, base_volume, days_remaining)
        put_oi = estimate_enhanced_open_interest(strike, current_price, false, relevant_wall, base_volume, days_remaining)
        
        // Apply weight factor
        weight = array.get(max_pain_weights, i)
        call_oi := call_oi * weight
        put_oi := put_oi * weight
        
        array.push(max_pain_call_oi, call_oi)
        array.push(max_pain_put_oi, put_oi)
        
        i += 1

calculate_enhanced_max_pain(days_remaining) =>
    if array.size(max_pain_strike_prices) == 0 or array.size(max_pain_call_oi) == 0
        [close, 0.5]  // Return current price with low confidence
    else
        best_strike = close
        min_total_pain = 1e20
        max_total_pain = 0.0
        
        strike_count = array.size(max_pain_strike_prices)
        
        // Test each strike as potential expiration price
        test_idx = 0
        while test_idx < strike_count
            test_price = array.get(max_pain_strike_prices, test_idx)
            total_pain = 0.0
            
            // Calculate weighted total pain at this test price
            strike_idx = 0
            while strike_idx < strike_count
                strike = array.get(max_pain_strike_prices, strike_idx)
                call_oi = array.get(max_pain_call_oi, strike_idx)
                put_oi = array.get(max_pain_put_oi, strike_idx)
                weight = array.get(max_pain_weights, strike_idx)
                
                // Enhanced pain calculation with expiry-aware time decay
                time_decay_factor = get_expiry_time_decay(days_remaining)
                
                if test_price > strike
                    call_pain = call_oi * (test_price - strike) * time_decay_factor * weight
                    total_pain += call_pain
                
                if test_price < strike  
                    put_pain = put_oi * (strike - test_price) * time_decay_factor * weight
                    total_pain += put_pain
                
                strike_idx += 1
            
            max_total_pain := math.max(max_total_pain, total_pain)
            
            if total_pain < min_total_pain
                min_total_pain := total_pain
                best_strike := test_price
            
            test_idx += 1
        
        // Calculate confidence based on pain distribution
        confidence = if max_total_pain > 0
            pain_spread = (max_total_pain - min_total_pain) / max_total_pain
            base_confidence = math.min(0.95, pain_spread * 1.2)
            
            // Reduce confidence for far-out expiries
            time_confidence_factor = if days_remaining <= 3
                1.0  // High confidence near expiry
            else if days_remaining <= 7
                0.9  // Good confidence within week
            else
                0.7  // Lower confidence further out
            
            base_confidence * time_confidence_factor
        else
            0.5
        
        [best_strike, confidence]

update_max_pain_metrics(max_pain_level, current_price, confidence_level, iv_level, current_regime_param, days_remaining) =>
    if not na(max_pain_level) and current_price > 0
        distance_pct = ((max_pain_level - current_price) / current_price) * 100
        
        // Calculate dynamic pin zone using actual days to expiry
        dynamic_zone = calculate_dynamic_pin_zone(iv_level, days_remaining, current_price, confidence_level, current_regime_param)
        
        abs_distance = math.abs(distance_pct)
        
        // Risk assessment using dynamic thresholds and time-aware logic
        risk_level = if abs_distance <= dynamic_zone * 0.5
            "CRITICAL"  // Very high pin probability
        else if abs_distance <= dynamic_zone
            "HIGH"
        else if abs_distance <= dynamic_zone * 2.0
            "MEDIUM"
        else
            "LOW"
        
        // Color intensity increases as expiry approaches
        base_risk_color = if abs_distance <= dynamic_zone * 0.5
            color.red
        else if abs_distance <= dynamic_zone
            color.orange
        else if abs_distance <= dynamic_zone * 2.0
            color.yellow
        else
            color.green
        
        // Enhance color saturation for near-expiry situations
        risk_color = if days_remaining <= 3 and abs_distance <= dynamic_zone
            color.new(base_risk_color, 0)  // Full intensity near expiry
        else
            color.new(base_risk_color, 20)  // Slightly transparent further out
        
        [distance_pct, risk_level, risk_color, dynamic_zone]
    else
        [0.0, "LOW", color.green, static_pin_zone_pct]

// === ENHANCED DATA VALIDATION ===
validate_enhanced_wall_data(wall_price, wall_strength, current_price, regime) =>
    price_valid = not na(wall_price) and wall_price > 0
    price_ratio = price_valid ? wall_price / current_price : 0
    price_reasonable = price_ratio >= 0.2 and price_ratio <= 5.0
    strength_valid = not na(wall_strength) and wall_strength >= 0 and wall_strength <= 100
    
    regime_threshold = str.contains(regime, "High Volatility") ? 12.0 : 
                      str.contains(regime, "Low Volatility") ? 28.0 : 20.0
    
    strength_meaningful = wall_strength >= regime_threshold
    final_valid = price_valid and price_reasonable and strength_valid and strength_meaningful
    
    [final_valid, price_reasonable, strength_meaningful]

// === REGIME-AWARE WALL STRENGTH ADJUSTMENT ===
calculate_regime_adjusted_strength(base_strength, regime) =>
    if not adjust_walls_by_regime
        base_strength
    else
        multiplier = if regime == "High Volatility"
            regime_strength_boost
        else if regime == "High Volatility (Est.)"
            regime_strength_boost * 0.85
        else if regime == "Low Volatility"
            0.88
        else if regime == "Low Volatility (Est.)"
            0.92
        else
            1.0
        
        math.max(0.0, math.min(100.0, base_strength * multiplier))

// === ENHANCED IV ZONE CALCULATION ===
get_enhanced_iv_zone_width(iv_percent, days_to_expiry, wall_price, current_price) =>
    if use_iv_zones and not na(iv_percent) and iv_percent > 0 and not na(days_to_expiry)
        time_factor = math.sqrt(days_to_expiry / 365.25)
        base_move_pct = (iv_percent / 100.0) * time_factor * iv_zone_multiplier
        
        if time_decay_factor and days_to_expiry < 30
            time_decay_adjustment = 0.6 + (days_to_expiry / 75.0)
            base_move_pct := base_move_pct * time_decay_adjustment
        
        if not na(wall_price) and current_price > 0
            distance_factor = math.abs(wall_price - current_price) / current_price
            distance_multiplier = 1.0 + (distance_factor * 0.25)
            base_move_pct := base_move_pct * distance_multiplier
        
        zone_pct = base_move_pct * 100
        math.max(0.3, math.min(zone_pct, 15.0))
    else
        fallback_zone_pct

// === ENHANCED WALL STYLING ===
get_enhanced_wall_styling(base_color, strength, regime, timeframe) =>
    base_transparency = if strength_based_opacity
        strength_factor = math.max(0.1, strength / 100.0)
        base_opacity = 100 - (strength_factor * 80)
        
        regime_adjustment = str.contains(regime, "High Volatility") ? -15 :
                           str.contains(regime, "Low Volatility") ? +20 : 0
        
        math.max(5, math.min(85, base_opacity + regime_adjustment))
    else
        strength >= 80 ? 10 : (strength >= 60 ? 20 : (strength >= 40 ? 35 : 60))
    
    final_color = color.new(base_color, base_transparency)
    line_width = strength >= 85 ? 4 : strength >= 70 ? 3 : strength >= 50 ? 2 : 1
    line_style = strength >= 75 ? line.style_solid : 
                 strength >= 50 ? line.style_dashed :
                 strength >= 30 ? line.style_dotted : line.style_dotted
    
    [final_color, line_style, line_width]

// === WALL CLEANUP FUNCTION ===
cleanup_wall_arrays() =>
    // Clean up line arrays individually
    while array.size(active_swing_put_lines) > max_historical_walls
        old_line = array.shift(active_swing_put_lines)
        if not na(old_line)
            line.delete(old_line)
    
    while array.size(active_swing_call_lines) > max_historical_walls
        old_line = array.shift(active_swing_call_lines)
        if not na(old_line)
            line.delete(old_line)
    
    while array.size(active_long_put_lines) > max_historical_walls
        old_line = array.shift(active_long_put_lines)
        if not na(old_line)
            line.delete(old_line)
    
    while array.size(active_long_call_lines) > max_historical_walls
        old_line = array.shift(active_long_call_lines)
        if not na(old_line)
            line.delete(old_line)
    
    while array.size(active_quarterly_put_lines) > max_historical_walls
        old_line = array.shift(active_quarterly_put_lines)
        if not na(old_line)
            line.delete(old_line)
    
    while array.size(active_quarterly_call_lines) > max_historical_walls
        old_line = array.shift(active_quarterly_call_lines)
        if not na(old_line)
            line.delete(old_line)
    
    while array.size(active_gamma_flip_lines) > max_historical_walls
        old_line = array.shift(active_gamma_flip_lines)
        if not na(old_line)
            line.delete(old_line)
    
    while array.size(active_max_pain_lines) > max_historical_walls
        old_line = array.shift(active_max_pain_lines)
        if not na(old_line)
            line.delete(old_line)
    
    // Clean up box arrays individually
    while array.size(active_swing_put_zones) > max_historical_walls
        old_box = array.shift(active_swing_put_zones)
        if not na(old_box)
            box.delete(old_box)
    
    while array.size(active_swing_call_zones) > max_historical_walls
        old_box = array.shift(active_swing_call_zones)
        if not na(old_box)
            box.delete(old_box)
    
    while array.size(active_long_put_zones) > max_historical_walls
        old_box = array.shift(active_long_put_zones)
        if not na(old_box)
            box.delete(old_box)
    
    while array.size(active_long_call_zones) > max_historical_walls
        old_box = array.shift(active_long_call_zones)
        if not na(old_box)
            box.delete(old_box)
    
    while array.size(active_quarterly_put_zones) > max_historical_walls
        old_box = array.shift(active_quarterly_put_zones)
        if not na(old_box)
            box.delete(old_box)
    
    while array.size(active_quarterly_call_zones) > max_historical_walls
        old_box = array.shift(active_quarterly_call_zones)
        if not na(old_box)
            box.delete(old_box)
    
    while array.size(active_pin_zones) > max_historical_walls
        old_box = array.shift(active_pin_zones)
        if not na(old_box)
            box.delete(old_box)

// === COMPREHENSIVE WALL DRAWING ===
draw_enhanced_gamma_wall(wall_price, wall_strength, base_color, wall_label, is_call, timeframe_suffix, dte, iv_percent, gex_value, line_array, zone_array) =>
    
    if not na(wall_price) and wall_price > 0 and wall_strength >= min_strength
        current_price = close
        [is_valid, price_ok, strength_ok] = validate_enhanced_wall_data(wall_price, wall_strength, current_price, current_regime)
        
        if is_valid and (not hide_weak_walls or wall_strength >= 40)
            adjusted_strength = calculate_regime_adjusted_strength(wall_strength, current_regime)
            [wall_color, line_style, line_width] = get_enhanced_wall_styling(base_color, adjusted_strength, current_regime, timeframe_suffix)
            
            start_bar = bar_index
            end_bar = if wall_extension_method == "Fixed"
                start_bar + extension_bars
            else if wall_extension_method == "To Current Bar"
                bar_index
            else
                start_bar + 200
            
            // Create wall line
            wall_line = line.new(x1=start_bar, y1=wall_price, x2=end_bar, y2=wall_price,
                               color=wall_color, width=line_width, style=line_style)
            
            // Add to management array
            array.push(line_array, wall_line)
            
            // Create IV-based zone if enabled
            if show_wall_zones and use_iv_zones and not na(zone_array)
                zone_width_pct = get_enhanced_iv_zone_width(iv_percent, dte, wall_price, current_price)
                zone_size = wall_price * (zone_width_pct / 100)
                zone_top = wall_price + zone_size
                zone_bottom = wall_price - zone_size
                zone_color = color.new(base_color, 93)
                
                wall_zone = box.new(left=start_bar, top=zone_top, right=end_bar, bottom=zone_bottom,
                                  bgcolor=zone_color, border_color=color.new(base_color, 85),
                                  border_width=1, border_style=line.style_dashed)
                
                array.push(zone_array, wall_zone)
            
            // Create enhanced label
            if show_wall_labels and barstate.islast
                distance_pct = ((wall_price - current_price) / current_price) * 100
                strength_grade = if adjusted_strength >= 90
                    "A+"
                else if adjusted_strength >= 80
                    "A"
                else if adjusted_strength >= 70
                    "B"
                else if adjusted_strength >= 60
                    "C"
                else if adjusted_strength >= 50
                    "D"
                else
                    "F"
                
                label_text = wall_label + " " + timeframe_suffix + "\n" +
                           "$" + str.tostring(wall_price, "#.##") + "\n" +
                           "Str: " + str.tostring(adjusted_strength, "#") + " (" + strength_grade + ")\n" +
                           "Dist: " + str.tostring(distance_pct, "+#.1") + "%\n" +
                           str.tostring(dte, "#") + " DTE"
                
                if not na(gex_value) and gex_value != 0
                    gex_sign = gex_value >= 0 ? "+" : ""
                    label_text := label_text + "\nGEX: " + gex_sign + str.tostring(gex_value, "#.1") + "M"
                
                if show_iv_info and not na(iv_percent) and iv_percent > 0
                    label_text := label_text + "\nIV: " + str.tostring(iv_percent, "#.0") + "%"
                
                label_style = is_call ? label.style_label_down : label.style_label_up
                label_x = end_bar - math.round(extension_bars * 0.3)
                
                label_size_setting = if label_size == "Tiny"
                    size.tiny
                else if label_size == "Small"
                    size.small
                else if label_size == "Normal"
                    size.normal
                else
                    size.large
                
                label.new(x=label_x, y=wall_price, text=label_text,
                         style=label_style, color=wall_color, textcolor=color.white,
                         size=label_size_setting)
            
            true
        else
            false
    else
        false

// === GAMMA FLIP LEVEL DRAWING ===
draw_gamma_flip_level(gamma_flip_price) =>
    if show_gamma_flip and not na(gamma_flip_price) and gamma_flip_price > 0
        start_bar = bar_index
        end_bar = start_bar + extension_bars
        
        flip_color = color.new(gamma_flip_color, 30)
        flip_line = line.new(x1=start_bar, y1=gamma_flip_price, x2=end_bar, y2=gamma_flip_price,
                           color=flip_color, width=2, style=line.style_dashed)
        
        array.push(active_gamma_flip_lines, flip_line)
        
        if barstate.islast and show_wall_labels
            distance_pct = ((gamma_flip_price - close) / close) * 100
            flip_text = "Gamma Flip\n$" + str.tostring(gamma_flip_price, "#.##") + "\n" +
                       "Dist: " + str.tostring(distance_pct, "+#.1") + "%"
            
            label.new(x=end_bar - 10, y=gamma_flip_price, text=flip_text,
                     style=label.style_label_left, color=flip_color, textcolor=color.white,
                     size=size.small)

// === ENHANCED MAX PAIN DRAWING FUNCTIONS ===
draw_max_pain_level(max_pain_price, expiry_bar_index) =>
    if enable_max_pain and show_max_pain_line and not na(max_pain_price) and max_pain_price > 0
        start_bar = bar_index
        
        // SIMPLE: One bar = one day, so extend by actual days remaining
        days_remaining_actual = math.max(1, days_to_expiry)
        
        end_bar = if expiry_type == "Weekly Friday"
            // Weekly: 1-7 days typically, so 1-7 bars
            start_bar + math.min(days_remaining_actual, 10)  // Cap at 10 for safety
        else if expiry_type == "Monthly (3rd Fri)"
            // Monthly: 7-30+ days typically, so 7-30+ bars  
            start_bar + math.min(days_remaining_actual, 35)  // Cap at 35 for chart readability
        else if expiry_type == "Manual Days"
            // Manual: whatever user sets
            start_bar + math.min(days_remaining_actual, 40)
        else
            // Auto-detect: moderate cap
            start_bar + math.min(days_remaining_actual, 25)
        
        pain_color = color.new(max_pain_color, 20)
        pain_line = line.new(x1=start_bar, y1=max_pain_price, x2=end_bar, y2=max_pain_price,
                           color=pain_color, width=3, style=line.style_solid)
        
        array.push(active_max_pain_lines, pain_line)
        
        if barstate.islast and show_wall_labels
            distance_pct = ((max_pain_price - close) / close) * 100
            confidence_text = max_pain_confidence >= 0.8 ? " (High)" : max_pain_confidence >= 0.6 ? " (Med)" : " (Low)"
            expiry_status = days_to_expiry <= 3 ? " ⚡" : days_to_expiry <= 7 ? " 🔥" : ""
            
            pain_text = "Max Pain" + expiry_status + "\n$" + str.tostring(max_pain_price, "#.##") + "\n" +
                       "Dist: " + str.tostring(distance_pct, "+#.1") + "%\n" +
                       "Risk: " + pin_risk_level + confidence_text + "\n" +
                       expiry_info + "\nBars:" + str.tostring(end_bar - start_bar)
            
            label.new(x=end_bar + 2, y=max_pain_price, text=pain_text,
                     style=label.style_label_left, color=pain_color, textcolor=color.white,
                     size=size.small)

draw_pin_zone(max_pain_price, expiry_bar_index) =>
    if enable_max_pain and show_pin_zone and not na(max_pain_price) and max_pain_price > 0
        start_bar = bar_index
        
        // SIMPLE: One bar = one day, so extend by actual days remaining (same as max pain line)
        days_remaining_actual = math.max(1, days_to_expiry)
        
        end_bar = if expiry_type == "Weekly Friday"
            // Weekly: 1-7 days typically, so 1-7 bars
            start_bar + math.min(days_remaining_actual, 10)  // Cap at 10 for safety
        else if expiry_type == "Monthly (3rd Fri)"
            // Monthly: 7-30+ days typically, so 7-30+ bars  
            start_bar + math.min(days_remaining_actual, 35)  // Cap at 35 for chart readability
        else if expiry_type == "Manual Days"
            // Manual: whatever user sets
            start_bar + math.min(days_remaining_actual, 40)
        else
            // Auto-detect: moderate cap
            start_bar + math.min(days_remaining_actual, 25)
        
        // Use dynamic pin zone if enabled
        pin_zone_to_use = use_dynamic_pin_zone ? dynamic_pin_zone_pct : static_pin_zone_pct
        pin_range = max_pain_price * (pin_zone_to_use / 100)
        upper_pin = max_pain_price + pin_range
        lower_pin = max_pain_price - pin_range
        
        // ENHANCED: More dramatic color intensity based on expiry timing
        base_transparency = if max_pain_confidence >= 0.8
            75  // High confidence = more visible
        else if max_pain_confidence >= 0.6
            80  // Medium confidence
        else
            85  // Low confidence = less visible
        
        // ENHANCED: Much more dramatic time-based adjustments
        time_adjustment = if days_to_expiry <= 1
            -35  // Very intense on expiry day
        else if days_to_expiry <= 3
            -25  // Very intense in last 3 days
        else if days_to_expiry <= 7
            -10  // More visible in last week (weekly expiry)
        else if days_to_expiry <= 14
            0    // Normal for bi-weekly
        else if days_to_expiry <= 21
            +5   // Slightly less visible for 3-week monthly
        else
            +15  // Much less visible for far expiries
        
        zone_transparency = math.max(30, math.min(90, base_transparency + time_adjustment))
        
        zone_color = color.new(pin_zone_color, zone_transparency)
        pin_box = box.new(left=start_bar, top=upper_pin, right=end_bar, bottom=lower_pin,
                         bgcolor=zone_color, border_color=color.new(pin_zone_color, zone_transparency - 15),
                         border_width=2, border_style=line.style_dashed)
        
        array.push(active_pin_zones, pin_box)

// === MAIN PROCESSING ===
current_symbol = syminfo.ticker

// Parse data for current symbol
[st_put_wall, st_call_wall, lt_put_wall, lt_call_wall, quarterly_put_wall, quarterly_call_wall,
 st_put_strength, st_call_strength, lt_put_strength, lt_call_strength, q_put_strength, q_call_strength,
 lower_1sd, upper_1sd, lower_1_5sd, upper_1_5sd, lower_2sd, upper_2sd,
 gamma_flip, swing_iv, long_iv, quarterly_iv, cp_ratio, activity_score, trend,
 swing_dte, long_dte, quarterly_dte,
 st_put_gex, st_call_gex, lt_put_gex, lt_call_gex, q_put_gex, q_call_gex, parse_error] = parse_dynamic_gamma_data(current_symbol)

// Update validation status
data_validation_passed := parse_error == ""
parsing_error := parse_error

// Update current gamma flip for global access
current_gamma_flip := gamma_flip

// === ENHANCED MAX PAIN PROCESSING ===
if enable_max_pain and barstate.islast
    // FIXED: Enhanced expiry calculation that respects user selection
    [calculated_days, calculated_expiry_bar, expiry_valid, expiry_description, method_description] = calculate_expiry_details()
    
    // FIXED: Only use calculated values when they're valid AND not overridden
    if expiry_type == "Manual Days"
        // Manual override always takes precedence
        days_to_expiry := manual_days_to_expiry
        is_expiry_valid := true
        expiry_info := "Manual: " + str.tostring(manual_days_to_expiry) + "D"
        actual_expiry_method := "Manual Override"
    else if expiry_valid and calculated_days > 0 and calculated_days <= 45
        // Use calculated expiry when valid and reasonable
        days_to_expiry := calculated_days
        is_expiry_valid := true
        expiry_info := expiry_description
        actual_expiry_method := method_description
    else
        // Fallback with more reasonable defaults based on expiry type
        if expiry_type == "Weekly Friday"
            days_to_expiry := 5  // Default to next Friday
        else if expiry_type == "Monthly (3rd Fri)"
            days_to_expiry := 14  // Default to ~2 weeks for monthly
        else
            days_to_expiry := 7   // Auto-detect fallback
        
        is_expiry_valid := true
        expiry_info := "Fallback: " + str.tostring(days_to_expiry) + "D"
        actual_expiry_method := "Fallback (" + expiry_type + ")"
    
    current_expiry_bar := bar_index + days_to_expiry
    
    // Proceed with max pain calculation when enabled
    if is_expiry_valid and days_to_expiry > 0
        // Generate enhanced strikes using gamma wall context with all required parameters
        generate_enhanced_strikes(close, max_pain_strikes, strike_spacing, st_put_wall, st_call_wall, lt_put_wall, lt_call_wall, swing_iv)
        populate_enhanced_oi_data(close, activity_score, st_put_wall, st_call_wall, days_to_expiry)
        
        // Calculate enhanced max pain with confidence scoring using actual days to expiry
        [calculated_max_pain, pain_confidence] = calculate_enhanced_max_pain(days_to_expiry)
        
        // Lower confidence threshold for testing - accept anything above 0.5
        effective_threshold = math.min(confidence_threshold, 0.5)
        
        // Update max pain even with lower confidence for visibility
        if pain_confidence >= effective_threshold
            current_max_pain := calculated_max_pain
            max_pain_confidence := pain_confidence
            
            // Update metrics using enhanced calculation with all required parameters including actual days
            [distance_pct, risk_level, risk_color, dynamic_zone] = update_max_pain_metrics(calculated_max_pain, close, pain_confidence, swing_iv, current_regime, days_to_expiry)
            max_pain_distance_pct := distance_pct
            pin_risk_level := risk_level
            pin_risk_color := risk_color
            dynamic_pin_zone_pct := dynamic_zone

// === WALL RENDERING WITH CLEANUP ===
if barstate.islast and data_validation_passed and (bar_index - last_data_update) > 5
    last_data_update := bar_index
    
    // Clean up old walls periodically
    cleanup_wall_arrays()
    
    // Draw swing walls (14D) with swing-specific IV
    if show_swing_walls or show_all_timeframes
        draw_enhanced_gamma_wall(st_put_wall, st_put_strength, swing_put_color, "ST Put", false, 
                               "(14D)", swing_dte, swing_iv, st_put_gex, 
                               active_swing_put_lines, active_swing_put_zones)
        
        draw_enhanced_gamma_wall(st_call_wall, st_call_strength, swing_call_color, "ST Call", true,
                               "(14D)", swing_dte, swing_iv, st_call_gex,
                               active_swing_call_lines, active_swing_call_zones)
    
    // Draw long walls (30D) with long-specific IV
    if show_long_walls or show_all_timeframes
        draw_enhanced_gamma_wall(lt_put_wall, lt_put_strength, long_put_color, "LT Put", false,
                               "(30D)", long_dte, long_iv, lt_put_gex,
                               active_long_put_lines, active_long_put_zones)
        
        draw_enhanced_gamma_wall(lt_call_wall, lt_call_strength, long_call_color, "LT Call", true,
                               "(30D)", long_dte, long_iv, lt_call_gex,
                               active_long_call_lines, active_long_call_zones)
    
    // Draw quarterly walls (90D) with quarterly-specific IV
    if show_quarterly_walls or show_all_timeframes
        draw_enhanced_gamma_wall(quarterly_put_wall, q_put_strength, quarterly_put_color, "Q Put", false,
                               "(90D)", quarterly_dte, quarterly_iv, q_put_gex,
                               active_quarterly_put_lines, active_quarterly_put_zones)
        
        draw_enhanced_gamma_wall(quarterly_call_wall, q_call_strength, quarterly_call_color, "Q Call", true,
                               "(90D)", quarterly_dte, quarterly_iv, q_call_gex,
                               active_quarterly_call_lines, active_quarterly_call_zones)
    
    // Draw gamma flip level
    if not na(gamma_flip)
        draw_gamma_flip_level(gamma_flip)
    
    // Draw max pain elements - simplified conditions for better visibility
    if enable_max_pain and not na(current_max_pain)
        draw_max_pain_level(current_max_pain, current_expiry_bar)
        draw_pin_zone(current_max_pain, current_expiry_bar)

// === HELPER FUNCTION FOR TABLE INFO ===
add_enhanced_wall_info(enhanced_info_table, wall_price, strength, wall_name, wall_color, iv_val, gex_val, row_idx, current_regime, min_strength) =>
    if not na(wall_price) and wall_price > 0 and strength >= min_strength
        adj_strength = calculate_regime_adjusted_strength(strength, current_regime)
        
        table.cell(enhanced_info_table, 0, row_idx, wall_name, text_color=wall_color, text_size=size.small)
        table.cell(enhanced_info_table, 1, row_idx, "$" + str.tostring(wall_price, "#.##"), text_color=color.white, text_size=size.small)
        
        strength_color = if adj_strength >= 80
            color.lime
        else if adj_strength >= 60
            color.yellow
        else if adj_strength >= 40
            color.orange
        else
            color.gray
        
        table.cell(enhanced_info_table, 2, row_idx, str.tostring(adj_strength, "#"), text_color=strength_color, text_size=size.small)
        
        // Show timeframe-specific IV
        iv_color = if iv_val >= 40
            color.red
        else if iv_val >= 25
            color.yellow
        else
            color.green
        
        table.cell(enhanced_info_table, 3, row_idx, str.tostring(iv_val, "#") + "%", text_color=iv_color, text_size=size.small)
        
        // GEX information
        if not na(gex_val) and gex_val != 0
            gex_color = gex_val >= 0 ? color.green : color.red
            table.cell(enhanced_info_table, 4, row_idx, str.tostring(gex_val, "#.1"), text_color=gex_color, text_size=size.small)
        else
            table.cell(enhanced_info_table, 4, row_idx, "N/A", text_color=color.gray, text_size=size.small)
        
        row_idx + 1
    else
        row_idx

// === ENHANCED INFORMATION TABLE WITH MAX PAIN ===
if show_info_table and barstate.islast and data_validation_passed
    var table enhanced_info_table = table.new(position.bottom_right, 6, 15, bgcolor=color.new(color.black, 85), border_width=1)
    
    table.clear(enhanced_info_table, 0, 0, 5, 14)
    
    // Enhanced header
    table.cell(enhanced_info_table, 0, 0, "Enhanced Gamma & Max Pain", text_color=color.white, text_size=size.normal, bgcolor=color.new(color.blue, 70))
    table.cell(enhanced_info_table, 1, 0, current_symbol, text_color=color.white, text_size=size.normal, bgcolor=color.new(color.blue, 70))
    table.cell(enhanced_info_table, 2, 0, "Price", text_color=color.white, text_size=size.small, bgcolor=color.new(color.blue, 70))
    table.cell(enhanced_info_table, 3, 0, "Str", text_color=color.white, text_size=size.small, bgcolor=color.new(color.blue, 70))
    table.cell(enhanced_info_table, 4, 0, "IV%", text_color=color.white, text_size=size.small, bgcolor=color.new(color.blue, 70))
    table.cell(enhanced_info_table, 5, 0, "GEX(M)", text_color=color.white, text_size=size.small, bgcolor=color.new(color.blue, 70))
    
    current_row = 1
    
    // Add all wall information with their specific IVs
    current_row := add_enhanced_wall_info(enhanced_info_table, st_put_wall, st_put_strength, "ST Put", swing_put_color, swing_iv, st_put_gex, current_row, current_regime, min_strength)
    current_row := add_enhanced_wall_info(enhanced_info_table, st_call_wall, st_call_strength, "ST Call", swing_call_color, swing_iv, st_call_gex, current_row, current_regime, min_strength)
    current_row := add_enhanced_wall_info(enhanced_info_table, lt_put_wall, lt_put_strength, "LT Put", long_put_color, long_iv, lt_put_gex, current_row, current_regime, min_strength)
    current_row := add_enhanced_wall_info(enhanced_info_table, lt_call_wall, lt_call_strength, "LT Call", long_call_color, long_iv, lt_call_gex, current_row, current_regime, min_strength)
    
    if show_quarterly_walls
        current_row := add_enhanced_wall_info(enhanced_info_table, quarterly_put_wall, q_put_strength, "Q Put", quarterly_put_color, quarterly_iv, q_put_gex, current_row, current_regime, min_strength)
        current_row := add_enhanced_wall_info(enhanced_info_table, quarterly_call_wall, q_call_strength, "Q Call", quarterly_call_color, quarterly_iv, q_call_gex, current_row, current_regime, min_strength)
    
    // Gamma flip information
    if show_gamma_flip and not na(gamma_flip) and current_row <= 12
        table.cell(enhanced_info_table, 0, current_row, "Gamma Flip:", text_color=gamma_flip_color, text_size=size.small)
        table.cell(enhanced_info_table, 1, current_row, "$" + str.tostring(gamma_flip, "#.##"), text_color=color.white, text_size=size.small)
        
        distance_pct = ((gamma_flip - close) / close) * 100
        distance_color = math.abs(distance_pct) <= 1.0 ? color.orange : color.white
        table.cell(enhanced_info_table, 2, current_row, str.tostring(distance_pct, "+#.1") + "%", text_color=distance_color, text_size=size.small)
        current_row += 1
    
    // Max Pain information
    if enable_max_pain and not na(current_max_pain) and current_row <= 12
        table.cell(enhanced_info_table, 0, current_row, "Max Pain:", text_color=max_pain_color, text_size=size.small)
        table.cell(enhanced_info_table, 1, current_row, "$" + str.tostring(current_max_pain, "#.##"), text_color=color.white, text_size=size.small)
        table.cell(enhanced_info_table, 2, current_row, str.tostring(max_pain_distance_pct, "+#.1") + "%", text_color=color.white, text_size=size.small)
        current_row += 1
        
        // Pin Risk with confidence and expiry status
        confidence_color = max_pain_confidence >= 0.8 ? color.lime : max_pain_confidence >= 0.6 ? color.yellow : color.orange
        expiry_urgency = days_to_expiry <= 3 ? " ⚡" : days_to_expiry <= 7 ? " 🔥" : ""
        
        table.cell(enhanced_info_table, 0, current_row, "Pin Risk:", text_color=color.gray, text_size=size.small)
        table.cell(enhanced_info_table, 1, current_row, pin_risk_level + expiry_urgency, text_color=pin_risk_color, text_size=size.small)
        table.cell(enhanced_info_table, 2, current_row, str.tostring(max_pain_confidence * 100, "#") + "%", text_color=confidence_color, text_size=size.small)
        current_row += 1
        
        // Dynamic Pin Zone with expiry info
        zone_info = use_dynamic_pin_zone ? str.tostring(dynamic_pin_zone_pct, "#.1") + "%" : str.tostring(static_pin_zone_pct, "#.1") + "%"
        table.cell(enhanced_info_table, 0, current_row, "Pin Zone:", text_color=color.gray, text_size=size.small)
        table.cell(enhanced_info_table, 1, current_row, zone_info, text_color=color.white, text_size=size.small)
        table.cell(enhanced_info_table, 2, current_row, expiry_info, text_color=color.gray, text_size=size.small)
        current_row += 1
        
        // Strike Count
        table.cell(enhanced_info_table, 0, current_row, "Strikes:", text_color=color.gray, text_size=size.small)
        table.cell(enhanced_info_table, 1, current_row, str.tostring(array.size(max_pain_strike_prices)), text_color=color.white, text_size=size.small)
        current_row += 1
    
    // Market regime information
    if enable_regime_detection and current_row <= 12
        table.cell(enhanced_info_table, 0, current_row, "Regime:", text_color=color.gray, text_size=size.tiny)
        regime_color = str.contains(current_regime, "High Volatility") ? color.red :
                      str.contains(current_regime, "Low Volatility") ? color.green : color.yellow
        
        regime_short = str.replace(str.replace(current_regime, " Volatility", ""), " (Est.)", "*")
        table.cell(enhanced_info_table, 1, current_row, regime_short, text_color=regime_color, text_size=size.tiny)
        table.cell(enhanced_info_table, 2, current_row, "VIX:" + str.tostring(regime_vix, "#.1"), text_color=color.gray, text_size=size.tiny)
        current_row += 1
    
    // Additional metrics
    if current_row <= 12
        table.cell(enhanced_info_table, 0, current_row, "C/P Ratio:", text_color=color.gray, text_size=size.tiny)
        table.cell(enhanced_info_table, 1, current_row, str.tostring(cp_ratio, "#.1"), text_color=color.white, text_size=size.tiny)
        table.cell(enhanced_info_table, 2, current_row, "Activity:" + str.tostring(activity_score, "#"), text_color=color.gray, text_size=size.tiny)

// === REGIME DISPLAY ===
if enable_regime_detection and barstate.islast and data_validation_passed
    var label regime_display = na
    
    if not na(regime_display)
        label.delete(regime_display)
    
    regime_text = current_regime + "\nVIX: " + str.tostring(regime_vix, "#.1")
    
    if show_iv_info and swing_iv > 0
        regime_text := regime_text + "\nSwing IV: " + str.tostring(swing_iv, "#") + "%"
    
    if enable_max_pain and not na(current_max_pain)
        regime_text := regime_text + "\nMax Pain: $" + str.tostring(current_max_pain, "#.##")
    
    label_x = if regime_display_position == "Top Right" or regime_display_position == "Bottom Right"
        bar_index
    else
        bar_index - 40
    
    label_y = if regime_display_position == "Top Left" or regime_display_position == "Top Right"
        high * 1.02
    else
        low * 0.98
    
    label_style = if regime_display_position == "Top Left" or regime_display_position == "Top Right"
        label.style_label_down
    else
        label.style_label_up
    
    regime_label_color = if str.contains(current_regime, "High Volatility")
        color.new(color.red, 25)
    else if str.contains(current_regime, "Low Volatility")
        color.new(color.green, 25)
    else
        color.new(color.blue, 25)
    
    regime_display := label.new(x=label_x, y=label_y, text=regime_text, style=label_style,
                               color=regime_label_color, textcolor=color.white, size=size.small)

// === WALL APPROACH CHECK FUNCTION ===
check_wall_approach(wall_price, wall_strength, wall_name, iv_val, current_symbol, alert_distance_pct) =>
    if not na(wall_price) and wall_price > 0 and wall_strength >= 50
        distance_pct = math.abs(close - wall_price) / wall_price * 100
        if distance_pct <= alert_distance_pct
            alert("Approaching " + wall_name + ": " + current_symbol + " nearing $" + str.tostring(wall_price, "#.##") + 
                  " (Distance: " + str.tostring(distance_pct, "#.1") + "%, IV: " + str.tostring(iv_val, "#.0") + "%)", 
                  alert.freq_once_per_bar)

// === COMPREHENSIVE ALERT SYSTEM ===
if barstate.isconfirmed
    // Wall breach alerts
    if enable_wall_breach_alerts
        if ta.crossover(close, st_call_wall) and st_call_strength >= 60 and not na(st_call_wall)
            alert_msg = "Strong Call Wall Breach: " + current_symbol + " broke $" + str.tostring(st_call_wall, "#.##") + 
                       " (Str: " + str.tostring(st_call_strength, "#") + ", IV: " + str.tostring(swing_iv, "#.0") + "%)"
            if not na(st_call_gex)
                alert_msg := alert_msg + " GEX: " + str.tostring(st_call_gex, "#.1") + "M"
            alert(alert_msg, alert.freq_once_per_bar)
        
        if ta.crossunder(close, st_put_wall) and st_put_strength >= 60 and not na(st_put_wall)
            alert_msg = "Strong Put Wall Breach: " + current_symbol + " broke $" + str.tostring(st_put_wall, "#.##") + 
                       " (Str: " + str.tostring(st_put_strength, "#") + ", IV: " + str.tostring(swing_iv, "#.0") + "%)"
            if not na(st_put_gex)
                alert_msg := alert_msg + " GEX: " + str.tostring(st_put_gex, "#.1") + "M"
            alert(alert_msg, alert.freq_once_per_bar)
        
        if ta.crossover(close, st_call_wall) and st_call_strength >= 80 and not na(st_call_wall)
            alert("CRITICAL Call Wall Breach: " + current_symbol + " SMASHED $" + str.tostring(st_call_wall, "#.##") + 
                  " - Major breakout potential!", alert.freq_once_per_bar)
        
        if ta.crossunder(close, st_put_wall) and st_put_strength >= 80 and not na(st_put_wall)
            alert("CRITICAL Put Wall Breach: " + current_symbol + " CRASHED through $" + str.tostring(st_put_wall, "#.##") + 
                  " - Major breakdown potential!", alert.freq_once_per_bar)
    
    // Gamma flip alerts
    if enable_gamma_flip_alerts and not na(gamma_flip)
        if ta.crossover(close, gamma_flip)
            alert("Gamma Flip Cross: " + current_symbol + " crossed above gamma flip at $" + str.tostring(gamma_flip, "#.##") + 
                  " - Positive gamma territory", alert.freq_once_per_bar)
        
        if ta.crossunder(close, gamma_flip)
            alert("Gamma Flip Cross: " + current_symbol + " crossed below gamma flip at $" + str.tostring(gamma_flip, "#.##") + 
                  " - Negative gamma territory", alert.freq_once_per_bar)
    
    // Enhanced Max Pain alerts with expiry awareness
    if enable_max_pain_alerts and enable_max_pain and not na(current_max_pain) and is_expiry_valid
        distance_to_pain = math.abs(close - current_max_pain) / current_max_pain * 100
        pin_zone_to_use = use_dynamic_pin_zone ? dynamic_pin_zone_pct : static_pin_zone_pct
        
        // Alert thresholds tighten dramatically as expiry approaches
        alert_threshold = if days_to_expiry <= 1
            pin_zone_to_use * 0.2  // Very tight on expiry day
        else if days_to_expiry <= 3
            pin_zone_to_use * 0.4  // Tight in last 3 days
        else if days_to_expiry <= 7
            pin_zone_to_use * 0.6  // Tighter for weekly expiries
        else
            pin_zone_to_use * 0.8  // Normal threshold for monthly
        
        if distance_to_pain <= alert_threshold
            urgency_indicator = days_to_expiry <= 1 ? "CRITICAL: " : days_to_expiry <= 3 ? "URGENT: " : days_to_expiry <= 7 ? "ALERT: " : ""
            
            alert(urgency_indicator + "Max Pain Proximity: " + current_symbol + " within " + str.tostring(alert_threshold, "#.1") + "% of Max Pain at $" + str.tostring(current_max_pain, "#.##") + 
                  " (" + expiry_info + " - " + pin_risk_level + " pin risk!) Method: " + actual_expiry_method, alert.freq_once_per_bar)
    
    // Wall approach alerts
    if enable_approach_alerts
        check_wall_approach(st_call_wall, st_call_strength, "ST Call Wall", swing_iv, current_symbol, alert_distance_pct)
        check_wall_approach(st_put_wall, st_put_strength, "ST Put Wall", swing_iv, current_symbol, alert_distance_pct)
        check_wall_approach(lt_call_wall, lt_call_strength, "LT Call Wall", long_iv, current_symbol, alert_distance_pct)
        check_wall_approach(lt_put_wall, lt_put_strength, "LT Put Wall", long_iv, current_symbol, alert_distance_pct)
    
    // Enhanced regime change alerts
    if enable_regime_change_alerts
        var string previous_regime = "Normal Volatility"
        
        if current_regime != previous_regime
            alert("Market Regime Change: " + previous_regime + " → " + current_regime + 
                  " (VIX: " + str.tostring(regime_vix, "#.1") + ") - Adjust wall expectations accordingly!", alert.freq_once_per_bar)
            previous_regime := current_regime

// === ENHANCED DEBUG INFORMATION ===
if show_debug_info and barstate.islast
    var table debug_table = table.new(position.top_left, 3, 20, bgcolor=color.new(color.black, 90), border_width=1)
    
    table.cell(debug_table, 0, 0, "Enhanced Debug Information", text_color=color.yellow, text_size=size.small, bgcolor=color.new(color.gray, 75))
    table.cell(debug_table, 0, 1, "Symbol:", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 1, 1, current_symbol, text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 0, 2, "Data Valid:", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 1, 2, str.tostring(data_validation_passed), text_color=data_validation_passed ? color.green : color.red, text_size=size.tiny)
    table.cell(debug_table, 0, 3, "Parse Error:", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 1, 3, parsing_error == "" ? "None" : parsing_error, text_color=parsing_error == "" ? color.green : color.red, text_size=size.tiny)
    table.cell(debug_table, 0, 4, "Regime:", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 1, 4, current_regime, text_color=color.yellow, text_size=size.tiny)
    table.cell(debug_table, 0, 5, "ST Walls:", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 1, 5, str.tostring(st_put_wall, "#") + "/" + str.tostring(st_call_wall, "#"), text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 0, 6, "IVs:", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 1, 6, str.tostring(swing_iv, "#") + "/" + str.tostring(long_iv, "#"), text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 0, 7, "Gamma Flip:", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 1, 7, str.tostring(gamma_flip, "#.##"), text_color=color.orange, text_size=size.tiny)
    table.cell(debug_table, 0, 8, "Max Pain:", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 1, 8, str.tostring(current_max_pain, "#.##"), text_color=max_pain_color, text_size=size.tiny)
    table.cell(debug_table, 0, 9, "Pin Risk:", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 1, 9, pin_risk_level, text_color=pin_risk_color, text_size=size.tiny)
    table.cell(debug_table, 0, 10, "Expiry Valid:", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 1, 10, str.tostring(is_expiry_valid), text_color=is_expiry_valid ? color.green : color.red, text_size=size.tiny)
    table.cell(debug_table, 0, 11, "Days to Expiry:", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 1, 11, str.tostring(days_to_expiry), text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 0, 12, "Strikes:", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 1, 12, str.tostring(array.size(max_pain_strike_prices)), text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 0, 13, "Confidence:", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 1, 13, str.tostring(max_pain_confidence * 100, "#") + "%", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 0, 14, "Update:", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 1, 14, last_update, text_color=color.gray, text_size=size.tiny)
    
    // ENHANCED: Additional debug fields for expiry tracking
    table.cell(debug_table, 0, 15, "Expiry Type:", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 1, 15, expiry_type, text_color=color.yellow, text_size=size.tiny)
    table.cell(debug_table, 0, 16, "Calc Method:", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 1, 16, actual_expiry_method, text_color=color.green, text_size=size.tiny)
    table.cell(debug_table, 0, 17, "Pin Zone %:", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 1, 17, str.tostring(dynamic_pin_zone_pct, "#.1") + "%", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 0, 18, "Zone Type:", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 1, 18, use_dynamic_pin_zone ? "Dynamic" : "Static", text_color=use_dynamic_pin_zone ? color.lime : color.orange, text_size=size.tiny)
    table.cell(debug_table, 0, 19, "Expiry Info:", text_color=color.white, text_size=size.tiny)
    table.cell(debug_table, 1, 19, expiry_info, text_color=color.gray, text_size=size.tiny)

// === COMPREHENSIVE PLOTTING FOR DATA WINDOW ===
// Wall prices
plot(st_put_wall, "ST Put Wall", color=color.new(swing_put_color, 70), linewidth=1, display=display.data_window)
plot(st_call_wall, "ST Call Wall", color=color.new(swing_call_color, 70), linewidth=1, display=display.data_window)
plot(lt_put_wall, "LT Put Wall", color=color.new(long_put_color, 70), linewidth=1, display=display.data_window)
plot(lt_call_wall, "LT Call Wall", color=color.new(long_call_color, 70), linewidth=1, display=display.data_window)
plot(quarterly_put_wall, "Q Put Wall", color=color.new(quarterly_put_color, 70), linewidth=1, display=display.data_window)
plot(quarterly_call_wall, "Q Call Wall", color=color.new(quarterly_call_color, 70), linewidth=1, display=display.data_window)

// Regime-adjusted strengths
plot(calculate_regime_adjusted_strength(st_put_strength, current_regime), "Adj ST Put Strength", color=color.red, display=display.data_window)
plot(calculate_regime_adjusted_strength(st_call_strength, current_regime), "Adj ST Call Strength", color=color.green, display=display.data_window)
plot(calculate_regime_adjusted_strength(lt_put_strength, current_regime), "Adj LT Put Strength", color=color.orange, display=display.data_window)
plot(calculate_regime_adjusted_strength(lt_call_strength, current_regime), "Adj LT Call Strength", color=color.blue, display=display.data_window)
plot(calculate_regime_adjusted_strength(q_put_strength, current_regime), "Adj Q Put Strength", color=color.purple, display=display.data_window)
plot(calculate_regime_adjusted_strength(q_call_strength, current_regime), "Adj Q Call Strength", color=color.yellow, display=display.data_window)

// Standard deviation ranges
plot(lower_1sd, "Lower 1SD", color=color.new(color.gray, 50), display=display.data_window)
plot(upper_1sd, "Upper 1SD", color=color.new(color.gray, 50), display=display.data_window)
plot(lower_1_5sd, "Lower 1.5SD", color=color.new(color.gray, 60), display=display.data_window)
plot(upper_1_5sd, "Upper 1.5SD", color=color.new(color.gray, 60), display=display.data_window)
plot(lower_2sd, "Lower 2SD", color=color.new(color.gray, 70), display=display.data_window)
plot(upper_2sd, "Upper 2SD", color=color.new(color.gray, 70), display=display.data_window)

// Key levels
plot(gamma_flip, "Gamma Flip Point", color=gamma_flip_color, display=display.data_window)
plot(current_max_pain, "Max Pain Level", color=max_pain_color, display=display.data_window)

// Enhanced Max Pain metrics
plot(max_pain_distance_pct, "Distance to Pain %", color=color.white, display=display.data_window)
plot(array.size(max_pain_strike_prices), "Strike Count", color=color.gray, display=display.data_window)
plot(days_to_expiry, "Days to Expiry", color=color.orange, display=display.data_window)
plot(max_pain_confidence * 100, "Max Pain Confidence %", color=color.lime, display=display.data_window)
plot(dynamic_pin_zone_pct, "Dynamic Pin Zone %", color=color.aqua, display=display.data_window)

// Enhanced IV values for each timeframe
plot(swing_iv, "Swing IV%", color=color.purple, display=display.data_window)
plot(long_iv, "Long IV%", color=color.blue, display=display.data_window)
plot(quarterly_iv, "Quarterly IV%", color=color.orange, display=display.data_window)

// GEX values with enhanced labeling
plot(st_put_gex, "ST Put GEX (M)", color=color.new(color.red, 40), display=display.data_window)
plot(st_call_gex, "ST Call GEX (M)", color=color.new(color.green, 40), display=display.data_window)
plot(lt_put_gex, "LT Put GEX (M)", color=color.new(color.orange, 40), display=display.data_window)
plot(lt_call_gex, "LT Call GEX (M)", color=color.new(color.blue, 40), display=display.data_window)
plot(q_put_gex, "Q Put GEX (M)", color=color.new(color.purple, 40), display=display.data_window)
plot(q_call_gex, "Q Call GEX (M)", color=color.new(color.yellow, 40), display=display.data_window)

// Enhanced market metrics
plot(cp_ratio, "Call/Put Ratio", color=color.yellow, display=display.data_window)
plot(activity_score, "Activity Score", color=color.green, display=display.data_window)
plot(regime_vix, "Current VIX", color=color.red, display=display.data_window)
plot(trend, "Trend Score", color=color.white, display=display.data_window)

// Enhanced expiry tracking metrics
plot(get_expiry_time_decay(days_to_expiry), "Time Decay Factor", color=color.green, display=display.data_window)
plot(is_expiry_valid ? 1 : 0, "Expiry Valid Flag", color=color.yellow, display=display.data_window)

// Enhanced regime metrics
plot(str.contains(current_regime, "High Volatility") ? 1 : str.contains(current_regime, "Low Volatility") ? -1 : 0, "Regime Signal", color=color.purple, display=display.data_window)

// Enhanced wall validation metrics - fixed tuple access
var bool st_put_valid = false
var bool st_call_valid = false

if barstate.islast
    [st_put_valid_result, st_put_price_ok, st_put_strength_ok] = validate_enhanced_wall_data(st_put_wall, st_put_strength, close, current_regime)
    [st_call_valid_result, st_call_price_ok, st_call_strength_ok] = validate_enhanced_wall_data(st_call_wall, st_call_strength, close, current_regime)
    st_put_valid := st_put_valid_result
    st_call_valid := st_call_valid_result

plot(st_put_valid ? 1 : 0, "ST Put Wall Valid", color=color.red, display=display.data_window)
plot(st_call_valid ? 1 : 0, "ST Call Wall Valid", color=color.green, display=display.data_window)

// === FINAL STATUS INDICATORS ===
// These help identify if the script is working correctly
var color status_color = color.orange

if barstate.islast
    status_color := if data_validation_passed and enable_max_pain and not na(current_max_pain)
        color.lime  // All systems operational
    else if data_validation_passed and not enable_max_pain
        color.yellow  // Walls working, max pain disabled
    else if not data_validation_passed
        color.red  // Data issues
    else
        color.orange  // Unknown state

// Plot a small status indicator
plot(close * 0.999, "System Status", color=status_color, linewidth=1, display=display.data_window) 