import React, { Fragment, useEffect, useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { getQSConfig, parseQueryString } from '@util/qs';
import { Title } from '@patternfly/react-core';
import PaginatedDataList from '@components/PaginatedDataList';
import DataListToolbar from '@components/DataListToolbar';
import CheckboxListItem from '@components/CheckboxListItem';
import SelectedList from '@components/SelectedList';

const QS_CONFIG = getQSConfig('node_resource', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function NodeTypeStep({
  i18n,
  search,
  nodeType,
  nodeResource,
  updateNodeResource,
}) {
  const [contentError, setContentError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [rowCount, setRowCount] = useState(0);
  const [rows, setRows] = useState([]);

  let headerText = '';

  switch (nodeType) {
    case 'inventory_source_sync':
      headerText = i18n._(t`Inventory Sources`);
      break;
    case 'job_template':
      headerText = i18n._(t`Job Templates`);
      break;
    case 'project_sync':
      headerText = i18n._(t`Projects`);
      break;
    case 'workflow_job_template':
      headerText = i18n._(t`Workflow Job Templates`);
      break;
    default:
      break;
  }

  const fetchRows = queryString => {
    const params = parseQueryString(QS_CONFIG, queryString);
    return search(params);
  };

  useEffect(() => {
    async function fetchData() {
      try {
        const {
          data: { count, results },
        } = await fetchRows(location.node_resource);

        setRows(results);
        setRowCount(count);
      } catch (error) {
        setContentError(error);
      } finally {
        setIsLoading(false);
      }
    }
    fetchData();
  }, [location]);

  return (
    <Fragment>
      <Title headingLevel="h1" size="xl">
        {headerText}
      </Title>
      <p>{i18n._(t`Select a resource to be executed from the list below.`)}</p>
      {nodeResource && (
        <SelectedList
          displayKey="name"
          label={i18n._(t`Selected`)}
          onRemove={() => updateNodeResource(null)}
          selected={[nodeResource]}
        />
      )}
      <PaginatedDataList
        contentError={contentError}
        hasContentLoading={isLoading}
        items={rows}
        itemCount={rowCount}
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
    </Fragment>
  );
}

export default withI18n()(NodeTypeStep);
