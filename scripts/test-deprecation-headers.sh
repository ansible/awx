#!/usr/bin/env bash
#
# Test all 6 deprecation header scenarios against a running AWX instance.
#
# Usage:
#   BASE_URL=https://localhost TOKEN=your_token bash scripts/test-deprecation-headers.sh
#
# Environment variables:
#   BASE_URL  - AWX base URL (default: https://localhost)
#   TOKEN     - OAuth2 token for authentication (required)
#   INSECURE  - Set to "1" to skip TLS verification (default: 1)

set -euo pipefail

BASE_URL="${BASE_URL:-https://localhost}"
TOKEN="${TOKEN:?ERROR: TOKEN environment variable is required}"
INSECURE="${INSECURE:-1}"

CURL_OPTS=(-s -o /dev/null -D -)
if [[ "$INSECURE" == "1" ]]; then
    CURL_OPTS+=(-k)
fi
AUTH_HEADER="Authorization: Bearer ${TOKEN}"

PASS=0
FAIL=0
TOTAL=0

check_header() {
    local headers="$1"
    local header_name="$2"
    local expected_value="$3"

    local actual
    actual=$(echo "$headers" | grep -i "^${header_name}:" | sed "s/^${header_name}: *//i" | tr -d '\r')

    if [[ -z "$actual" ]]; then
        echo "    MISSING: ${header_name}"
        return 1
    fi

    if [[ -n "$expected_value" ]]; then
        if echo "$actual" | grep -qi "$expected_value"; then
            echo "    OK: ${header_name}: ${actual}"
            return 0
        else
            echo "    MISMATCH: ${header_name}: ${actual} (expected to contain: ${expected_value})"
            return 1
        fi
    else
        echo "    OK: ${header_name}: ${actual}"
        return 0
    fi
}

run_test() {
    local scenario="$1"
    local description="$2"
    local method="$3"
    local url="$4"
    local body="${5:-}"
    shift 5
    local -a expected_headers=("$@")

    TOTAL=$((TOTAL + 1))
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "SCENARIO ${scenario}: ${description}"
    echo "  ${method} ${url}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    local headers
    if [[ "$method" == "POST" && -n "$body" ]]; then
        headers=$(curl "${CURL_OPTS[@]}" -X POST \
            -H "$AUTH_HEADER" \
            -H "Content-Type: application/json" \
            -d "$body" \
            "${BASE_URL}${url}")
    else
        headers=$(curl "${CURL_OPTS[@]}" -X GET \
            -H "$AUTH_HEADER" \
            "${BASE_URL}${url}")
    fi

    local test_passed=true
    for expected in "${expected_headers[@]}"; do
        local header_name="${expected%%=*}"
        local header_value="${expected#*=}"
        if ! check_header "$headers" "$header_name" "$header_value"; then
            test_passed=false
        fi
    done

    if $test_passed; then
        echo "  => PASS"
        PASS=$((PASS + 1))
    else
        echo "  => FAIL"
        FAIL=$((FAIL + 1))
    fi
}

echo "=============================================="
echo "  DEPRECATION HEADERS - INTEGRATION TEST"
echo "=============================================="
echo "  Target: ${BASE_URL}"
echo "  TLS verification: $([ "$INSECURE" == "1" ] && echo "disabled" || echo "enabled")"
echo ""

# Scenario 1: Deprecated endpoint
run_test 1 "Deprecated endpoint" \
    GET "/api/v2/dashboard/" "" \
    "X-Deprecated=true" \
    "X-Deprecated-Detail=dashboard" \
    "Link=rel=\"deprecation\"" \
    "Warning=299"

# Scenario 2: Deprecated parameter (user/team fields on credential create)
# NOTE: This POST will likely fail (400/403) because it's incomplete,
# but we only care about the deprecation headers on the response.
run_test 2 "Deprecated parameter (user/team fields)" \
    POST "/api/v2/credentials/" \
    '{"name":"dep-test","credential_type":1,"user":1}' \
    "X-Deprecated=true" \
    "X-Deprecated-Detail=user"

# Scenario 3: Deprecated field (credential on inventory_sources)
run_test 3 "Deprecated field (credential on inventory_sources)" \
    GET "/api/v2/inventory_sources/" "" \
    "X-Deprecated=true" \
    "X-Deprecated-Detail=credential"

# Scenario 4: Deprecated behavior (GET logout)
run_test 4 "Deprecated behavior (GET for logout)" \
    GET "/api/logout/" "" \
    "X-Deprecated=true" \
    "X-Deprecated-Detail=GET method"

# Scenario 5: Deprecated API version
run_test 5 "Deprecated API version (v2)" \
    GET "/api/v2/" "" \
    "X-Deprecated=true" \
    "X-Deprecated-Detail=v2" \
    "Link=rel=\"deprecation\""

# Scenario 6: Multiple deprecations on one endpoint
run_test 6 "Multiple deprecations (endpoint + parameter)" \
    GET "/api/v2/dashboard/?legacy_format=true" "" \
    "X-Deprecated=true" \
    "X-Deprecated-Detail=legacy_format" \
    "Warning=299"

echo ""
echo "=============================================="
echo "  RESULTS: ${PASS}/${TOTAL} passed, ${FAIL} failed"
echo "=============================================="

if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
