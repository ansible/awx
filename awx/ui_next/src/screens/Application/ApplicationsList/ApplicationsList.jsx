import React, { useCallback, useEffect } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { useLocation, useRouteMatch } from 'react-router-dom';

import { Card, PageSection } from '@patternfly/react-core';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import ErrorDetail from '../../../components/ErrorDetail';
import AlertModal from '../../../components/AlertModal';

import DatalistToolbar from '../../../components/DataListToolbar';
import { ApplicationsAPI } from '../../../api';
import PaginatedDataList, {
  ToolbarDeleteButton,
  ToolbarAddButton,
} from '../../../components/PaginatedDataList';
import useSelected from '../../../util/useSelected';

import ApplicationListItem from './ApplicationListItem';

const QS_CONFIG = getQSConfig('applications', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});
function ApplicationsList({ i18n }) {
  const location = useLocation();
  const match = useRouteMatch();

  const {
    isLoading,
    error,
    request: fetchApplications,
    result: { applications, itemCount, actions },
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);

      const [response, actionsResponse] = await Promise.all([
        ApplicationsAPI.read(params),
        ApplicationsAPI.readOptions(),
      ]);

      return {
        applications: response.data.results,
        itemCount: response.data.count,
        actions: actionsResponse.data.actions,
      };
    }, [location]),
    {
      applications: [],
      itemCount: 0,
      actions: {},
    }
  );

  useEffect(() => {
    fetchApplications();
  }, [fetchApplications]);

  const { selected, isAllSelected, handleSelect, setSelected } = useSelected(
    applications
  );

  const {
    isLoading: deleteLoading,
    deletionError,
    deleteItems: handleDeleteApplications,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(async () => {
      await Promise.all(selected.map(({ id }) => ApplicationsAPI.destroy(id)));
    }, [selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchApplications,
    }
  );

  const handleDelete = async () => {
    await handleDeleteApplications();
    setSelected([]);
  };

  const canAdd = actions && actions.POST;

  return (
    <>
      <PageSection>
        <Card>
          <PaginatedDataList
            contentError={error}
            hasContentLoading={isLoading || deleteLoading}
            items={applications}
            itemCount={itemCount}
            pluralizedItemName={i18n._(t`Applications`)}
            qsConfig={QS_CONFIG}
            onRowClick={handleSelect}
            toolbarSearchColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
                isDefault: true,
              },
              {
                name: i18n._(t`Description`),
                key: 'description',
              },
            ]}
            toolbarSortColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
              },
              {
                name: i18n._(t`Created`),
                key: 'created',
              },
              {
                name: i18n._(t`Organization`),
                key: 'organization',
              },
              {
                name: i18n._(t`Description`),
                key: 'description',
              },
            ]}
            renderToolbar={props => (
              <DatalistToolbar
                {...props}
                showSelectAll
                isAllSelected={isAllSelected}
                onSelectAll={isSelected =>
                  setSelected(isSelected ? [...applications] : [])
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
                    pluralizedItemName={i18n._(t`Applications`)}
                  />,
                ]}
              />
            )}
            renderItem={application => (
              <ApplicationListItem
                key={application.id}
                value={application.name}
                application={application}
                detailUrl={`${match.url}/${application.id}/details`}
                onSelect={() => handleSelect(application)}
                isSelected={selected.some(row => row.id === application.id)}
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
        isOpen={deletionError}
        variant="error"
        title={i18n._(t`Error!`)}
        onClose={clearDeletionError}
      >
        {i18n._(t`Failed to delete one or more applications.`)}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </>
  );
}
export default withI18n()(ApplicationsList);
