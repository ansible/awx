import React, { useState, useEffect } from 'react';
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
import Lookup from './NewLookup';
import SelectList from './shared/SelectList';
import multiCredentialReducer from './shared/multiCredentialReducer';

const QS_CONFIG = getQSConfig('credentials', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

// TODO: move into reducer
function toggleCredentialSelection(credentialsToUpdate, newCredential) {
  let newCredentialsList;
  const isSelectedCredentialInState =
    credentialsToUpdate.filter(cred => cred.id === newCredential.id).length > 0;

  if (isSelectedCredentialInState) {
    newCredentialsList = credentialsToUpdate.filter(
      cred => cred.id !== newCredential.id
    );
  } else {
    newCredentialsList = credentialsToUpdate.filter(
      credential =>
        credential.kind === 'vault' || credential.kind !== newCredential.kind
    );
    newCredentialsList = [...newCredentialsList, newCredential];
  }
  return newCredentialsList;
}

async function loadCredentialTypes() {
  const { data } = await CredentialTypesAPI.read();
  const acceptableTypes = ['machine', 'cloud', 'net', 'ssh', 'vault'];
  const credentialTypes = [];
  // TODO: cleanup
  data.results.forEach(cred => {
    acceptableTypes.forEach(aT => {
      if (aT === cred.kind) {
        // This object has several repeated values as some of it's children
        // require different field values.
        cred = {
          id: cred.id,
          key: cred.id,
          kind: cred.kind,
          type: cred.namespace,
          value: cred.name,
          label: cred.name,
          isDisabled: false,
        };
        credentialTypes.push(cred);
      }
    });
  });
  return credentialTypes;
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
        setSelectedType(types[0]);
      } catch (err) {
        onError(err);
      }
    })();
  }, []);

  useEffect(() => {
    console.log('useEffect', selectedType);
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

  // handleCredentialTypeSelect(value, type) {
  //   const { credentialTypes } = this.state;
  //   const selectedType = credentialTypes.filter(item => item.label === type);
  //   this.setState({ selectedCredentialType: selectedType[0] }, () => {
  //     this.loadCredentials();
  //   });
  // }

  // const {
  //   selectedCredentialType,
  //   credentialTypes,
  //   credentials,
  //   credentialsCount,
  // } = state;

  return (
    <FormGroup label={i18n._(t`Credentials`)} fieldId="multiCredential">
      {tooltip && <FieldTooltip content={tooltip} />}
      <Lookup
        reducer={multiCredentialReducer}
        onToggleItem={toggleCredentialSelection}
        id="multiCredential"
        lookupHeader={i18n._(t`Credentials`)}
        // name="credentials"
        value={value}
        multiple
        onChange={onChange}
        // items={credentials}
        // count={credentialsCount}
        qsConfig={QS_CONFIG}
        // columns={}
        // TODO bind removeItem
        renderItemChip={({ item, removeItem, canDelete }) => (
          <CredentialChip
            key={item.id}
            onClick={() => removeItem(item)}
            isReadOnly={!canDelete}
            credential={item}
          />
        )}
        renderSelectList={({ state, dispatch, canDelete }) => {
          return (
            <>
              {credentialTypes && credentialTypes.length > 0 && (
                <ToolbarItem css=" display: flex; align-items: center;">
                  <div css="flex: 0 0 25%;">{i18n._(t`Selected Category`)}</div>
                  <VerticalSeperator />
                  <AnsibleSelect
                    css="flex: 1 1 75%;"
                    id="multiCredentialsLookUp-select"
                    label={i18n._(t`Selected Category`)}
                    data={credentialTypes}
                    value={selectedType && selectedType.label}
                    onChange={(e, label) => {
                      setSelectedType(
                        credentialTypes.find(o => o.label === label)
                      );
                    }}
                  />
                </ToolbarItem>
              )}
              <SelectList
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
                multiple={selectedType && selectedType.value === 'Vault'}
                header={i18n._(t`Credentials`)}
                name="credentials"
                qsConfig={QS_CONFIG}
                readOnly={!canDelete}
                selectItem={() => {}}
                deselectItem={() => {}}
              />
            </>
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
