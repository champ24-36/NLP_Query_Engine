#!/bin/bash

# Test runner script

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Running NLP Query Engine Tests"
echo "=========================================="

# Parse arguments
TEST_TYPE=${1:-"all"}
COVERAGE=${2:-"yes"}

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

cd backend

# Function to run tests
run_tests() {
    local test_path=$1
    local test_name=$2
    
    echo ""
    echo -e "${YELLOW}Running $test_name...${NC}"
    
    if [ "$COVERAGE" == "yes" ]; then
        pytest "$test_path" -v --cov=. --cov-report=html --cov-report=term-missing
    else
        pytest "$test_path" -v
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $test_name passed${NC}"
    else
        echo -e "${RED}✗ $test_name failed${NC}"
        exit 1
    fi
}

# Run tests based on type
case $TEST_TYPE in
    "unit")
        run_tests "tests/unit/" "Unit Tests"
        ;;
    "integration")
        run_tests "tests/integration/" "Integration Tests"
        ;;
    "performance")
        run_tests "tests/performance/" "Performance Tests"
        ;;
    "all")
        run_tests "tests/unit/" "Unit Tests"
        run_tests "tests/integration/" "Integration Tests"
        echo -e "${YELLOW}Skipping performance tests (run with 'performance' flag)${NC}"
        ;;
    *)
        echo "Usage: ./run_tests.sh [unit|integration|performance|all] [yes|no coverage]"
        exit 1
        ;;
esac

# Show coverage report location
if [ "$COVERAGE" == "yes" ]; then
    echo ""
    echo "=========================================="
    echo -e "${GREEN}Coverage report generated at:${NC}"
    echo "  backend/htmlcov/index.html"
    echo "=========================================="
fi

echo ""
echo -e "${GREEN}All tests completed successfully!${NC}"
