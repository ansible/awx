import React, { Component } from 'react';
import { Link, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import {
  CardBody as PFCardBody,
  Button,
  TextList,
  TextListItem,
  TextListVariants,
  TextListItemVariants,
} from '@patternfly/react-core';
import styled from 'styled-components';
import { withNetwork } from '../../../../contexts/Network';
import BasicChip from '../../../../components/BasicChip/BasicChip';

const CardBody = styled(PFCardBody)`
  padding-top: 20px;
`;

const DetailList = styled(TextList)`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(270px, 1fr));
  grid-gap: 20px;

  & > div {
    display: grid;
    grid-template-columns: 10em 1fr;
    grid-gap: 20px;
  }
`;

const DetailName = styled(TextListItem)`
  && {
    grid-column: 1;
    font-weight: var(--pf-global--FontWeight--bold);
    text-align: right;
  }
`;

const DetailValue = styled(TextListItem)`
  && {
    grid-column: 2;
    word-break: break-all;
  }
`;

const InstanceGroupsDetail = styled.div`
  grid-column: 1 / -1;
`;

const Detail = ({ label, value }) => {
  if (!value) return null;
  return (
    <div>
      <DetailName component={TextListItemVariants.dt}>{label}</DetailName>
      <DetailValue component={TextListItemVariants.dd}>{value}</DetailValue>
    </div>
  );
};

class OrganizationDetail extends Component {
  constructor (props) {
    super(props);

    this.state = {
      instanceGroups: [],
      isToggleOpen: false,
      error: false
    };

    this.handleChipToggle = this.handleChipToggle.bind(this);
    this.loadInstanceGroups = this.loadInstanceGroups.bind(this);
  }

  componentDidMount () {
    this.loadInstanceGroups();
  }

  handleChipToggle = () => {
    this.setState((prevState) => ({
      isToggleOpen: !prevState.isToggleOpen
    }));
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
      isToggleOpen,
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
    const showOverflowChipAfter = 5;

    const instanceGroupChips = instanceGroups.slice(0, isToggleOpen
      ? instanceGroups.length : showOverflowChipAfter)
      .map(instanceGroup => (
        <BasicChip
          key={instanceGroup.id}
        >
          {instanceGroup.name}
        </BasicChip>
      ));

    const overflowChip = (instanceGroups.length > showOverflowChipAfter) ? (
      <BasicChip
        isOverflowChip
        onToggle={this.handleChipToggle}
      >
        {isToggleOpen ? 'Show less' : `${(instanceGroups.length - showOverflowChipAfter).toString()} more`}
      </BasicChip>
    ) : null;

    return (
      <CardBody>
        <DetailList component={TextListVariants.dl}>
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
            <InstanceGroupsDetail>
              <DetailName component={TextListItemVariants.dt}>
                {i18n._(t`Instance Groups`)}
              </DetailName>
              <DetailValue component={TextListItemVariants.dd}>
                {instanceGroupChips}
                {overflowChip}
              </DetailValue>
            </InstanceGroupsDetail>
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
