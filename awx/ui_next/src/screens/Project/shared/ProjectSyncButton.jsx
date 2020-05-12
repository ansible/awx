import React, { Fragment } from 'react';
import { number } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import AlertModal from '../../../components/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail';
import { ProjectsAPI } from '../../../api';

class ProjectSyncButton extends React.Component {
  static propTypes = {
    projectId: number.isRequired,
  };

  constructor(props) {
    super(props);

    this.state = {
      syncError: null,
    };

    this.handleSync = this.handleSync.bind(this);
    this.handleSyncErrorClose = this.handleSyncErrorClose.bind(this);
  }

  handleSyncErrorClose() {
    this.setState({ syncError: null });
  }

  async handleSync() {
    const { i18n, projectId } = this.props;
    try {
      const { data: syncConfig } = await ProjectsAPI.readSync(projectId);
      if (syncConfig.can_update) {
        await ProjectsAPI.sync(projectId);
      } else {
        this.setState({
          syncError: i18n._(
            t`You don't have the necessary permissions to sync this project.`
          ),
        });
      }
    } catch (err) {
      this.setState({ syncError: err });
    }
  }

  render() {
    const { syncError } = this.state;
    const { i18n, children } = this.props;
    return (
      <Fragment>
        {children(this.handleSync)}
        {syncError && (
          <AlertModal
            isOpen={syncError}
            variant="error"
            title={i18n._(t`Error!`)}
            onClose={this.handleSyncErrorClose}
          >
            {i18n._(t`Failed to sync job.`)}
            <ErrorDetail error={syncError} />
          </AlertModal>
        )}
      </Fragment>
    );
  }
}

export default withI18n()(ProjectSyncButton);
