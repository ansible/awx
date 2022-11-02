import React, { useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { t, Plural } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';
import { CredentialsAPI } from 'api';
import useSelected from 'hooks/useSelected';
import useToast, { AlertVariant } from 'hooks/useToast';
import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import DataListToolbar from 'components/DataListToolbar';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
  ToolbarAddButton,
  ToolbarDeleteButton,
  getSearchableKeys,
} from 'components/PaginatedTable';
import useRequest, { useDeleteItems } from 'hooks/useRequest';
import { getQSConfig, parseQueryString } from 'util/qs';
import { relatedResourceDeleteRequests } from 'util/getRelatedResourceDeleteDetails';
import CredentialListItem from './CredentialListItem';

const QS_CONFIG = getQSConfig('credential', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function CredentialList() {
  const location = useLocation();
  const { addToast, Toast, toastProps } = useToast();

  const {
    result: {
      credentials,
      credentialCount,
      actions,
      relatedSearchableKeys,
      searchableKeys,
    },
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
      const searchKeys = getSearchableKeys(credActions.data.actions?.GET);
      if (credActions.data.actions?.GET.type) {
        searchKeys.push({ key: 'credential_type__kind', type: 'string' });
      }
      return {
        credentials: creds.data.results,
        credentialCount: creds.data.count,
        actions: credActions.data.actions,
        relatedSearchableKeys: (
          credActions?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: searchKeys,
      };
    }, [location]),
    {
      credentials: [],
      credentialCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchCredentials();
  }, [fetchCredentials]);

  const {
    selected,
    isAllSelected,
    handleSelect,
    setSelected,
    selectAll,
    clearSelected,
  } = useSelected(credentials);

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteCredentials,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(
      () => Promise.all(selected.map(({ id }) => CredentialsAPI.destroy(id))),
      [selected]
    ),
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

  const handleCopy = useCallback(
    (newCredentialId) => {
      addToast({
        id: newCredentialId,
        title: t`Credential copied successfully`,
        variant: AlertVariant.success,
        hasTimeout: true,
      });
    },
    [addToast]
  );

  const canAdd =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');
  const deleteDetailsRequests = relatedResourceDeleteRequests.credential(
    selected[0]
  );
  return (
    <>
      <PageSection>
        <Card>
          <PaginatedTable
            contentError={contentError}
            hasContentLoading={isLoading || isDeleteLoading}
            items={credentials}
            itemCount={credentialCount}
            qsConfig={QS_CONFIG}
            clearSelected={clearSelected}
            toolbarSearchableKeys={searchableKeys}
            toolbarRelatedSearchableKeys={relatedSearchableKeys}
            toolbarSearchColumns={[
              {
                name: t`Name`,
                key: 'name__icontains',
                isDefault: true,
              },
              {
                name: t`Description`,
                key: 'description__icontains',
              },
              {
                name: t`Created By (Username)`,
                key: 'created_by__username__icontains',
              },
              {
                name: t`Modified By (Username)`,
                key: 'modified_by__username__icontains',
              },
              {
                name: t`Credential Type`,
                key: 'credential_type__search',
              },
            ]}
            headerRow={
              <HeaderRow qsConfig={QS_CONFIG}>
                <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
                <HeaderCell>{t`Type`}</HeaderCell>
                <HeaderCell>{t`Actions`}</HeaderCell>
              </HeaderRow>
            }
            renderRow={(item, index) => (
              <CredentialListItem
                key={item.id}
                credential={item}
                fetchCredentials={fetchCredentials}
                detailUrl={`/credentials/${item.id}/details`}
                isSelected={selected.some((row) => row.id === item.id)}
                onSelect={() => handleSelect(item)}
                onCopy={handleCopy}
                rowIndex={index}
              />
            )}
            renderToolbar={(props) => (
              <DataListToolbar
                {...props}
                isAllSelected={isAllSelected}
                onSelectAll={selectAll}
                qsConfig={QS_CONFIG}
                additionalControls={[
                  ...(canAdd
                    ? [<ToolbarAddButton key="add" linkTo="/credentials/add" />]
                    : []),
                  <ToolbarDeleteButton
                    key="delete"
                    onDelete={handleDelete}
                    itemsToDelete={selected}
                    pluralizedItemName={t`Credentials`}
                    deleteDetailsRequests={deleteDetailsRequests}
                    deleteMessage={
                      <Plural
                        value={selected.length}
                        one="This credential is currently being used by other resources. Are you sure you want to delete it?"
                        other="Deleting these credentials could impact other resources that rely on them. Are you sure you want to delete anyway?"
                      />
                    }
                  />,
                ]}
              />
            )}
          />
        </Card>
        <AlertModal
          aria-label={t`Deletion Error`}
          isOpen={deletionError}
          variant="error"
          title={t`Error!`}
          onClose={clearDeletionError}
        >
          {t`Failed to delete one or more credentials.`}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      </PageSection>
      <Toast {...toastProps} />
    </>
  );
}

export default CredentialList;
