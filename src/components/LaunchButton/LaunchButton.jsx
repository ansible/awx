import React, { Fragment } from 'react';
import { withRouter } from 'react-router-dom';
import { number } from 'prop-types';
import { Button, Tooltip } from '@patternfly/react-core';
import { RocketIcon } from '@patternfly/react-icons';
import styled from 'styled-components';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import AlertModal from '@components/AlertModal';
import ErrorDetail from '@components/ErrorDetail';
import { JobTemplatesAPI } from '@api';

const StyledLaunchButton = styled(Button)`
  padding: 5px 8px;

  &:hover {
    background-color:#d9534f;
    color: white;
  }
`;

class LaunchButton extends React.Component {
  static propTypes = {
    templateId: number.isRequired,
  };

  constructor (props) {
    super(props);

    this.state = {
      launchError: null,
      promptError: false
    };

    this.handleLaunch = this.handleLaunch.bind(this);
    this.handleLaunchErrorClose = this.handleLaunchErrorClose.bind(this);
    this.handlePromptErrorClose = this.handlePromptErrorClose.bind(this);
  }

  handleLaunchErrorClose () {
    this.setState({ launchError: null });
  }

  handlePromptErrorClose () {
    this.setState({ promptError: false });
  }

  async handleLaunch () {
    const { history, templateId } = this.props;
    try {
      const { data: launchConfig } = await JobTemplatesAPI.readLaunch(templateId);
      if (launchConfig.can_start_without_user_input) {
        const { data: job } = await JobTemplatesAPI.launch(templateId);
        history.push(`/jobs/${job.id}/details`);
      } else {
        this.setState({ promptError: true });
      }
    } catch (err) {
      this.setState({ launchError: err });
    }
  }

  render () {
    const {
      launchError,
      promptError
    } = this.state;
    const { i18n } = this.props;
    return (
      <Fragment>
        <Tooltip
          content={i18n._(t`Launch Job`)}
          position="top"
        >
          <div>
            <StyledLaunchButton
              variant="plain"
              aria-label={i18n._(t`Launch`)}
              onClick={this.handleLaunch}
            >
              <RocketIcon />
            </StyledLaunchButton>
          </div>
        </Tooltip>
        <AlertModal
          isOpen={launchError}
          variant="danger"
          title={i18n._(t`Error!`)}
          onClose={this.handleLaunchErrorClose}
        >
          {i18n._(t`Failed to launch job.`)}
          <ErrorDetail error={launchError} />
        </AlertModal>
        <AlertModal
          isOpen={promptError}
          variant="info"
          title={i18n._(t`Attention!`)}
          onClose={this.handlePromptErrorClose}
        >
          {i18n._(t`Launching jobs with promptable fields is not supported at this time.`)}
        </AlertModal>
      </Fragment>
    );
  }
}

export default withI18n()(withRouter(LaunchButton));
