import React, { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';
import { CredentialsAPI } from '../../../api';
import AlertModal from '../../../components/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail';
import DataListToolbar from '../../../components/DataListToolbar';
import PaginatedDataList, {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '../../../components/PaginatedDataList';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import CredentialListItem from './CredentialListItem';

const QS_CONFIG = getQSConfig('credential', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function CredentialList({ i18n }) {
  const [selected, setSelected] = useState([]);
  const location = useLocation();

  const {
    result: { credentials, credentialCount, actions },
    error: contentError,
    isLoading,
    request: fetchCredentials,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [creds, credActions] = await Promise.all([
        CredentialsAPI.read(params),
        CredentialsAPI.readOptions(),
      ]);
      return {
        credentials: creds.data.results,
        credentialCount: creds.data.count,
        actions: credActions.data.actions,
      };
    }, [location]),
    {
      credentials: [],
      credentialCount: 0,
      actions: {},
    }
  );

  useEffect(() => {
    fetchCredentials();
  }, [fetchCredentials]);

  const isAllSelected =
    selected.length > 0 && selected.length === credentials.length;
  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteCredentials,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(async () => {
      return Promise.all(selected.map(({ id }) => CredentialsAPI.destroy(id)));
    }, [selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchCredentials,
    }
  );

  const handleDelete = async () => {
    await deleteCredentials();
    setSelected([]);
  };

  const handleSelectAll = isSelected => {
    setSelected(isSelected ? [...credentials] : []);
  };

  const handleSelect = row => {
    if (selected.some(s => s.id === row.id)) {
      setSelected(selected.filter(s => s.id !== row.id));
    } else {
      setSelected(selected.concat(row));
    }
  };

  const canAdd =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');

  return (
    <PageSection>
      <Card>
        <PaginatedDataList
          contentError={contentError}
          hasContentLoading={isLoading || isDeleteLoading}
          items={credentials}
          itemCount={credentialCount}
          qsConfig={QS_CONFIG}
          onRowClick={handleSelect}
          toolbarSearchColumns={[
            {
              name: i18n._(t`Name`),
              key: 'name__icontains',
              isDefault: true,
            },
            {
              name: i18n._(t`Description`),
              key: 'description__icontains',
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
          renderItem={item => (
            <CredentialListItem
              key={item.id}
              credential={item}
              fetchCredentials={fetchCredentials}
              detailUrl={`/credentials/${item.id}/details`}
              isSelected={selected.some(row => row.id === item.id)}
              onSelect={() => handleSelect(item)}
            />
          )}
          renderToolbar={props => (
            <DataListToolbar
              {...props}
              showSelectAll
              isAllSelected={isAllSelected}
              onSelectAll={handleSelectAll}
              qsConfig={QS_CONFIG}
              additionalControls={[
                ...(canAdd
                  ? [<ToolbarAddButton key="add" linkTo="/credentials/add" />]
                  : []),
                <ToolbarDeleteButton
                  key="delete"
                  onDelete={handleDelete}
                  itemsToDelete={selected}
                  pluralizedItemName={i18n._(t`Credentials`)}
                />,
              ]}
            />
          )}
        />
      </Card>
      <AlertModal
        aria-label={i18n._(t`Deletion Error`)}
        isOpen={deletionError}
        variant="error"
        title={i18n._(t`Error!`)}
        onClose={clearDeletionError}
      >
        {i18n._(t`Failed to delete one or more credentials.`)}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </PageSection>
  );
}

export default withI18n()(CredentialList);
