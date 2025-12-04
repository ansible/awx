.. _creating_api_endpoints:

===============================
Creating New API Endpoints
===============================

This guide walks you through creating a new REST API endpoint in AWX. AWX uses the Django REST Framework (DRF) to provide a comprehensive, versioned API for all resources.

----

.. contents:: Table of Contents
   :depth: 3
   :local:

----

Overview
========

AWX follows a consistent pattern for creating API endpoints. Each endpoint requires four main components:

1. **Model** - Defines the database schema and business logic
2. **Serializer** - Handles data validation and JSON serialization
3. **Views** - Implements endpoint logic and HTTP method handling
4. **URL Configuration** - Maps URLs to views

All API endpoints in AWX follow RESTful conventions and are versioned under the ``/api/v2/`` path.

Architecture
============

Directory Structure
-------------------

.. code-block:: text

    awx/
    ├── main/
    │   └── models/              # Database models
    │       ├── __init__.py
    │       ├── base.py         # Base model classes
    │       └── your_model.py   # Your new model
    ├── api/
    │   ├── serializers.py      # Data serializers
    │   ├── views/              # API views
    │   │   ├── __init__.py
    │   │   └── your_resource.py
    │   └── urls/               # URL routing
    │       ├── __init__.py
    │       ├── urls.py         # Main URL configuration
    │       └── your_resource.py

Key Principles
--------------

.. important::
   All AWX API endpoints must follow these principles:

   - **RESTful design** - Use proper HTTP methods (GET, POST, PUT, PATCH, DELETE)
   - **Pagination** - All list endpoints must be paginated
   - **Permission checking** - Implement proper RBAC controls
   - **Consistent response format** - Use standard JSON response structure
   - **API versioning** - All endpoints under ``/api/v2/``

Step-by-Step Guide
===================

Step 1: Create the Model
-------------------------

Models define your database schema and business logic. Create a new model file in ``awx/main/models/`` or add to an existing one.

**Location:** ``awx/main/models/your_model.py``

.. code-block:: python

    from django.db import models
    from django.utils.translation import gettext_lazy as _
    from awx.api.versioning import reverse
    from awx.main.models.base import CommonModelNameNotUnique

    class YourResource(CommonModelNameNotUnique):
        """
        Description of your resource.
        """

        class Meta:
            app_label = 'main'
            ordering = ('name',)

        # Add your fields
        configuration = models.JSONField(
            default=dict,
            blank=True,
            help_text=_('Configuration data for the resource.'),
        )

        status = models.CharField(
            max_length=20,
            choices=[
                ('active', 'Active'),
                ('inactive', 'Inactive'),
            ],
            default='active',
            help_text=_('Current status of the resource.'),
        )

        # Relationships
        organization = models.ForeignKey(
            'Organization',
            related_name='your_resources',
            on_delete=models.CASCADE,
            help_text=_('Organization this resource belongs to.'),
        )

        def get_absolute_url(self, request=None):
            return reverse('api:your_resource_detail',
                         kwargs={'pk': self.pk},
                         request=request)

**Model Best Practices:**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Practice
     - Description
   * - **Inherit from base classes**
     - Use ``CommonModelNameNotUnique`` or ``CommonModel`` for standard fields
   * - **Define Meta class**
     - Always include ``app_label = 'main'`` and appropriate ordering
   * - **Use help_text**
     - Provide clear descriptions for API documentation
   * - **Implement get_absolute_url()**
     - Return the canonical API URL for the resource
   * - **Use gettext_lazy**
     - Wrap user-facing strings with ``_()`` for i18n support

Step 2: Create the Serializer
------------------------------

Serializers handle data validation and conversion between Python objects and JSON.

**Location:** ``awx/api/serializers.py``

