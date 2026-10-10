#!/usr/bin/env bash
#
# Test all 6 deprecation header scenarios against a running AWX instance.
#
# Usage:
#   TOKEN=your_token bash scripts/test-deprecation-headers.sh
#   AUTH=admin:password bash scripts/test-deprecation-headers.sh
#
# Environment variables:
#   BASE_URL  - AWX base URL (default: https://localhost:8043)
#   TOKEN     - OAuth2 token for authentication
#   AUTH      - Basic auth credentials (user:pass), used if TOKEN is not set
#   INSECURE  - Set to "1" to skip TLS verification (default: 1)

set -euo pipefail

BASE_URL="${BASE_URL:-https://localhost:8043}"
INSECURE="${INSECURE:-1}"

CURL_OPTS=(-s -o /dev/null -D -)
if [[ "$INSECURE" == "1" ]]; then
    CURL_OPTS+=(-k)
fi

if [[ -n "${TOKEN:-}" ]]; then
    AUTH_OPTS=(-H "Authorization: Bearer ${TOKEN}")
elif [[ -n "${AUTH:-}" ]]; then
    AUTH_OPTS=(-u "${AUTH}")
else
    echo "ERROR: Set TOKEN or AUTH environment variable"
    exit 1
fi

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
            "${AUTH_OPTS[@]}" \
            -H "Content-Type: application/json" \
            -d "$body" \
            "${BASE_URL}${url}")
    else
        headers=$(curl "${CURL_OPTS[@]}" -X GET \
            "${AUTH_OPTS[@]}" \
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

# Scenario 2: Deprecated parameter (user/team fields on credentials endpoint)
# Now emits on every response, including GET
run_test 2 "Deprecated parameter (user/team fields)" \
    GET "/api/v2/credentials/" "" \
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

# Scenario 6: Multiple deprecations on one endpoint (endpoint + parameter in same detail)
run_test 6 "Multiple deprecations (endpoint + parameter)" \
    GET "/api/v2/dashboard/?legacy_format=true" "" \
    "X-Deprecated=true" \
    "X-Deprecated-Detail=legacy_format" \
    "Link=rel=\"deprecation\"" \
    "Warning=299"

echo ""
echo "=============================================="
echo "  RESULTS: ${PASS}/${TOTAL} passed, ${FAIL} failed"
echo "=============================================="

if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
