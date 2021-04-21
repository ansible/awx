import React, { useCallback, useEffect } from 'react';
import { useHistory, Link, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
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
import { ConfigAPI, SettingsAPI, MeAPI, RootAPI } from '../../../../api';
import useRequest, { useDismissableError } from '../../../../util/useRequest';
import ContentLoading from '../../../../components/ContentLoading';
import ContentError from '../../../../components/ContentError';
import { FormSubmitError } from '../../../../components/FormField';
import { useConfig } from '../../../../contexts/Config';
import issuePendoIdentity from './pendoUtils';
import SubscriptionStep from './SubscriptionStep';
import AnalyticsStep from './AnalyticsStep';
import EulaStep from './EulaStep';

const CustomFooter = withI18n()(({ i18n, isSubmitLoading }) => {
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
                aria-label={i18n._(t`Submit`)}
                variant="primary"
                onClick={onNext}
                isDisabled={
                  (!values.manifest_file && !values.subscription) ||
                  !me?.is_superuser ||
                  !values.eula ||
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
                aria-label={i18n._(t`Cancel subscription edit`)}
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
});

function SubscriptionEdit({ i18n }) {
  const history = useHistory();
  const { license_info, setConfig } = useConfig();
  const hasValidKey = Boolean(license_info?.valid_key);
  const subscriptionMgmtRoute = useRouteMatch({
    path: '/subscription_management',
  });

  const {
    isLoading: isContentLoading,
    error: contentError,
    request: fetchContent,
    result: { brandName, pendoApiKey },
  } = useRequest(
    useCallback(async () => {
      const {
        data: { BRAND_NAME, PENDO_API_KEY },
      } = await RootAPI.readAssetVariables();
      return {
        brandName: BRAND_NAME,
        pendoApiKey: PENDO_API_KEY,
      };
    }, []),
    {
      brandName: null,
      pendoApiKey: null,
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
    useCallback(async form => {
      if (form.manifest_file) {
        await ConfigAPI.create({
          manifest: form.manifest_file,
          eula_accepted: form.eula,
        });
      } else if (form.subscription) {
        await ConfigAPI.attach({ pool_id: form.subscription.pool_id });
        await ConfigAPI.create({
          eula_accepted: form.eula,
        });
      }

      const [
        { data },
        {
          data: {
            results: [me],
          },
        },
      ] = await Promise.all([ConfigAPI.read(), MeAPI.read()]);
      const newConfig = { ...data, me };
      setConfig(newConfig);

      if (!hasValidKey) {
        if (form.pendo) {
          await SettingsAPI.updateCategory('ui', {
            PENDO_TRACKING_STATE: 'detailed',
          });
          await issuePendoIdentity(newConfig, pendoApiKey);
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
  const handleSubmit = async values => {
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
        ? i18n._(t`Subscription Management`)
        : `${brandName} ${i18n._(t`Subscription`)}`,
      id: 'subscription-step',
      component: <SubscriptionStep />,
    },
    ...(!hasValidKey
      ? [
          {
            name: i18n._(t`User and Insights analytics`),
            id: 'analytics-step',
            component: <AnalyticsStep />,
          },
        ]
      : []),
    {
      name: i18n._(t`End user license agreement`),
      component: <EulaStep />,
      id: 'eula-step',
      nextButtonText: i18n._(t`Submit`),
    },
  ];

  return (
    <>
      <Formik
        initialValues={{
          eula: false,
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
        {formik => (
          <Form
            onSubmit={e => {
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
            title={i18n._(t`Save successful!`)}
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

export default withI18n()(SubscriptionEdit);
