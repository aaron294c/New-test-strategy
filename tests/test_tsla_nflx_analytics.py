#!/usr/bin/env python3
"""
Comprehensive test suite for TSLA and NFLX analytics integration
Validates that TSLA and NFLX work identically to GLD/SLV pattern
"""

import sys
import os
import json

# Add backend to path
sys.path.insert(0, '/workspaces/New-test-strategy/backend')

def test_imports():
    """Test 1: Verify all required imports work"""
    print("\n" + "="*80)
    print("TEST 1: Importing stock_statistics module")
    print("="*80)

    try:
        from stock_statistics import (
            BinStatistics,
            SignalStrength,
            StockMetadata,
            STOCK_METADATA,
            get_stock_data
        )
        print("✅ Successfully imported core classes and functions")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_tsla_data_exists():
    """Test 2: Verify TSLA_4H_DATA and TSLA_DAILY_DATA exist"""
    print("\n" + "="*80)
    print("TEST 2: Checking TSLA data structures")
    print("="*80)

    try:
        from stock_statistics import TSLA_4H_DATA, TSLA_DAILY_DATA

        # Check 4H data
        print(f"✅ TSLA_4H_DATA exists with {len(TSLA_4H_DATA)} bins")
        assert len(TSLA_4H_DATA) == 8, f"Expected 8 bins, got {len(TSLA_4H_DATA)}"

        # Check Daily data
        print(f"✅ TSLA_DAILY_DATA exists with {len(TSLA_DAILY_DATA)} bins")
        assert len(TSLA_DAILY_DATA) == 8, f"Expected 8 bins, got {len(TSLA_DAILY_DATA)}"

        return True
    except ImportError as e:
        print(f"❌ TSLA data not found in stock_statistics.py: {e}")
        print("   Run: python backend/generate_tsla_stats.py first")
        return False
    except AssertionError as e:
        print(f"❌ Data structure validation failed: {e}")
        return False


def test_nflx_data_exists():
    """Test 3: Verify NFLX_4H_DATA and NFLX_DAILY_DATA exist"""
    print("\n" + "="*80)
    print("TEST 3: Checking NFLX data structures")
    print("="*80)

    try:
        from stock_statistics import NFLX_4H_DATA, NFLX_DAILY_DATA

        # Check 4H data
        print(f"✅ NFLX_4H_DATA exists with {len(NFLX_4H_DATA)} bins")
        assert len(NFLX_4H_DATA) == 8, f"Expected 8 bins, got {len(NFLX_4H_DATA)}"

        # Check Daily data
        print(f"✅ NFLX_DAILY_DATA exists with {len(NFLX_DAILY_DATA)} bins")
        assert len(NFLX_DAILY_DATA) == 8, f"Expected 8 bins, got {len(NFLX_DAILY_DATA)}"

        return True
    except ImportError as e:
        print(f"❌ NFLX data not found in stock_statistics.py: {e}")
        print("   Run: python backend/generate_nflx_stats.py first")
        return False
    except AssertionError as e:
        print(f"❌ Data structure validation failed: {e}")
        return False


def test_metadata_contains_tsla_nflx():
    """Test 4: Verify TSLA and NFLX are in STOCK_METADATA"""
    print("\n" + "="*80)
    print("TEST 4: Checking STOCK_METADATA for TSLA and NFLX")
    print("="*80)

    try:
        from stock_statistics import STOCK_METADATA

        # Check TSLA
        assert "TSLA" in STOCK_METADATA, "TSLA not found in STOCK_METADATA"
        print(f"✅ TSLA found in STOCK_METADATA")

        # Check NFLX
        assert "NFLX" in STOCK_METADATA, "NFLX not found in STOCK_METADATA"
        print(f"✅ NFLX found in STOCK_METADATA")

        return True
    except AssertionError as e:
        print(f"❌ Metadata validation failed: {e}")
        return False


