import React, { useEffect } from 'react';

import { Trans, t } from '@lingui/macro';
import { useField } from 'formik';
import { Button, Flex, FormGroup } from '@patternfly/react-core';
import getDocsBaseUrl from 'util/getDocsBaseUrl';
import { required } from 'util/validators';
import FormField, { CheckboxField, PasswordField } from 'components/FormField';
import { useConfig } from 'contexts/Config';

const ANALYTICSLINK = 'https://www.ansible.com/products/automation-analytics';

function AnalyticsStep() {
  const config = useConfig();
  const [manifest] = useField('manifest_file');
  const [insights] = useField('insights');
  const [, , usernameHelpers] = useField('username');
  const [, , passwordHelpers] = useField('password');
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
          By default, we collect and transmit analytics data on the serice usage
          to Red Hat. There are two categories of data collected by the service.
          For more information, see{' '}
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
          aria-label={t`User analytics`}
          label={t`User analytics`}
          id="pendo-field"
          description={t`This data is used to enhance
                   future releases of the Tower Software and help
                   streamline customer experience and success.`}
        />
      </FormGroup>
      <FormGroup fieldId="insights">
        <CheckboxField
          name="insights"
          isDisabled={!config.me.is_superuser}
          aria-label={t`Insights for Ansible Automation Platform`}
          label={t`Insights for Ansible Automation Platform`}
          id="insights-field"
          description={t`This data is used to enhance
                   future releases of the Software and to provide
                   Insights for Ansible Automation Platform.`}
        />
      </FormGroup>
      {requireCredentialFields && (
        <>
          <br />
          <p>
            <Trans>
              Provide your Red Hat or Red Hat Satellite credentials to enable
              Insights for Ansible Automation Platform.
            </Trans>
          </p>
          <FormField
            id="username-field"
            isDisabled={!config.me.is_superuser}
            isRequired={requireCredentialFields}
            label={t`Username`}
            name="username"
            type="text"
            validate={required(null)}
          />
          <PasswordField
            id="password-field"
            isDisabled={!config.me.is_superuser}
            isRequired={requireCredentialFields}
            label={t`Password`}
            name="password"
            validate={required(null)}
          />
        </>
      )}
      <Flex alignItems={{ default: 'alignItemsCenter' }}>
        <img
          width="300"
          src="/static/media/insights-analytics-dashboard.jpeg"
          alt={t`Insights for Ansible Automation Platform dashboard`}
        />
        <Button
          component="a"
          href={ANALYTICSLINK}
          target="_blank"
          variant="secondary"
          ouiaId="analytics-link"
        >
          <Trans>
            Learn more about Insights for Ansible Automation Platform
          </Trans>
        </Button>
      </Flex>
    </Flex>
  );
}
export default AnalyticsStep;
