import React, { useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';

import { t } from '@lingui/macro';
import { useField } from 'formik';
import { CredentialsAPI } from 'api';
import CheckboxListItem from 'components/CheckboxListItem';
import ContentError from 'components/ContentError';
import DataListToolbar from 'components/DataListToolbar';
import { getQSConfig, parseQueryString } from 'util/qs';
import useRequest from 'hooks/useRequest';
import PaginatedTable, {
  HeaderCell,
  HeaderRow,
  getSearchableKeys,
} from 'components/PaginatedTable';

const QS_CONFIG = getQSConfig('credential', {
  page: 1,
  page_size: 5,
  order_by: 'name',
  credential_type__kind: 'external',
});

function CredentialsStep() {
  const [selectedCredential, , selectedCredentialHelper] =
    useField('credential');
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
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
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
    <PaginatedTable
      contentError={credentialsError}
      hasContentLoading={isCredentialsLoading}
      itemCount={count}
      items={credentials}
      qsConfig={QS_CONFIG}
      headerRow={
        <HeaderRow isExpandable={false} qsConfig={QS_CONFIG}>
          <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
        </HeaderRow>
      }
      renderRow={(credential, index) => (
        <CheckboxListItem
          rowIndex={index}
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
      renderToolbar={(props) => <DataListToolbar {...props} fillWidth />}
      showPageSizeOptions={false}
      toolbarSearchColumns={[
        {
          name: t`Name`,
          key: 'name__icontains',
          isDefault: true,
        },
        {
          name: t`Created By (Username)`,
          key: 'created_by__username__icontains',
        },
        {
          name: t`Modified By (Username)`,
          key: 'modified_by__username__icontains',
        },
      ]}
      toolbarSearchableKeys={searchableKeys}
      toolbarRelatedSearchableKeys={relatedSearchableKeys}
    />
  );
}

export default CredentialsStep;
