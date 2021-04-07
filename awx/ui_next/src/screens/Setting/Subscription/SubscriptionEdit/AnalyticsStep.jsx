import React, { useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';
import { useField } from 'formik';
import { Button, Flex, FormGroup } from '@patternfly/react-core';
import getDocsBaseUrl from '../../../../util/getDocsBaseUrl';
import { required } from '../../../../util/validators';
import FormField, {
  CheckboxField,
  PasswordField,
} from '../../../../components/FormField';
import { useConfig } from '../../../../contexts/Config';

const ANALYTICSLINK = 'https://www.ansible.com/products/automation-analytics';

function AnalyticsStep({ i18n }) {
  const config = useConfig();
  const [manifest] = useField({
    name: 'manifest_file',
  });
  const [insights] = useField({
    name: 'insights',
  });
  const [, , usernameHelpers] = useField({
    name: 'username',
  });
  const [, , passwordHelpers] = useField({
    name: 'password',
  });
  const requireCredentialFields = manifest.value && insights.value;

  useEffect(() => {
    if (!requireCredentialFields) {
      usernameHelpers.setValue('');
      passwordHelpers.setValue('');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requireCredentialFields]);

  return (
    <Flex
      spaceItems={{ default: 'spaceItemsMd' }}
      direction={{ default: 'column' }}
    >
      <Trans>User and Insights analytics</Trans>
      <p>
        <Trans>
          By default, Tower collects and transmits analytics data on Tower usage
          to Red Hat. There are two categories of data collected by Tower. For
          more information, see{' '}
          <Button
            component="a"
            href={`${getDocsBaseUrl(
              config
            )}/html/installandreference/user-data.html#index-0`}
            variant="link"
            isInline
            ouiaId="tower-documentation-link"
            target="_blank"
          >
            this Tower documentation page
          </Button>
          . Uncheck the following boxes to disable this feature.
        </Trans>
      </p>
      <FormGroup fieldId="pendo">
        <CheckboxField
          name="pendo"
          isDisabled={!config.me.is_superuser}
          aria-label={i18n._(t`User analytics`)}
          label={i18n._(t`User analytics`)}
          id="pendo-field"
          description={i18n._(t`This data is used to enhance
                   future releases of the Tower Software and help
                   streamline customer experience and success.`)}
        />
      </FormGroup>
      <FormGroup fieldId="insights">
        <CheckboxField
          name="insights"
          isDisabled={!config.me.is_superuser}
          aria-label={i18n._(t`Insights analytics`)}
          label={i18n._(t`Insights Analytics`)}
          id="insights-field"
          description={i18n._(t`This data is used to enhance
                   future releases of the Tower Software and to provide
                   Insights Analytics to Tower subscribers.`)}
        />
      </FormGroup>
      {requireCredentialFields && (
        <>
          <br />
          <p>
            <Trans>
              Provide your Red Hat or Red Hat Satellite credentials to enable
              Insights Analytics.
            </Trans>
          </p>
          <FormField
            id="username-field"
            isDisabled={!config.me.is_superuser}
            isRequired={requireCredentialFields}
            label={i18n._(t`Username`)}
            name="username"
            type="text"
            validate={required(null, i18n)}
          />
          <PasswordField
            id="password-field"
            isDisabled={!config.me.is_superuser}
            isRequired={requireCredentialFields}
            label={i18n._(t`Password`)}
            name="password"
            validate={required(null, i18n)}
          />
        </>
      )}
      <Flex alignItems={{ default: 'alignItemsCenter' }}>
        <img
          width="300"
          src="/static/media/insights-analytics-dashboard.jpeg"
          alt={i18n._(t`Insights Analytics dashboard`)}
        />
        <Button
          component="a"
          href={ANALYTICSLINK}
          target="_blank"
          variant="secondary"
          ouiaId="analytics-link"
        >
          <Trans>Learn more about Insights Analytics</Trans>
        </Button>
      </Flex>
    </Flex>
  );
}
export default withI18n()(AnalyticsStep);
