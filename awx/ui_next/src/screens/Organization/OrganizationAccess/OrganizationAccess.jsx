import React, { Fragment } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { OrganizationsAPI, TeamsAPI, UsersAPI } from '@api';
import AddResourceRole from '@components/AddRole/AddResourceRole';
import AlertModal from '@components/AlertModal';
import DataListToolbar from '@components/DataListToolbar';
import PaginatedDataList, {
  ToolbarAddButton,
} from '@components/PaginatedDataList';
import { getQSConfig, encodeQueryString, parseQueryString } from '@util/qs';
import { Organization } from '@types';

import DeleteRoleConfirmationModal from './DeleteRoleConfirmationModal';
import OrganizationAccessItem from './OrganizationAccessItem';

const QS_CONFIG = getQSConfig('access', {
  page: 1,
  page_size: 5,
  order_by: 'first_name',
});

class OrganizationAccess extends React.Component {
  static propTypes = {
    organization: Organization.isRequired,
  };

  constructor(props) {
    super(props);
    this.state = {
      accessRecords: [],
      contentError: null,
      hasContentLoading: true,
      hasDeletionError: false,
      deletionRecord: null,
      deletionRole: null,
      isAddModalOpen: false,
      itemCount: 0,
    };
    this.loadAccessList = this.loadAccessList.bind(this);
    this.handleAddClose = this.handleAddClose.bind(this);
    this.handleAddOpen = this.handleAddOpen.bind(this);
    this.handleAddSuccess = this.handleAddSuccess.bind(this);
    this.handleDeleteCancel = this.handleDeleteCancel.bind(this);
    this.handleDeleteConfirm = this.handleDeleteConfirm.bind(this);
    this.handleDeleteErrorClose = this.handleDeleteErrorClose.bind(this);
    this.handleDeleteOpen = this.handleDeleteOpen.bind(this);
  }

  componentDidMount() {
    this.loadAccessList();
  }

  componentDidUpdate(prevProps) {
    const { location } = this.props;

    const prevParams = parseQueryString(QS_CONFIG, prevProps.location.search);
    const currentParams = parseQueryString(QS_CONFIG, location.search);

    if (encodeQueryString(currentParams) !== encodeQueryString(prevParams)) {
      this.loadAccessList();
    }
  }

  async loadAccessList() {
    const { organization, location } = this.props;
    const params = parseQueryString(QS_CONFIG, location.search);

    this.setState({ contentError: null, hasContentLoading: true });
    try {
      const {
        data: { results: accessRecords = [], count: itemCount = 0 },
      } = await OrganizationsAPI.readAccessList(organization.id, params);
      this.setState({ itemCount, accessRecords });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  handleDeleteOpen(deletionRole, deletionRecord) {
    this.setState({ deletionRole, deletionRecord });
  }

  handleDeleteCancel() {
    this.setState({ deletionRole: null, deletionRecord: null });
  }

  handleDeleteErrorClose() {
    this.setState({
      hasDeletionError: false,
      deletionRecord: null,
      deletionRole: null,
    });
  }

  async handleDeleteConfirm() {
    const { deletionRole, deletionRecord } = this.state;

    if (!deletionRole || !deletionRecord) {
      return;
    }

    let promise;
    if (typeof deletionRole.team_id !== 'undefined') {
      promise = TeamsAPI.disassociateRole(
        deletionRole.team_id,
        deletionRole.id
      );
    } else {
      promise = UsersAPI.disassociateRole(deletionRecord.id, deletionRole.id);
    }

    this.setState({ hasContentLoading: true });
    try {
      await promise.then(this.loadAccessList);
      this.setState({
        deletionRole: null,
        deletionRecord: null,
      });
    } catch (error) {
      this.setState({
        hasContentLoading: false,
        hasDeletionError: true,
      });
    }
  }

  handleAddClose() {
    this.setState({ isAddModalOpen: false });
  }

  handleAddOpen() {
    this.setState({ isAddModalOpen: true });
  }

  handleAddSuccess() {
    this.setState({ isAddModalOpen: false });
    this.loadAccessList();
  }

  render() {
    const { organization, i18n } = this.props;
    const {
      accessRecords,
      contentError,
      hasContentLoading,
      deletionRole,
      deletionRecord,
      hasDeletionError,
      itemCount,
      isAddModalOpen,
    } = this.state;
    const canEdit = organization.summary_fields.user_capabilities.edit;
    const isDeleteModalOpen =
      !hasContentLoading && !hasDeletionError && deletionRole;

    return (
      <Fragment>
        <PaginatedDataList
          error={contentError}
          hasContentLoading={hasContentLoading}
          items={accessRecords}
          itemCount={itemCount}
          itemName={itemCount.length === 1 ? i18n._(t`Role`): i18n._(t`Roles`)}
          qsConfig={QS_CONFIG}
          toolbarColumns={[
            {
              name: i18n._(t`First Name`),
              key: 'first_name',
              isSortable: true,
              isSearchable: true,
            },
            {
              name: i18n._(t`Username`),
              key: 'username',
              isSortable: true,
              isSearchable: true,
            },
            {
              name: i18n._(t`Last Name`),
              key: 'last_name',
              isSortable: true,
              isSearchable: true,
            },
          ]}
          renderToolbar={props => (
            <DataListToolbar
              {...props}
              qsConfig={QS_CONFIG}
              additionalControls={
                canEdit
                  ? [
                      <ToolbarAddButton
                        key="add"
                        onClick={this.handleAddOpen}
                      />,
                    ]
                  : null
              }
            />
          )}
          renderItem={accessRecord => (
            <OrganizationAccessItem
              key={accessRecord.id}
              accessRecord={accessRecord}
              onRoleDelete={this.handleDeleteOpen}
            />
          )}
        />
        {isAddModalOpen && (
          <AddResourceRole
            onClose={this.handleAddClose}
            onSave={this.handleAddSuccess}
            roles={organization.summary_fields.object_roles}
          />
        )}
        {isDeleteModalOpen && (
          <DeleteRoleConfirmationModal
            role={deletionRole}
            username={deletionRecord.username}
            onCancel={this.handleDeleteCancel}
            onConfirm={this.handleDeleteConfirm}
          />
        )}
        <AlertModal
          isOpen={hasDeletionError}
          variant="danger"
          title={i18n._(t`Error!`)}
          onClose={this.handleDeleteErrorClose}
        >
          {i18n._(t`Failed to delete role`)}
        </AlertModal>
      </Fragment>
    );
  }
}

export { OrganizationAccess as _OrganizationAccess };
export default withI18n()(withRouter(OrganizationAccess));