def test_data_structure_matches_gld_pattern():
    """Test 5: Verify TSLA/NFLX data structure matches GLD/SLV pattern"""
    print("\n" + "="*80)
    print("TEST 5: Validating data structure matches GLD/SLV pattern")
    print("="*80)

    try:
        from stock_statistics import (
            GLD_4H_DATA, TSLA_4H_DATA, NFLX_4H_DATA,
            BinStatistics
        )

        # Expected bins (same as GLD)
        expected_bins = ['0-5', '5-15', '15-25', '25-50', '50-75', '75-85', '85-95', '95-100']

        # Check TSLA
        tsla_bins = list(TSLA_4H_DATA.keys())
        assert tsla_bins == expected_bins, f"TSLA bins mismatch: {tsla_bins}"
        print(f"✅ TSLA has correct bin structure: {tsla_bins}")

        # Check NFLX
        nflx_bins = list(NFLX_4H_DATA.keys())
        assert nflx_bins == expected_bins, f"NFLX bins mismatch: {nflx_bins}"
        print(f"✅ NFLX has correct bin structure: {nflx_bins}")

        # Verify each bin is a BinStatistics object
        for bin_name in expected_bins:
            assert isinstance(TSLA_4H_DATA[bin_name], BinStatistics), \
                f"TSLA {bin_name} is not a BinStatistics object"
            assert isinstance(NFLX_4H_DATA[bin_name], BinStatistics), \
                f"NFLX {bin_name} is not a BinStatistics object"

        print(f"✅ All bins are BinStatistics objects")

        return True
    except Exception as e:
        print(f"❌ Data structure validation failed: {e}")
        return False


def test_required_fields_present():
    """Test 6: Verify all required fields are present in BinStatistics"""
    print("\n" + "="*80)
    print("TEST 6: Validating required fields in BinStatistics")
    print("="*80)

    required_fields = [
        'bin_range', 'mean', 'median', 'std', 'sample_size',
        'se', 't_score', 'percentile_5th', 'percentile_95th',
        'upside', 'downside'
    ]

    try:
        from stock_statistics import TSLA_4H_DATA, NFLX_4H_DATA

        # Check TSLA
        sample_bin = TSLA_4H_DATA['25-50']
        for field in required_fields:
            assert hasattr(sample_bin, field), f"TSLA missing field: {field}"
        print(f"✅ TSLA has all required fields: {required_fields}")

        # Check NFLX
        sample_bin = NFLX_4H_DATA['25-50']
        for field in required_fields:
            assert hasattr(sample_bin, field), f"NFLX missing field: {field}"
        print(f"✅ NFLX has all required fields: {required_fields}")

        return True
    except Exception as e:
        print(f"❌ Field validation failed: {e}")
        return False


def test_get_stock_data_function():
    """Test 7: Verify get_stock_data() works for TSLA and NFLX"""
    print("\n" + "="*80)
    print("TEST 7: Testing get_stock_data() function")
    print("="*80)

    try:
        from stock_statistics import get_stock_data

        # Test TSLA 4H
        tsla_4h = get_stock_data('TSLA', '4H')
        assert len(tsla_4h) == 8, f"TSLA 4H should have 8 bins, got {len(tsla_4h)}"
        print(f"✅ get_stock_data('TSLA', '4H') works - {len(tsla_4h)} bins")

        # Test TSLA Daily
        tsla_daily = get_stock_data('TSLA', 'Daily')
        assert len(tsla_daily) == 8, f"TSLA Daily should have 8 bins, got {len(tsla_daily)}"
        print(f"✅ get_stock_data('TSLA', 'Daily') works - {len(tsla_daily)} bins")

        # Test NFLX 4H
        nflx_4h = get_stock_data('NFLX', '4H')
        assert len(nflx_4h) == 8, f"NFLX 4H should have 8 bins, got {len(nflx_4h)}"
        print(f"✅ get_stock_data('NFLX', '4H') works - {len(nflx_4h)} bins")

        # Test NFLX Daily
        nflx_daily = get_stock_data('NFLX', 'Daily')
        assert len(nflx_daily) == 8, f"NFLX Daily should have 8 bins, got {len(nflx_daily)}"
        print(f"✅ get_stock_data('NFLX', 'Daily') works - {len(nflx_daily)} bins")

        return True
    except Exception as e:
        print(f"❌ get_stock_data() test failed: {e}")
        return False


def test_metadata_structure():
    """Test 8: Verify STOCK_METADATA structure for TSLA and NFLX"""
    print("\n" + "="*80)
    print("TEST 8: Validating STOCK_METADATA structure")
    print("="*80)

    required_metadata_fields = [
        'ticker', 'name', 'personality', 'reliability_4h', 'reliability_daily',
        'tradeable_4h_zones', 'dead_zones_4h', 'best_4h_bin', 'best_4h_t_score',
        'ease_rating', 'is_mean_reverter', 'is_momentum', 'volatility_level',
        'entry_guidance', 'avoid_guidance', 'special_notes'
    ]

    try:
        from stock_statistics import STOCK_METADATA

        # Check TSLA metadata
        tsla_meta = STOCK_METADATA['TSLA']
        for field in required_metadata_fields:
            assert hasattr(tsla_meta, field), f"TSLA metadata missing field: {field}"
        print(f"✅ TSLA metadata has all required fields")
        print(f"   Ticker: {tsla_meta.ticker}")
        print(f"   Name: {tsla_meta.name}")
        print(f"   Personality: {tsla_meta.personality}")
        print(f"   Ease Rating: {tsla_meta.ease_rating}/5")

        # Check NFLX metadata
        nflx_meta = STOCK_METADATA['NFLX']
        for field in required_metadata_fields:
            assert hasattr(nflx_meta, field), f"NFLX metadata missing field: {field}"
        print(f"✅ NFLX metadata has all required fields")
        print(f"   Ticker: {nflx_meta.ticker}")
        print(f"   Name: {nflx_meta.name}")
        print(f"   Personality: {nflx_meta.personality}")
        print(f"   Ease Rating: {nflx_meta.ease_rating}/5")

        return True
    except Exception as e:
        print(f"❌ Metadata structure validation failed: {e}")
        return False


