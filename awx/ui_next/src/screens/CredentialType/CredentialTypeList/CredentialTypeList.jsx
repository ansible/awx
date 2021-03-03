import React, { useEffect, useCallback } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';

import { CredentialTypesAPI } from '../../../api';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import useSelected from '../../../util/useSelected';
import {
  ToolbarDeleteButton,
  ToolbarAddButton,
} from '../../../components/PaginatedDataList';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
} from '../../../components/PaginatedTable';
import ErrorDetail from '../../../components/ErrorDetail';
import AlertModal from '../../../components/AlertModal';
import DatalistToolbar from '../../../components/DataListToolbar';

import CredentialTypeListItem from './CredentialTypeListItem';

const QS_CONFIG = getQSConfig('credential-type', {
  page: 1,
  page_size: 20,
  managed_by_tower: false,
});

function CredentialTypeList({ i18n }) {
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
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          responseActions.data.actions?.GET || {}
        ).filter(key => responseActions.data.actions?.GET[key].filterable),
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

  const { selected, isAllSelected, handleSelect, setSelected } = useSelected(
    credentialTypes
  );

  const {
    isLoading: deleteLoading,
    deletionError,
    deleteItems: deleteCredentialTypes,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(() => {
      return Promise.all(
        selected.map(({ id }) => CredentialTypesAPI.destroy(id))
      );
    }, [selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchCredentialTypes,
    }
  );

  const handleDelete = async () => {
    await deleteCredentialTypes();
    setSelected([]);
  };

  const canAdd = actions && actions.POST;

  return (
    <>
      <PageSection>
        <Card>
          <PaginatedTable
            contentError={contentError}
            hasContentLoading={isLoading || deleteLoading}
            items={credentialTypes}
            itemCount={credentialTypesCount}
            pluralizedItemName={i18n._(t`Credential Types`)}
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
            toolbarSearchableKeys={searchableKeys}
            toolbarRelatedSearchableKeys={relatedSearchableKeys}
            renderToolbar={props => (
              <DatalistToolbar
                {...props}
                showSelectAll
                isAllSelected={isAllSelected}
                onSelectAll={isSelected =>
                  setSelected(isSelected ? [...credentialTypes] : [])
                }
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
                    pluralizedItemName={i18n._(t`Credential Types`)}
                  />,
                ]}
              />
            )}
            headerRow={
              <HeaderRow qsConfig={QS_CONFIG}>
                <HeaderCell sortKey="name">{i18n._(t`Name`)}</HeaderCell>
                <HeaderCell>{i18n._(t`Actions`)}</HeaderCell>
              </HeaderRow>
            }
            renderRow={(credentialType, index) => (
              <CredentialTypeListItem
                key={credentialType.id}
                value={credentialType.name}
                credentialType={credentialType}
                detailUrl={`${match.url}/${credentialType.id}/details`}
                onSelect={() => handleSelect(credentialType)}
                isSelected={selected.some(row => row.id === credentialType.id)}
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
        aria-label={i18n._(t`Deletion error`)}
        isOpen={deletionError}
        onClose={clearDeletionError}
        title={i18n._(t`Error`)}
        variant="error"
      >
        {i18n._(t`Failed to delete one or more credential types.`)}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </>
  );
}

export default withI18n()(CredentialTypeList);
