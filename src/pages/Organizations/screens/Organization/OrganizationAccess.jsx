import React from 'react';
import AccessList from '../../../../components/AccessList';

class OrganizationAccess extends React.Component {
  constructor (props) {
    super(props);

    this.getOrgAccessList = this.getOrgAccessList.bind(this);
  }

  getOrgAccessList (id, params) {
    const { api } = this.props;
    return api.getOrganzationAccessList(id, params);
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
        match={match}
        location={location}
        history={history}
      />
    );
  }
}

export default OrganizationAccess;