.. code-block:: python

    class YourResourceSerializer(BaseSerializer):
        """
        Serializer for YourResource model.
        """

        class Meta:
            model = YourResource
            fields = ('*', '-description', 'organization', 'configuration', 'status')
            read_only_fields = ('created', 'modified')

        def get_related(self, obj):
            """Provide URLs to related resources."""
            res = super(YourResourceSerializer, self).get_related(obj)
            if obj.organization:
                res['organization'] = self.reverse(
                    'api:organization_detail',
                    kwargs={'pk': obj.organization.pk}
                )
            return res

        def validate_configuration(self, value):
            """Custom field validation."""
            if not isinstance(value, dict):
                raise serializers.ValidationError(
                    "Configuration must be a JSON object"
                )
            # Add your validation logic
            required_keys = ['key1', 'key2']
            for key in required_keys:
                if key not in value:
                    raise serializers.ValidationError(
                        f"Configuration must include '{key}'"
                    )
            return value

        def validate(self, attrs):
            """Cross-field validation."""
            if attrs.get('status') == 'active' and not attrs.get('configuration'):
                raise serializers.ValidationError(
                    "Active resources must have configuration"
                )
            return super(YourResourceSerializer, self).validate(attrs)

**Serializer Field Specification:**

.. code-block:: python

    # Include all default fields plus specific fields
    fields = ('*', 'field1', 'field2')

    # Include all fields except description
    fields = ('*', '-description')

    # Include only specific fields
    fields = ('id', 'name', 'created', 'modified')

**Key Serializer Methods:**

- ``get_related(obj)`` - Returns URLs to related resources
- ``validate_<field>(value)`` - Field-level validation
- ``validate(attrs)`` - Object-level validation
- ``create(validated_data)`` - Custom creation logic
- ``update(instance, validated_data)`` - Custom update logic

Step 3: Implement the Views
----------------------------

Views handle HTTP requests and implement endpoint logic. Create a new file in ``awx/api/views/``.

**Location:** ``awx/api/views/your_resource.py``

.. code-block:: python

    from django.utils.translation import gettext_lazy as _
    from awx.api.generics import (
        ListCreateAPIView,
        RetrieveUpdateDestroyAPIView,
        SubListCreateAttachDetachAPIView,
    )
    from awx.main.models import YourResource, Organization
    from awx.api.serializers import YourResourceSerializer


    class YourResourceList(ListCreateAPIView):
        """
        List and create YourResource objects.

        GET /api/v2/your_resources/
        POST /api/v2/your_resources/
        """
        name = _("Your Resources")
        model = YourResource
        serializer_class = YourResourceSerializer


    class YourResourceDetail(RetrieveUpdateDestroyAPIView):
        """
        Retrieve, update, or delete a YourResource object.

        GET /api/v2/your_resources/{pk}/
        PUT /api/v2/your_resources/{pk}/
        PATCH /api/v2/your_resources/{pk}/
        DELETE /api/v2/your_resources/{pk}/
        """
        model = YourResource
        serializer_class = YourResourceSerializer


    class OrganizationYourResourceList(SubListCreateAttachDetachAPIView):
        """
        List and manage YourResource objects for a specific Organization.

        GET /api/v2/organizations/{pk}/your_resources/
        POST /api/v2/organizations/{pk}/your_resources/
        """
        name = _("Organization Your Resources")
        model = YourResource
        serializer_class = YourResourceSerializer
        parent_model = Organization
        relationship = 'your_resources'

**Common View Classes:**

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - View Class
     - Purpose
   * - ``ListCreateAPIView``
     - List all objects (GET) and create new objects (POST)
   * - ``RetrieveUpdateDestroyAPIView``
     - Get (GET), update (PUT/PATCH), and delete (DELETE) a single object
   * - ``RetrieveUpdateAPIView``
     - Get (GET) and update (PUT/PATCH) without delete capability
   * - ``SubListCreateAttachDetachAPIView``
     - Manage relationships between resources
   * - ``SubListAPIView``
     - Read-only list of related resources

**Required View Attributes:**

- ``model`` - The model class for this view
- ``serializer_class`` - The serializer to use for this view
- ``name`` - Human-readable name for the endpoint (wrapped in ``_()``)

**Optional View Attributes:**

.. code-block:: python

    class YourResourceList(ListCreateAPIView):
        model = YourResource
        serializer_class = YourResourceSerializer

        # Optimize queries
        select_related_fields = ('organization',)
        prefetch_related_fields = ('related_objects',)

        # Custom filtering
        search_fields = ('name', 'description')
        filter_fields = ('status', 'organization')

        # Custom ordering
        ordering_fields = ('name', 'created', 'modified')

**Adding Custom Logic:**

