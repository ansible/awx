import React, { useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';

import { t } from '@lingui/macro';
import { func, shape } from 'prop-types';
import { ProjectsAPI } from '../../../../../../api';
import { getQSConfig, parseQueryString } from '../../../../../../util/qs';
import useRequest from '../../../../../../util/useRequest';
import PaginatedDataList from '../../../../../../components/PaginatedDataList';
import DataListToolbar from '../../../../../../components/DataListToolbar';
import CheckboxListItem from '../../../../../../components/CheckboxListItem';

const QS_CONFIG = getQSConfig('projects', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function ProjectsList({ nodeResource, onUpdateNodeResource }) {
  const location = useLocation();

  const {
    result: { projects, count, relatedSearchableKeys, searchableKeys },
    error,
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
        count: response.data.count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          actionsResponse.data.actions?.GET || {}
        ).filter(key => actionsResponse.data.actions?.GET[key].filterable),
      };
    }, [location]),
    {
      projects: [],
      count: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  return (
    <PaginatedDataList
      contentError={error}
      hasContentLoading={isLoading}
      itemCount={count}
      items={projects}
      onRowClick={row => onUpdateNodeResource(row)}
      qsConfig={QS_CONFIG}
      renderItem={item => (
        <CheckboxListItem
          isSelected={!!(nodeResource && nodeResource.id === item.id)}
          itemId={item.id}
          key={item.id}
          name={item.name}
          label={item.name}
          onSelect={() => onUpdateNodeResource(item)}
          onDeselect={() => onUpdateNodeResource(null)}
          isRadio
        />
      )}
      renderToolbar={props => <DataListToolbar {...props} fillWidth />}
      showPageSizeOptions={false}
      toolbarSearchColumns={[
        {
          name: t`Name`,
          key: 'name__icontains',
          isDefault: true,
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
      toolbarSortColumns={[
        {
          name: t`Name`,
          key: 'name',
        },
      ]}
      toolbarSearchableKeys={searchableKeys}
      toolbarRelatedSearchableKeys={relatedSearchableKeys}
    />
  );
}

ProjectsList.propTypes = {
  nodeResource: shape(),
  onUpdateNodeResource: func.isRequired,
};

ProjectsList.defaultProps = {
  nodeResource: null,
};

export default ProjectsList;
