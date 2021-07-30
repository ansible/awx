import React, { useEffect, useCallback } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';

import { t, Plural } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';

import { CredentialTypesAPI } from 'api';
import { getQSConfig, parseQueryString } from 'util/qs';
import useRequest, { useDeleteItems } from 'hooks/useRequest';
import useSelected from 'hooks/useSelected';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
  ToolbarDeleteButton,
  ToolbarAddButton,
  getSearchableKeys,
} from 'components/PaginatedTable';
import ErrorDetail from 'components/ErrorDetail';
import AlertModal from 'components/AlertModal';
import DatalistToolbar from 'components/DataListToolbar';
import { relatedResourceDeleteRequests } from 'util/getRelatedResourceDeleteDetails';
import CredentialTypeListItem from './CredentialTypeListItem';

const QS_CONFIG = getQSConfig('credential-type', {
  page: 1,
  page_size: 20,
  managed: false,
});

function CredentialTypeList() {
  const location = useLocation();
  const match = useRouteMatch();

  const {
    error: contentError,
    isLoading,
    request: fetchCredentialTypes,
    result: {
      credentialTypes,
      credentialTypesCount,
      actions,
      relatedSearchableKeys,
      searchableKeys,
    },
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);

      const [response, responseActions] = await Promise.all([
        CredentialTypesAPI.read(params),
        CredentialTypesAPI.readOptions(),
      ]);

      return {
        credentialTypes: response.data.results,
        credentialTypesCount: response.data.count,
        actions: responseActions.data.actions,
        relatedSearchableKeys: (
          responseActions?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(responseActions.data.actions?.GET),
      };
    }, [location]),
    {
      credentialTypes: [],
      credentialTypesCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchCredentialTypes();
  }, [fetchCredentialTypes]);

  const { selected, isAllSelected, handleSelect, clearSelected, selectAll } =
    useSelected(credentialTypes);

  const {
    isLoading: deleteLoading,
    deletionError,
    deleteItems: deleteCredentialTypes,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(
      () =>
        Promise.all(selected.map(({ id }) => CredentialTypesAPI.destroy(id))),
      [selected]
    ),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchCredentialTypes,
    }
  );

  const handleDelete = async () => {
    await deleteCredentialTypes();
    clearSelected();
  };

  const canAdd = actions && actions.POST;

  const deleteDetailsRequests = relatedResourceDeleteRequests.credentialType(
    selected[0]
  );

  return (
    <>
      <PageSection>
        <Card>
          <PaginatedTable
            contentError={contentError}
            hasContentLoading={isLoading || deleteLoading}
            items={credentialTypes}
            itemCount={credentialTypesCount}
            pluralizedItemName={t`Credential Types`}
            qsConfig={QS_CONFIG}
            clearSelected={clearSelected}
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
            ]}
            toolbarSearchableKeys={searchableKeys}
            toolbarRelatedSearchableKeys={relatedSearchableKeys}
            renderToolbar={(props) => (
              <DatalistToolbar
                {...props}
                isAllSelected={isAllSelected}
                onSelectAll={selectAll}
                qsConfig={QS_CONFIG}
                additionalControls={[
                  ...(canAdd
                    ? [
                        <ToolbarAddButton
                          key="add"
                          linkTo={`${match.url}/add`}
                        />,
                      ]
                    : []),
                  <ToolbarDeleteButton
                    key="delete"
                    onDelete={handleDelete}
                    itemsToDelete={selected}
                    pluralizedItemName={t`Credential Types`}
                    deleteDetailsRequests={deleteDetailsRequests}
                    deleteMessage={
                      <Plural
                        value={selected.length}
                        one="This credential type is currently being used by some credentials and cannot be deleted."
                        other="Credential types that are being used by credentials cannot be deleted. Are you sure you want to delete anyway?"
                      />
                    }
                  />,
                ]}
              />
            )}
            headerRow={
              <HeaderRow qsConfig={QS_CONFIG}>
                <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
                <HeaderCell>{t`Actions`}</HeaderCell>
              </HeaderRow>
            }
            renderRow={(credentialType, index) => (
              <CredentialTypeListItem
                key={credentialType.id}
                value={credentialType.name}
                credentialType={credentialType}
                detailUrl={`${match.url}/${credentialType.id}/details`}
                onSelect={() => handleSelect(credentialType)}
                isSelected={selected.some(
                  (row) => row.id === credentialType.id
                )}
                rowIndex={index}
              />
            )}
            emptyStateControls={
              canAdd && (
                <ToolbarAddButton key="add" linkTo={`${match.url}/add`} />
              )
            }
          />
        </Card>
      </PageSection>
      <AlertModal
        aria-label={t`Deletion error`}
        isOpen={deletionError}
        onClose={clearDeletionError}
        title={t`Error`}
        variant="error"
      >
        {t`Failed to delete one or more credential types.`}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </>
  );
}

export default CredentialTypeList;
