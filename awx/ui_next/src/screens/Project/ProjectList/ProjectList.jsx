import React, { Fragment, useState, useEffect, useCallback } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';

import { ProjectsAPI } from '@api';
import useRequest, { useDeleteItems } from '@util/useRequest';
import AlertModal from '@components/AlertModal';
import DataListToolbar from '@components/DataListToolbar';
import ErrorDetail from '@components/ErrorDetail';
import PaginatedDataList, {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '@components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '@util/qs';

import ProjectListItem from './ProjectListItem';

const QS_CONFIG = getQSConfig('project', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function ProjectList({ i18n }) {
  const location = useLocation();
  const match = useRouteMatch();
  const [selected, setSelected] = useState([]);

  const {
    result: { projects, itemCount, actions },
    error: contentError,
    isLoading,
    request: fetchProjects,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, actionsResponse] = await Promise.all([
        ProjectsAPI.read(params),
        ProjectsAPI.readOptions(),
      ]);
      return {
        projects: response.data.results,
        itemCount: response.data.count,
        actions: actionsResponse.data.actions,
      };
    }, [location]),
    {
      projects: [],
      itemCount: 0,
      actions: {},
    }
  );

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const isAllSelected =
    selected.length === projects.length && selected.length > 0;
  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteProjects,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(async () => {
      return Promise.all(selected.map(({ id }) => ProjectsAPI.destroy(id)));
    }, [selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchProjects,
    }
  );

  const handleProjectDelete = async () => {
    await deleteProjects();
    setSelected([]);
  };

  const hasContentLoading = isDeleteLoading || isLoading;
  const canAdd = actions && actions.POST;

  const handleSelectAll = isSelected => {
    setSelected(isSelected ? [...projects] : []);
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
          <PaginatedDataList
            contentError={contentError}
            hasContentLoading={hasContentLoading}
            items={projects}
            itemCount={itemCount}
            pluralizedItemName={i18n._(t`Projects`)}
            qsConfig={QS_CONFIG}
            onRowClick={handleSelect}
            toolbarSearchColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
                isDefault: true,
              },
              {
                name: i18n._(t`Type`),
                key: 'type',
                options: [
                  [``, i18n._(t`Manual`)],
                  [`git`, i18n._(t`Git`)],
                  [`hg`, i18n._(t`Mercurial`)],
                  [`svn`, i18n._(t`Subversion`)],
                  [`insights`, i18n._(t`Red Hat Insights`)],
                ],
              },
              {
                name: i18n._(t`SCM URL`),
                key: 'scm_url',
              },
              {
                name: i18n._(t`Modified By (Username)`),
                key: 'modified_by__username',
              },
              {
                name: i18n._(t`Created By (Username)`),
                key: 'created_by__username',
              },
            ]}
            toolbarSortColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
              },
            ]}
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
                    onDelete={handleProjectDelete}
                    itemsToDelete={selected}
                    pluralizedItemName={i18n._(t`Projects`)}
                  />,
                ]}
              />
            )}
            renderItem={o => (
              <ProjectListItem
                key={o.id}
                project={o}
                detailUrl={`${match.url}/${o.id}`}
                isSelected={selected.some(row => row.id === o.id)}
                onSelect={() => handleSelect(o)}
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
        title={i18n._(t`Error!`)}
        onClose={clearDeletionError}
      >
        {i18n._(t`Failed to delete one or more projects.`)}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </Fragment>
  );
}

export default withI18n()(ProjectList);
