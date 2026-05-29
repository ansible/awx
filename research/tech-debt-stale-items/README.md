# Tech Debt Items Auto-Closed by Bot

These are AAP Controller (awx) Jira issues reported by `cmeyers2` that were automatically
closed by the `autobot-jira-api` (pme bot) with the message:

> "This issue has been inactive for over 6 months, and is being automatically closed.
> If you feel this is still a priority you may reopen the issue."

**Total bot-closed:** 40 of 49 matching issues (9 were closed by humans)

---

## Epics (7)

| Key | Summary |
|-----|---------|
| [AAP-19478](https://issues.redhat.com/browse/AAP-19478) | Downstream source of truth |
| [AAP-21703](https://issues.redhat.com/browse/AAP-21703) | Make Controller Jobs Re-entrant |
| [AAP-22448](https://issues.redhat.com/browse/AAP-22448) | Consolidate similar awx services features |
| [AAP-22516](https://issues.redhat.com/browse/AAP-22516) | replace rsyslog, probably with open-telemetry |
| [AAP-22696](https://issues.redhat.com/browse/AAP-22696) | revisit configure tower in tower |
| [AAP-22829](https://issues.redhat.com/browse/AAP-22829) | Container first approach |
| [AAP-26531](https://issues.redhat.com/browse/AAP-26531) | replace docker with podman in AWX dev |

## Spikes (2)

| Key | Summary |
|-----|---------|
| [AAP-26251](https://issues.redhat.com/browse/AAP-26251) | otel collector settings reload |
| [AAP-30871](https://issues.redhat.com/browse/AAP-30871) | Why can/can't we backport a migration? |

## Tasks (31)

| Key | Summary |
|-----|---------|
| [AAP-21684](https://issues.redhat.com/browse/AAP-21684) | Create a manifest of upstream -> downstream file dependencies |
| [AAP-22117](https://issues.redhat.com/browse/AAP-22117) | revisit logs include guid |
| [AAP-22494](https://issues.redhat.com/browse/AAP-22494) | revisit urls |
| [AAP-22513](https://issues.redhat.com/browse/AAP-22513) | revisit how we organize our logging |
| [AAP-22713](https://issues.redhat.com/browse/AAP-22713) | revisit awx testing |
| [AAP-22880](https://issues.redhat.com/browse/AAP-22880) | credentials associated with our AWX day job |
| [AAP-23410](https://issues.redhat.com/browse/AAP-23410) | Platform Tech Item Similarity and Differences |
| [AAP-23929](https://issues.redhat.com/browse/AAP-23929) | revisit logging dynamic_level_filter |
| [AAP-23966](https://issues.redhat.com/browse/AAP-23966) | task manager metrics should be additive |
| [AAP-24446](https://issues.redhat.com/browse/AAP-24446) | revisit awx collection linting |
| [AAP-24452](https://issues.redhat.com/browse/AAP-24452) | simplify awx_collection integration CI test |
| [AAP-24889](https://issues.redhat.com/browse/AAP-24889) | modifying settings in tests causes chaos |
| [AAP-24946](https://issues.redhat.com/browse/AAP-24946) | upstream packaging changes can break downstream without the developer knowing |
| [AAP-24955](https://issues.redhat.com/browse/AAP-24955) | requirements.in has more than just prod runtime requirements |
| [AAP-25083](https://issues.redhat.com/browse/AAP-25083) | awx-ee has different requirements.yml collection names than downstream |
| [AAP-25236](https://issues.redhat.com/browse/AAP-25236) | fixture import across dirs is brittle |
| [AAP-26287](https://issues.redhat.com/browse/AAP-26287) | Help users understand why job output is empty or laggy |
| [AAP-26300](https://issues.redhat.com/browse/AAP-26300) | Deprecate PROXY_IP_ALLOWED_LIST |
| [AAP-26481](https://issues.redhat.com/browse/AAP-26481) | output otlp compat log format |
| [AAP-26532](https://issues.redhat.com/browse/AAP-26532) | decide what to do with sidecars |
| [AAP-26556](https://issues.redhat.com/browse/AAP-26556) | Product Review ADR |
| [AAP-26957](https://issues.redhat.com/browse/AAP-26957) | awx sso middleware process_request() can effect the entire app |
| [AAP-27372](https://issues.redhat.com/browse/AAP-27372) | Make task manager faster |
| [AAP-27583](https://issues.redhat.com/browse/AAP-27583) | Better ansible-runner cleanup path debug |
| [AAP-27657](https://issues.redhat.com/browse/AAP-27657) | Replace metrics in [wsrelay] service |
| [AAP-27659](https://issues.redhat.com/browse/AAP-27659) | Submit job re-entrant to ADR process |
| [AAP-29156](https://issues.redhat.com/browse/AAP-29156) | Create base service class |
| [AAP-29157](https://issues.redhat.com/browse/AAP-29157) | Make service first class discoverable and configurable |
| [AAP-30869](https://issues.redhat.com/browse/AAP-30869) | CredentialType registration requires all apps but should only require main |
| [AAP-34674](https://issues.redhat.com/browse/AAP-34674) | Replace metrics in [callback_receiver] service |
| [AAP-34675](https://issues.redhat.com/browse/AAP-34675) | Replace metrics in [dispatcher] service |

---

## Not Bot-Closed (9)

These matched the stale label query but were last commented on by a human, not the bot.

| Key | Summary | Last Commenter |
|-----|---------|----------------|
| [AAP-26533](https://issues.redhat.com/browse/AAP-26533) | explore using podman for the dev env | cmeyers2 |
| [AAP-26244](https://issues.redhat.com/browse/AAP-26244) | Explore "push up" plan of removing configure tower in tower | arominge |
| [AAP-31012](https://issues.redhat.com/browse/AAP-31012) | Code health | cmeyers2 |
| [AAP-25855](https://issues.redhat.com/browse/AAP-25855) | bump AWX dependencies | rh-ee-jmack |
| [AAP-22877](https://issues.redhat.com/browse/AAP-22877) | Better receptor cleanup path debug | lyasin |
| [AAP-25537](https://issues.redhat.com/browse/AAP-25537) | decide what do with tower-qa | cmeyers2 |
| [AAP-24949](https://issues.redhat.com/browse/AAP-24949) | requirements.in may have unused deps | jajackso1 |
| [AAP-25548](https://issues.redhat.com/browse/AAP-25548) | Triage Deprecation Warnings - Make a List | lyasin |
| [AAP-25854](https://issues.redhat.com/browse/AAP-25854) | pin django-ansible-base version | lyasin |
