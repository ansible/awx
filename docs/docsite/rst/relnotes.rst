.. _release_notes:

**************
Release Notes
**************


Refer to `AWX Release Notes <https://github.com/ansible/awx/releases>`_.

.. _ir_known_issues:

*************
Known Issues
*************

.. index:: 
   single: known issues
   single: issues, known
   pair: job slice; limitations


.. contents::
    :local:


Job slicing and limit interactions
=====================================

When passing a limit to a Sliced Job, if the limit causes slices to have no hosts assigned, those slices will fail, causing the overall job to fail.


Misuse of job slicing can cause errors in job scheduling
============================================================

Job slicing is intended to scale job executions horizontally. Enabling job slicing on a job template divides an inventory to be acted upon in the number of slices configured at launch time and then starts a job for each slice.

It is expected that the number of slices will be equal to or less than the number of controller nodes. Setting an extremely high number of job slices (e.g., thousands), while allowed, can cause performance degradation as the job scheduler is not designed to schedule simultaneously thousands of workflow nodes, which are what the sliced jobs become.
