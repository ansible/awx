#!/usr/bin/env bash
#
# 6 curl commands demonstrating each deprecation header scenario.
# Run against a local AWX dev instance.

# Scenario 1: Deprecated endpoint
echo "=== Scenario 1: Deprecated endpoint ==="
curl -sk -u admin:password -D - -o /dev/null https://localhost:8043/api/v2/dashboard/
echo ""

# Scenario 2: Deprecated parameter (user/team fields on credentials endpoint)
echo "=== Scenario 2: Deprecated parameter ==="
curl -sk -u admin:password -D - -o /dev/null https://localhost:8043/api/v2/credentials/
echo ""

# Scenario 3: Deprecated field (credential on inventory_sources)
echo "=== Scenario 3: Deprecated field ==="
curl -sk -u admin:password -D - -o /dev/null https://localhost:8043/api/v2/inventory_sources/
echo ""

# Scenario 4: Deprecated behavior (GET for logout)
echo "=== Scenario 4: Deprecated behavior ==="
curl -sk -u admin:password -D - -o /dev/null https://localhost:8043/api/logout/
echo ""

# Scenario 5: Deprecated API version
echo "=== Scenario 5: Deprecated API version ==="
curl -sk -u admin:password -D - -o /dev/null https://localhost:8043/api/v2/
echo ""

# Scenario 6: Multiple deprecations (endpoint + parameter)
echo "=== Scenario 6: Multiple deprecations ==="
curl -sk -u admin:password -D - -o /dev/null "https://localhost:8043/api/v2/dashboard/?legacy_format=true"
echo ""