def test_statistical_validity():
    """Test 9: Verify statistical values are valid (not NaN, reasonable ranges)"""
    print("\n" + "="*80)
    print("TEST 9: Validating statistical values")
    print("="*80)

    try:
        from stock_statistics import TSLA_4H_DATA, NFLX_4H_DATA
        import math

        # Check TSLA
        for bin_name, stats in TSLA_4H_DATA.items():
            assert not math.isnan(stats.mean), f"TSLA {bin_name} mean is NaN"
            assert not math.isnan(stats.t_score), f"TSLA {bin_name} t_score is NaN"
            assert stats.sample_size > 0, f"TSLA {bin_name} has zero samples"
        print(f"✅ TSLA statistical values are valid")

        # Check NFLX
        for bin_name, stats in NFLX_4H_DATA.items():
            assert not math.isnan(stats.mean), f"NFLX {bin_name} mean is NaN"
            assert not math.isnan(stats.t_score), f"NFLX {bin_name} t_score is NaN"
            assert stats.sample_size > 0, f"NFLX {bin_name} has zero samples"
        print(f"✅ NFLX statistical values are valid")

        return True
    except Exception as e:
        print(f"❌ Statistical validation failed: {e}")
        return False


def test_display_sample_data():
    """Test 10: Display sample data for visual inspection"""
    print("\n" + "="*80)
    print("TEST 10: Sample data display")
    print("="*80)

    try:
        from stock_statistics import TSLA_4H_DATA, NFLX_4H_DATA, STOCK_METADATA

        # Display TSLA sample
        print(f"\nTSLA 25-50% bin (4H):")
        stats = TSLA_4H_DATA['25-50']
        print(f"  Mean: {stats.mean}%")
        print(f"  T-Score: {stats.t_score}")
        print(f"  Sample Size: {stats.sample_size}")
        print(f"  Std Dev: {stats.std}%")

        # Display NFLX sample
        print(f"\nNFLX 25-50% bin (4H):")
        stats = NFLX_4H_DATA['25-50']
        print(f"  Mean: {stats.mean}%")
        print(f"  T-Score: {stats.t_score}")
        print(f"  Sample Size: {stats.sample_size}")
        print(f"  Std Dev: {stats.std}%")

        # Display metadata
        print(f"\nTSLA Metadata:")
        meta = STOCK_METADATA['TSLA']
        print(f"  Best 4H Bin: {meta.best_4h_bin}")
        print(f"  Best T-Score: {meta.best_4h_t_score}")
        print(f"  Tradeable Zones: {meta.tradeable_4h_zones}")

        print(f"\nNFLX Metadata:")
        meta = STOCK_METADATA['NFLX']
        print(f"  Best 4H Bin: {meta.best_4h_bin}")
        print(f"  Best T-Score: {meta.best_4h_t_score}")
        print(f"  Tradeable Zones: {meta.tradeable_4h_zones}")

        print(f"\n✅ Sample data displayed successfully")
        return True
    except Exception as e:
        print(f"❌ Sample data display failed: {e}")
        return False


def run_all_tests():
    """Run all tests and generate summary report"""
    print("\n" + "="*80)
    print("TSLA/NFLX ANALYTICS INTEGRATION TEST SUITE")
    print("="*80)

    tests = [
        ("Import Test", test_imports),
        ("TSLA Data Exists", test_tsla_data_exists),
        ("NFLX Data Exists", test_nflx_data_exists),
        ("Metadata Contains TSLA/NFLX", test_metadata_contains_tsla_nflx),
        ("Data Structure Matches GLD Pattern", test_data_structure_matches_gld_pattern),
        ("Required Fields Present", test_required_fields_present),
        ("get_stock_data() Function", test_get_stock_data_function),
        ("Metadata Structure", test_metadata_structure),
        ("Statistical Validity", test_statistical_validity),
        ("Sample Data Display", test_display_sample_data),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! TSLA and NFLX integration is complete.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review output above.")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
