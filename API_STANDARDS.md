Coding Standards and Practices
==============================

This is not meant to be a style document so much as a practices document for ensuring performance and convention in the Ansible Tower API.

Paginate Everything
===================

Anything that returns a collection must be paginated.

Assume large data sets
======================

Don't test exclusively with small data.  Assume 1000-10000 hosts in all operations, with years of event data.

Some of our users have 30,000 machines they manage.

API performance
===============

In general, the expected response time for any API call is something like 1/4 of a second or less.  Signs of slow API
performance should be regularly checked, particularly for missing indexes.

Missing Indexes
===============

Any filters the UI uses should be indexed.

Migrations
==========

Always think about any existing data when adding any new fields.  It's ok to wait in upgrade time to get the database to be 
consistent.

Limit Queries
=============

The number of queries made should be constant time and must not vary with the size of the result set.

Consider RBAC
=============

The returns of all collections must be filtered by who has access to view them, without exception

Discoverability
===============

All API endpoints must be able to be traversed from "/", and have comments, where possible, explaining their purpose

Friendly Comments
=================

All API comments are exposed by the API browser and must be fit for customers.   Avoid jokes in API comments and error
messages, as well as FIXME comments in places that the API will display.

UI Sanity
=========

Where possible the API should provide API endpoints that feed raw data into the UI, the UI should not have to do lots of
data transformations, as it is going to be less responsive and able to do these things.

When requiring a collection of times of size N, the UI must not make any extra API queries for each item in the result set

Effective Usage of Query Sets
=============================

The system must return Django result sets rather than building JSON in memory in nearly all cases.  Use things like
exclude and joins, and let the database do the work.

Serializers
===========

No database queries may be made in serializers because these are executed once per item, rather than paginated.

REST verbs
==========

REST verbs should be RESTy.  Don't use GETs to do things that should be a PUT or POST.

Unit tests
==========

Every URL/route must have unit test coverage.  Consider both positive and negative tests.


