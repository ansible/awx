.. _release_notes:

**************
Release Notes
**************

.. index::
   pair: release notes; v23.0.0
   pair: release notes; v23.1.0


For versions older than 23.0.0, refer to `AWX Release Notes <https://github.com/ansible/awx/releases>`_.

23.1.0
-------

- Re-ran the updater script after upstream removal of Python `future` dependency (@AlanCoding #14265)
- Fixed approval node documentation in ``workflow_job_template collection`` module (@sean-m-sullivan #14359)
- Cleaned up old auto-cleanup host metrics data (@slemrmartin #14255)
- Added instructions for solving database-related issues during initial startup (@Andersson007 #14225)
- Fixed undefined property error when a task was skipped and taskAction is debug or yum (@ivanilsonaraujojr #14372)
- Updated runner to provide ``job_explanation`` more detail when reporting errors (@AlanCoding #13482)
- Updated CI ``actions/checkout`` and ``actions/setup-python`` to latest versions to eliminate node warnings (@relrod #14398)
- Allowed ``saml_admin_attr`` to work in conjunction with SAML Org Map (@john-westcott-iv #14285)
- Removed unnecessary scheduler state save (@AlanCoding #14396)
- Created AWX docsite with RST content (@oraNod and @tvo318 #14328)
- Corrected reporting for task container resource limits set (in K8s), revising the handling of execution nodes specifically. (@djyasin #14315)
- Added check for building the AWX docsite (@AlanCoding #14406)
- Added readthedocs configuration for AWX docs (@oraNod #14413)
- Added release notes for AWX version 23.0.0 (@tvo318 #14409)
- Enabled collection integration tests on GHA (@relrod #14397)
- Updated missing inventory error messages (@marshmalien #14416)
- Fixed collection metadata license to match intent (@AlanCoding #14404)
- Updated activity stream to prevent it from logging entries when instances go offline (@AlanCoding #14385)
- Corrected the information about the default behavior described in the the docker-compose instructions (@AlanCoding #14418)
- Bumped babel dependencies (@keithjgrant #14370)
- Added example secrets in the docs to an allow list so it will be ignored in security scans (@oraNod #14408)
- Rebuilt ``package-lock`` file (@keithjgrant #14423)
- Implemented a base64 encoding check on the JSON Web Token (JWT) returned from a Conjur Enterprise authentication (@infamousjoeg #14386)
- Added a check that detects jobs already in progress to prevent users from launching multiple jobs by rapidly clicking on buttons (@mabashian #14407)


23.0.0
-------

- Added hop nodes support for k8s (@fosterseth #13904)
- Reverted "Improve performance for AWX CLI export (#13182)"  (@jbradberry #14342)
- Corrected spelling on database downtime and tolerance variable (@tuxpreacher #14347)
- Fixed schedule rruleset (@KaraokeKev #13611)
- Updates ``python-tss-sdk`` dependency (@delinea-sagar #14207)
- Fixed UI_NEXT build process broken by ansible/ansible-ui#766 (@TheRealHaoLiu #14349)
- Fixed task and web docs (@abwalczyk #14350)
- Fixed UI_NEXT build step file path issue (@TheRealHaoLiu #14357)
- Added required epoch time field for Splunk HEC event receiver (@digitalbadger-uk #14246)
- Fixed edit constructed inventory hanging loading state (@marshmalien #14343)
- Added location for locales in nginx config (@mabashian #14368)
- Updated cryptography for CVE-2023-38325 (@relrod #14358)
- Applied ``AWX_TASK_ENV`` when performing credential plugin lookups (@AlanCoding #14271)
- Enforced mutually exclusive options in credential module of the collection (@djdanielsson #14363)
- Added an example to clarify that the ``awx.subscriptions`` module should be used prior to ``awx.license`` (@phess #14351)
- Fixed default Redis URL to pass check in redis-py>4.4 (@ChandlerSwift #14344)
- Fixed typo in the description of ``scm_update_on_launch`` (@bxbrenden #14382)
- Fixed CVE-2023-40267 (@TheRealHaoLiu #14388)
- Updated PR body checks (@AlanCoding #14389)