.. code-block:: python

    class YourResourceDetail(RetrieveUpdateDestroyAPIView):
        model = YourResource
        serializer_class = YourResourceSerializer

        def destroy(self, request, *args, **kwargs):
            """Custom delete logic."""
            obj = self.get_object()

            # Check for dependencies
            if obj.related_jobs.filter(status='running').exists():
                return Response(
                    {'error': 'Cannot delete resource with running jobs'},
                    status=status.HTTP_409_CONFLICT
                )

            return super().destroy(request, *args, **kwargs)

Step 4: Configure URL Routing
------------------------------

URL configurations map URLs to views. Create a new URL file in ``awx/api/urls/``.

**Location:** ``awx/api/urls/your_resource.py``

.. code-block:: python

    from django.urls import re_path
    from awx.api.views.your_resource import (
        YourResourceList,
        YourResourceDetail,
    )

    urls = [
        re_path(r'^$', YourResourceList.as_view(), name='your_resource_list'),
        re_path(r'^(?P<pk>[0-9]+)/$', YourResourceDetail.as_view(),
                name='your_resource_detail'),
    ]

    __all__ = ['urls']

**URL Pattern Conventions:**

.. code-block:: python

    # List endpoint - /api/v2/your_resources/
    re_path(r'^$', YourResourceList.as_view(), name='your_resource_list')

    # Detail endpoint - /api/v2/your_resources/123/
    re_path(r'^(?P<pk>[0-9]+)/$', YourResourceDetail.as_view(),
            name='your_resource_detail')

    # Action endpoint - /api/v2/your_resources/123/launch/
    re_path(r'^(?P<pk>[0-9]+)/launch/$', YourResourceLaunch.as_view(),
            name='your_resource_launch')

    # Nested resource - /api/v2/your_resources/123/children/
    re_path(r'^(?P<pk>[0-9]+)/children/$', YourResourceChildrenList.as_view(),
            name='your_resource_children_list')

Step 5: Register URLs
----------------------

Add your URL configuration to the main API routing file.

**Location:** ``awx/api/urls/urls.py``

.. code-block:: python

    # Add import at the top of the file
    from awx.api.urls import your_resource as your_resource_urls

    # Add to v2_urls list (in alphabetical order)
    v2_urls = [
        # ... other URLs ...
        re_path(r'^your_resources/', include(your_resource_urls.urls)),
        # ... more URLs ...
    ]

.. note::
   Maintain alphabetical order in the imports and URL list for consistency.

Result: Your New API Endpoints
===============================

Following the steps above creates these functional API endpoints:

.. list-table::
   :header-rows: 1
   :widths: 10 40 50

   * - Method
     - URL
     - Description
   * - GET
     - ``/api/v2/your_resources/``
     - List all resources (paginated)
   * - POST
     - ``/api/v2/your_resources/``
     - Create a new resource
   * - GET
     - ``/api/v2/your_resources/{pk}/``
     - Retrieve a specific resource
   * - PUT
     - ``/api/v2/your_resources/{pk}/``
     - Update a resource (full replacement)
   * - PATCH
     - ``/api/v2/your_resources/{pk}/``
     - Partially update a resource
   * - DELETE
     - ``/api/v2/your_resources/{pk}/``
     - Delete a resource
   * - OPTIONS
     - ``/api/v2/your_resources/``
     - Get metadata about the endpoint

Automatic Features
===================

By using AWX's base classes, your endpoints automatically include:

Authentication & Authorization
-------------------------------

- **JWT Authentication** - Token-based authentication
- **Session Authentication** - Browser-based authentication
- **Basic Authentication** - Username/password authentication
- **Permission Checking** - Role-based access control (RBAC)

.. code-block:: bash

    # Example authenticated request
    curl -H "Authorization: Bearer <token>" \
         https://awx.example.com/api/v2/your_resources/

Pagination
----------

All list endpoints are automatically paginated with configurable page sizes.

.. code-block:: json

    {
        "count": 100,
        "next": "https://awx.example.com/api/v2/your_resources/?page=2",
        "previous": null,
        "results": [
            {
                "id": 1,
                "name": "Resource 1",
                ...
            }
        ]
    }

**Query Parameters:**

- ``page`` - Page number (default: 1)
- ``page_size`` - Number of results per page (max: 200)

Filtering and Searching
------------------------

.. code-block:: bash

    # Filter by status
    GET /api/v2/your_resources/?status=active

    # Search by name
    GET /api/v2/your_resources/?search=myresource

    # Order by created date
    GET /api/v2/your_resources/?order_by=-created

