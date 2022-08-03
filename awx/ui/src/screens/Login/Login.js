/* eslint-disable react/jsx-no-useless-fragment */
import React, { useCallback, useEffect, useState, useRef } from 'react';
import { Redirect, withRouter } from 'react-router-dom';

import { t } from '@lingui/macro';
import { Formik } from 'formik';
import styled from 'styled-components';
import DOMPurify from 'dompurify';

import {
  Alert,
  Brand,
  Button as PFButton,
  Divider,
  Dropdown,
  DropdownItem,
  DropdownToggle as PFDropdownToggle,
  LoginMainFooterBandItem as PFLoginMainFooterBandItem,
  LoginForm,
  Login as PFLogin,
  LoginHeader,
  LoginFooter,
  LoginMainHeader,
  LoginMainBody,
  LoginMainFooter as PFLoginMainFooter,
  Tooltip,
  Title as PFTitle,
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
import { getCurrentUserId } from 'util/auth';
import { SESSION_REDIRECT_URL, SESSION_USER_ID } from '../../constants';

const loginLogoSrc = 'static/media/logo-login.svg';

const Login = styled(PFLogin)`
  & .pf-c-brand {
    max-height: 285px;
  }
`;

const LoginMainFooterBandItem = styled(PFLoginMainFooterBandItem)`
  padding-bottom: 24px;
`;

const LoginMainFooter = styled(PFLoginMainFooter)`
  & .pf-c-login__main-footer-links {
    padding-left: 48px !important;
    padding-right: 48px !important;
    justify-content: space-between !important;
  }
`;

const Button = styled(PFButton)`
  min-width: 200px;
`;

const DropdownToggle = styled(PFDropdownToggle)`
  --pf-c-dropdown__toggle--MinWidth: 200px;
  --pf-c-dropdown__toggle--FontSize: 14px;
  padding-right: 0px;
  padding-left: 26px;
  justify-content: center !important;
`;

const Title = styled(PFTitle)`
  text-align: left !important;
  width: 100% !important;
  padding-bottom: 8px;
  padding-top: 24px;
`;

function AWXLogin({ alt, isAuthenticated }) {
  const { authRedirectTo, isSessionExpired, setAuthRedirectTo } = useSession();
  const isNewUser = useRef(true);
  const hasVerifiedUser = useRef(false);

  const [isOpen, setIsOpen] = useState(false);

  const handleSelect = () => {
    setIsOpen(!isOpen);
  };

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

  if (isAuthenticated(document.cookie) && !hasVerifiedUser.current) {
    const currentUserId = getCurrentUserId(document.cookie);
    const verifyIsNewUser = () => {
      const previousUserId = JSON.parse(
        window.localStorage.getItem(SESSION_USER_ID)
      );
      if (previousUserId === null) {
        return true;
      }
      return currentUserId.toString() !== previousUserId.toString();
    };
    isNewUser.current = verifyIsNewUser();
    hasVerifiedUser.current = true;
    window.localStorage.setItem(SESSION_USER_ID, JSON.stringify(currentUserId));
  }

  if (isAuthenticated(document.cookie) && hasVerifiedUser.current) {
    const redirect = isNewUser.current ? '/' : authRedirectTo;
    return <Redirect to={redirect} />;
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
        __html: DOMPurify.sanitize(loginInfo),
      }}
    />
  );

  const setSessionRedirect = () => {
    window.sessionStorage.setItem(SESSION_REDIRECT_URL, authRedirectTo);
  };

  const dropdownItems = [];
  const githubCount = Object.keys(socialAuthOptions).filter((item) =>
    item.includes('github')
  ).length;

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
            {Object.keys(socialAuthOptions).length === 0 ? null : (
              <>
                <Divider />
                <Title size="md" headingLevel="h6">
                  {t`Log in with`}
                </Title>
              </>
            )}
            {socialAuthOptions &&
              Object.keys(socialAuthOptions).map((authKey) => {
                const loginUrl = socialAuthOptions[authKey].login_url;
                if (authKey === 'azuread-oauth2') {
                  return (
                    <LoginMainFooterBandItem
                      data-cy="social-auth-azure"
                      key={authKey}
                    >
                      <Tooltip content={t`Log in with Azure AD`}>
                        <Button
                          ouiaId="social-auth-azure"
                          aria-label={t`Azure AD`}
                          variant="secondary"
                          icon={<AzureIcon />}
                          isSmall
                          component="a"
                          href={loginUrl}
                          onClick={setSessionRedirect}
                        >
                          {t`Azure AD`}
                        </Button>
                      </Tooltip>
                    </LoginMainFooterBandItem>
                  );
                }
                if (authKey === 'google-oauth2') {
                  return (
                    <LoginMainFooterBandItem
                      data-cy="social-auth-google"
                      key={authKey}
                    >
                      <Tooltip content={t`Log in with Google`}>
                        <Button
                          ouiaId="social-auth-google"
                          aria-label={t`Google`}
                          variant="secondary"
                          icon={<GoogleIcon />}
                          isSmall
                          component="a"
                          href={loginUrl}
                          onClick={setSessionRedirect}
                        >
                          {t`Google`}
                        </Button>
                      </Tooltip>
                    </LoginMainFooterBandItem>
                  );
                }
                if (authKey.startsWith('saml')) {
                  const samlIDP = authKey.split(':')[1] || null;
                  return (
                    <LoginMainFooterBandItem
                      data-cy="social-auth-saml"
                      key={authKey}
                    >
                      <Tooltip
                        content={
                          samlIDP
                            ? t`Log in with SAML ${samlIDP}`
                            : t`Log in with SAML`
                        }
                      >
                        <Button
                          ouiaId="social-auth-saml"
                          aria-label={t`SAML`}
                          variant="secondary"
                          icon={<UserCircleIcon />}
                          isSmall
                          component="a"
                          href={loginUrl}
                          onClick={setSessionRedirect}
                        >
                          {t`SAML`}
                        </Button>
                      </Tooltip>
                    </LoginMainFooterBandItem>
                  );
                }
                if (authKey.includes('github')) {
                  const githubtype = authKey.split('-');
                  for (let i = 0; i < githubtype.length; i++) {
                    githubtype[i] =
                      githubtype[i][0].toUpperCase() +
                      githubtype[i].substring(1);
                  }
                  if (githubCount === 1) {
                    return (
                      <LoginMainFooterBandItem
                        data-cy="social-auth-github"
                        key={authKey}
                      >
                        <Tooltip
                          content={t`Log in with GitHub ${githubtype[1]} ${githubtype[2]}`}
                        >
                          <Button
                            ouiaId="social-auth-github"
                            aria-label={t`GitHub ${githubtype[1]} ${githubtype[2]}`}
                            variant="secondary"
                            icon={<GithubIcon />}
                            isSmall
                            component="a"
                            href={loginUrl}
                            onClick={setSessionRedirect}
                          >
                            {t`GitHub ${githubtype[1]} ${githubtype[2]}`}
                          </Button>
                        </Tooltip>
                      </LoginMainFooterBandItem>
                    );
                  }
                  dropdownItems.push(
                    <DropdownItem
                      href={loginUrl}
                      key={authKey}
                      onClick={setSessionRedirect}
                      ouiaId={authKey}
                    >
                      {t`GitHub ${githubtype[1]} ${githubtype[2]}`}
                    </DropdownItem>
                  );
                }
                if (dropdownItems.length === githubCount && githubCount > 1) {
                  return (
                    <Dropdown
                      ouiaId="github-dropdown"
                      key="github-selection-dropdown"
                      isOpen={isOpen}
                      onSelect={handleSelect}
                      toggle={
                        <DropdownToggle
                          onToggle={setIsOpen}
                          id="toggle-split-button-action-secondary"
                          toggleVariant="secondary"
                          ouiaId="github-dropdown-toggle"
                        >
                          <GithubIcon />
                          {' '}{`GitHub`}
                        </DropdownToggle>
                      }
                      dropdownItems={dropdownItems}
                    />
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
