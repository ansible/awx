import React, { useEffect, useCallback } from 'react';
import { useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import { Form, FormGroup } from '@patternfly/react-core';
import { CredentialsAPI } from '../../api';

import { getQSConfig, parseQueryString, mergeParams } from '../../util/qs';
import useRequest from '../../util/useRequest';
import ContentError from '../ContentError';
import ContentLoading from '../ContentLoading';
import { required } from '../../util/validators';
import OptionsList from '../OptionsList';

const QS_CONFIG = getQSConfig('credentials', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function AdHocCredentialStep({ i18n, credentialTypeId, onEnableLaunch }) {
  const history = useHistory();
  const {
    error,
    isLoading,
    request: fetchCredentials,
    result: { credentials, credentialCount },
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, history.location.search);

      const {
        data: { results, count },
      } = await CredentialsAPI.read(
        mergeParams(params, { credential_type: credentialTypeId })
      );

      return {
        credentials: results,
        credentialCount: count,
      };
    }, [credentialTypeId, history.location.search]),
    { credentials: [], credentialCount: 0 }
  );

  useEffect(() => {
    fetchCredentials();
  }, [fetchCredentials]);

  const [credentialField, credentialMeta, credentialHelpers] = useField({
    name: 'credential',
    validate: required(null, i18n),
  });
  if (error) {
    return <ContentError error={error} />;
  }
  if (isLoading) {
    return <ContentLoading error={error} />;
  }
  return (
    <Form>
      <FormGroup
        fieldId="credential"
        label={i18n._(t`Machine Credential`)}
        isRequired
        validated={
          !credentialMeta.touched || !credentialMeta.error ? 'default' : 'error'
        }
        helperTextInvalid={credentialMeta.error}
      >
        <OptionsList
          value={credentialField.value || []}
          options={credentials}
          optionCount={credentialCount}
          header={i18n._(t`Machine Credential`)}
          readOnly
          qsConfig={QS_CONFIG}
          searchColumns={[
            {
              name: i18n._(t`Name`),
              key: 'name',
              isDefault: true,
            },
            {
              name: i18n._(t`Created By (Username)`),
              key: 'created_by__username',
            },
            {
              name: i18n._(t`Modified By (Username)`),
              key: 'modified_by__username',
            },
          ]}
          sortColumns={[
            {
              name: i18n._(t`Name`),
              key: 'name',
            },
          ]}
          name="credential"
          selectItem={value => {
            credentialHelpers.setValue([value]);
            onEnableLaunch();
          }}
          deselectItem={() => {
            credentialHelpers.setValue([]);
          }}
        />
      </FormGroup>
    </Form>
  );
}

export default withI18n()(AdHocCredentialStep);
