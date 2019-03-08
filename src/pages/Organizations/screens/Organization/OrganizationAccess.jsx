import React from 'react';
import AccessList from '../../../../components/AccessList';

class OrganizationAccess extends React.Component {
  constructor (props) {
    super(props);

    this.getOrgAccessList = this.getOrgAccessList.bind(this);
    this.removeRole = this.removeRole.bind(this);
  }

  getOrgAccessList (id, params) {
    const { api } = this.props;
    return api.getOrganzationAccessList(id, params);
  }

  removeRole (url, id) {
    const { api } = this.props;
    return api.disassociate(url, id);
  }

  render () {
    const {
      location,
      match,
      history,
    } = this.props;

    return (
      <AccessList
        getAccessList={this.getOrgAccessList}
        removeRole={this.removeRole}
        match={match}
        location={location}
        history={history}
      />
    );
  }
}

export default OrganizationAccess;
