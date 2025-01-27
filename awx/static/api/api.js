/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

(function () {
  $(function () {
    const POLLING_INTERVAL_MS = 5000; // Check every 5 seconds for updates
    const SSO_BUTTON_ID = "sso-button";
    const SSO_CONTAINER_ID = "sso-container";
    let originalPageURL = window.location.href; // Store the original page URL

    /**
     * Attach SSO button event listener for redirection
     */
    function attachSSOButtonListener() {
      const ssoButton = document.getElementById(SSO_BUTTON_ID);
      const idpElement = document.getElementById('debug_samlIdpName');
      const hostname = window.location.hostname;
      const redirectUrl = 'api';

      if (ssoButton && idpElement) {
        const idp = idpElement.textContent.trim();

        ssoButton.addEventListener('click', function (e) {
          e.preventDefault();
          console.log("SSO button clicked, initiating SAML authentication.");
          const ssoUrl = `https://${hostname}/sso/login/saml/?idp=${idp}&next=${redirectUrl}`;
          sessionStorage.setItem('samlAuthInitiated', 'true');
          window.location.href = ssoUrl;
        });
      }
    }

    /**
     * Check and handle post-authentication redirection
     */
    function handlePostAuthentication() {
      const hostname = window.location.hostname;
      const redirectUrl = 'api';
      if (sessionStorage.getItem('samlAuthInitiated') === 'true') {
        sessionStorage.removeItem('samlAuthInitiated');
        console.log("SAML authentication completed. Redirecting to /api.");
        window.location.href = `https://${hostname}/${redirectUrl}`;
      }
    }

    document.addEventListener('DOMContentLoaded', function () {
      attachSSOButtonListener();
      handlePostAuthentication();
    });

    /**
     * Create the SSO button as an anchor tag if it doesn't already exist.
     */
    function createSSOButton() {
      let container = document.getElementById(SSO_CONTAINER_ID);

      // Create a container for the button if it doesn't exist
      if (!container) {
        container = document.createElement("div");
        container.id = SSO_CONTAINER_ID;
        container.className = "form-actions-no-box";
        container.style.marginTop = "20px";
        document.body.appendChild(container); // Adjust as needed for placement
      }

      // Create the button as an <a> tag if it doesn't exist
      let button = document.getElementById(SSO_BUTTON_ID);
      if (!button) {
        button = document.createElement("a");
        button.id = SSO_BUTTON_ID;
        button.className = "btn btn-secondary";
        button.style.display = "none"; // Initially hidden
        button.setAttribute("role", "button");
        button.href = "#"; // Default href to avoid empty links
        container.appendChild(button);
      }

      return button;
    }

    const loginButton = createSSOButton();

  /**
   * Update the SSO button's state.
   * @param {boolean} isVisible - Whether the button should be visible.
   * @param {boolean} isEnabled - Whether the button should be enabled.
   * @param {string} authMethod - The SSO authentication method (e.g., "google" or "saml").
   * @param {string} idpName - The SAML IdP name (if applicable).
   */
  function updateSSOButtonState(isVisible, isEnabled, authMethod, idpName) {
    if (loginButton) {
      let loginUrl;
  
      // Determine the correct login URL based on the authentication method
      if (authMethod === "saml" && idpName) {
        loginUrl = `https://${window.location.hostname}/sso/login/saml/?idp=${idpName}&next=/api`;
      } else if (authMethod === "google") {
        loginUrl = `https://${window.location.hostname}/sso/login/google-oauth2`;
      } else {
        loginUrl = "#"; // Default if no valid auth method
      }
  
      if (isVisible && (authMethod === "saml" || authMethod === "google")) {
        // Update the button's text and href based on the auth method
        loginButton.textContent = authMethod === "google" ? "Sign in with Google" : `Sign in with SAML (${idpName})`;
        loginButton.href = loginUrl;
        loginButton.style.display = "block"; // Make button visible
        loginButton.disabled = !isEnabled; // Enable/disable based on input
        console.log(`SSO button updated: Visible (${isVisible}), Enabled (${isEnabled}), URL: ${loginUrl}`);
      } else {
        // Hide and reset the button if not visible or invalid auth method
        loginButton.style.display = "none";
        loginButton.href = "#";
        console.warn("SSO button hidden or invalid authentication method.");
      }
    }
  }

    /**
     * Validate and update the login button based on authentication options.
     * @param {Object} data - The data returned from the API.
     */
    function validateAndUpdateSSOButton(data) {
      if (data && typeof data === "object") {
        const { enabled_idps, saml_idp_name, sso_authentication_method } = data;
    
        // Check if the SSO authentication method is "saml" or "google"
        if (sso_authentication_method === "saml" || sso_authentication_method === "google") {
          // Force the SSO button to be visible for both "saml" and "google"
          if (sso_authentication_method === "saml") {
            updateSSOButtonState(true, true, "saml", saml_idp_name || "Default SAML IdP");
            console.log("SSO button forced visible for SAML.");
          } else if (sso_authentication_method === "google") {
            updateSSOButtonState(true, true, "google", "");
            console.log("SSO button forced visible for Google.");
          } else {
            updateSSOButtonState(false, false);
            console.warn(`SSO button not enabled: unsupported authentication method "${sso_authentication_method}".`);
          }
        } else {
          // If method is unsupported or invalid, hide the button
          updateSSOButtonState(false, false);
          console.warn(`SSO button not enabled: unsupported authentication method "${sso_authentication_method}".`);
        }
      } else {
        // If API response is invalid, disable and hide the button
        updateSSOButtonState(false, false);
        console.error("Invalid API response: SSO button disabled.");
      }
    }

    /**
     * Fetch authentication options and update the UI dynamically.
     */
    async function fetchAuthOptions() {
      try {
        const response = await fetch('/api/');
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Fetched data from API:', data);
        validateAndUpdateSSOButton(data);
      } catch (error) {
        console.error('Error fetching authentication options:', error);
        updateSSOButtonState(false, false);
      }
    }

    /**
     * Monitor authentication options for changes and update in real-time.
     */
    function monitorAuthChanges() {
      let lastKnownData = null;

      async function checkForChanges() {
        try {
          const response = await fetch('/api/');
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }

          const data = await response.json();
          console.log('Current Auth Detected:', data.sso_authentication_method);
          const currentData = JSON.stringify({
            enabled_idps: data.enabled_idps,
            saml_idp_name: data.saml_idp_name,
            sso_authentication_method: data.sso_authentication_method,
          });

          if (currentData !== lastKnownData) {
            console.log('Detected changes in authentication options:', data);
            lastKnownData = currentData;
            validateAndUpdateSSOButton(data);
          }
        } catch (error) {
          console.error('Error checking for changes in authentication options:', error);
        }
      }

      // Poll for changes at a faster interval
      setInterval(checkForChanges, POLLING_INTERVAL_MS);
    }


    

    // Fetch and configure authentication options on page load
    fetchAuthOptions();

    // Start monitoring for changes in real-time
    monitorAuthChanges();
    // Additional Features
    $(function () {

      // Add syntax highlighting to examples in description.
      $('.description pre').addClass('prettyprint');
      prettyPrint();

      // Make links from relative URLs to resources.
      $('span.str').each(function() {
        var s = $(this).html();
        if (s.match(/^"\/.*\/"$/) || s.match(/^"\/.*\/\?.*"$/)) {
          $(this).html('"<a href=' + s + '>' + s.replace(/"/g, '') + '</a>"');
        }
      });

      // Make links for all inventory script hosts.
      $('.request-info .pln').filter(function() {
        return $(this).text() === 'script';
      }).each(function() {
        $('.response-info span.str').filter(function() {
          return $(this).text() === '"hosts"';
        }).each(function() {
          $(this).nextUntil('span.pun:contains("]")').filter('span.str').each(function() {
            if ($(this).text().match(/^".+"$/)) {
              var s = $(this).text().replace(/"/g, '');
              $(this).html('"<a href="?host=' + s + '">' + s + '</a>"');
            }
            else if ($(this).text() !== '"') {
              var s = $(this).text();
              $(this).html('<a href="?host=' + s + '">' + s + '</a>');
            }
          });
        });
      });

      // Add classes/icons for dynamically showing/hiding help.
      if ($('.description').html()) {
        $('.description').addClass('prettyprint').parent().css('float', 'none');
        $('.hidden a.hide-description').prependTo('.description');
        $('a.hide-description').click(function() {
          $(this).tooltip('hide');
          $('.description').slideUp('fast');
          return false;
        });
        $('.hidden a.toggle-description').appendTo('.page-header h1');
        $('a.toggle-description').click(function() {
          $(this).tooltip('hide');
          $('.description').slideToggle('fast');
          return false;
        });
      }

      $('[data-toggle="tooltip"]').tooltip();

      if ($(window).scrollTop() >= 115) {
        $('body').addClass('show-title');
      }
      $(window).scroll(function() {
        if ($(window).scrollTop() >= 115) {
          $('body').addClass('show-title');
        }
        else {
          $('body').removeClass('show-title');
        }
      });

      $('a.resize').click(function() {
        $(this).tooltip('hide');
        if ($(this).find('span.glyphicon-resize-full').size()) {
          $(this).find('span.glyphicon').addClass('glyphicon-resize-small').removeClass('glyphicon-resize-full');
          $('.container').addClass('container-fluid').removeClass('container');
          document.cookie = 'api_width=wide; path=/api/';
        }
        else {
          $(this).find('span.glyphicon').addClass('glyphicon-resize-full').removeClass('glyphicon-resize-small');
          $('.container-fluid').addClass('container').removeClass('container-fluid');
          document.cookie = 'api_width=fixed; path=/api/';
        }
        return false;
      });

      function getCookie(name) {
        var value = "; " + document.cookie;
        var parts = value.split("; " + name + "=");
        if (parts.length == 2) return parts.pop().split(";").shift();
      }
      if (getCookie('api_width') == 'wide') {
        $('a.resize').click();
      }

    });
  });
})();

