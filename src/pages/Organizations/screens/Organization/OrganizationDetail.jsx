import React, { Component } from 'react';
import { Link } from 'react-router-dom';
import { I18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';
import {
  CardBody,
  Button,
  Text,
  TextContent,
  TextVariants,
} from '@patternfly/react-core';
import BasicChip from '../../../../components/BasicChip/BasicChip';

const detailWrapperStyle = {
  display: 'flex'
};

const detailLabelStyle = {
  fontWeight: '700',
  lineHeight: '24px',
  marginRight: '20px',
  minWidth: '150px',
  textAlign: 'right'
};

const detailValueStyle = {
  lineHeight: '24px',
  wordBreak: 'break-all'
};

const Detail = ({ label, value }) => {
  let detail = null;
  if (value) {
    detail = (
      <TextContent style={detailWrapperStyle}>
        <Text component={TextVariants.h6} style={detailLabelStyle}>{ label }</Text>
        <Text component={TextVariants.p} style={detailValueStyle}>{ value }</Text>
      </TextContent>
    );
  }
  return detail;
};

class OrganizationDetail extends Component {
  constructor (props) {
    super(props);

    this.state = {
      instanceGroups: [],
      isToggleOpen: false,
      error: false
    };

    this.showOverflowChipAfter = 5;
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
      this.setState({ error: true });
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
        modified
      },
      match
    } = this.props;

    const instanceGroupChips = instanceGroups.slice(0, isToggleOpen
      ? instanceGroups.length : this.showOverflowChipAfter)
      .map(instanceGroup => (
        <BasicChip
          key={instanceGroup.id}
        >
          {instanceGroup.name}
        </BasicChip>
      ));

    const overflowChip = (instanceGroups.length > this.showOverflowChipAfter) ? (
      <BasicChip
        isOverflowChip
        onToggle={this.handleChipToggle}
      >
        {isToggleOpen ? 'Show less' : `${(instanceGroups.length - this.showOverflowChipAfter).toString()} more`}
      </BasicChip>
    ) : null;

    return (
      <I18n>
        {({ i18n }) => (
          <CardBody>
            <div className="pf-l-grid pf-m-gutter pf-m-all-12-col-on-md pf-m-all-6-col-on-lg pf-m-all-4-col-on-xl">
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
                <TextContent style={{ display: 'flex', gridColumn: '1 / -1' }}>
                  <Text
                    component={TextVariants.h6}
                    style={detailLabelStyle}
                  >
                    <Trans>Instance Groups</Trans>
                  </Text>
                  <div style={detailValueStyle}>
                    {instanceGroupChips}
                    {overflowChip}
                  </div>
                </TextContent>
              )}
            </div>
            <div style={{ display: 'flex', flexDirection: 'row-reverse', marginTop: '20px' }}>
              <Link to={`/organizations/${match.params.id}/edit`}>
                <Button><Trans>Edit</Trans></Button>
              </Link>
            </div>
            {error ? 'error!' : ''}
          </CardBody>
        )}
      </I18n>
    );
  }
}

export default OrganizationDetail;