Standard Response Format
-------------------------

All responses follow a consistent JSON structure:

.. code-block:: json

    {
        "id": 1,
        "type": "your_resource",
        "url": "/api/v2/your_resources/1/",
        "related": {
            "organization": "/api/v2/organizations/5/"
        },
        "summary_fields": {
            "organization": {
                "id": 5,
                "name": "Default"
            }
        },
        "created": "2025-11-12T10:00:00.000000Z",
        "modified": "2025-11-12T10:00:00.000000Z",
        "name": "My Resource",
        "description": "Resource description",
        "configuration": {"key": "value"},
        "status": "active"
    }

Error Handling
--------------

Standardized error responses with appropriate HTTP status codes:

.. code-block:: json

    {
        "detail": "Not found."
    }

.. code-block:: json

    {
        "name": ["This field is required."],
        "configuration": ["Configuration must include 'key1'"]
    }

Advanced Topics
===============

Custom Actions
--------------

Add custom actions beyond standard CRUD operations:

.. code-block:: python

    from rest_framework.decorators import action
    from rest_framework.response import Response
    from rest_framework import status

    class YourResourceDetail(RetrieveUpdateDestroyAPIView):
        model = YourResource
        serializer_class = YourResourceSerializer

        @action(detail=True, methods=['post'])
        def activate(self, request, pk=None):
            """Activate a resource."""
            obj = self.get_object()
            obj.status = 'active'
            obj.save()
            return Response(
                self.serializer_class(obj).data,
                status=status.HTTP_200_OK
            )

Permission Checking
-------------------

Override permission checking for custom access control:

.. code-block:: python

    class YourResourceList(ListCreateAPIView):
        model = YourResource
        serializer_class = YourResourceSerializer

        def check_permissions(self, request):
            """Custom permission checking."""
            if request.method == 'POST':
                # Check if user can create resources
                if not request.user.can_access(
                    self.model, 'add', request.data
                ):
                    self.permission_denied(request)
            return super().check_permissions(request)

Query Optimization
------------------

Optimize database queries to prevent N+1 problems:

.. code-block:: python

    class YourResourceList(ListCreateAPIView):
        model = YourResource
        serializer_class = YourResourceSerializer

        # Optimize foreign key lookups
        select_related_fields = ('organization', 'created_by')

        # Optimize many-to-many and reverse foreign keys
        prefetch_related_fields = ('labels', 'related_objects')

.. warning::
   **Critical Performance Rule**: The number of database queries MUST be constant and MUST NOT vary with the result set size.

Testing Your Endpoint
======================

Create tests in ``awx/main/tests/functional/`` to verify your endpoint behavior.

**Location:** ``awx/main/tests/functional/test_your_resource.py``

.. code-block:: python

    import pytest
    from awx.main.models import YourResource, Organization

    @pytest.mark.django_db
    class TestYourResourceAPI:
        """Test YourResource API endpoints."""

        def test_list_your_resources(self, get, admin_user, organization):
            """Test listing resources."""
            # Create test data
            YourResource.objects.create(
                name='Test Resource',
                organization=organization,
            )

            # Make API request
            response = get(
                url='/api/v2/your_resources/',
                user=admin_user,
                expect=200
            )

            # Verify response
            assert response.data['count'] == 1
            assert response.data['results'][0]['name'] == 'Test Resource'

        def test_create_your_resource(self, post, admin_user, organization):
            """Test creating a resource."""
            data = {
                'name': 'New Resource',
                'organization': organization.id,
                'configuration': {'key': 'value'},
                'status': 'active',
            }

            response = post(
                url='/api/v2/your_resources/',
                data=data,
                user=admin_user,
                expect=201
            )

            assert response.data['name'] == 'New Resource'
            assert YourResource.objects.filter(name='New Resource').exists()

        def test_create_validation_error(self, post, admin_user, organization):
            """Test validation errors."""
            data = {
                'name': '',  # Invalid: empty name
                'organization': organization.id,
            }

            response = post(
                url='/api/v2/your_resources/',
                data=data,
                user=admin_user,
                expect=400
            )

            assert 'name' in response.data

**Test Coverage Requirements:**

