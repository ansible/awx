import React, { Component } from 'react';
import { withRouter, Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';

import { t } from '@lingui/macro';
import {
  Card,
  PageSection,
  Dropdown,
  DropdownItem,
  DropdownPosition,
} from '@patternfly/react-core';

import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from '@api';
import AlertModal from '@components/AlertModal';
import DatalistToolbar from '@components/DataListToolbar';
import ErrorDetail from '@components/ErrorDetail';
import PaginatedDataList, {
  ToolbarDeleteButton,
  ToolbarAddButton,
} from '@components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '@util/qs';

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
      isAddOpen: false,
    };

    this.loadTemplates = this.loadTemplates.bind(this);
    this.handleSelectAll = this.handleSelectAll.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
    this.handleTemplateDelete = this.handleTemplateDelete.bind(this);
    this.handleDeleteErrorClose = this.handleDeleteErrorClose.bind(this);
    this.handleAddToggle = this.handleAddToggle.bind(this);
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

  handleAddToggle(e) {
    const { isAddOpen } = this.state;
    document.addEventListener('click', this.handleAddToggle, false);

    if (this.node && this.node.contains(e.target) && isAddOpen) {
      document.removeEventListener('click', this.handleAddToggle, false);
      this.setState({ isAddOpen: false });
    } else if (this.node && this.node.contains(e.target) && !isAddOpen) {
      this.setState({ isAddOpen: true });
    } else {
      this.setState({ isAddOpen: false });
      document.removeEventListener('click', this.handleAddToggle, false);
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
    const { actions: cachedActions } = this.state;
    const params = parseQueryString(QS_CONFIG, location.search);

    let optionsPromise;
    if (cachedActions) {
      optionsPromise = Promise.resolve({ data: { actions: cachedActions } });
    } else {
      optionsPromise = JobTemplatesAPI.readOptions();
    }

    const promises = Promise.all([
      JobTemplatesAPI.read(params),
      optionsPromise,
    ]);

    this.setState({ contentError: null, hasContentLoading: true });

    try {
      const [
        {
          data: { count, results },
        },
        {
          data: { actions },
        },
      ] = await promises;

      this.setState({
        actions,
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
      isAddOpen,
      actions,
    } = this.state;
    const { match, i18n } = this.props;
    const canAdd =
      actions && Object.prototype.hasOwnProperty.call(actions, 'POST');
    const isAllSelected =
      selected.length === templates.length && selected.length > 0;
    return (
      <PageSection>
        <Card>
          <PaginatedDataList
            contentError={contentError}
            hasContentLoading={hasContentLoading}
            items={templates}
            itemCount={itemCount}
            pluralizedItemName="Templates"
            qsConfig={QS_CONFIG}
            toolbarColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
                isSortable: true,
                isSearchable: true,
              },
              {
                name: i18n._(t`Modified`),
                key: 'modified',
                isSortable: true,
                isNumeric: true,
              },
              {
                name: i18n._(t`Created`),
                key: 'created',
                isSortable: true,
                isNumeric: true,
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
                  canAdd && (
                    <div
                      ref={node => {
                        this.node = node;
                      }}
                      key="add"
                    >
                      <Dropdown
                        isPlain
                        isOpen={isAddOpen}
                        position={DropdownPosition.right}
                        toggle={
                          <ToolbarAddButton onClick={this.handleAddToggle} />
                        }
                        dropdownItems={[
                          <DropdownItem key="job">
                            <Link to={`${match.url}/job_template/add/`}>
                              {i18n._(t`Job Template`)}
                            </Link>
                          </DropdownItem>,
                          <DropdownItem key="workflow">
                            <Link to={`${match.url}_workflow/add/`}>
                              {i18n._(t`Workflow Template`)}
                            </Link>
                          </DropdownItem>,
                        ]}
                      />
                    </div>
                  ),
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
            emptyStateControls={
              canAdd && (
                <div
                  ref={node => {
                    this.node = node;
                  }}
                  key="add"
                >
                  <Dropdown
                    isPlain
                    isOpen={isAddOpen}
                    position={DropdownPosition.right}
                    toggle={<ToolbarAddButton onClick={this.handleAddToggle} />}
                    dropdownItems={[
                      <DropdownItem key="job">
                        <Link to={`${match.url}/job_template/add/`}>
                          {i18n._(t`Job Template`)}
                        </Link>
                      </DropdownItem>,
                      <DropdownItem key="workflow">
                        <Link to={`${match.url}_workflow/add/`}>
                          {i18n._(t`Workflow Template`)}
                        </Link>
                      </DropdownItem>,
                    ]}
                  />
                </div>
              )
            }
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
