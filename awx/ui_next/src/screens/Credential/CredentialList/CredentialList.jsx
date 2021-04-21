import React, { useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';
import { CredentialsAPI } from '../../../api';
import useSelected from '../../../util/useSelected';
import AlertModal from '../../../components/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail';
import DataListToolbar from '../../../components/DataListToolbar';
import {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '../../../components/PaginatedDataList';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
} from '../../../components/PaginatedTable';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import CredentialListItem from './CredentialListItem';
import { relatedResourceDeleteRequests } from '../../../util/getRelatedResourceDeleteDetails';

const QS_CONFIG = getQSConfig('credential', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function CredentialList({ i18n }) {
  const location = useLocation();
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
      const searchKeys = Object.keys(
        credActions.data.actions?.GET || {}
      ).filter(key => credActions.data.actions?.GET[key].filterable);
      const item = searchKeys.indexOf('type');
      if (item) {
        searchKeys[item] = 'credential_type__kind';
      }
      return {
        credentials: creds.data.results,
        credentialCount: creds.data.count,
        actions: credActions.data.actions,
        relatedSearchableKeys: (
          credActions?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
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

  const { selected, isAllSelected, handleSelect, setSelected } = useSelected(
    credentials
  );

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteCredentials,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(() => {
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

  const canAdd =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');
  const deleteDetailsRequests = relatedResourceDeleteRequests.credential(
    selected[0]
  );
  return (
    <PageSection>
      <Card>
        <PaginatedTable
          contentError={contentError}
          hasContentLoading={isLoading || isDeleteLoading}
          items={credentials}
          itemCount={credentialCount}
          qsConfig={QS_CONFIG}
          onRowClick={handleSelect}
          toolbarSearchableKeys={searchableKeys}
          toolbarRelatedSearchableKeys={relatedSearchableKeys}
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
          headerRow={
            <HeaderRow qsConfig={QS_CONFIG}>
              <HeaderCell sortKey="name">{i18n._(t`Name`)}</HeaderCell>
              <HeaderCell>{i18n._(t`Type`)}</HeaderCell>
              <HeaderCell alignRight>{i18n._(t`Actions`)}</HeaderCell>
            </HeaderRow>
          }
          renderRow={(item, index) => (
            <CredentialListItem
              key={item.id}
              credential={item}
              fetchCredentials={fetchCredentials}
              detailUrl={`/credentials/${item.id}/details`}
              isSelected={selected.some(row => row.id === item.id)}
              onSelect={() => handleSelect(item)}
              rowIndex={index}
            />
          )}
          renderToolbar={props => (
            <DataListToolbar
              {...props}
              showSelectAll
              isAllSelected={isAllSelected}
              onSelectAll={isSelected =>
                setSelected(isSelected ? [...credentials] : [])
              }
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
                  deleteDetailsRequests={deleteDetailsRequests}
                  deleteMessage={i18n._(
                    '{numItemsToDelete, plural, one {This credential is currently being used by other resources. Are you sure you want to delete it?} other {Deleting these credentials could impact other resources that rely on them. Are you sure you want to delete anyway?}}',
                    { numItemsToDelete: selected.length }
                  )}
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
