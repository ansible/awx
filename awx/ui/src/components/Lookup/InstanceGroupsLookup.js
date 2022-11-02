import React, { useCallback, useEffect } from 'react';
import { arrayOf, string, func, bool } from 'prop-types';
import { withRouter } from 'react-router-dom';
import { t, Trans } from '@lingui/macro';
import { FormGroup } from '@patternfly/react-core';
import { InstanceGroupsAPI } from 'api';
import { InstanceGroup } from 'types';
import { getSearchableKeys } from 'components/PaginatedTable';
import { getQSConfig, parseQueryString } from 'util/qs';
import useRequest from 'hooks/useRequest';
import Popover from '../Popover';
import OptionsList from '../OptionsList';
import Lookup from './Lookup';
import LookupErrorMessage from './shared/LookupErrorMessage';
import FieldWithPrompt from '../FieldWithPrompt';

const QS_CONFIG = getQSConfig('instance-groups', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function InstanceGroupsLookup({
  id,
  value,
  onChange,
  tooltip,
  className,
  required,
  history,
  fieldName,
  validate,
  isPromptableField,
  promptId,
  promptName,
}) {
  const {
    result: { instanceGroups, count, relatedSearchableKeys, searchableKeys },
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
        instanceGroups: data.results,
        count: data.count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
      };
    }, [history.location]),
    {
      instanceGroups: [],
      count: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchInstanceGroups();
  }, [fetchInstanceGroups]);

  const renderLookup = () => (
    <>
      <Lookup
        id="org-instance-groups"
        header={t`Instance Groups`}
        value={value}
        onChange={onChange}
        onUpdate={fetchInstanceGroups}
        fieldName={fieldName}
        validate={validate}
        qsConfig={QS_CONFIG}
        multiple
        required={required}
        isLoading={isLoading}
        modalDescription={
          <>
            <b>
              <Trans>Selected</Trans>
            </b>
            <br />
            <Trans>
              Note: The order in which these are selected sets the execution
              precedence. Select more than one to enable drag.
            </Trans>
          </>
        }
        renderOptionsList={({ state, dispatch, canDelete }) => (
          <OptionsList
            value={state.selectedItems}
            options={instanceGroups}
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
            multiple={state.multiple}
            header={t`Instance Groups`}
            name="instanceGroups"
            qsConfig={QS_CONFIG}
            readOnly={!canDelete}
            selectItem={(item) => dispatch({ type: 'SELECT_ITEM', item })}
            deselectItem={(item) => dispatch({ type: 'DESELECT_ITEM', item })}
            sortSelectedItems={(selectedItems) =>
              dispatch({ type: 'SET_SELECTED_ITEMS', selectedItems })
            }
            isSelectedDraggable
          />
        )}
      />
      <LookupErrorMessage error={error} />
    </>
  );

  return isPromptableField ? (
    <FieldWithPrompt
      fieldId={id}
      label={t`Instance Groups`}
      promptId={promptId}
      promptName={promptName}
      tooltip={tooltip}
    >
      {renderLookup()}
    </FieldWithPrompt>
  ) : (
    <FormGroup
      className={className}
      label={t`Instance Groups`}
      labelIcon={tooltip && <Popover content={tooltip} />}
      fieldId={id}
    >
      {renderLookup()}
    </FormGroup>
  );
}

InstanceGroupsLookup.propTypes = {
  id: string,
  value: arrayOf(InstanceGroup).isRequired,
  tooltip: string,
  onChange: func.isRequired,
  className: string,
  required: bool,
  validate: func,
  fieldName: string,
};

InstanceGroupsLookup.defaultProps = {
  id: 'org-instance-groups',
  tooltip: '',
  className: '',
  required: false,
  validate: () => undefined,
  fieldName: 'instance_groups',
};

export default withRouter(InstanceGroupsLookup);
