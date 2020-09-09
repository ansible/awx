/* eslint react/no-unused-state: 0 */
import React, { Component } from 'react';
import { withRouter, Redirect } from 'react-router-dom';
import { CardBody } from '../../../components/Card';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import { JobTemplatesAPI } from '../../../api';
import { JobTemplate } from '../../../types';
import { getAddedAndRemoved } from '../../../util/lists';
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
    this.submitLabels = this.submitLabels.bind(this);
  }

  componentDidMount() {
    this.loadRelated();
  }

  async loadRelated() {
    this.setState({ contentError: null, hasContentLoading: true });
    try {
      const [relatedCredentials] = await this.loadRelatedCredentials();
      this.setState({
        relatedCredentials,
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

  async handleSubmit(values) {
    const { template, history } = this.props;
    const {
      labels,
      instanceGroups,
      initialInstanceGroups,
      credentials,
      webhook_credential,
      webhook_key,
      webhook_url,
      ...remainingValues
    } = values;

    this.setState({ formSubmitError: null });
    remainingValues.project = values.project.id;
    remainingValues.webhook_credential = webhook_credential?.id || null;
    try {
      await JobTemplatesAPI.update(template.id, remainingValues);
      await Promise.all([
        this.submitLabels(labels, template?.organization),
        this.submitInstanceGroups(instanceGroups, initialInstanceGroups),
        this.submitCredentials(credentials),
      ]);
      history.push(this.detailsUrl);
    } catch (error) {
      this.setState({ formSubmitError: error });
    }
  }

  async submitLabels(labels = [], orgId) {
    const { template } = this.props;

    const { added, removed } = getAddedAndRemoved(
      template.summary_fields.labels.results,
      labels
    );

    const disassociationPromises = removed.map(label =>
      JobTemplatesAPI.disassociateLabel(template.id, label)
    );
    const associationPromises = added.map(label => {
      return JobTemplatesAPI.associateLabel(template.id, label, orgId);
    });

    const results = await Promise.all([
      ...disassociationPromises,
      ...associationPromises,
    ]);
    return results;
  }

  async submitInstanceGroups(groups, initialGroups) {
    const { template } = this.props;
    const { added, removed } = getAddedAndRemoved(initialGroups, groups);
    const disassociatePromises = await removed.map(group =>
      JobTemplatesAPI.disassociateInstanceGroup(template.id, group.id)
    );
    const associatePromises = await added.map(group =>
      JobTemplatesAPI.associateInstanceGroup(template.id, group.id)
    );
    return Promise.all([...disassociatePromises, ...associatePromises]);
  }

  async submitCredentials(newCredentials) {
    const { template } = this.props;
    const { added, removed } = getAddedAndRemoved(
      template.summary_fields.credentials,
      newCredentials
    );
    const disassociateCredentials = removed.map(cred =>
      JobTemplatesAPI.disassociateCredentials(template.id, cred.id)
    );
    const disassociatePromise = await Promise.all(disassociateCredentials);
    const associateCredentials = added.map(cred =>
      JobTemplatesAPI.associateCredentials(template.id, cred.id)
    );
    const associatePromise = Promise.all(associateCredentials);
    return Promise.all([disassociatePromise, associatePromise]);
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
      return (
        <CardBody>
          <ContentLoading />
        </CardBody>
      );
    }

    if (contentError) {
      return (
        <CardBody>
          <ContentError error={contentError} />
        </CardBody>
      );
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
          submitError={formSubmitError}
        />
      </CardBody>
    );
  }
}

export default withRouter(JobTemplateEdit);
