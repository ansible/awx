import React, { Component } from 'react';
import { Link, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { CardBody, Button } from '@patternfly/react-core';
import styled from 'styled-components';

const ActionButtonWrapper = styled.div`
  display: flex;
  justify-content: flex-end;
`;
class JobDetail extends Component {
  constructor (props) {
    super(props);
  }

  render () {
    const {
      job,
      i18n
    } = this.props;


    return (
      <CardBody>
        <b>{job.name}</b>

        <ActionButtonWrapper>
          <Button
            variant='secondary'
            aria-label="close"
            component={Link}
            to={`/jobs`}
          >
            {i18n._(t`Close`)}
          </Button>
        </ActionButtonWrapper>
      </CardBody>
    );
  }
}

export default withI18n()(withRouter(JobDetail));
