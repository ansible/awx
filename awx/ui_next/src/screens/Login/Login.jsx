import React, { useCallback, useEffect } from 'react';
import { Redirect, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Formik } from 'formik';
import styled from 'styled-components';
import { LoginForm, LoginPage as PFLoginPage } from '@patternfly/react-core';
import useRequest, { useDismissableError } from '../../util/useRequest';
import { RootAPI } from '../../api';
import { BrandName } from '../../variables';
import AlertModal from '../../components/AlertModal';
import ErrorDetail from '../../components/ErrorDetail';

import brandLogo from './brand-logo.svg';

const LoginPage = styled(PFLoginPage)`
  & .pf-c-brand {
    max-height: 285px;
  }
`;

function AWXLogin({ alt, i18n, isAuthenticated }) {
  const {
    isLoading: isCustomLoginInfoLoading,
    error: customLoginInfoError,
    request: fetchCustomLoginInfo,
    result: { logo, loginInfo },
  } = useRequest(
    useCallback(async () => {
      const {
        data: { custom_logo, custom_login_info },
      } = await RootAPI.read();
      const logoSrc = custom_logo
        ? `data:image/jpeg;${custom_logo}`
        : brandLogo;
      return {
        logo: logoSrc,
        loginInfo: custom_login_info,
      };
    }, []),
    { logo: brandLogo, loginInfo: null }
  );

  const {
    error: loginInfoError,
    dismissError: dismissLoginInfoError,
  } = useDismissableError(customLoginInfoError);

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

  const {
    error: authError,
    dismissError: dismissAuthError,
  } = useDismissableError(authenticationError);

  const handleSubmit = async values => {
    dismissAuthError();
    await authenticate(values);
  };

  const brandName = BrandName;

  if (isCustomLoginInfoLoading) {
    return null;
  }

  if (isAuthenticated(document.cookie)) {
    return <Redirect to="/" />;
  }

  let helperText;
  if (authError?.response?.status === 401) {
    helperText = i18n._(t`Invalid username or password. Please try again.`);
  } else {
    helperText = i18n._(t`There was a problem signing in. Please try again.`);
  }

  return (
    <LoginPage
      brandImgSrc={logo}
      brandImgAlt={alt || brandName}
      loginTitle={i18n._(t`Welcome to Ansible ${brandName}! Please Sign In.`)}
      textContent={loginInfo}
    >
      <Formik
        initialValues={{
          password: '',
          username: '',
        }}
        onSubmit={handleSubmit}
      >
        {formik => (
          <>
            <LoginForm
              className={authError ? 'pf-m-error' : ''}
              helperText={helperText}
              isLoginButtonDisabled={isAuthenticating}
              isValidPassword={!authError}
              isValidUsername={!authError}
              loginButtonLabel={i18n._(t`Log In`)}
              onChangePassword={val => {
                formik.setFieldValue('password', val);
                dismissAuthError();
              }}
              onChangeUsername={val => {
                formik.setFieldValue('username', val);
                dismissAuthError();
              }}
              onLoginButtonClick={formik.handleSubmit}
              passwordLabel={i18n._(t`Password`)}
              passwordValue={formik.values.password}
              showHelperText={authError}
              usernameLabel={i18n._(t`Username`)}
              usernameValue={formik.values.username}
            />
          </>
        )}
      </Formik>
      {loginInfoError && (
        <AlertModal
          isOpen={loginInfoError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissLoginInfoError}
        >
          {i18n._(
            t`Failed to fetch custom login configuration settings.  System defaults will be shown instead.`
          )}
          <ErrorDetail error={loginInfoError} />
        </AlertModal>
      )}
    </LoginPage>
  );
}

export default withI18n()(withRouter(AWXLogin));
export { AWXLogin as _AWXLogin };
