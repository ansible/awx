/* eslint react/no-unused-state: 0 */
import React, { Component } from 'react';
import { withRouter, Redirect } from 'react-router-dom';
import { CardBody } from '@patternfly/react-core';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import { JobTemplatesAPI, ProjectsAPI } from '@api';
import { JobTemplate } from '@types';
import JobTemplateForm from '../shared/JobTemplateForm';

class JobTemplateEdit extends Component {
  static propTypes = {
    template: JobTemplate.isRequired,
  };

  constructor(props) {
    super(props);

    this.state = {
      hasContentLoading: true,
      contentError: null,
      formSubmitError: null,
      relatedCredentials: [],
      relatedProjectPlaybooks: [],
    };

    const {
      template: { id, type },
    } = props;
    this.detailsUrl = `/templates/${type}/${id}/details`;

    this.handleCancel = this.handleCancel.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.loadRelatedCredentials = this.loadRelatedCredentials.bind(this);
    this.loadRelatedProjectPlaybooks = this.loadRelatedProjectPlaybooks.bind(
      this
    );
    this.submitLabels = this.submitLabels.bind(this);
  }

  componentDidMount() {
    this.loadRelated();
  }

  async loadRelated() {
    this.setState({ contentError: null, hasContentLoading: true });
    try {
      const [relatedCredentials, relatedProjectPlaybooks] = await Promise.all([
        this.loadRelatedCredentials(),
        this.loadRelatedProjectPlaybooks(),
      ]);
      this.setState({
        relatedCredentials,
        relatedProjectPlaybooks,
      });
    } catch (contentError) {
      this.setState({ contentError });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  async loadRelatedCredentials() {
    const {
      template: { id },
    } = this.props;
    const params = {
      page: 1,
      page_size: 200,
      order_by: 'name',
    };
    try {
      const {
        data: { results: credentials = [] },
      } = await JobTemplatesAPI.readCredentials(id, params);
      return credentials;
    } catch (err) {
      if (err.status !== 403) throw err;

      this.setState({ hasRelatedCredentialAccess: false });
      const {
        template: {
          summary_fields: { credentials = [] },
        },
      } = this.props;

      return credentials;
    }
  }

  async loadRelatedProjectPlaybooks() {
    const {
      template: { project },
    } = this.props;
    try {
      const { data: playbooks = [] } = await ProjectsAPI.readPlaybooks(project);
      this.setState({ relatedProjectPlaybooks: playbooks });
      return playbooks;
    } catch (err) {
      throw err;
    }
  }

  async handleSubmit(values) {
    const { template, history } = this.props;
    const {
      newLabels,
      removedLabels,
      addedInstanceGroups,
      removedInstanceGroups,
      ...remainingValues
    } = values;

    this.setState({ formSubmitError: null });
    try {
      await JobTemplatesAPI.update(template.id, remainingValues);
      await Promise.all([
        this.submitLabels(newLabels, removedLabels),
        this.submitInstanceGroups(addedInstanceGroups, removedInstanceGroups),
      ]);
      history.push(this.detailsUrl);
    } catch (formSubmitError) {
      this.setState({ formSubmitError });
    }
  }

  async submitLabels(newLabels = [], removedLabels = []) {
    const { template } = this.props;
    const disassociationPromises = removedLabels.map(label =>
      JobTemplatesAPI.disassociateLabel(template.id, label)
    );
    const associationPromises = newLabels
      .filter(label => !label.organization)
      .map(label => JobTemplatesAPI.associateLabel(template.id, label));
    const creationPromises = newLabels
      .filter(label => label.organization)
      .map(label => JobTemplatesAPI.generateLabel(template.id, label));

    const results = await Promise.all([
      ...disassociationPromises,
      ...associationPromises,
      ...creationPromises,
    ]);
    return results;
  }

  async submitInstanceGroups(addedGroups, removedGroups) {
    const { template } = this.props;
    const associatePromises = addedGroups.map(group =>
      JobTemplatesAPI.associateInstanceGroup(template.id, group.id)
    );
    const disassociatePromises = removedGroups.map(group =>
      JobTemplatesAPI.disassociateInstanceGroup(template.id, group.id)
    );
    return Promise.all([...associatePromises, ...disassociatePromises]);
  }

  handleCancel() {
    const { history } = this.props;
    history.push(this.detailsUrl);
  }

  render() {
    const { template } = this.props;
    const {
      contentError,
      formSubmitError,
      hasContentLoading,
      relatedProjectPlaybooks,
    } = this.state;
    const canEdit = template.summary_fields.user_capabilities.edit;

    if (hasContentLoading) {
      return <ContentLoading />;
    }

    if (contentError) {
      return <ContentError error={contentError} />;
    }

    if (!canEdit) {
      return <Redirect to={this.detailsUrl} />;
    }

    return (
      <CardBody>
        <JobTemplateForm
          template={template}
          handleCancel={this.handleCancel}
          handleSubmit={this.handleSubmit}
          relatedProjectPlaybooks={relatedProjectPlaybooks}
        />
        {formSubmitError ? <div> error </div> : null}
      </CardBody>
    );
  }
}

export default withRouter(JobTemplateEdit);
