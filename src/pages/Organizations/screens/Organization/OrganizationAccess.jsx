import React, { Fragment } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import AlertModal from '../../../../components/AlertModal';
import PaginatedDataList, { ToolbarAddButton } from '../../../../components/PaginatedDataList';
import DataListToolbar from '../../../../components/DataListToolbar';
import OrganizationAccessItem from '../../components/OrganizationAccessItem';
import DeleteRoleConfirmationModal from '../../components/DeleteRoleConfirmationModal';
import AddResourceRole from '../../../../components/AddRole/AddResourceRole';
import {
  getQSConfig,
  encodeQueryString,
  parseNamespacedQueryString
} from '../../../../util/qs';
import { Organization } from '../../../../types';
import { OrganizationsAPI, TeamsAPI, UsersAPI } from '../../../../api';

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
    this.state = {
      accessRecords: [],
      contentError: false,
      contentLoading: true,
      deletionError: false,
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

  componentDidMount () {
    this.loadAccessList();
  }

  componentDidUpdate (prevProps) {
    const { location } = this.props;

    const prevParams = parseNamespacedQueryString(QS_CONFIG, prevProps.location.search);
    const currentParams = parseNamespacedQueryString(QS_CONFIG, location.search);

    if (encodeQueryString(currentParams) !== encodeQueryString(prevParams)) {
      this.loadAccessList();
    }
  }

  async loadAccessList () {
    const { organization, location } = this.props;
    const params = parseNamespacedQueryString(QS_CONFIG, location.search);

    this.setState({ contentError: false, contentLoading: true });
    try {
      const {
        data: {
          results: accessRecords = [],
          count: itemCount = 0
        }
      } = await OrganizationsAPI.readAccessList(organization.id, params);
      this.setState({ itemCount, accessRecords });
    } catch (error) {
      this.setState({ contentError: true });
    } finally {
      this.setState({ contentLoading: false });
    }
  }

  handleDeleteOpen (deletionRole, deletionRecord) {
    this.setState({ deletionRole, deletionRecord });
  }

  handleDeleteCancel () {
    this.setState({ deletionRole: null, deletionRecord: null });
  }

  handleDeleteErrorClose () {
    this.setState({
      deletionError: false,
      deletionRecord: null,
      deletionRole: null
    });
  }

  async handleDeleteConfirm () {
    const { deletionRole, deletionRecord } = this.state;

    if (!deletionRole || !deletionRecord) {
      return;
    }

    let promise;
    if (typeof deletionRole.team_id !== 'undefined') {
      promise = TeamsAPI.disassociateRole(deletionRole.team_id, deletionRole.id);
    } else {
      promise = UsersAPI.disassociateRole(deletionRecord.id, deletionRole.id);
    }

    this.setState({ contentLoading: true });
    try {
      await promise.then(this.loadAccessList);
      this.setState({
        deletionRole: null,
        deletionRecord: null
      });
    } catch (error) {
      this.setState({
        contentLoading: false,
        deletionError: true
      });
    }
  }

  handleAddClose () {
    this.setState({ isAddModalOpen: false });
  }

  handleAddOpen () {
    this.setState({ isAddModalOpen: true });
  }

  handleAddSuccess () {
    this.setState({ isAddModalOpen: false });
    this.loadAccessList();
  }

  render () {
    const { organization, i18n } = this.props;
    const {
      accessRecords,
      contentError,
      contentLoading,
      deletionRole,
      deletionRecord,
      deletionError,
      itemCount,
      isAddModalOpen,
    } = this.state;
    const canEdit = organization.summary_fields.user_capabilities.edit;
    const isDeleteModalOpen = !contentLoading && !deletionError && deletionRole;

    return (
      <Fragment>
        <PaginatedDataList
          contentError={contentError}
          contentLoading={contentLoading}
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
                <ToolbarAddButton key="add" onClick={this.handleAddOpen} />
              ] : null}
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
          isOpen={deletionError}
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
