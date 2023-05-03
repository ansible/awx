import React, { useCallback, useEffect } from 'react';
import { arrayOf, string, func, bool, shape } from 'prop-types';
import { withRouter } from 'react-router-dom';
import { t } from '@lingui/macro';
import { FormGroup, Chip } from '@patternfly/react-core';
import { InstancesAPI } from 'api';
import { Instance } from 'types';
import { getSearchableKeys } from 'components/PaginatedTable';
import { getQSConfig, parseQueryString, mergeParams } from 'util/qs';
import useRequest from 'hooks/useRequest';
import Popover from '../Popover';
import OptionsList from '../OptionsList';
import Lookup from './Lookup';
import LookupErrorMessage from './shared/LookupErrorMessage';
import FieldWithPrompt from '../FieldWithPrompt';

const QS_CONFIG = getQSConfig('instances', {
  page: 1,
  page_size: 5,
  order_by: 'hostname',
});

function PeersLookup({
  id,
  value,
  onChange,
  tooltip,
  className,
  required,
  history,
  fieldName,
  multiple,
  validate,
  columns,
  isPromptableField,
  promptId,
  promptName,
  formLabel,
  typePeers,
  instance_details,
}) {
  const {
    result: { instances, count, relatedSearchableKeys, searchableKeys },
    request: fetchInstances,
    error,
    isLoading,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, history.location.search);
      const peersFilter = {};
      if (typePeers) {
        peersFilter.not__node_type = ['control', 'hybrid'];
        if (instance_details) {
          if (instance_details.id) {
            peersFilter.not__id = instance_details.id;
            peersFilter.not__hostname = instance_details.peers;
          }
        }
      }

      const [{ data }, actionsResponse] = await Promise.all([
        InstancesAPI.read(
          mergeParams(params, {
            ...peersFilter,
          })
        ),
        InstancesAPI.readOptions(),
      ]);
      return {
        instances: data.results,
        count: data.count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
      };
    }, [history.location, typePeers, instance_details]),
    {
      instances: [],
      count: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchInstances();
  }, [fetchInstances]);

  const renderLookup = () => (
    <>
      <Lookup
        id={fieldName}
        header={formLabel}
        value={value}
        onChange={onChange}
        onUpdate={fetchInstances}
        fieldName={fieldName}
        validate={validate}
        qsConfig={QS_CONFIG}
        multiple={multiple}
        required={required}
        isLoading={isLoading}
        label={formLabel}
        renderItemChip={({ item, removeItem, canDelete }) => (
          <Chip
            key={item.id}
            onClick={() => removeItem(item)}
            isReadOnly={!canDelete}
          >
            {item.hostname}
          </Chip>
        )}
        renderOptionsList={({ state, dispatch, canDelete }) => (
          <OptionsList
            value={state.selectedItems}
            options={instances}
            optionCount={count}
            columns={columns}
            header={formLabel}
            displayKey="hostname"
            searchColumns={[
              {
                name: t`Hostname`,
                key: 'hostname__icontains',
                isDefault: true,
              },
            ]}
            sortColumns={[
              {
                name: t`Hostname`,
                key: 'hostname',
              },
            ]}
            searchableKeys={searchableKeys}
            relatedSearchableKeys={relatedSearchableKeys}
            multiple={multiple}
            label={formLabel}
            name={fieldName}
            qsConfig={QS_CONFIG}
            readOnly={!canDelete}
            selectItem={(item) => dispatch({ type: 'SELECT_ITEM', item })}
            deselectItem={(item) => dispatch({ type: 'DESELECT_ITEM', item })}
          />
        )}
      />
      <LookupErrorMessage error={error} />
    </>
  );

  return isPromptableField ? (
    <FieldWithPrompt
      fieldId={id}
      label={formLabel}
      promptId={promptId}
      promptName={promptName}
      tooltip={tooltip}
    >
      {renderLookup()}
    </FieldWithPrompt>
  ) : (
    <FormGroup
      className={className}
      label={formLabel}
      labelIcon={tooltip && <Popover content={tooltip} />}
      fieldId={id}
    >
      {renderLookup()}
    </FormGroup>
  );
}

PeersLookup.propTypes = {
  id: string,
  value: arrayOf(Instance).isRequired,
  tooltip: string,
  onChange: func.isRequired,
  className: string,
  required: bool,
  validate: func,
  multiple: bool,
  fieldName: string,
  columns: arrayOf(Object),
  formLabel: string,
  instance_details: (Instance, shape({})),
  typePeers: bool,
};

PeersLookup.defaultProps = {
  id: 'instances',
  tooltip: '',
  className: '',
  required: false,
  validate: () => undefined,
  fieldName: 'instances',
  columns: [
    {
      key: 'hostname',
      name: t`Hostname`,
    },
    {
      key: 'node_type',
      name: t`Node Type`,
    },
  ],
  formLabel: t`Instances`,
  instance_details: {},
  multiple: true,
  typePeers: false,
};

export default withRouter(PeersLookup);
