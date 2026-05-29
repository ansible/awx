# Notifications Integration: Surface Area Analysis

## Summary

The notifications system allows AWX to emit alerts to external services when jobs start, succeed, fail, or when workflow approvals change state. It is composed of models, backends, API views, RBAC, Celery tasks, and client libraries.

---

## 1. Models (`awx/main/models/notifications.py`)

### `NotificationTemplate`
- Belongs to an `Organization` (unique on `(organization, name)`)
- Fields: `notification_type`, `notification_configuration` (JSONField, password subfields encrypted), `messages` (JSONField with per-event templates)
- Supported types: `awssns`, `email`, `slack`, `twilio`, `pagerduty`, `grafana`, `webhook`, `mattermost`, `rocketchat`, `irc`
- Methods:
  - `send(subject, body)` — decrypts secrets, instantiates the backend, sends via Django's email message abstraction
  - `generate_notification(msg, body)` — creates a `Notification` record
  - `display_notification_configuration()` — masks `$encrypted$` fields for API output
  - `save()` — handles merging old messages and encrypting password subfields

### `Notification`
- Represents a single dispatch event (not the template)
- Fields: `notification_template` (FK), `status` (pending/successful/failed), `error`, `notifications_sent`, `notification_type`, `recipients`, `subject`, `body`

### `JobNotificationMixin`
- Mixed into every `UnifiedJob` subclass that emits notifications
- `STATUS_TO_TEMPLATE_TYPE` maps running/succeeded/failed → started/success/error
- `JOB_FIELDS_ALLOWED_LIST` — explicit allowlist of job fields safe for Jinja2 template rendering
- `context(serialized_job)` — builds the Jinja2 render context
- `context_stub()` — static stub context for message validation
- `build_notification_message(nt, status)` — renders message + body via `jinja2.sandbox.ImmutableSandboxedEnvironment`
- `send_notification_templates(status)` — iterates applicable templates, generates `Notification` records, queues `send_notifications` task via `connection.on_commit`

### `NotificationFieldsModel` (`awx/main/models/base.py:391`)
- Base mixin applied to `UnifiedJobTemplate` and `Organization`
- Adds M2M fields: `notification_templates_error`, `notification_templates_success`, `notification_templates_started`
- `Organization` additionally has `notification_templates_approvals`

---

## 2. Notification Backends (`awx/main/notifications/`)

