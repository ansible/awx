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
  minWidth: '150px',
  marginRight: '20px',
  textAlign: 'right'
};

const Detail = ({ label, value }) => {
  let detail = null;
  if (value) {
    detail = (
      <TextContent style={detailWrapperStyle}>
        <Text component={TextVariants.h6} style={detailLabelStyle}>{ label }</Text>
        <Text component={TextVariants.p}>{ value }</Text>
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

    return (
      <I18n>
        {({ i18n }) => (
          <CardBody className="pf-u-pt-lg">
            <div className="pf-l-grid pf-m-gutter pf-m-all-12-col-on-md pf-m-all-6-col-on-lg pf-m-all-4-col-on-xl">
              <Detail
                label={i18n._(t`Name`)}
                value={name}
              />
              <Detail
                label={i18n._(t`Description`)}
                value={description}
              />
              {(instanceGroups && instanceGroups.length > 0) && (
                <TextContent style={detailWrapperStyle}>
                  <Text
                    component={TextVariants.h6}
                    style={detailLabelStyle}
                  >
                    <Trans>Instance Groups</Trans>
                  </Text>
                  <div>
                    {instanceGroups.map(instanceGroup => (
                      <BasicChip
                        key={instanceGroup.id}
                        text={instanceGroup.name}
                      />
                    ))}
                  </div>
                </TextContent>
              )}
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
            </div>
            <div className="pf-u-display-flex pf-u-flex-direction-row-reverse pf-u-ml-auto pf-u-mt-md">
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
