import React, { useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import { CredentialsAPI } from '../../../../../api';
import CheckboxListItem from '../../../../../components/CheckboxListItem';
import ContentError from '../../../../../components/ContentError';
import DataListToolbar from '../../../../../components/DataListToolbar';
import PaginatedDataList from '../../../../../components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '../../../../../util/qs';
import useRequest from '../../../../../util/useRequest';

const QS_CONFIG = getQSConfig('credential', {
  page: 1,
  page_size: 5,
  order_by: 'name',
  credential_type__kind: 'external',
});

function CredentialsStep({ i18n }) {
  const [selectedCredential, , selectedCredentialHelper] = useField(
    'credential'
  );
  const history = useHistory();

  const {
    result: { credentials, count, relatedSearchableKeys, searchableKeys },
    error: credentialsError,
    isLoading: isCredentialsLoading,
    request: fetchCredentials,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, history.location.search);
      const [{ data }, actionsResponse] = await Promise.all([
        CredentialsAPI.read({ ...params }),
        CredentialsAPI.readOptions(),
      ]);
      return {
        credentials: data.results,
        count: data.count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          actionsResponse.data.actions?.GET || {}
        ).filter(key => actionsResponse.data.actions?.GET[key].filterable),
      };
    }, [history.location.search]),
    { credentials: [], count: 0, relatedSearchableKeys: [], searchableKeys: [] }
  );

  useEffect(() => {
    fetchCredentials();
  }, [fetchCredentials]);

  if (credentialsError) {
    return <ContentError error={credentialsError} />;
  }

  return (
    <PaginatedDataList
      contentError={credentialsError}
      hasContentLoading={isCredentialsLoading}
      itemCount={count}
      items={credentials}
      onRowClick={row => selectedCredentialHelper.setValue(row)}
      qsConfig={QS_CONFIG}
      renderItem={credential => (
        <CheckboxListItem
          isSelected={selectedCredential?.value?.id === credential.id}
          itemId={credential.id}
          key={credential.id}
          name={credential.name}
          label={credential.name}
          onSelect={() => selectedCredentialHelper.setValue(credential)}
          onDeselect={() => selectedCredentialHelper.setValue(null)}
          isRadio
        />
      )}
      renderToolbar={props => <DataListToolbar {...props} fillWidth />}
      showPageSizeOptions={false}
      toolbarSearchColumns={[
        {
          name: i18n._(t`Name`),
          key: 'name__icontains',
          isDefault: true,
        },
        {
          name: i18n._(t`Created By (Username)`),
          key: 'created_by__username__icontains',
        },
        {
          name: i18n._(t`Modified By (Username)`),
          key: 'modified_by__username__icontains',
        },
      ]}
      toolbarSortColumns={[
        {
          name: i18n._(t`Name`),
          key: 'name',
        },
      ]}
      toolbarSearchableKeys={searchableKeys}
      toolbarRelatedSearchableKeys={relatedSearchableKeys}
    />
  );
}

export default withI18n()(CredentialsStep);
