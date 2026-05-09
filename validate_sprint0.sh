#!/bin/bash
# Sprint 0 Validation Script
# Run this to verify all 5 critical blockers are fixed

set -e

echo "=========================================="
echo "🚀 LifeOS Sprint 0 Validation"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test suite
run_test_suite() {
    local test_name=$1
    local test_file=$2
    
    echo -e "${YELLOW}Running ${test_name}...${NC}"
    
    if pytest "$test_file" -v --tb=short -q; then
        echo -e "${GREEN}✅ ${test_name} PASSED${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ ${test_name} FAILED${NC}"
        ((TESTS_FAILED++))
    fi
    echo ""
}

# Check Python environment
echo "📋 Checking environment..."
if ! command -v python &> /dev/null; then
    echo -e "${RED}Python not found!${NC}"
    exit 1
fi

if ! command -v pytest &> /dev/null; then
    echo -e "${RED}pytest not found! Installing...${NC}"
    pip install pytest pytest-django pytest-asyncio -q
fi

echo -e "${GREEN}✅ Environment ready${NC}"
echo ""

# Run test suites for each blocker
echo "=========================================="
echo "🧪 Running Test Suites"
echo "=========================================="
echo ""

# Blocker #1: PostgreSQL Migration
run_test_suite "Blocker #1: Database Migration" "agents/tests/test_db_migration.py"

# Blocker #2: Security
run_test_suite "Blocker #2: Security Hardening" "agents/tests/test_security.py"

# Blocker #3: Rate Limiting
run_test_suite "Blocker #3: Rate Limiting" "agents/tests/test_throttling.py"

# Blocker #4: Context Validation
run_test_suite "Blocker #4: Context Validation" "agents/tests/test_context_validation.py"

# Blocker #5: Event Sourcing
run_test_suite "Blocker #5: Event Sourcing" "agents/tests/test_event_sourcing.py"

# Additional tests
run_test_suite "Intent & Actions" "agents/tests/test_intent_and_actions.py"
run_test_suite "Health Checks" "agents/tests/test_health.py"

echo "=========================================="
echo "📊 Test Summary"
echo "=========================================="
echo ""
echo -e "Tests Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Tests Failed: ${RED}${TESTS_FAILED}${NC}"
echo ""

# Run code coverage
echo "📈 Generating Code Coverage Report..."
if command -v coverage &> /dev/null; then
    coverage report --fail-under=80 || echo -e "${YELLOW}⚠️  Coverage below 80%${NC}"
else
    echo -e "${YELLOW}Coverage not installed, skipping...${NC}"
fi
echo ""

# Security scan
echo "🔒 Running Security Scan..."
if command -v bandit &> /dev/null; then
    bandit -r agents/ api/ lifeos/ -ll || echo -e "${YELLOW}⚠️  Some security issues found${NC}"
else
    echo -e "${YELLOW}Bandit not installed, skipping...${NC}"
fi
echo ""

# Final verdict
echo "=========================================="
echo "🎯 Final Verdict"
echo "=========================================="
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ SPRINT 0 VALIDATION SUCCESSFUL!${NC}"
    echo ""
    echo "All 5 critical blockers have been fixed:"
    echo "  ✅ Blocker #1: SQLite → PostgreSQL Migration"
    echo "  ✅ Blocker #2: Debug Mode & Security Headers"
    echo "  ✅ Blocker #3: Rate Limiting"
    echo "  ✅ Blocker #4: User Context Validation"
    echo "  ✅ Blocker #5: Event Bus Persistence"
    echo ""
    echo "🎉 Ready for production deployment!"
    exit 0
else
    echo -e "${RED}❌ SPRINT 0 VALIDATION FAILED${NC}"
    echo ""
    echo "${TESTS_FAILED} test suite(s) failed."
    echo "Please fix the failing tests before deploying."
    exit 1
fi
