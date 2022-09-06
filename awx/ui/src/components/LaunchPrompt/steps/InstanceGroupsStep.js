import React, { useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import { InstanceGroupsAPI } from 'api';
import { getSearchableKeys } from 'components/PaginatedTable';
import { getQSConfig, parseQueryString } from 'util/qs';
import useRequest from 'hooks/useRequest';
import useSelected from 'hooks/useSelected';
import OptionsList from '../../OptionsList';
import ContentLoading from '../../ContentLoading';
import ContentError from '../../ContentError';

const QS_CONFIG = getQSConfig('instance-groups', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function InstanceGroupsStep() {
  const [field, , helpers] = useField('instance_groups');
  const { selected, handleSelect, setSelected } = useSelected([], field.value);

  const history = useHistory();

  const {
    result: { instance_groups, count, relatedSearchableKeys, searchableKeys },
    request: fetchInstanceGroups,
    error,
    isLoading,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, history.location.search);
      const [{ data }, actionsResponse] = await Promise.all([
        InstanceGroupsAPI.read(params),
        InstanceGroupsAPI.readOptions(),
      ]);
      return {
        instance_groups: data.results,
        count: data.count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
      };
    }, [history.location]),
    {
      instance_groups: [],
      count: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchInstanceGroups();
  }, [fetchInstanceGroups]);

  useEffect(() => {
    helpers.setValue(selected);
  }, [selected]); // eslint-disable-line react-hooks/exhaustive-deps

  if (isLoading) {
    return <ContentLoading />;
  }
  if (error) {
    return <ContentError error={error} />;
  }

  return (
    <OptionsList
      value={selected}
      options={instance_groups}
      optionCount={count}
      searchColumns={[
        {
          name: t`Name`,
          key: 'name__icontains',
          isDefault: true,
        },
        {
          name: t`Credential Name`,
          key: 'credential__name__icontains',
        },
      ]}
      sortColumns={[
        {
          name: t`Name`,
          key: 'name',
        },
      ]}
      searchableKeys={searchableKeys}
      relatedSearchableKeys={relatedSearchableKeys}
      multiple
      header={t`Instance Groups`}
      name="instanceGroups"
      qsConfig={QS_CONFIG}
      selectItem={handleSelect}
      deselectItem={handleSelect}
      sortSelectedItems={(selectedItems) => setSelected(selectedItems)}
      isSelectedDraggable
    />
  );
}

export default InstanceGroupsStep;