- Test all HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Test positive cases (successful operations)
- Test negative cases (validation errors, permission denials)
- Test edge cases (empty data, missing fields, etc.)

Best Practices
==============

Naming Conventions
------------------

Follow consistent naming patterns:

.. code-block:: python

    # Model: CamelCase, singular
    class YourResource(CommonModel):
        pass

    # Serializer: Model name + "Serializer"
    class YourResourceSerializer(BaseSerializer):
        pass

    # Views: Model name + View type
    class YourResourceList(ListCreateAPIView):
        pass

    class YourResourceDetail(RetrieveUpdateDestroyAPIView):
        pass

    # URL names: lowercase with underscores
    name='your_resource_list'
    name='your_resource_detail'

Code Organization
-----------------

1. **Keep views simple** - Move complex business logic to models or service modules
2. **Use base classes** - Leverage AWX's base classes for consistency
3. **Document thoroughly** - Add docstrings to all classes and methods
4. **Follow DRY principle** - Don't repeat yourself; use mixins and base classes
5. **Handle errors gracefully** - Provide clear error messages

Security Considerations
-----------------------

.. important::
   Always consider security when creating new endpoints:

   - **Validate all input** - Never trust user-provided data
   - **Check permissions** - Verify user has required access
   - **Sanitize output** - Don't expose sensitive information
   - **Log access attempts** - Track who accesses what
   - **Use parameterized queries** - Prevent SQL injection

Performance Optimization
------------------------

1. **Use select_related** - For foreign key relationships
2. **Use prefetch_related** - For many-to-many and reverse foreign keys
3. **Implement pagination** - Always paginate list endpoints
4. **Add database indexes** - Index frequently queried fields
5. **Avoid N+1 queries** - Optimize serializer data access

Documentation
-------------

Your endpoint will automatically appear in:

- **Swagger/OpenAPI** documentation at ``/api/`` (development mode)
- **Browsable API** - Navigate to your endpoint in a browser
- **OPTIONS responses** - Metadata about available methods and fields

Common Pitfalls
===============

Avoid these common mistakes:

1. **Forgetting to register URLs** - Your endpoint won't be accessible
2. **Missing permission checks** - Security vulnerability
3. **N+1 query problems** - Poor performance with large datasets
4. **Inconsistent naming** - Makes codebase harder to navigate
5. **Insufficient testing** - Bugs in production
6. **Not handling edge cases** - Unexpected errors
7. **Exposing sensitive data** - Security risk

Troubleshooting
===============

Endpoint not found (404)
------------------------

Check:

1. URL registered in ``awx/api/urls/urls.py``
2. URL pattern is correct
3. Server restarted after code changes

Permission denied (403)
-----------------------

Check:

1. User has required permissions
2. RBAC rules configured correctly
3. ``check_permissions()`` implementation

Validation errors (400)
-----------------------

Check:

1. All required fields provided
2. Data types match field definitions
3. Custom validation logic in serializer

Database errors (500)
---------------------

Check:

1. Model relationships configured correctly
2. Migrations applied (``make migrations``)
3. Database constraints satisfied

Additional Resources
====================

Reference Implementations
-------------------------

Study these existing implementations for examples:

- **Simple resource**: ``awx/api/views/labels.py``
- **Complex resource**: ``awx/api/views/job_templates.py``
- **Relationship management**: ``awx/api/views/organizations.py``
- **Custom actions**: ``awx/api/views/jobs.py`` (launch, cancel)

Documentation
-------------

- **Django REST Framework**: https://www.django-rest-framework.org/
- **Django Models**: https://docs.djangoproject.com/en/stable/topics/db/models/
- **AWX API Guide**: :ref:`rest_api/index`
- **Contributing Guide**: :ref:`contributor_guide`

----

Summary
=======

Creating a new API endpoint in AWX involves:

1. ✓ Define a model in ``awx/main/models/``
2. ✓ Create a serializer in ``awx/api/serializers.py``
3. ✓ Implement views in ``awx/api/views/``
4. ✓ Configure URLs in ``awx/api/urls/``
5. ✓ Register URLs in ``awx/api/urls/urls.py``
6. ✓ Write tests in ``awx/main/tests/functional/``
7. ✓ Test your endpoint
8. ✓ Document any special behavior

By following these patterns and best practices, your endpoint will be consistent with the rest of the AWX API and provide a great developer experience.
