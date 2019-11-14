import React from 'react';
import { withRouter } from 'react-router-dom';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormGroup, Tooltip } from '@patternfly/react-core';
import { QuestionCircleIcon as PFQuestionCircleIcon } from '@patternfly/react-icons';
import styled from 'styled-components';
import { CredentialsAPI, CredentialTypesAPI } from '@api';
import CategoryLookup from '@components/Lookup/CategoryLookup';
import { getQSConfig, parseQueryString } from '@util/qs';

const QuestionCircleIcon = styled(PFQuestionCircleIcon)`
  margin-left: 10px;
`;

const QS_CONFIG = getQSConfig('credentials', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

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

class MultiCredentialsLookup extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      selectedCredentialType: { label: 'Machine', id: 1, kind: 'ssh' },
      credentialTypes: [],
    };
    this.loadCredentialTypes = this.loadCredentialTypes.bind(this);
    this.handleCredentialTypeSelect = this.handleCredentialTypeSelect.bind(
      this
    );
    this.loadCredentials = this.loadCredentials.bind(this);
  }

  componentDidMount() {
    this.loadCredentialTypes();
    this.loadCredentials();
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
      this.setState({ credentialTypes });
    } catch (err) {
      onError(err);
    }
  }

  async loadCredentials() {
    const { history, onError } = this.props;
    const { selectedCredentialType } = this.state;
    const params = parseQueryString(QS_CONFIG, history.location.search);
    params.credential_type = selectedCredentialType.id || 1;
    try {
      const { data } = await CredentialsAPI.read(params);
      this.setState({
        credentials: data.results,
        count: data.count,
      });
    } catch (err) {
      onError(err);
    }
  }

  handleCredentialTypeSelect(value, type) {
    const { credentialTypes } = this.state;
    const selectedType = credentialTypes.filter(item => item.label === type);
    this.setState({ selectedCredentialType: selectedType[0] }, () => {
      this.loadCredentials();
    });
  }

  render() {
    const {
      selectedCredentialType,
      credentialTypes,
      credentials,
      count,
    } = this.state;
    const { tooltip, i18n, value, onChange } = this.props;
    return (
      <FormGroup label={i18n._(t`Credentials`)} fieldId="multiCredential">
        {tooltip && (
          <Tooltip position="right" content={tooltip}>
            <QuestionCircleIcon />
          </Tooltip>
        )}
        {credentialTypes && (
          <CategoryLookup
            selectCategoryOptions={credentialTypes}
            selectCategory={this.handleCredentialTypeSelect}
            selectedCategory={selectedCredentialType}
            onToggleItem={toggleCredentialSelection}
            onloadCategories={this.loadCredentialTypes}
            id="multiCredential"
            lookupHeader={i18n._(t`Credentials`)}
            name="credentials"
            value={value}
            multiple
            onChange={onChange}
            items={credentials}
            count={count}
            qsConfig={QS_CONFIG}
            columns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
                isSortable: true,
                isSearchable: true,
              },
            ]}
          />
        )}
      </FormGroup>
    );
  }
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
