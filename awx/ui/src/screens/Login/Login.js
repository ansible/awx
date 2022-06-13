/* eslint-disable react/jsx-no-useless-fragment */
import React, { useCallback, useEffect } from 'react';
import { Redirect, withRouter } from 'react-router-dom';

import { t } from '@lingui/macro';
import { Formik } from 'formik';
import styled from 'styled-components';
import sanitizeHtml from 'sanitize-html';
import {
  Alert,
  Brand,
  LoginMainFooterLinksItem,
  LoginForm,
  Login as PFLogin,
  LoginHeader,
  LoginFooter,
  LoginMainHeader,
  LoginMainBody,
  LoginMainFooter,
  Tooltip,
} from '@patternfly/react-core';

import {
  AzureIcon,
  GoogleIcon,
  GithubIcon,
  UserCircleIcon,
} from '@patternfly/react-icons';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import { AuthAPI, RootAPI } from 'api';
import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import { useSession } from 'contexts/Session';
import { SESSION_REDIRECT_URL } from '../../constants';

const loginLogoSrc = 'static/media/logo-login.svg';

const Login = styled(PFLogin)`
  & .pf-c-brand {
    max-height: 285px;
  }
`;

function AWXLogin({ alt, isAuthenticated }) {
  const { authRedirectTo, isSessionExpired, setAuthRedirectTo } = useSession();

  const {
    isLoading: isCustomLoginInfoLoading,
    error: customLoginInfoError,
    request: fetchCustomLoginInfo,
    result: { brandName, logo, loginInfo, socialAuthOptions },
  } = useRequest(
    useCallback(async () => {
      const [
        {
          data: { custom_logo, custom_login_info },
        },
        {
          data: { BRAND_NAME },
        },
        { data: authData },
      ] = await Promise.all([
        RootAPI.read(),
        RootAPI.readAssetVariables(),
        AuthAPI.read(),
      ]);
      const logoSrc = custom_logo
        ? `data:image/jpeg;${custom_logo}`
        : loginLogoSrc;

      return {
        brandName: BRAND_NAME,
        logo: logoSrc,
        loginInfo: custom_login_info,
        socialAuthOptions: authData,
      };
    }, []),
    {
      brandName: null,
      logo: loginLogoSrc,
      loginInfo: null,
      socialAuthOptions: {},
    }
  );

  const { error: loginInfoError, dismissError: dismissLoginInfoError } =
    useDismissableError(customLoginInfoError);

  useEffect(() => {
    fetchCustomLoginInfo();
  }, [fetchCustomLoginInfo]);

  const {
    isLoading: isAuthenticating,
    error: authenticationError,
    request: authenticate,
  } = useRequest(
    useCallback(async ({ username, password }) => {
      await RootAPI.login(username, password);
    }, [])
  );

  const { error: authError, dismissError: dismissAuthError } =
    useDismissableError(authenticationError);

  const handleSubmit = async (values) => {
    dismissAuthError();
    await authenticate(values);
    setAuthRedirectTo('/home');
  };

  if (isCustomLoginInfoLoading) {
    return null;
  }
  if (isAuthenticated(document.cookie)) {
    return <Redirect to={authRedirectTo || '/'} />;
  }

  let helperText;
  if (authError?.response?.status === 401) {
    helperText = t`Invalid username or password. Please try again.`;
  } else {
    helperText = t`There was a problem logging in. Please try again.`;
  }

  const HeaderBrand = (
    <Brand data-cy="brand-logo" src={logo} alt={alt || brandName} />
  );
  const Header = <LoginHeader headerBrand={HeaderBrand} />;
  const Footer = (
    <LoginFooter
      data-cy="login-footer"
      dangerouslySetInnerHTML={{
        __html: sanitizeHtml(loginInfo),
      }}
    />
  );

  const setSessionRedirect = () => {
    window.sessionStorage.setItem(SESSION_REDIRECT_URL, authRedirectTo);
  };

  return (
    <Login header={Header} footer={Footer}>
      <LoginMainHeader
        data-cy="login-header"
        title={brandName ? t`Welcome to ${brandName}!` : ''}
        subtitle={t`Please log in`}
      />
      <LoginMainBody>
        {isSessionExpired.current ? (
          <Alert
            variant="warning"
            isInline
            title={t`Your session has expired. Please log in to continue where you left off.`}
            ouiaId="session-expired-warning-alert"
          />
        ) : null}
        <Formik
          initialValues={{
            password: '',
            username: '',
          }}
          onSubmit={handleSubmit}
        >
          {(formik) => (
            <LoginForm
              data-cy="login-form"
              className={authError ? 'pf-m-error' : ''}
              helperText={helperText}
              isLoginButtonDisabled={isAuthenticating}
              isValidPassword={!authError}
              isValidUsername={!authError}
              loginButtonLabel={t`Log In`}
              onChangePassword={(val) => {
                formik.setFieldValue('password', val);
                dismissAuthError();
              }}
              onChangeUsername={(val) => {
                formik.setFieldValue('username', val);
                dismissAuthError();
              }}
              onLoginButtonClick={formik.handleSubmit}
              passwordLabel={t`Password`}
              passwordValue={formik.values.password}
              showHelperText={authError}
              usernameLabel={t`Username`}
              usernameValue={formik.values.username}
            />
          )}
        </Formik>
        {loginInfoError && (
          <AlertModal
            isOpen={loginInfoError}
            variant="error"
            title={t`Error!`}
            onClose={dismissLoginInfoError}
            data-cy="login-info-error"
          >
            {t`Failed to fetch custom login configuration settings.  System defaults will be shown instead.`}
            <ErrorDetail error={loginInfoError} />
          </AlertModal>
        )}
      </LoginMainBody>
      <LoginMainFooter
        socialMediaLoginContent={
          <>
            {socialAuthOptions &&
              Object.keys(socialAuthOptions).map((authKey) => {
                const loginUrl = socialAuthOptions[authKey].login_url;
                if (authKey === 'azuread-oauth2') {
                  return (
                    <LoginMainFooterLinksItem
                      data-cy="social-auth-azure"
                      href={loginUrl}
                      key={authKey}
                      onClick={setSessionRedirect}
                    >
                      <Tooltip content={t`Sign in with Azure AD`}>
                        <AzureIcon size="lg" />
                      </Tooltip>
                    </LoginMainFooterLinksItem>
                  );
                }
                if (authKey === 'github') {
                  return (
                    <LoginMainFooterLinksItem
                      data-cy="social-auth-github"
                      href={loginUrl}
                      key={authKey}
                      onClick={setSessionRedirect}
                    >
                      <Tooltip content={t`Sign in with GitHub`}>
                        <GithubIcon size="lg" />
                      </Tooltip>
                    </LoginMainFooterLinksItem>
                  );
                }
                if (authKey === 'github-org') {
                  return (
                    <LoginMainFooterLinksItem
                      data-cy="social-auth-github-org"
                      href={loginUrl}
                      key={authKey}
                      onClick={setSessionRedirect}
                    >
                      <Tooltip content={t`Sign in with GitHub Organizations`}>
                        <GithubIcon size="lg" />
                      </Tooltip>
                    </LoginMainFooterLinksItem>
                  );
                }
                if (authKey === 'github-team') {
                  return (
                    <LoginMainFooterLinksItem
                      data-cy="social-auth-github-team"
                      href={loginUrl}
                      key={authKey}
                      onClick={setSessionRedirect}
                    >
                      <Tooltip content={t`Sign in with GitHub Teams`}>
                        <GithubIcon size="lg" />
                      </Tooltip>
                    </LoginMainFooterLinksItem>
                  );
                }
                if (authKey === 'github-enterprise') {
                  return (
                    <LoginMainFooterLinksItem
                      data-cy="social-auth-github-enterprise"
                      href={loginUrl}
                      key={authKey}
                      onClick={setSessionRedirect}
                    >
                      <Tooltip content={t`Sign in with GitHub Enterprise`}>
                        <GithubIcon size="lg" />
                      </Tooltip>
                    </LoginMainFooterLinksItem>
                  );
                }
                if (authKey === 'github-enterprise-org') {
                  return (
                    <LoginMainFooterLinksItem
                      data-cy="social-auth-github-enterprise-org"
                      href={loginUrl}
                      key={authKey}
                      onClick={setSessionRedirect}
                    >
                      <Tooltip
                        content={t`Sign in with GitHub Enterprise Organizations`}
                      >
                        <GithubIcon size="lg" />
                      </Tooltip>
                    </LoginMainFooterLinksItem>
                  );
                }
                if (authKey === 'github-enterprise-team') {
                  return (
                    <LoginMainFooterLinksItem
                      data-cy="social-auth-github-enterprise-team"
                      href={loginUrl}
                      key={authKey}
                      onClick={setSessionRedirect}
                    >
                      <Tooltip
                        content={t`Sign in with GitHub Enterprise Teams`}
                      >
                        <GithubIcon size="lg" />
                      </Tooltip>
                    </LoginMainFooterLinksItem>
                  );
                }
                if (authKey === 'google-oauth2') {
                  return (
                    <LoginMainFooterLinksItem
                      data-cy="social-auth-google"
                      href={loginUrl}
                      key={authKey}
                      onClick={setSessionRedirect}
                    >
                      <Tooltip content={t`Sign in with Google`}>
                        <GoogleIcon size="lg" />
                      </Tooltip>
                    </LoginMainFooterLinksItem>
                  );
                }
                if (authKey.startsWith('saml')) {
                  const samlIDP = authKey.split(':')[1] || null;
                  return (
                    <LoginMainFooterLinksItem
                      data-cy="social-auth-saml"
                      href={loginUrl}
                      key={authKey}
                      onClick={setSessionRedirect}
                    >
                      <Tooltip
                        content={
                          samlIDP
                            ? t`Sign in with SAML ${samlIDP}`
                            : t`Sign in with SAML`
                        }
                      >
                        <UserCircleIcon size="lg" />
                      </Tooltip>
                    </LoginMainFooterLinksItem>
                  );
                }

                return null;
              })}
          </>
        }
      />
    </Login>
  );
}

export default withRouter(AWXLogin);
export { AWXLogin as _AWXLogin };
