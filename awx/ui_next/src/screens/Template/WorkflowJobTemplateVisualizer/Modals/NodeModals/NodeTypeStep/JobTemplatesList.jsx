import React, { useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { func, shape } from 'prop-types';
import { JobTemplatesAPI } from '../../../../../../api';
import { getQSConfig, parseQueryString } from '../../../../../../util/qs';
import useRequest from '../../../../../../util/useRequest';
import PaginatedDataList from '../../../../../../components/PaginatedDataList';
import DataListToolbar from '../../../../../../components/DataListToolbar';
import CheckboxListItem from '../../../../../../components/CheckboxListItem';

const QS_CONFIG = getQSConfig('job_templates', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function JobTemplatesList({ i18n, nodeResource, onUpdateNodeResource }) {
  const location = useLocation();

  const {
    result: { jobTemplates, count },
    error,
    isLoading,
    request: fetchJobTemplates,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const results = await JobTemplatesAPI.read(params, {
        role_level: 'execute_role',
      });
      return {
        jobTemplates: results.data.results,
        count: results.data.count,
      };
    }, [location]),
    {
      jobTemplates: [],
      count: 0,
    }
  );

  useEffect(() => {
    fetchJobTemplates();
  }, [fetchJobTemplates]);

  return (
    <PaginatedDataList
      contentError={error}
      hasContentLoading={isLoading}
      itemCount={count}
      items={jobTemplates}
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
          name: i18n._(t`Name`),
          key: 'name',
          isDefault: true,
        },
        {
          name: i18n._(t`Playbook name`),
          key: 'playbook',
        },
        {
          name: i18n._(t`Created by (username)`),
          key: 'created_by__username',
        },
        {
          name: i18n._(t`Modified by (username)`),
          key: 'modified_by__username',
        },
      ]}
      toolbarSortColumns={[
        {
          name: i18n._(t`Name`),
          key: 'name',
        },
      ]}
    />
  );
}

JobTemplatesList.propTypes = {
  nodeResource: shape(),
  onUpdateNodeResource: func.isRequired,
};

JobTemplatesList.defaultProps = {
  nodeResource: null,
};

export default withI18n()(JobTemplatesList);
