import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { useHistory } from 'react-router-dom';
import { CardBody } from '../../../components/Card';
import { OrganizationsAPI } from '../../../api';
import { Config } from '../../../contexts/Config';

import NotificationTemplateForm from '../shared/NotificationTemplateForm';

function NotificationTemplateEdit({ template, defaultMessages }) {
  const detailsUrl = `/notification_templates/${template.id}/details`;
  const history = useHistory();
  const [formError, setFormError] = useState(null);

  const handleSubmit = async (
    values,
    groupsToAssociate,
    groupsToDisassociate
  ) => {
    try {
      await OrganizationsAPI.update(template.id, values);
      await Promise.all(
        groupsToAssociate.map(id =>
          OrganizationsAPI.associateInstanceGroup(template.id, id)
        )
      );
      await Promise.all(
        groupsToDisassociate.map(id =>
          OrganizationsAPI.disassociateInstanceGroup(template.id, id)
        )
      );
      history.push(detailsUrl);
    } catch (error) {
      setFormError(error);
    }
  };

  const handleCancel = () => {
    history.push(detailsUrl);
  };

  return (
    <CardBody>
      <NotificationTemplateForm
        template={template}
        defaultMessages={defaultMessages}
        onSubmit={handleSubmit}
        onCancel={handleCancel}
        submitError={formError}
      />
    </CardBody>
  );
}

NotificationTemplateEdit.propTypes = {
  template: PropTypes.shape().isRequired,
};

NotificationTemplateEdit.contextTypes = {
  custom_virtualenvs: PropTypes.arrayOf(PropTypes.string),
};

export { NotificationTemplateEdit as _NotificationTemplateEdit };
export default NotificationTemplateEdit;
