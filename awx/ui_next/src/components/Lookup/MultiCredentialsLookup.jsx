import React, { Fragment, useState, useEffect } from 'react';
import { withRouter } from 'react-router-dom';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { ToolbarItem, Alert } from '@patternfly/react-core';
import { CredentialsAPI, CredentialTypesAPI } from '@api';
import AnsibleSelect from '@components/AnsibleSelect';
import CredentialChip from '@components/CredentialChip';
import { getQSConfig, parseQueryString } from '@util/qs';
import Lookup from './Lookup';
import OptionsList from './shared/OptionsList';

const QS_CONFIG = getQSConfig('credentials', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

async function loadCredentialTypes() {
  const pageSize = 200;
  const acceptableKinds = ['machine', 'cloud', 'net', 'ssh', 'vault'];
  // The number of credential types a user can have is unlimited. In practice, it is unlikely for
  // users to have more than a page at the maximum request size.
  const {
    data: { next, results },
  } = await CredentialTypesAPI.read({ page_size: pageSize });
  let nextResults = [];
  if (next) {
    const { data } = await CredentialTypesAPI.read({
      page_size: pageSize,
      page: 2,
    });
    nextResults = data.results;
  }
  return results
    .concat(nextResults)
    .filter(type => acceptableKinds.includes(type.kind));
}

async function loadCredentials(params, selectedCredentialTypeId) {
  params.credential_type = selectedCredentialTypeId || 1;
  const { data } = await CredentialsAPI.read(params);
  return data;
}

function MultiCredentialsLookup(props) {
  const { value, onChange, onError, history, i18n } = props;
  const [credentialTypes, setCredentialTypes] = useState([]);
  const [selectedType, setSelectedType] = useState(null);
  const [credentials, setCredentials] = useState([]);
  const [credentialsCount, setCredentialsCount] = useState(0);

  useEffect(() => {
    (async () => {
      try {
        const types = await loadCredentialTypes();
        setCredentialTypes(types);
        const match = types.find(type => type.kind === 'ssh') || types[0];
        setSelectedType(match);
      } catch (err) {
        onError(err);
      }
    })();
  }, [onError]);

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
  }, [selectedType, history.location.search, onError]);

  const renderChip = ({ item, removeItem, canDelete }) => (
    <CredentialChip
      key={item.id}
      onClick={() => removeItem(item)}
      isReadOnly={!canDelete}
      credential={item}
    />
  );

  const isVault = selectedType?.kind === 'vault';

  return (
    <Lookup
      id="multiCredential"
      header={i18n._(t`Credentials`)}
      value={value}
      multiple
      onChange={onChange}
      qsConfig={QS_CONFIG}
      renderItemChip={renderChip}
      renderOptionsList={({ state, dispatch, canDelete }) => {
        return (
          <Fragment>
            {isVault && (
              <Alert
                variant="info"
                isInline
                css="margin-bottom: 20px;"
                title={i18n._(
                  t`You cannot select multiple vault credentials with the same vault ID. Doing so will automatically deselect the other with the same vault ID.`
                )}
              />
            )}
            {credentialTypes && credentialTypes.length > 0 && (
              <ToolbarItem css=" display: flex; align-items: center;">
                <div css="flex: 0 0 25%; margin-right: 32px">
                  {i18n._(t`Selected Category`)}
                </div>
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
              searchColumns={[
                {
                  name: i18n._(t`Name`),
                  key: 'name',
                  isDefault: true,
                },
                {
                  name: i18n._(t`Created By (Username)`),
                  key: 'created_by__username',
                },
                {
                  name: i18n._(t`Modified By (Username)`),
                  key: 'modified_by__username',
                },
              ]}
              sortColumns={[
                {
                  name: i18n._(t`Name`),
                  key: 'name',
                },
              ]}
              multiple={isVault}
              header={i18n._(t`Credentials`)}
              name="credentials"
              qsConfig={QS_CONFIG}
              readOnly={!canDelete}
              selectItem={item => {
                const hasSameVaultID = val =>
                  val?.inputs?.vault_id !== undefined &&
                  val?.inputs?.vault_id === item?.inputs?.vault_id;
                const hasSameKind = val => val.kind === item.kind;
                const selectedItems = state.selectedItems.filter(i =>
                  isVault ? !hasSameVaultID(i) : !hasSameKind(i)
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
  );
}

MultiCredentialsLookup.propTypes = {
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
  value: [],
};

export { MultiCredentialsLookup as _MultiCredentialsLookup };
export default withI18n()(withRouter(MultiCredentialsLookup));
