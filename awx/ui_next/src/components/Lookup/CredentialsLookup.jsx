import React from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { withRouter } from 'react-router-dom';
import { t } from '@lingui/macro';
import { FormGroup, Tooltip } from '@patternfly/react-core';
import { QuestionCircleIcon as PFQuestionCircleIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

import { CredentialsAPI, CredentialTypesAPI } from '@api';
import Lookup from '@components/Lookup';

const QuestionCircleIcon = styled(PFQuestionCircleIcon)`
  margin-left: 10px;
`;

class CredentialsLookup extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      credentials: props.credentials,
      selectedCredentialType: { label: 'Machine', id: 1, kind: 'ssh' },
      credentialTypes: [],
    };

    this.handleCredentialTypeSelect = this.handleCredentialTypeSelect.bind(
      this
    );
    this.loadCredentials = this.loadCredentials.bind(this);
    this.loadCredentialTypes = this.loadCredentialTypes.bind(this);
    this.toggleCredential = this.toggleCredential.bind(this);
  }

  componentDidMount() {
    this.loadCredentials({ page: 1, page_size: 5, order_by: 'name' });
    this.loadCredentialTypes();
  }

  componentDidUpdate(prevState) {
    const { selectedType } = this.state;
    if (prevState.selectedType !== selectedType) {
      Promise.all([this.loadCredentials()]);
    }
  }

  async loadCredentialTypes() {
    const { onError } = this.props;
    try {
      const { data } = await CredentialTypesAPI.read();
      const acceptableTypes = ['machine', 'cloud', 'net', 'ssh', 'vault'];
      const credentialTypes = [];
      data.results.forEach(cred => {
        acceptableTypes.forEach(aT => {
          if (aT === cred.kind) {
            // This object has several repeated values as some of it's children
            // require different field values.
            cred = {
              id: cred.id,
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
      this.setState({ credentialTypes });
    } catch (err) {
      onError(err);
    }
  }

  async loadCredentials(params) {
    const { selectedCredentialType } = this.state;
    params.credential_type = selectedCredentialType.id || 1;
    return CredentialsAPI.read(params);
  }

  handleCredentialTypeSelect(value, type) {
    const { credentialTypes } = this.state;
    const selectedType = credentialTypes.filter(item => item.label === type);
    this.setState({ selectedCredentialType: selectedType[0] });
  }

  toggleCredential(item) {
    const { credentials: stateToUpdate, selectedCredentialType } = this.state;
    const { onChange } = this.props;
    const index = stateToUpdate.findIndex(
      credential => credential.id === item.id
    );
    if (index > -1) {
      const newCredentialsList = stateToUpdate.filter(
        cred => cred.id !== item.id
      );
      this.setState({ credentials: newCredentialsList });
      onChange(newCredentialsList);
      return;
    }

    const credentialTypeOccupied = stateToUpdate.some(
      cred => cred.kind === item.kind
    );
    if (selectedCredentialType.value === 'Vault' || !credentialTypeOccupied) {
      item.credentialType = selectedCredentialType;
      this.setState({ credentials: [...stateToUpdate, item] });
      onChange([...stateToUpdate, item]);
    } else {
      const credsList = [...stateToUpdate];
      const occupyingCredIndex = stateToUpdate.findIndex(
        occupyingCred => occupyingCred.kind === item.kind
      );
      credsList.splice(occupyingCredIndex, 1, item);
      this.setState({ credentials: credsList });
      onChange(credsList);
    }
  }

  render() {
    const { tooltip, i18n } = this.props;
    const { credentials, selectedCredentialType, credentialTypes } = this.state;

    return (
      <FormGroup label={i18n._(t`Credentials`)} fieldId="org-credentials">
        {tooltip && (
          <Tooltip position="right" content={tooltip}>
            <QuestionCircleIcon />
          </Tooltip>
        )}
        {credentialTypes && (
          <Lookup
            selectCategoryOptions={credentialTypes}
            selectCategory={this.handleCredentialTypeSelect}
            selectedCategory={selectedCredentialType}
            onToggleItem={this.toggleCredential}
            onloadCategories={this.loadCredentialTypes}
            id="org-credentials"
            lookupHeader={i18n._(t`Credentials`)}
            name="credentials"
            value={credentials}
            multiple
            onLookupSave={() => {}}
            getItems={this.loadCredentials}
            qsNamespace="credentials"
            columns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
                isSortable: true,
                isSearchable: true,
              },
            ]}
            sortedColumnKey="name"
          />
        )}
      </FormGroup>
    );
  }
}

CredentialsLookup.propTypes = {
  tooltip: PropTypes.string,
  onChange: PropTypes.func.isRequired,
};

CredentialsLookup.defaultProps = {
  tooltip: '',
};
export { CredentialsLookup as _CredentialsLookup };

export default withI18n()(withRouter(CredentialsLookup));
