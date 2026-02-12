"""
Quick test of OpenClaw AI integration
Tests ollama_client with all safety layers
"""
import sys
sys.path.insert(0, 'C:\\OpenClaw')

from core.ollama_client import ollama_client
from core.schema_validator import schema_validator
from core.risk_classifier import risk_classifier
from core.semantic_guard import semantic_guard

print("=" * 60)
print("OpenClaw Phase 2 Integration Test")
print("=" * 60)

# Test 1: Check Ollama availability
print("\n[1] Checking Ollama availability...")
available = ollama_client.check_availability()
print(f"   Ollama available: {available}")

if not available:
    print("   ❌ Ollama not available. Exiting.")
    sys.exit(1)

# Test 2: Parse simple command
print("\n[2] Testing command parsing...")
user_input = "create a file called test.txt with hello world"
print(f"   Input: '{user_input}'")

try:
    parsed = ollama_client.parse_command(user_input)
    print(f"   ✓ Parsed: {parsed['operation']}({parsed['args']})")
    print(f"   Confidence: {parsed['confidence']:.2f}")
except Exception as e:
    print(f"   ❌ Parse error: {e}")
    sys.exit(1)

# Test 3: Schema validation
print("\n[3] Testing schema validation...")
valid, error = schema_validator.validate(parsed)
if valid:
    print(f"   ✓ Schema valid")
else:
    print(f"   ❌ Schema invalid: {error}")
    sys.exit(1)

# Test 4: Semantic guard
print("\n[4] Testing semantic guard...")
safe, reason = semantic_guard.check_command(parsed, user_input)
if safe:
    print(f"   ✓ Semantically safe")
else:
    print(f"   ❌ Blocked: {reason}")
    sys.exit(1)

# Test 5: Risk classification
print("\n[5] Testing risk classification...")
risk = risk_classifier.classify_operation(parsed['operation'], parsed['args'])
print(f"   Risk level: {risk.name}")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("Phase 2 Week 1 Integration: COMPLETE")
print("=" * 60)
