import React, { useCallback, useEffect } from 'react';
import { useHistory, Link, useRouteMatch } from 'react-router-dom';
import { t, Trans } from '@lingui/macro';
import { Formik, useFormikContext } from 'formik';
import {
  Alert,
  AlertGroup,
  Button,
  Form,
  Wizard,
  WizardContextConsumer,
  WizardFooter,
} from '@patternfly/react-core';
import { ConfigAPI, SettingsAPI, RootAPI } from 'api';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import ContentLoading from 'components/ContentLoading';
import ContentError from 'components/ContentError';
import { FormSubmitError } from 'components/FormField';
import { useConfig } from 'contexts/Config';
import SubscriptionStep from './SubscriptionStep';
import AnalyticsStep from './AnalyticsStep';
import EulaStep from './EulaStep';

const CustomFooter = ({ isSubmitLoading }) => {
  const { values, errors } = useFormikContext();
  const { me, license_info } = useConfig();
  const history = useHistory();

  return (
    <WizardFooter>
      <WizardContextConsumer>
        {({ activeStep, onNext, onBack }) => (
          <>
            {activeStep.id === 'eula-step' ? (
              <Button
                id="subscription-wizard-submit"
                aria-label={t`Submit`}
                variant="primary"
                onClick={onNext}
                isDisabled={
                  (!values.manifest_file && !values.subscription) ||
                  !me?.is_superuser ||
                  Object.keys(errors).length !== 0
                }
                type="button"
                ouiaId="subscription-wizard-submit"
                isLoading={isSubmitLoading}
              >
                <Trans>Submit</Trans>
              </Button>
            ) : (
              <Button
                id="subscription-wizard-next"
                ouiaId="subscription-wizard-next"
                variant="primary"
                onClick={onNext}
                type="button"
              >
                <Trans>Next</Trans>
              </Button>
            )}
            <Button
              id="subscription-wizard-back"
              variant="secondary"
              ouiaId="subscription-wizard-back"
              onClick={onBack}
              isDisabled={activeStep.id === 'subscription-step'}
              type="button"
            >
              <Trans>Back</Trans>
            </Button>
            {license_info?.valid_key && (
              <Button
                id="subscription-wizard-cancel"
                ouiaId="subscription-wizard-cancel"
                variant="link"
                aria-label={t`Cancel subscription edit`}
                onClick={() => history.push('/settings/subscription/details')}
              >
                <Trans>Cancel</Trans>
              </Button>
            )}
          </>
        )}
      </WizardContextConsumer>
    </WizardFooter>
  );
};

function SubscriptionEdit() {
  const history = useHistory();
  const { request: updateConfig, license_info } = useConfig();
  const hasValidKey = Boolean(license_info?.valid_key);
  const subscriptionMgmtRoute = useRouteMatch({
    path: '/subscription_management',
  });

  const {
    isLoading: isContentLoading,
    error: contentError,
    request: fetchContent,
    result: { brandName },
  } = useRequest(
    useCallback(async () => {
      const {
        data: { BRAND_NAME },
      } = await RootAPI.readAssetVariables();
      return {
        brandName: BRAND_NAME,
      };
    }, []),
    {
      brandName: null,
    }
  );

  useEffect(() => {
    if (subscriptionMgmtRoute && hasValidKey) {
      history.push('/settings/subscription/edit');
    }
    fetchContent();
  }, [fetchContent]); // eslint-disable-line react-hooks/exhaustive-deps

  const {
    error: submitError,
    isLoading: submitLoading,
    result: submitSuccessful,
    request: submitRequest,
  } = useRequest(
    useCallback(async (form) => {
      if (form.manifest_file) {
        await ConfigAPI.create({
          manifest: form.manifest_file,
        });
      } else if (form.subscription) {
        await ConfigAPI.attach({ pool_id: form.subscription.pool_id });
      }

      if (!hasValidKey) {
        if (form.pendo) {
          await SettingsAPI.updateCategory('ui', {
            PENDO_TRACKING_STATE: 'detailed',
          });
        } else {
          await SettingsAPI.updateCategory('ui', {
            PENDO_TRACKING_STATE: 'off',
          });
        }

        if (form.insights) {
          await SettingsAPI.updateCategory('system', {
            INSIGHTS_TRACKING_STATE: true,
          });
        } else {
          await SettingsAPI.updateCategory('system', {
            INSIGHTS_TRACKING_STATE: false,
          });
        }
      }

      await updateConfig();

      return true;
    }, []) // eslint-disable-line react-hooks/exhaustive-deps
  );

  useEffect(() => {
    if (submitSuccessful) {
      setTimeout(() => {
        history.push(
          subscriptionMgmtRoute ? '/home' : '/settings/subscription/details'
        );
      }, 3000);
    }
  }, [submitSuccessful, history, subscriptionMgmtRoute]);

  const { error, dismissError } = useDismissableError(submitError);
  const handleSubmit = async (values) => {
    dismissError();
    await submitRequest(values);
  };

  if (isContentLoading) {
    return <ContentLoading />;
  }

  if (contentError) {
    return <ContentError />;
  }

  const steps = [
    {
      name: hasValidKey
        ? t`Subscription Management`
        : `${brandName} ${t`Subscription`}`,
      id: 'subscription-step',
      component: <SubscriptionStep />,
    },
    ...(!hasValidKey
      ? [
          {
            name: t`User and Automation Analytics`,
            id: 'analytics-step',
            component: <AnalyticsStep />,
          },
        ]
      : []),
    {
      name: t`End user license agreement`,
      component: <EulaStep />,
      id: 'eula-step',
      nextButtonText: t`Submit`,
    },
  ];

  return (
    <>
      <Formik
        initialValues={{
          insights: true,
          manifest_file: null,
          manifest_filename: '',
          pendo: true,
          subscription: null,
          password: '',
          username: '',
        }}
        onSubmit={handleSubmit}
      >
        {(formik) => (
          <Form
            onSubmit={(e) => {
              e.preventDefault();
            }}
          >
            <Wizard
              steps={steps}
              onSave={formik.handleSubmit}
              footer={<CustomFooter isSubmitLoading={submitLoading} />}
              height="fit-content"
            />
            {error && (
              <div style={{ margin: '0 24px 24px 24px' }}>
                <FormSubmitError error={error} />
              </div>
            )}
          </Form>
        )}
      </Formik>
      <AlertGroup isToast>
        {submitSuccessful && (
          <Alert
            variant="success"
            title={t`Save successful!`}
            ouiaId="success-alert"
          >
            {subscriptionMgmtRoute ? (
              <Link to="/home">
                <Trans>Redirecting to dashboard</Trans>
              </Link>
            ) : (
              <Link to="/settings/subscription/details">
                <Trans>Redirecting to subscription detail</Trans>
              </Link>
            )}
          </Alert>
        )}
      </AlertGroup>
    </>
  );
}

export default SubscriptionEdit;
