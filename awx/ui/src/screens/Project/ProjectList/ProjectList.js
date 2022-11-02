import React, { useEffect, useCallback } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';
import { t, Plural } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';
import { ProjectsAPI } from 'api';
import useRequest, {
  useDeleteItems,
  useDismissableError,
} from 'hooks/useRequest';
import AlertModal from 'components/AlertModal';
import DataListToolbar from 'components/DataListToolbar';
import ErrorDetail from 'components/ErrorDetail';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
  ToolbarAddButton,
  ToolbarDeleteButton,
  getSearchableKeys,
} from 'components/PaginatedTable';
import useSelected from 'hooks/useSelected';
import useExpanded from 'hooks/useExpanded';
import useToast, { AlertVariant } from 'hooks/useToast';
import { relatedResourceDeleteRequests } from 'util/getRelatedResourceDeleteDetails';
import { getQSConfig, parseQueryString } from 'util/qs';
import useWsProjects from './useWsProjects';

import ProjectListItem from './ProjectListItem';

const QS_CONFIG = getQSConfig('project', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function ProjectList() {
  const location = useLocation();
  const match = useRouteMatch();
  const { addToast, Toast, toastProps } = useToast();

  const {
    request: fetchUpdatedProject,
    error: fetchUpdatedProjectError,
    result: updatedProject,
  } = useRequest(
    useCallback(async (projectId) => {
      if (!projectId) {
        return {};
      }
      const { data } = await ProjectsAPI.readDetail(projectId);
      return data;
    }, []),
    null
  );

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
    setValue: setProjects,
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
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
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

  const { expanded, isAllExpanded, handleExpand, expandAll } =
    useExpanded(projects);

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteProjects,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(
      () => Promise.all(selected.map(({ id }) => ProjectsAPI.destroy(id))),
      [selected]
    ),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchProjects,
    }
  );

  const handleCopy = useCallback(
    (newId) => {
      addToast({
        id: newId,
        title: t`Project copied successfully`,
        variant: AlertVariant.success,
        hasTimeout: true,
      });
    },
    [addToast]
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

  useEffect(() => {
    if (updatedProject) {
      const updatedProjects = projects.map((project) =>
        project.id === updatedProject.id ? updatedProject : project
      );
      setProjects({
        results: updatedProjects,
        itemCount,
        actions,
        relatedSearchableKeys,
        searchableKeys,
      });
    }
    /* eslint-disable-next-line react-hooks/exhaustive-deps */
  }, [updatedProject]);

  const { error: projectError, dismissError: dismissProjectError } =
    useDismissableError(fetchUpdatedProjectError);

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
            renderToolbar={(props) => (
              <DataListToolbar
                {...props}
                isAllExpanded={isAllExpanded}
                onExpandAll={expandAll}
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
                isExpanded={expanded.some((row) => row.id === project.id)}
                onExpand={() => handleExpand(project)}
                fetchProjects={fetchProjects}
                key={project.id}
                project={project}
                detailUrl={`${match.url}/${project.id}`}
                isSelected={selected.some((row) => row.id === project.id)}
                onSelect={() => handleSelect(project)}
                onCopy={handleCopy}
                rowIndex={index}
                onRefreshRow={(projectId) => fetchUpdatedProject(projectId)}
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
      <Toast {...toastProps} />
      {deletionError && (
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
      )}
      {projectError && (
        <AlertModal
          isOpen={projectError}
          variant="error"
          aria-label={t`Error fetching updated project`}
          title={t`Error!`}
          onClose={dismissProjectError}
        >
          {t`Failed to fetch the updated project data.`}
          <ErrorDetail error={projectError} />
        </AlertModal>
      )}
    </>
  );
}

export default ProjectList;
