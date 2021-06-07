import React, { useEffect, useCallback } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';
import { t, Plural } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';

import { ProjectsAPI } from '../../../api';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import AlertModal from '../../../components/AlertModal';
import DataListToolbar from '../../../components/DataListToolbar';
import ErrorDetail from '../../../components/ErrorDetail';
import {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '../../../components/PaginatedDataList';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
} from '../../../components/PaginatedTable';
import useWsProjects from './useWsProjects';
import useSelected from '../../../util/useSelected';
import { relatedResourceDeleteRequests } from '../../../util/getRelatedResourceDeleteDetails';
import { getQSConfig, parseQueryString } from '../../../util/qs';

import ProjectListItem from './ProjectListItem';

const QS_CONFIG = getQSConfig('project', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function ProjectList() {
  const location = useLocation();
  const match = useRouteMatch();

  const {
    result: {
      results,
      itemCount,
      actions,
      relatedSearchableKeys,
      searchableKeys,
    },
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
        results: response.data.results,
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
      results: [],
      itemCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const projects = useWsProjects(results);

  const {
    selected,
    isAllSelected,
    handleSelect,
    setSelected,
    selectAll,
    clearSelected,
  } = useSelected(projects);

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteProjects,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(() => {
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

  const deleteDetailsRequests = relatedResourceDeleteRequests.project(
    selected[0]
  );

  return (
    <>
      <PageSection>
        <Card>
          <PaginatedTable
            contentError={contentError}
            hasContentLoading={hasContentLoading}
            items={projects}
            itemCount={itemCount}
            pluralizedItemName={t`Projects`}
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
                name: t`Type`,
                key: 'or__scm_type',
                options: [
                  [``, t`Manual`],
                  [`git`, t`Git`],
                  [`svn`, t`Subversion`],
                  [`archive`, t`Remote Archive`],
                  [`insights`, t`Red Hat Insights`],
                ],
              },
              {
                name: t`Source Control URL`,
                key: 'scm_url__icontains',
              },
              {
                name: t`Modified By (Username)`,
                key: 'modified_by__username__icontains',
              },
              {
                name: t`Created By (Username)`,
                key: 'created_by__username__icontains',
              },
            ]}
            toolbarSearchableKeys={searchableKeys}
            toolbarRelatedSearchableKeys={relatedSearchableKeys}
            headerRow={
              <HeaderRow qsConfig={QS_CONFIG} isExpandable>
                <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
                <HeaderCell>{t`Status`}</HeaderCell>
                <HeaderCell>{t`Type`}</HeaderCell>
                <HeaderCell>{t`Revision`}</HeaderCell>
                <HeaderCell>{t`Actions`}</HeaderCell>
              </HeaderRow>
            }
            renderToolbar={props => (
              <DataListToolbar
                {...props}
                showSelectAll
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
                    onDelete={handleProjectDelete}
                    itemsToDelete={selected}
                    pluralizedItemName={t`Projects`}
                    deleteDetailsRequests={deleteDetailsRequests}
                    deleteMessage={
                      <Plural
                        value={selected.length}
                        one="This project is currently being used by other resources. Are you sure you want to delete it?"
                        other="Deleting these projects could impact other resources that rely on them. Are you sure you want to delete anyway?"
                      />
                    }
                  />,
                ]}
              />
            )}
            renderRow={(project, index) => (
              <ProjectListItem
                fetchProjects={fetchProjects}
                key={project.id}
                project={project}
                detailUrl={`${match.url}/${project.id}`}
                isSelected={selected.some(row => row.id === project.id)}
                onSelect={() => handleSelect(project)}
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
        aria-label={t`Deletion Error`}
        title={t`Error!`}
        onClose={clearDeletionError}
      >
        {t`Failed to delete one or more projects.`}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </>
  );
}

export default ProjectList;
