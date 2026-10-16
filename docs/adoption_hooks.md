# Job Adoption Hooks

## Overview

When a controller fails in a High Availability (HADR) deployment, surviving controllers adopt running jobs to continue execution and recover state. Some job types require post-execution finalization to recover correctly:

- **InventoryUpdate**: Must import discovered inventory/hosts/variables
- **ProjectUpdate**: Must update project cache and `scm_revision`
- **Job**: Must finalize fact cache (if inventory is present)

Adoption hooks automatically invoke type-specific post-run logic to ensure these jobs recover fully, including data recovery that would normally be lost on controller failure.

## How It Works

### Hook Invocation

When adoption completes and a job reaches a terminal status:

1. **Condition Check**: Determine if this job type needs a hook
   - `InventoryUpdate` and `ProjectUpdate`: Always (on successful status)
   - `Job`: Only if it has an inventory (for fact cache)
   
2. **Artifact Validation**: Verify required files exist
   - `InventoryUpdate`: Requires `output.json` with discovered inventory
   - `ProjectUpdate` / `Job`: No strict requirements

3. **Hook Execution**: Run the job type's post-run hook
   - Instantiate the task class (e.g., `RunInventoryUpdate`)
   - Override `AWX_PRIVATE_DATA_DIR` to use adoption's directory (not lost controller's)
   - Call the hook to finalize state

4. **Error Handling**: If hook fails
   - Job is marked as failed with detailed error message
   - Error explanation is logged to job_explanation
   - Full traceback is available in result_traceback

### Example: InventoryUpdate Recovery

When an InventoryUpdate is adopted:

```
Lost Controller (CTRL0): Running InventoryUpdate Job 42
↓
CTRL0 crashes, work unit streams to surviving CTRL1
↓
CTRL1 adoption: Reattaches to Job 42's work unit
↓
Job 42 execution completes (status=successful)
↓
Adoption Hook Triggers:
  - Validates output.json exists in adoption directory
  - Runs RunInventoryUpdate.post_run_hook('successful')
  - Imports discovered inventory/hosts/groups
  - Updates InventorySource.last_job_run
↓
Job 42 marked as successful with full inventory recovered
```

Without adoption hooks, the discovered inventory would be lost because the import happens in post-run.

## Configuration

Adoption hooks are enabled by default and require no configuration. They run automatically during adoption finalization.

### Emergency Disable

If hook execution causes adoption failures in production, hooks can be disabled by setting:

```python
# In settings.py or via environment variable
HADR_ADOPTION_ENABLE_HOOKS = False
```

**Note**: Disabling hooks causes InventoryUpdate and ProjectUpdate adoptions to lose data. Only disable temporarily while investigating issues.

## Troubleshooting

### Hook Execution Failures

If a job fails during adoption with a message like "adoption hook failed", check:

1. **Artifact Validation Failures**
   - Error: `InventoryUpdate output.json not found`
   - Cause: Execution environment did not produce output (job crash, disk space)
   - Solution: Check execution environment logs, verify disk space on adoption controller

2. **Import Constraint Violations** (InventoryUpdate)
   - Error: `Inventory host uniqueness constraint failed`
   - Cause: Discovered hosts conflict with existing inventory
   - Solution: Check for duplicate host names in discovered inventory and existing hosts

3. **Project Cache Write Failures** (ProjectUpdate)
   - Error: `Failed to write project cache`
   - Cause: Permissions issue or disk full on adoption controller
   - Solution: Verify adoption directory permissions, check disk space

### Debug Output

Hook execution details are logged with timing information:

```
Job 42 (type=InventoryUpdate): invoking RunInventoryUpdate.post_run_hook() during adoption (status=successful)
Job 42: adoption hook succeeded in 1.23s
```

Check logs for these messages to confirm hook execution. Failures include:

```
Job 42: adoption hook raised unexpected exception after 0.45s
```

### Live Cluster Validation

To verify adoption hooks work correctly:

1. Create an InventoryUpdate job on a controller
2. Force the controller to crash/disconnect
3. Verify surviving controller adopts the job and completes hook
4. Check that discovered inventory is imported correctly

## Design Notes

### Why Hooks in Adoption?

Normal job execution already invokes post-run hooks. Adoption must replicate this behavior because:

- Post-run hooks make persistent state changes (database inserts, file writes)
- These are REQUIRED for correct job recovery, not optional cleanup
- Without hooks, InventoryUpdate adoption silently loses discovered data

### No Separate Registry

Adoption reuses AWX's existing `job._get_task_class()` method instead of building a separate hook registry. This:

- Leverages existing job-to-task mapping
- Automatically works for new job types without code changes
- Reduces maintenance surface area

### Job Environment Override

During hook execution, `job.job_env['AWX_PRIVATE_DATA_DIR']` is temporarily set to adoption's directory. This is critical because:

- Normal job env points to lost controller's directory (may not exist)
- Adoption needs hooks to use adoption's directory for artifact access
- Original env is restored after hook for debugging/logging

### Error Handling Strategy

- **PostRunError**: Structured exceptions from hooks (e.g., constraint violations)
- **Generic Exception**: All other failures, logged with full traceback
- **Never Silent**: Job is always marked failed if hook fails (no surprise failures)

## Related Documentation

- [High Availability (HADR) Overview](clustering.md)
- [Job Execution and Streaming](job_execution.md)
- [Fact Caching](fact_cache.md)