All backends extend both `AWXBaseEmailBackend` (Django's `BaseEmailBackend`) and `CustomNotificationBase`.

| Backend | File | Key dependency |
|---|---|---|
| AWS SNS | `awssns_backend.py` | boto3 |
| Email | `email_backend.py` | Django SMTP |
| Slack | `slack_backend.py` | slack_sdk |
| Twilio | `twilio_backend.py` | twilio |
| PagerDuty | `pagerduty_backend.py` | requests |
| Grafana | `grafana_backend.py` | requests |
| Webhook | `webhook_backend.py` | requests |
| Mattermost | `mattermost_backend.py` | requests |
| Rocket.Chat | `rocketchat_backend.py` | requests |
| IRC | `irc_backend.py` | socket |

Each backend declares:
- `init_parameters` — typed field schema (string/int/bool/list/password/object)
- `recipient_parameter` — which config key holds destination addresses
- `sender_parameter` — which config key holds sender identity (or None)
- `send_messages(messages)` — implements actual dispatch

`CustomNotificationBase` (`custom_notification_base.py`) provides default Jinja2 message templates for all event types and `job_metadata_messages` variants (used by webhook/grafana for JSON body format).

---

## 3. API Layer

### URLs

**Notification Templates** (`awx/api/urls/notification_template.py`):
- `GET/POST /api/v2/notification_templates/` — list/create
- `GET/PUT/PATCH/DELETE /api/v2/notification_templates/<pk>/` — detail
- `POST /api/v2/notification_templates/<pk>/test/` — send a test notification
- `GET /api/v2/notification_templates/<pk>/notifications/` — list dispatched notifications
- `POST /api/v2/notification_templates/<pk>/copy/` — copy template

**Notifications** (`awx/api/urls/notification.py`):
- `GET /api/v2/notifications/` — list
- `GET /api/v2/notifications/<pk>/` — detail

### Per-resource Notification Template Sub-lists (`awx/api/views/__init__.py`)

Each resource that supports notifications exposes attach/detach sub-lists for each event type:

| Resource | Events |
|---|---|
| JobTemplate | started, error, success |
| Project | started, error, success |
| InventorySource | started, error, success |
| WorkflowJobTemplate | started, error, success, approval |
| SystemJobTemplate | started, error, success |

And read-only notification lists on completed job records:
- `Job`, `ProjectUpdate`, `InventoryUpdate`, `WorkflowJob`, `AdHocCommand`, `SystemJob`

### Serializers (`awx/api/serializers.py`)

**`NotificationTemplateSerializer`**:
- Exposes `notification_configuration` with password fields masked
- `validate_messages` — validates event keys (started/success/error/workflow_approval), sub-event keys (running/approved/timed_out/denied), and that `message` type strings contain no newlines
- `get_summary_fields` — includes 5 most recent notifications (id, status, created, error)
- `show_capabilities`: edit, delete, copy

**`NotificationSerializer`**: read-only representation of a `Notification` record

---

## 4. RBAC (`awx/main/access.py`)

- `NotificationTemplateAccess` — governs CRUD on templates
  - Visible to: superusers, org admins, users with `notification_admin_role` on the org
  - Org members cannot see templates
- `NotificationAccess` — governs read access to dispatched notifications
- `Organization.notification_admin_role` — org-level role granting notification management without full org admin

---

## 5. Task Layer (`awx/main/tasks/system.py`)

- `send_notifications(notification_list, job_id=None)` — Celery task
  - Called via `connection.on_commit` to ensure it only runs after the DB transaction commits
  - Associates `Notification` records with the `UnifiedJob`
  - Calls `notification_template.send(subject, body)` per notification
  - Updates `Notification.status` to successful/failed with error detail

- `events_processed_hook(unified_job)` — called after the final job event is processed
  - Triggers `send_notification_templates('succeeded'|'failed')`

- Job runner (`awx/main/tasks/jobs.py:666`) calls `send_notification_templates("running")` at job start

- Workflow approval task (`awx/main/tasks/system.py:930`) calls `send_notification_templates('failed')` on timeout

---

## 6. Template Resolution (per job type)

Each `UnifiedJob` subclass implements `get_notification_templates()` which returns a dict of `{started: [...], success: [...], error: [...]}`. The union of template-level and org-level assignments is returned:

- **Job** — templates from `JobTemplate` + `Project` + org-level fallbacks
- **ProjectUpdate** — templates from `Project` + org-level fallbacks
- **InventoryUpdate** — templates from `InventorySource` + org-level fallbacks
- **WorkflowJob** — templates from `WorkflowJobTemplate` + org-level fallbacks + approval templates
- **AdHocCommand** — org-level only
- **SystemJob** — templates from `SystemJobTemplate` only (no org fallback)

---

## 7. Client Libraries

### awxkit (`awxkit/awxkit/api/`)
- `pages/notification_templates.py` — `NotificationTemplates`, `NotificationTemplate` page objects
- `pages/notifications.py` — `Notifications`, `Notification` page objects
- `mixins/has_notifications.py` — `HasNotifications` mixin applied to resources that have notification sub-lists

### Ansible Collection (`awx_collection/plugins/modules/notification_template.py`)
- Module for managing `NotificationTemplate` objects via the AWX API

---

## 8. Tests

| File | Scope |
|---|---|
| `awx/main/tests/functional/test_notifications.py` | End-to-end API + model tests |
| `awx/main/tests/functional/api/test_notifications.py` | API-layer tests |
| `awx/main/tests/functional/models/test_notifications.py` | Model unit tests |
| `awx/main/tests/functional/rbac/test_rbac_notifications.py` | Access control tests |
| `awx/main/tests/unit/api/serializers/test_notification_template_serializers.py` | Serializer validation |
| `awx/main/tests/unit/notifications/test_*.py` | Per-backend unit tests (slack, webhook, grafana, awssns, rocketchat) |

---

## Key Coupling Points to Address in Isolation

1. `JobNotificationMixin` lives in `awx/main/models/notifications.py` — still tightly coupled to `UnifiedJob`; needs a clean interface for the isolated app to call back into
2. `send_notifications` Celery task is in `awx/main/tasks/system.py` — will need to move or be importable from the notifications app
3. `UnifiedJobSerializer` is imported inside `build_notification_message` to avoid circular imports — isolation will need to formalize this boundary
4. `NotificationFieldsModel` is in `awx/main/models/base.py` — moving it to the notifications app would require all models that use it to import across app boundaries
5. Per-resource API sub-lists (e.g. `JobTemplateNotificationTemplatesStartedList`) live in the main `awx/api/views/__init__.py` — these reference both the main and notification models
