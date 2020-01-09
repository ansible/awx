import React, { Component } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';

import {
  JobTemplatesAPI,
  UnifiedJobTemplatesAPI,
  WorkflowJobTemplatesAPI,
} from '@api';
import AlertModal from '@components/AlertModal';
import DatalistToolbar from '@components/DataListToolbar';
import ErrorDetail from '@components/ErrorDetail';
import PaginatedDataList, {
  ToolbarDeleteButton,
} from '@components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '@util/qs';

import AddDropDownButton from '@components/AddDropDownButton';
import TemplateListItem from './TemplateListItem';

// The type value in const QS_CONFIG below does not have a space between job_template and
// workflow_job_template so the params sent to the API match what the api expects.
const QS_CONFIG = getQSConfig('template', {
  page: 1,
  page_size: 20,
  order_by: 'name',
  type: 'job_template,workflow_job_template',
});

class TemplatesList extends Component {
  constructor(props) {
    super(props);

    this.state = {
      hasContentLoading: true,
      contentError: null,
      deletionError: null,
      selected: [],
      templates: [],
      itemCount: 0,
    };

    this.loadTemplates = this.loadTemplates.bind(this);
    this.handleSelectAll = this.handleSelectAll.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
    this.handleTemplateDelete = this.handleTemplateDelete.bind(this);
    this.handleDeleteErrorClose = this.handleDeleteErrorClose.bind(this);
  }

  componentDidMount() {
    this.loadTemplates();
  }

  componentDidUpdate(prevProps) {
    const { location } = this.props;

    if (location !== prevProps.location) {
      this.loadTemplates();
    }
  }

  componentWillUnmount() {
    document.removeEventListener('click', this.handleAddToggle, false);
  }

  handleDeleteErrorClose() {
    this.setState({ deletionError: null });
  }

  handleSelectAll(isSelected) {
    const { templates } = this.state;
    const selected = isSelected ? [...templates] : [];
    this.setState({ selected });
  }

  handleSelect(template) {
    const { selected } = this.state;
    if (selected.some(s => s.id === template.id)) {
      this.setState({ selected: selected.filter(s => s.id !== template.id) });
    } else {
      this.setState({ selected: selected.concat(template) });
    }
  }

  async handleTemplateDelete() {
    const { selected, itemCount } = this.state;

    this.setState({ hasContentLoading: true });
    try {
      await Promise.all(
        selected.map(({ type, id }) => {
          let deletePromise;
          if (type === 'job_template') {
            deletePromise = JobTemplatesAPI.destroy(id);
          } else if (type === 'workflow_job_template') {
            deletePromise = WorkflowJobTemplatesAPI.destroy(id);
          }
          return deletePromise;
        })
      );
      this.setState({ itemCount: itemCount - selected.length });
    } catch (err) {
      this.setState({ deletionError: err });
    } finally {
      await this.loadTemplates();
    }
  }

  async loadTemplates() {
    const { location } = this.props;
    const {
      jtActions: cachedJTActions,
      wfjtActions: cachedWFJTActions,
    } = this.state;
    const params = parseQueryString(QS_CONFIG, location.search);

    let jtOptionsPromise;
    if (cachedJTActions) {
      jtOptionsPromise = Promise.resolve({
        data: { actions: cachedJTActions },
      });
    } else {
      jtOptionsPromise = JobTemplatesAPI.readOptions();
    }

    let wfjtOptionsPromise;
    if (cachedWFJTActions) {
      wfjtOptionsPromise = Promise.resolve({
        data: { actions: cachedWFJTActions },
      });
    } else {
      wfjtOptionsPromise = WorkflowJobTemplatesAPI.readOptions();
    }

    const promises = Promise.all([
      UnifiedJobTemplatesAPI.read(params),
      jtOptionsPromise,
      wfjtOptionsPromise,
    ]);

    this.setState({ contentError: null, hasContentLoading: true });

    try {
      const [
        {
          data: { count, results },
        },
        {
          data: { actions: jtActions },
        },
        {
          data: { actions: wfjtActions },
        },
      ] = await promises;

      this.setState({
        jtActions,
        wfjtActions,
        itemCount: count,
        templates: results,
        selected: [],
      });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  render() {
    const {
      contentError,
      hasContentLoading,
      deletionError,
      templates,
      itemCount,
      selected,
      jtActions,
      wfjtActions,
    } = this.state;
    const { match, i18n } = this.props;
    const canAddJT =
      jtActions && Object.prototype.hasOwnProperty.call(jtActions, 'POST');
    const canAddWFJT =
      wfjtActions && Object.prototype.hasOwnProperty.call(wfjtActions, 'POST');
    const addButtonOptions = [];
    if (canAddJT) {
      addButtonOptions.push({
        label: i18n._(t`Template`),
        url: `${match.url}/job_template/add/`,
      });
    }
    if (canAddWFJT) {
      addButtonOptions.push({
        label: i18n._(t`Workflow Template`),
        url: `${match.url}/workflow_job_template/add/`,
      });
    }
    const isAllSelected =
      selected.length === templates.length && selected.length > 0;
    const addButton = (
      <AddDropDownButton key="add" dropdownItems={addButtonOptions} />
    );
    return (
      <PageSection>
        <Card>
          <PaginatedDataList
            contentError={contentError}
            hasContentLoading={hasContentLoading}
            items={templates}
            itemCount={itemCount}
            pluralizedItemName={i18n._(t`Templates`)}
            qsConfig={QS_CONFIG}
            onRowClick={this.handleSelect}
            toolbarSearchColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
                isDefault: true,
              },
              {
                name: i18n._(t`Type`),
                key: 'type',
                options: [
                  [`job_template`, i18n._(t`Job Template`)],
                  [`workflow_job_template`, i18n._(t`Workflow Template`)],
                ],
              },
              {
                name: i18n._(t`Playbook name`),
                key: 'job_template__playbook',
              },
              {
                name: i18n._(t`Created By (Username)`),
                key: 'created_by__username',
              },
              {
                name: i18n._(t`Modified By (Username)`),
                key: 'modified_by__username',
              },
            ]}
            toolbarSortColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
              },
              {
                name: i18n._(t`Type`),
                key: 'type',
              },
            ]}
            renderToolbar={props => (
              <DatalistToolbar
                {...props}
                showSelectAll
                showExpandCollapse
                isAllSelected={isAllSelected}
                onSelectAll={this.handleSelectAll}
                qsConfig={QS_CONFIG}
                additionalControls={[
                  <ToolbarDeleteButton
                    key="delete"
                    onDelete={this.handleTemplateDelete}
                    itemsToDelete={selected}
                    pluralizedItemName="Templates"
                  />,
                  (canAddJT || canAddWFJT) && addButton,
                ]}
              />
            )}
            renderItem={template => (
              <TemplateListItem
                key={template.id}
                value={template.name}
                template={template}
                detailUrl={`${match.url}/${template.type}/${template.id}`}
                onSelect={() => this.handleSelect(template)}
                isSelected={selected.some(row => row.id === template.id)}
              />
            )}
            emptyStateControls={(canAddJT || canAddWFJT) && addButton}
          />
        </Card>
        <AlertModal
          isOpen={deletionError}
          variant="danger"
          title={i18n._(t`Error!`)}
          onClose={this.handleDeleteErrorClose}
        >
          {i18n._(t`Failed to delete one or more templates.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      </PageSection>
    );
  }
}

export { TemplatesList as _TemplatesList };
export default withI18n()(withRouter(TemplatesList));
