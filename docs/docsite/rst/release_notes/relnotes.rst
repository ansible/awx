.. _release_notes:

**************
Release Notes
**************

.. index::
   pair: release notes; v23.00


For versions older than 23.0.0, refer to `AWX Release Notes <https://github.com/ansible/awx/releases>`_.

.. Removed relnotes_current from common/.

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
