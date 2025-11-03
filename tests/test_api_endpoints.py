#!/usr/bin/env python3
"""
API endpoint tests for TSLA and NFLX
Tests that the Flask backend properly serves statistics
"""

import sys
import requests
import json

def test_api_available():
    """Test that the API server is running"""
    print("\n" + "="*80)
    print("API ENDPOINT TEST - Server Availability")
    print("="*80)

    try:
        # Try to connect to the API
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print("✅ API server is running at http://localhost:8000")
            return True
        else:
            print(f"⚠️  API server returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API server is not running")
        print("   Start it with: cd backend && python app.py")
        return False
    except requests.exceptions.Timeout:
        print("❌ API server timeout")
        return False


def test_tsla_endpoint():
    """Test GET /api/stocks/TSLA/statistics"""
    print("\n" + "="*80)
    print("API ENDPOINT TEST - TSLA Statistics")
    print("="*80)

    try:
        response = requests.get('http://localhost:8000/api/stocks/TSLA/statistics', timeout=5)

        if response.status_code == 200:
            data = response.json()

            # Validate response structure
            assert 'ticker' in data, "Missing 'ticker' field"
            assert data['ticker'] == 'TSLA', f"Expected ticker 'TSLA', got {data['ticker']}"
            assert 'timeframes' in data, "Missing 'timeframes' field"
            assert '4H' in data['timeframes'], "Missing '4H' timeframe"
            assert 'Daily' in data['timeframes'], "Missing 'Daily' timeframe"

            # Check 4H data
            bins_4h = data['timeframes']['4H']
            assert len(bins_4h) == 8, f"Expected 8 bins in 4H, got {len(bins_4h)}"

            # Check Daily data
            bins_daily = data['timeframes']['Daily']
            assert len(bins_daily) == 8, f"Expected 8 bins in Daily, got {len(bins_daily)}"

            print(f"✅ TSLA endpoint working correctly")
            print(f"   Ticker: {data['ticker']}")
            print(f"   4H bins: {len(bins_4h)}")
            print(f"   Daily bins: {len(bins_daily)}")

            # Display sample data
            sample_bin = bins_4h.get('25-50', {})
            if sample_bin:
                print(f"\n   Sample 4H data (25-50% bin):")
                print(f"     Mean: {sample_bin.get('mean')}%")
                print(f"     T-Score: {sample_bin.get('t_score')}")
                print(f"     Sample Size: {sample_bin.get('sample_size')}")

            return True
        else:
            print(f"❌ TSLA endpoint returned status {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        return False
    except json.JSONDecodeError:
        print("❌ Invalid JSON response")
        return False
    except AssertionError as e:
        print(f"❌ Response validation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_nflx_endpoint():
    """Test GET /api/stocks/NFLX/statistics"""
    print("\n" + "="*80)
    print("API ENDPOINT TEST - NFLX Statistics")
    print("="*80)

    try:
        response = requests.get('http://localhost:8000/api/stocks/NFLX/statistics', timeout=5)

        if response.status_code == 200:
            data = response.json()

            # Validate response structure
            assert 'ticker' in data, "Missing 'ticker' field"
            assert data['ticker'] == 'NFLX', f"Expected ticker 'NFLX', got {data['ticker']}"
            assert 'timeframes' in data, "Missing 'timeframes' field"
            assert '4H' in data['timeframes'], "Missing '4H' timeframe"
            assert 'Daily' in data['timeframes'], "Missing 'Daily' timeframe"

            # Check 4H data
            bins_4h = data['timeframes']['4H']
            assert len(bins_4h) == 8, f"Expected 8 bins in 4H, got {len(bins_4h)}"

            # Check Daily data
            bins_daily = data['timeframes']['Daily']
            assert len(bins_daily) == 8, f"Expected 8 bins in Daily, got {len(bins_daily)}"

            print(f"✅ NFLX endpoint working correctly")
            print(f"   Ticker: {data['ticker']}")
            print(f"   4H bins: {len(bins_4h)}")
            print(f"   Daily bins: {len(bins_daily)}")

            # Display sample data
            sample_bin = bins_4h.get('25-50', {})
            if sample_bin:
                print(f"\n   Sample 4H data (25-50% bin):")
                print(f"     Mean: {sample_bin.get('mean')}%")
                print(f"     T-Score: {sample_bin.get('t_score')}")
                print(f"     Sample Size: {sample_bin.get('sample_size')}")

            return True
        else:
            print(f"❌ NFLX endpoint returned status {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        return False
    except json.JSONDecodeError:
        print("❌ Invalid JSON response")
        return False
    except AssertionError as e:
        print(f"❌ Response validation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_compare_gld_tsla_structure():
    """Compare GLD and TSLA response structures to ensure consistency"""
    print("\n" + "="*80)
    print("API ENDPOINT TEST - Structure Comparison (GLD vs TSLA)")
    print("="*80)

    try:
        # Get GLD data
        gld_response = requests.get('http://localhost:8000/api/stocks/GLD/statistics', timeout=5)
        tsla_response = requests.get('http://localhost:8000/api/stocks/TSLA/statistics', timeout=5)

        if gld_response.status_code == 200 and tsla_response.status_code == 200:
            gld_data = gld_response.json()
            tsla_data = tsla_response.json()

            # Compare top-level keys
            gld_keys = set(gld_data.keys())
            tsla_keys = set(tsla_data.keys())
            assert gld_keys == tsla_keys, f"Top-level keys mismatch: GLD={gld_keys}, TSLA={tsla_keys}"
            print(f"✅ Top-level structure matches")

            # Compare timeframe keys
            gld_tf_keys = set(gld_data['timeframes'].keys())
            tsla_tf_keys = set(tsla_data['timeframes'].keys())
            assert gld_tf_keys == tsla_tf_keys, f"Timeframe keys mismatch"
            print(f"✅ Timeframe structure matches")

            # Compare bin keys
            gld_bins = set(gld_data['timeframes']['4H'].keys())
            tsla_bins = set(tsla_data['timeframes']['4H'].keys())
            assert gld_bins == tsla_bins, f"Bin keys mismatch"
            print(f"✅ Bin structure matches: {sorted(gld_bins)}")

            # Compare bin data structure
            gld_sample = gld_data['timeframes']['4H']['25-50']
            tsla_sample = tsla_data['timeframes']['4H']['25-50']
            gld_sample_keys = set(gld_sample.keys())
            tsla_sample_keys = set(tsla_sample.keys())
            assert gld_sample_keys == tsla_sample_keys, f"Bin data keys mismatch"
            print(f"✅ Bin data structure matches: {sorted(gld_sample_keys)}")

            return True
        else:
            print(f"❌ Failed to fetch comparison data")
            return False

    except Exception as e:
        print(f"❌ Comparison test failed: {e}")
        return False


def run_all_api_tests():
    """Run all API endpoint tests"""
    print("\n" + "="*80)
    print("API ENDPOINT TEST SUITE - TSLA/NFLX")
    print("="*80)

    tests = [
        ("Server Availability", test_api_available),
        ("TSLA Endpoint", test_tsla_endpoint),
        ("NFLX Endpoint", test_nflx_endpoint),
        ("Structure Comparison", test_compare_gld_tsla_structure),
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
    print("API TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 ALL API TESTS PASSED!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        if not results[0][1]:  # Server availability failed
            print("\nℹ️  Note: Make sure the API server is running:")
            print("   cd backend && python app.py")
        return False


if __name__ == '__main__':
    success = run_all_api_tests()
    sys.exit(0 if success else 1)
