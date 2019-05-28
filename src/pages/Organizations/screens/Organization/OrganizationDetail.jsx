import React, { Component } from 'react';
import { Link, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { CardBody as PFCardBody, Button } from '@patternfly/react-core';
import styled from 'styled-components';
import { DetailList, Detail } from '../../../../components/DetailList';
import { withNetwork } from '../../../../contexts/Network';
import { ChipGroup, Chip } from '../../../../components/Chip';

const CardBody = styled(PFCardBody)`
  padding-top: 20px;
`;

class OrganizationDetail extends Component {
  constructor (props) {
    super(props);

    this.state = {
      instanceGroups: [],
      error: false
    };
    this.loadInstanceGroups = this.loadInstanceGroups.bind(this);
  }

  componentDidMount () {
    this.loadInstanceGroups();
  }

  async loadInstanceGroups () {
    const {
      api,
      handleHttpError,
      match
    } = this.props;
    try {
      const {
        data
      } = await api.getOrganizationInstanceGroups(match.params.id);
      this.setState({
        instanceGroups: [...data.results]
      });
    } catch (err) {
      handleHttpError(err) || this.setState({ error: true });
    }
  }

  render () {
    const {
      error,
      instanceGroups,
    } = this.state;

    const {
      organization: {
        name,
        description,
        custom_virtualenv,
        created,
        modified,
        summary_fields
      },
      match,
      i18n
    } = this.props;

    return (
      <CardBody>
        <DetailList>
          <Detail
            label={i18n._(t`Name`)}
            value={name}
          />
          <Detail
            label={i18n._(t`Description`)}
            value={description}
          />
          <Detail
            label={i18n._(t`Ansible Environment`)}
            value={custom_virtualenv}
          />
          <Detail
            label={i18n._(t`Created`)}
            value={created}
          />
          <Detail
            label={i18n._(t`Last Modified`)}
            value={modified}
          />
          {(instanceGroups && instanceGroups.length > 0) && (
            <Detail
              fullWidth
              label={i18n._(t`Instance Groups`)}
              value={(
                <ChipGroup showOverflowAfter={5}>
                  {instanceGroups.map(ig => (
                    <Chip key={ig.id} isReadOnly>{ig.name}</Chip>
                  ))}
                </ChipGroup>
              )}
            />
          )}
        </DetailList>
        {summary_fields.user_capabilities.edit && (
          <div css="margin-top: 10px; text-align: right;">
            <Button
              component={Link}
              to={`/organizations/${match.params.id}/edit`}
            >
              {i18n._(t`Edit`)}
            </Button>
          </div>
        )}
        {error ? 'error!' : ''}
      </CardBody>
    );
  }
}

export default withI18n()(withRouter(withNetwork(OrganizationDetail)));
