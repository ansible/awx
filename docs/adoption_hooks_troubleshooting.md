# Adoption Hooks Troubleshooting Guide

## Quick Diagnostics

When adoption hook execution fails, use this flowchart:

```
Job adopted and marked FAILED during hook execution
├─ Check job_explanation field
│  └─ "output.json not found" → [ARTIFACT MISSING]
│  └─ "constraint violation" → [CONSTRAINT ERROR]
│  └─ "Permission denied" → [PERMISSION ERROR]
│  └─ "post_run_hook failed" → [HOOK ERROR]
│
├─ Check result_traceback field (full Python traceback)
│  └─ Trace to understand exception origin
│
└─ Check adoption controller logs (AWX logs, receptor logs)
   └─ Search for "Job {id}: adoption hook" messages
```

## Common Issues & Solutions

### 1. Artifact Missing (InventoryUpdate)

**Error Message:**
```
InventoryUpdate 42: output.json not found at /var/lib/awx/projects/42/artifacts/output.json
```

**Root Causes:**
- Execution environment crashed before producing output.json
- Disk full on execution environment, incomplete output
- File permissions issue on adoption controller preventing read

**Solutions:**

Check execution environment logs:
```bash
# On EE that was running the job
podman logs <container_id> | grep -i "error\|fail"
journalctl -u podman | grep error
```

Verify adoption directory permissions:
```bash
ls -la /var/lib/awx/projects/42/artifacts/
chmod 755 /var/lib/awx/projects/42/artifacts/
```

Check disk space:
```bash
df -h /var/lib/awx
# If >90% used, clean up old job artifacts
find /var/lib/awx/projects -mtime +30 -delete
```

**Workaround**: If output.json is corrupted but job completed successfully, manually re-run the InventoryUpdate on the adoption controller.

### 2. Inventory Constraint Violations

**Error Message:**
```
InventoryUpdate 42: constraint violation on host 'ansible.example.com': 
Unique constraint failed on (inventory_id, name)
```

**Root Causes:**
- Discovered hosts already exist in the inventory
- Duplicate hosts in the discovered inventory itself
- Host created manually between job start and adoption

**Solutions:**

List existing hosts in inventory:
```bash
# Via API
curl -s -u admin:password http://localhost/api/v2/inventories/3/hosts/ | jq '.results | map(.name)'

# Via Django shell
python manage.py shell
>>> from awx.main.models import Inventory
>>> inv = Inventory.objects.get(id=3)
>>> list(inv.hosts.values_list('name', flat=True))
```

Check discovered hosts in output.json:
```bash
cat /var/lib/awx/projects/42/artifacts/output.json | jq '.all.hosts | keys'
```

**Solutions:**

Option A: Delete conflicting hosts before re-running
```bash
# Via API (get host ID first)
curl -X DELETE -u admin:password http://localhost/api/v2/hosts/{host_id}/
```

Option B: Re-run InventoryUpdate after removing existing hosts
```bash
# Via API
curl -X POST -u admin:password http://localhost/api/v2/inventory_sources/5/update/
```

Option C: Merge inventories if discovery is intentionally overlapping
- Document the merged hosts as expected behavior
- Update inventory management scripts to deduplicate

### 3. Project Cache Write Failures

**Error Message:**
```
ProjectUpdate 42: failed to write project cache: Permission denied
```

**Root Causes:**
- Project directory not writable by AWX user
- Disk full on adoption controller
- Project directory deleted between job start and adoption

**Solutions:**

Check project directory:
```bash
ls -la /var/lib/awx/projects/my_project/
```

Fix permissions (AWX runs as `awx` user):
```bash
chown -R awx:awx /var/lib/awx/projects/my_project
chmod 755 /var/lib/awx/projects/my_project
```

Verify disk space:
```bash
df -h /var/lib/awx
```

**Workaround**: If permissions can't be fixed immediately, disable adoption hooks temporarily:

```python
# In settings.py
HADR_ADOPTION_ENABLE_HOOKS = False
```

Then manually re-run ProjectUpdate after fixing permissions.

### 4. Generic Hook Exceptions

**Error Message:**
```
adoption hook raised unexpected exception after 0.34s
Adoption hook failed: AttributeError: 'RunJob' object has no attribute 'post_run_hook'
```

