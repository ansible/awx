import React, { useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';

import { t } from '@lingui/macro';
import { func, shape } from 'prop-types';
import { ProjectsAPI } from 'api';
import { getQSConfig, parseQueryString } from 'util/qs';
import useRequest from 'hooks/useRequest';
import DataListToolbar from 'components/DataListToolbar';
import CheckboxListItem from 'components/CheckboxListItem';
import PaginatedTable, {
  HeaderCell,
  HeaderRow,
  getSearchableKeys,
} from 'components/PaginatedTable';

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
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
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
    <PaginatedTable
      contentError={error}
      hasContentLoading={isLoading}
      itemCount={count}
      items={projects}
      qsConfig={QS_CONFIG}
      headerRow={
        <HeaderRow isExpandable={false} qsConfig={QS_CONFIG}>
          <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
        </HeaderRow>
      }
      renderRow={(item, index) => (
        <CheckboxListItem
          rowIndex={index}
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
      renderToolbar={(props) => <DataListToolbar {...props} fillWidth />}
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
