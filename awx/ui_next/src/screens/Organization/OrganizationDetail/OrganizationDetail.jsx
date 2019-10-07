import React, { Component } from 'react';
import { Link, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { CardBody as PFCardBody, Button } from '@patternfly/react-core';
import styled from 'styled-components';

import { OrganizationsAPI } from '@api';
import { DetailList, Detail } from '@components/DetailList';
import { ChipGroup, Chip } from '@components/Chip';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import { formatDateString } from '@util/dates';

const CardBody = styled(PFCardBody)`
  padding-top: 20px;
`;

class OrganizationDetail extends Component {
  constructor(props) {
    super(props);

    this.state = {
      contentError: null,
      hasContentLoading: true,
      instanceGroups: [],
    };
    this.loadInstanceGroups = this.loadInstanceGroups.bind(this);
  }

  componentDidMount() {
    this.loadInstanceGroups();
  }

  async loadInstanceGroups() {
    const {
      match: {
        params: { id },
      },
    } = this.props;

    this.setState({ hasContentLoading: true });
    try {
      const {
        data: { results = [] },
      } = await OrganizationsAPI.readInstanceGroups(id);
      this.setState({ instanceGroups: [...results] });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  render() {
    const { hasContentLoading, contentError, instanceGroups } = this.state;
    const {
      organization: {
        name,
        description,
        custom_virtualenv,
        max_hosts,
        created,
        modified,
        summary_fields,
      },
      match,
      i18n,
    } = this.props;

    if (hasContentLoading) {
      return <ContentLoading />;
    }

    if (contentError) {
      return <ContentError error={contentError} />;
    }

    return (
      <CardBody>
        <DetailList>
          <Detail label={i18n._(t`Name`)} value={name} />
          <Detail label={i18n._(t`Description`)} value={description} />
          <Detail label={i18n._(t`Max Hosts`)} value={`${max_hosts}`} />
          <Detail
            label={i18n._(t`Ansible Environment`)}
            value={custom_virtualenv}
          />
          <Detail
            label={i18n._(t`Created`)}
            value={formatDateString(created)}
          />
          <Detail
            label={i18n._(t`Last Modified`)}
            value={formatDateString(modified)}
          />
          {instanceGroups && instanceGroups.length > 0 && (
            <Detail
              fullWidth
              label={i18n._(t`Instance Groups`)}
              value={
                <ChipGroup showOverflowAfter={5}>
                  {instanceGroups.map(ig => (
                    <Chip key={ig.id} isReadOnly>
                      {ig.name}
                    </Chip>
                  ))}
                </ChipGroup>
              }
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
      </CardBody>
    );
  }
}

export default withI18n()(withRouter(OrganizationDetail));
