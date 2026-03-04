# VitalHeart Phase 4 - Deployment Verification Script
# Purpose: Verify complete Phase 4 installation and functionality
# Usage: python deploy_verify.py

import sys
import time
import json
from pathlib import Path

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")

def print_status(text, status):
    emoji = "[PASS]" if status else "[FAIL]"
    print(f"{emoji} {text}")
    return status

def verify_dependencies():
    print_header("STEP 1: Verify Dependencies")
    
    results = []
    
    # Python version
    py_version = sys.version_info
    py_ok = py_version >= (3, 8)
    print_status(f"Python {py_version.major}.{py_version.minor}.{py_version.micro} (requires 3.8+)", py_ok)
    results.append(py_ok)
    
    # Required packages
    packages = ["requests", "psutil", "pytest"]
    for pkg in packages:
        try:
            __import__(pkg)
            print_status(f"{pkg} installed", True)
            results.append(True)
        except ImportError:
            print_status(f"{pkg} MISSING", False)
            results.append(False)
    
    # Optional packages
    try:
        import pynvml
        print_status("nvidia-ml-py installed (optional, for GPU metrics)", True)
    except ImportError:
        print_status("nvidia-ml-py not installed (optional, OK)", True)
    
    return all(results)

def verify_files():
    print_header("STEP 2: Verify Files")
    
    required_files = [
        "tokenanalytics.py",
        "test_tokenanalytics.py",
        "requirements.txt",
        "model_profiles.json",
        "README.md",
        "EXAMPLES.md",
        "BUILD_REPORT.md",
    ]
    
    results = []
    for filename in required_files:
        p = Path(filename)
        if p.exists():
            lines = len(p.read_text(encoding='utf-8').splitlines())
            print_status(f"{filename} exists ({lines} lines)", True)
            results.append(True)
        else:
            print_status(f"{filename} MISSING", False)
            results.append(False)
    
    return all(results)

def verify_model_profiles():
    print_header("STEP 3: Verify Model Profiles")
    
    try:
        with open("model_profiles.json", 'r') as f:
            data = json.load(f)
        
        profiles = data.get("model_profiles", {})
        expected_models = ["laia", "llama3", "llama3.1", "mistral", "gemma", "default"]
        
        results = []
        for model in expected_models:
            exists = model in profiles
            print_status(f"Profile for '{model}' exists", exists)
            results.append(exists)
        
        return all(results)
    except Exception as e:
        print_status(f"Failed to load model_profiles.json: {e}", False)
        return False

def verify_ollama():
    print_header("STEP 4: Verify Ollama API")
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print_status(f"Ollama API reachable ({len(models)} models available)", True)
            return True
        else:
            print_status(f"Ollama API returned {response.status_code}", False)
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"Ollama API NOT reachable: {e}", False)
        print("  [WARNING] Install Ollama from https://ollama.ai or start the service")
        return False

def verify_tests():
    print_header("STEP 5: Run Test Suite")
    
    try:
        import pytest
        print("Running 105 tests (this may take 5-10 seconds)...")
        
        start = time.time()
        result = pytest.main([
            "test_tokenanalytics.py",
            "--tb=no",
            "-q",
            "--disable-warnings"
        ])
        duration = time.time() - start
        
        if result == 0:
            print_status(f"All tests passed in {duration:.1f}s", True)
            return True
        else:
            print_status(f"Tests FAILED (exit code {result})", False)
            return False
    except Exception as e:
        print_status(f"Test execution failed: {e}", False)
        return False

def verify_import():
    print_header("STEP 6: Verify Import")
    
    try:
        from tokenanalytics import (
            TokenAnalyticsDaemon,
            TokenAnalyticsConfig,
            ModelProfiler,
            CostTracker,
            StateTransitionDetector
        )
        print_status("All components import successfully", True)
        return True
    except Exception as e:
        print_status(f"Import failed: {e}", False)
        return False

def verify_config():
    print_header("STEP 7: Verify Configuration")
    
    try:
        from tokenanalytics import TokenAnalyticsConfig
        
        config = TokenAnalyticsConfig()
        
        # Simple checks that config loads and key methods work
        print_status("TokenAnalyticsConfig instantiated successfully", True)
        
        # Check get_with_default works
        val = config.get_with_default("token_analytics", "model_profiling_enabled", default=True)
        print_status(f"get_with_default() works (model_profiling={val})", True)
        
        return True
    except Exception as e:
        print_status(f"Config verification failed: {e}", False)
        return False

def verify_database():
    print_header("STEP 8: Verify Database Schema")
    
    try:
        from tokenanalytics import TokenAnalyticsDatabase, TokenAnalyticsConfig
        import sqlite3
        
        config = TokenAnalyticsConfig()
        db = TokenAnalyticsDatabase(config)
        
        # Check tables exist
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            "token_analytics",
            "token_emotion_correlation",
            "token_hardware_correlation",
            "token_baselines",
            "token_costs",
            "generation_states",
            "state_transitions"
        ]
        
        results = []
        for table in expected_tables:
            exists = table in tables
            print_status(f"Table '{table}' exists", exists)
            results.append(exists)
        
        conn.close()
        return all(results)
    except Exception as e:
        print_status(f"Database verification failed: {e}", False)
        return False

def main():
    print("\n" + "="*70)
    print("  VitalHeart Phase 4: Token Analytics")
    print("  DEPLOYMENT VERIFICATION")
    print("  Date: February 14, 2026")
    print("="*70)
    
    results = []
    
    # Run all verification steps
    results.append(("Dependencies", verify_dependencies()))
    results.append(("Files", verify_files()))
    results.append(("Model Profiles", verify_model_profiles()))
    results.append(("Ollama API", verify_ollama()))
    results.append(("Import", verify_import()))
    results.append(("Configuration", verify_config()))
    results.append(("Database Schema", verify_database()))
    results.append(("Test Suite", verify_tests()))
    
    # Final summary
    print_header("DEPLOYMENT VERIFICATION SUMMARY")
    
    all_passed = all(r[1] for r in results)
    
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"[{'PASS' if passed else 'FAIL'}] {name:20} {status}")
    
    print("\n" + "="*70)
    if all_passed:
        print("  [SUCCESS] DEPLOYMENT VERIFICATION SUCCESSFUL")
        print("  Phase 4 is ready for production deployment!")
        print("="*70)
        print("\nNext steps:")
        print("  1. python tokenanalytics.py  # Start daemon")
        print("  2. Monitor logs for 24 hours")
        print("  3. Verify Phase 3 integration (if installed)")
        print("  4. Run production workload test")
        return 0
    else:
        print("  [FAIL] DEPLOYMENT VERIFICATION FAILED")
        print("  Please fix the issues above before deployment.")
        print("="*70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
