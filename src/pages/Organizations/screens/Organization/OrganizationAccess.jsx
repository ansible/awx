import React, { Fragment } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import PaginatedDataList, { ToolbarAddButton } from '../../../../components/PaginatedDataList';
import DataListToolbar from '../../../../components/DataListToolbar';
import OrganizationAccessItem from '../../components/OrganizationAccessItem';
import DeleteRoleConfirmationModal from '../../components/DeleteRoleConfirmationModal';
import AddResourceRole from '../../../../components/AddRole/AddResourceRole';
import { withNetwork } from '../../../../contexts/Network';
import { getQSConfig, parseNamespacedQueryString } from '../../../../util/qs';
import { Organization } from '../../../../types';

const QS_CONFIG = getQSConfig('access', {
  page: 1,
  page_size: 5,
  order_by: 'first_name',
});

class OrganizationAccess extends React.Component {
  static propTypes = {
    organization: Organization.isRequired,
  };

  constructor (props) {
    super(props);

    this.readOrgAccessList = this.readOrgAccessList.bind(this);
    this.confirmRemoveRole = this.confirmRemoveRole.bind(this);
    this.cancelRemoveRole = this.cancelRemoveRole.bind(this);
    this.removeRole = this.removeRole.bind(this);
    this.toggleAddModal = this.toggleAddModal.bind(this);
    this.handleSuccessfulRoleAdd = this.handleSuccessfulRoleAdd.bind(this);

    this.state = {
      isLoading: false,
      isInitialized: false,
      isAddModalOpen: false,
      error: null,
      itemCount: 0,
      accessRecords: [],
      roleToDelete: null,
      roleToDeleteAccessRecord: null,
    };
  }

  componentDidMount () {
    this.readOrgAccessList();
  }

  componentDidUpdate (prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      this.readOrgAccessList();
    }
  }

  async readOrgAccessList () {
    const { organization, api, handleHttpError, location } = this.props;
    this.setState({ isLoading: true });
    try {
      const { data } = await api.getOrganizationAccessList(
        organization.id,
        parseNamespacedQueryString(QS_CONFIG, location.search)
      );
      this.setState({
        itemCount: data.count || 0,
        accessRecords: data.results || [],
        isLoading: false,
        isInitialized: true,
      });
    } catch (error) {
      handleHttpError(error) || this.setState({
        error,
        isLoading: false,
      });
    }
  }

  confirmRemoveRole (role, accessRecord) {
    this.setState({
      roleToDelete: role,
      roleToDeleteAccessRecord: accessRecord,
    });
  }

  cancelRemoveRole () {
    this.setState({
      roleToDelete: null,
      roleToDeleteAccessRecord: null
    });
  }

  async removeRole () {
    const { api, handleHttpError } = this.props;
    const { roleToDelete: role, roleToDeleteAccessRecord: accessRecord } = this.state;
    if (!role || !accessRecord) {
      return;
    }
    const type = typeof role.team_id === 'undefined' ? 'users' : 'teams';
    this.setState({ isLoading: true });
    try {
      if (type === 'teams') {
        await api.disassociateTeamRole(role.team_id, role.id);
      } else {
        await api.disassociateUserRole(accessRecord.id, role.id);
      }
      this.setState({
        isLoading: false,
        roleToDelete: null,
        roleToDeleteAccessRecord: null,
      });
      this.readOrgAccessList();
    } catch (error) {
      handleHttpError(error) || this.setState({
        error,
        isLoading: false,
      });
    }
  }

  toggleAddModal () {
    const { isAddModalOpen } = this.state;
    this.setState({
      isAddModalOpen: !isAddModalOpen,
    });
  }

  handleSuccessfulRoleAdd () {
    this.toggleAddModal();
    this.readOrgAccessList();
  }

  render () {
    const { organization, i18n } = this.props;
    const {
      isLoading,
      isInitialized,
      itemCount,
      isAddModalOpen,
      accessRecords,
      roleToDelete,
      roleToDeleteAccessRecord,
      error,
    } = this.state;

    const canEdit = organization.summary_fields.user_capabilities.edit;

    if (error) {
      // TODO: better error state
      return <div>{error.message}</div>;
    }
    // TODO: better loading state
    return (
      <Fragment>
        {isLoading && (<div>Loading...</div>)}
        {roleToDelete && (
          <DeleteRoleConfirmationModal
            role={roleToDelete}
            username={roleToDeleteAccessRecord.username}
            onCancel={this.cancelRemoveRole}
            onConfirm={this.removeRole}
          />
        )}
        {isInitialized && (
          <PaginatedDataList
            items={accessRecords}
            itemCount={itemCount}
            itemName="role"
            qsConfig={QS_CONFIG}
            toolbarColumns={[
              { name: i18n._(t`Name`), key: 'first_name', isSortable: true },
              { name: i18n._(t`Username`), key: 'username', isSortable: true },
              { name: i18n._(t`Last Name`), key: 'last_name', isSortable: true },
            ]}
            renderToolbar={(props) => (
              <DataListToolbar
                {...props}
                additionalControls={canEdit ? [
                  <ToolbarAddButton key="add" onClick={this.toggleAddModal} />
                ] : null}
              />
            )}
            renderItem={accessRecord => (
              <OrganizationAccessItem
                key={accessRecord.id}
                accessRecord={accessRecord}
                onRoleDelete={this.confirmRemoveRole}
              />
            )}
          />
        )}
        {isAddModalOpen && (
          <AddResourceRole
            onClose={this.toggleAddModal}
            onSave={this.handleSuccessfulRoleAdd}
            roles={organization.summary_fields.object_roles}
          />
        )}
      </Fragment>
    );
  }
}

export { OrganizationAccess as _OrganizationAccess };
export default withI18n()(withNetwork(withRouter(OrganizationAccess)));