**Root Cause**: This indicates a code defect in the hook implementation.

**Solution**: This should not happen in production. If it does:

1. Report with job ID and full traceback
2. Check AWX version (adoption hooks added in version X.X)
3. Disable hooks temporarily while investigating:
   ```python
   HADR_ADOPTION_ENABLE_HOOKS = False
   ```

## Debugging Steps

### Enable Debug Logging

Set in Django settings:
```python
LOGGING = {
    'loggers': {
        'awx.main.tasks.adoption': {
            'level': 'DEBUG',
        },
    },
}
```

Or at runtime:
```bash
# In Django shell
import logging
logging.getLogger('awx.main.tasks.adoption').setLevel(logging.DEBUG)
```

### Inspect Adoption State

Via Django shell:
```python
from awx.main.models import Job
from awx.main.models.jobs import Job as JobModel
from awx.main.models.projects import ProjectUpdate
from awx.main.models.inventory import InventoryUpdate

# Find the failed adopted job
job = Job.objects.get(id=42)

# Check adoption-related fields
print(f"Status: {job.status}")
print(f"Job Explanation: {job.job_explanation}")
print(f"Result Traceback: {job.result_traceback[:500]}")
print(f"Job Env: {job.job_env}")
```

### Simulate Hook Execution Locally

```python
from awx.main.tasks.adoption import invoke_adoption_hooks

job = Job.objects.get(id=42)
callback = None  # In real adoption this is the runner callback
private_data_dir = '/var/lib/awx/projects'

success, error = invoke_adoption_hooks(job, callback, private_data_dir, 'successful')
print(f"Hook success: {success}")
if not success:
    print(f"Error: {error}")
```

## Monitoring & Alerting

### Log-based Monitoring

Watch for adoption hook messages:
```bash
# On AWX controller
tail -f /var/log/supervisor/awx-service.log | grep "adoption hook"
```

Alert on failures:
```bash
# Using grep to detect hook failures
tail -f /var/log/supervisor/awx-service.log | grep "adoption hook.*failed"
```

### Metrics to Track

Key indicators of adoption hook health:

1. **Hook execution count** (should increase after controller failover)
2. **Hook failure rate** (should be near 0%)
3. **Hook execution time** (usually <5s, >30s indicates issue)
4. **Job failures during adoption** (should match only actual failures)

### Example Monitoring Query

In Prometheus/Grafana (if AWX exports metrics):
```
rate(awx_adoption_hooks_total[5m]) > 0
awx_adoption_hook_failures_total
histogram_quantile(0.95, awx_adoption_hook_duration_seconds)
```

## Recovery Procedures

### Full Adoption Rollback

If adoption hook failures are widespread:

1. Disable hooks:
   ```python
   HADR_ADOPTION_ENABLE_HOOKS = False
   ```

2. Clear stuck adoption units (via receptor):
   ```bash
   receptor --socket /path/to/control.sock \
     -c 'sendwithresponse get_work_results("")'
   ```

3. Restart adoption service:
   ```bash
   systemctl restart awx-adoption
   ```

4. Re-enable hooks after root cause is fixed:
   ```python
   HADR_ADOPTION_ENABLE_HOOKS = True
   ```

### Manual Hook Recovery

For single job failures:

```python
from awx.main.tasks.adoption import invoke_adoption_hooks
from awx.main.models.jobs import Job

job = Job.objects.get(id=42)

# Retry the hook manually
success, error = invoke_adoption_hooks(
    job, 
    callback=None,
    private_data_dir='/var/lib/awx/projects',
    status='successful'
)

if success:
    # Mark job as successful if hook succeeds
    job.status = 'successful'
    job.save()
    print(f"Job {job.id} recovered successfully")
else:
    # Log error for investigation
    job.job_explanation = error['explanation']
    job.result_traceback = error['traceback']
    job.save()
    print(f"Job {job.id} recovery failed: {error['explanation']}")
```

## Contact & Support

If adoption hook issues persist after troubleshooting:

1. Check [Adoption Hooks Documentation](adoption_hooks.md)
2. Enable debug logging and collect logs
3. Document:
   - Job type and ID
   - Error message and traceback
   - Adoption controller and lost controller hostnames
   - AWX version and HADR cluster configuration
4. File issue with AWX support or development team
