import React, { Fragment, useState, useEffect, useCallback } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';

import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';

import { TeamsAPI } from '../../../api';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import AlertModal from '../../../components/AlertModal';
import DataListToolbar from '../../../components/DataListToolbar';
import ErrorDetail from '../../../components/ErrorDetail';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
} from '../../../components/PaginatedTable';
import {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '../../../components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '../../../util/qs';

import TeamListItem from './TeamListItem';

const QS_CONFIG = getQSConfig('team', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function TeamList() {
  const location = useLocation();
  const match = useRouteMatch();
  const [selected, setSelected] = useState([]);

  const {
    result: {
      teams,
      itemCount,
      actions,
      relatedSearchableKeys,
      searchableKeys,
    },
    error: contentError,
    isLoading,
    request: fetchTeams,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, actionsResponse] = await Promise.all([
        TeamsAPI.read(params),
        TeamsAPI.readOptions(),
      ]);
      return {
        teams: response.data.results,
        itemCount: response.data.count,
        actions: actionsResponse.data.actions,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          actionsResponse.data.actions?.GET || {}
        ).filter(key => actionsResponse.data.actions?.GET[key].filterable),
      };
    }, [location]),
    {
      teams: [],
      itemCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchTeams();
  }, [fetchTeams]);

  const isAllSelected = selected.length === teams.length && selected.length > 0;
  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteTeams,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(() => {
      return Promise.all(selected.map(team => TeamsAPI.destroy(team.id)));
    }, [selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchTeams,
    }
  );

  const handleTeamDelete = async () => {
    await deleteTeams();
    setSelected([]);
  };

  const hasContentLoading = isDeleteLoading || isLoading;
  const canAdd = actions && actions.POST;

  const handleSelectAll = isSelected => {
    setSelected(isSelected ? [...teams] : []);
  };

  const handleSelect = row => {
    if (selected.some(s => s.id === row.id)) {
      setSelected(selected.filter(s => s.id !== row.id));
    } else {
      setSelected(selected.concat(row));
    }
  };

  return (
    <Fragment>
      <PageSection>
        <Card>
          <PaginatedTable
            contentError={contentError}
            hasContentLoading={hasContentLoading}
            items={teams}
            itemCount={itemCount}
            pluralizedItemName={t`Teams`}
            qsConfig={QS_CONFIG}
            onRowClick={handleSelect}
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
                name: t`Organization Name`,
                key: 'organization__name__icontains',
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
            headerRow={
              <HeaderRow qsConfig={QS_CONFIG}>
                <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
                <HeaderCell>{t`Organization`}</HeaderCell>
                <HeaderCell>{t`Actions`}</HeaderCell>
              </HeaderRow>
            }
            renderToolbar={props => (
              <DataListToolbar
                {...props}
                showSelectAll
                isAllSelected={isAllSelected}
                onSelectAll={handleSelectAll}
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
                    onDelete={handleTeamDelete}
                    itemsToDelete={selected}
                    pluralizedItemName={t`Teams`}
                  />,
                ]}
              />
            )}
            renderRow={(team, index) => (
              <TeamListItem
                key={team.id}
                team={team}
                detailUrl={`${match.url}/${team.id}`}
                isSelected={selected.some(row => row.id === team.id)}
                onSelect={() => handleSelect(team)}
                rowIndex={index}
              />
            )}
            emptyStateControls={
              canAdd ? (
                <ToolbarAddButton key="add" linkTo={`${match.url}/add`} />
              ) : null
            }
          />
        </Card>
      </PageSection>
      <AlertModal
        isOpen={deletionError}
        variant="error"
        title={t`Error!`}
        onClose={clearDeletionError}
      >
        {t`Failed to delete one or more teams.`}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </Fragment>
  );
}

export default TeamList;
