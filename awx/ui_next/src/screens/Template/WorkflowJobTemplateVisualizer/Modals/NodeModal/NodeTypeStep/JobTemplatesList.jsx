import React, { useState, useEffect } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { JobTemplatesAPI } from '@api';
import { getQSConfig, parseQueryString } from '@util/qs';
import PaginatedDataList from '@components/PaginatedDataList';
import DataListToolbar from '@components/DataListToolbar';
import CheckboxListItem from '@components/CheckboxListItem';

const QS_CONFIG = getQSConfig('job_templates', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function JobTemplatesList({ i18n, history, nodeResource, updateNodeResource }) {
  const [jobTemplates, setJobTemplates] = useState([]);
  const [count, setCount] = useState(0);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setIsLoading(true);
      setJobTemplates([]);
      setCount(0);
      const params = parseQueryString(QS_CONFIG, history.location.search);
      try {
        const { data } = await JobTemplatesAPI.read(params, {
          role_level: 'execute_role',
        });
        setJobTemplates(data.results);
        setCount(data.count);
      } catch (err) {
        setError(err);
      } finally {
        setIsLoading(false);
      }
    })();
  }, [history.location]);

  return (
    <PaginatedDataList
      contentError={error}
      hasContentLoading={isLoading}
      items={jobTemplates}
      itemCount={count}
      qsConfig={QS_CONFIG}
      toolbarColumns={[
        {
          name: i18n._(t`Name`),
          key: 'name',
          isSortable: true,
          isSearchable: true,
        },
      ]}
      renderItem={item => (
        <CheckboxListItem
          isSelected={
            nodeResource && nodeResource.id === item.id ? true : false
          }
          itemId={item.id}
          key={item.id}
          name={item.name}
          label={item.name}
          onSelect={() => updateNodeResource(item)}
          onDeselect={() => updateNodeResource(null)}
          isRadio={true}
        />
      )}
      renderToolbar={props => <DataListToolbar {...props} fillWidth />}
      showPageSizeOptions={false}
    />
  );
}

export default withI18n()(withRouter(JobTemplatesList));
