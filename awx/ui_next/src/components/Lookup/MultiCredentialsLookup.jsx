import React, { Fragment, useState, useEffect } from 'react';
import { withRouter } from 'react-router-dom';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormGroup, ToolbarItem } from '@patternfly/react-core';
import { CredentialsAPI, CredentialTypesAPI } from '@api';
import AnsibleSelect from '@components/AnsibleSelect';
import { FieldTooltip } from '@components/FormField';
import { CredentialChip } from '@components/Chip';
import VerticalSeperator from '@components/VerticalSeparator';
import { getQSConfig, parseQueryString } from '@util/qs';
import Lookup from './Lookup';
import OptionsList from './shared/OptionsList';

const QS_CONFIG = getQSConfig('credentials', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

async function loadCredentialTypes() {
  const { data } = await CredentialTypesAPI.read();
  const acceptableTypes = ['machine', 'cloud', 'net', 'ssh', 'vault'];
  return data.results.filter(type => acceptableTypes.includes(type.kind));
}

async function loadCredentials(params, selectedCredentialTypeId) {
  params.credential_type = selectedCredentialTypeId || 1;
  const { data } = await CredentialsAPI.read(params);
  return data;
}

function MultiCredentialsLookup(props) {
  const { history, tooltip, value, onChange, onError, i18n } = props;
  const [credentialTypes, setCredentialTypes] = useState([]);
  const [selectedType, setSelectedType] = useState(null);
  const [credentials, setCredentials] = useState([]);
  const [credentialsCount, setCredentialsCount] = useState(0);

  useEffect(() => {
    (async () => {
      try {
        const types = await loadCredentialTypes();
        setCredentialTypes(types);
        setSelectedType(
          types.find(type => type.name === 'Machine') || types[0]
        );
      } catch (err) {
        onError(err);
      }
    })();
  }, []);

  useEffect(() => {
    (async () => {
      if (!selectedType) {
        return;
      }
      try {
        const params = parseQueryString(QS_CONFIG, history.location.search);
        const { results, count } = await loadCredentials(
          params,
          selectedType.id
        );
        setCredentials(results);
        setCredentialsCount(count);
      } catch (err) {
        onError(err);
      }
    })();
  }, [selectedType]);

  const isMultiple = selectedType && selectedType.name === 'Vault';
  const renderChip = ({ item, removeItem, canDelete }) => (
    <CredentialChip
      key={item.id}
      onClick={() => removeItem(item)}
      isReadOnly={!canDelete}
      credential={item}
    />
  );

  return (
    <FormGroup label={i18n._(t`Credentials`)} fieldId="multiCredential">
      {tooltip && <FieldTooltip content={tooltip} />}
      <Lookup
        id="multiCredential"
        lookupHeader={i18n._(t`Credentials`)}
        value={value}
        multiple
        onChange={onChange}
        qsConfig={QS_CONFIG}
        renderItemChip={renderChip}
        renderOptionsList={({ state, dispatch, canDelete }) => {
          return (
            <Fragment>
              {credentialTypes && credentialTypes.length > 0 && (
                <ToolbarItem css=" display: flex; align-items: center;">
                  <div css="flex: 0 0 25%;">{i18n._(t`Selected Category`)}</div>
                  <VerticalSeperator />
                  <AnsibleSelect
                    css="flex: 1 1 75%;"
                    id="multiCredentialsLookUp-select"
                    label={i18n._(t`Selected Category`)}
                    data={credentialTypes.map(type => ({
                      key: type.id,
                      value: type.id,
                      label: type.name,
                      isDisabled: false,
                    }))}
                    value={selectedType && selectedType.id}
                    onChange={(e, id) => {
                      setSelectedType(
                        credentialTypes.find(o => o.id === parseInt(id, 10))
                      );
                    }}
                  />
                </ToolbarItem>
              )}
              <OptionsList
                value={state.selectedItems}
                options={credentials}
                optionCount={credentialsCount}
                columns={[
                  {
                    name: i18n._(t`Name`),
                    key: 'name',
                    isSortable: true,
                    isSearchable: true,
                  },
                ]}
                multiple={isMultiple}
                header={i18n._(t`Credentials`)}
                name="credentials"
                qsConfig={QS_CONFIG}
                readOnly={!canDelete}
                selectItem={item => {
                  if (isMultiple) {
                    return dispatch({ type: 'SELECT_ITEM', item });
                  }
                  const selectedItems = state.selectedItems.filter(
                    i => i.kind !== item.kind
                  );
                  selectedItems.push(item);
                  return dispatch({
                    type: 'SET_SELECTED_ITEMS',
                    selectedItems,
                  });
                }}
                deselectItem={item => dispatch({ type: 'DESELECT_ITEM', item })}
                renderItemChip={renderChip}
              />
            </Fragment>
          );
        }}
      />
    </FormGroup>
  );
}

MultiCredentialsLookup.propTypes = {
  tooltip: PropTypes.string,
  value: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number,
      name: PropTypes.string,
      description: PropTypes.string,
      kind: PropTypes.string,
      clound: PropTypes.bool,
    })
  ),
  onChange: PropTypes.func.isRequired,
  onError: PropTypes.func.isRequired,
};

MultiCredentialsLookup.defaultProps = {
  tooltip: '',
  value: [],
};

export { MultiCredentialsLookup as _MultiCredentialsLookup };
export default withI18n()(withRouter(MultiCredentialsLookup));
