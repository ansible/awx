.. _ag_ent_auth:

Setting up Enterprise Authentication
==================================================


.. index::
    single: enterprise authentication
    single: authentication

This section describes setting up authentication for the following enterprise systems:

.. contents::
    :local:

- Enterprise users can only be created via the first successful login attempt from remote authentication backend.
- Enterprise users cannot be created/authenticated if non-enterprise users with the same name has already been created in AWX.
- AWX passwords of enterprise users should always be empty and cannot be set by any user if there are enterprise backend-enabled.
- If enterprise backends are disabled, an enterprise user can be converted to a normal AWX user by setting the password field. However, this operation is irreversible, as the converted AWX user can no longer be treated as enterprise user.


.. _ag_auth_azure:

Azure AD settings
-------------------

.. index::
    pair: authentication; Azure AD

To set up enterprise authentication for Microsoft Azure Active Directory (AD), you will need to obtain an OAuth2 key and secret by registering your organization-owned application from Azure at https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app. Each key and secret must belong to a unique application and cannot be shared or reused between different authentication backends. In order to register the application, you must supply it with your webpage URL, which is the Callback URL shown in the Settings Authentication screen.

1. Click **Settings** from the left navigation bar.

2. On the left side of the Settings window, click **Azure AD settings** from the list of Authentication options. 

3. The **Azure AD OAuth2 Callback URL** field is already pre-populated and non-editable.
   Once the application is registered, Azure displays the Application ID and Object ID.

4. Click **Edit** and copy and paste Azure's Application ID to the **Azure AD OAuth2 Key** field. 

   Following Azure AD's documentation for connecting your app to Microsoft Azure Active Directory, supply the key (shown at one time only) to the client for authentication.

5. Copy and paste the actual secret key created for your Azure AD application to the **Azure AD OAuth2 Secret** field of the Settings - Authentication screen.  

6. For details on completing the mapping fields, see :ref:`ag_org_team_maps`. 

7. Click **Save** when done.

8. To verify that the authentication was configured correctly, logout of AWX and the login screen will now display the Microsoft Azure logo to allow logging in with those credentials.

.. image:: ../common/images/configure-awx-auth-azure-logo.png
    :alt: AWX login screen displaying the Microsoft Azure logo for authentication.


For application registering basics in Azure AD, refer to the `Azure AD Identity Platform (v2)`_ overview. 

.. _`Azure AD Identity Platform (v2)`: https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-overview

.. _ag_auth_radius:

RADIUS settings
------------------

.. index::
    pair: authentication; RADIUS Authentication Settings


AWX can be configured to centrally use RADIUS as a source for authentication information.

1. Click **Settings** from the left navigation bar.

2. On the left side of the Settings window, click **RADIUS settings** from the list of Authentication options. 

3. Click **Edit** and enter the Host or IP of the Radius server in the **Radius Server** field. If this field is left blank, Radius authentication is disabled.

4. Enter the port and secret information in the next two fields.

5. Click **Save** when done.
