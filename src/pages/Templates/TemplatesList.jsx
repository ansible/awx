import React, { Component } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Card,
  PageSection,
  PageSectionVariants,
} from '@patternfly/react-core';
import { withNetwork } from '../../contexts/Network';
import { UnifiedJobTemplatesAPI } from '../../api';

import { getQSConfig, parseNamespacedQueryString } from '../../util/qs';
import DatalistToolbar from '../../components/DataListToolbar';
import PaginatedDataList from '../../components/PaginatedDataList';
import TemplateListItem from './components/TemplateListItem';

// The type value in const QS_CONFIG below does not have a space between job_template and
// workflow_job_template so the params sent to the API match what the api expects.
const QS_CONFIG = getQSConfig('template', {
  page: 1,
  page_size: 5,
  order_by: 'name',
  type: 'job_template,workflow_job_template'
});

class TemplatesList extends Component {
  constructor (props) {
    super(props);

    this.state = {
      error: null,
      isLoading: true,
      isInitialized: false,
      selected: [],
      templates: [],
    };
    this.readUnifiedJobTemplates = this.readUnifiedJobTemplates.bind(this);
    this.handleSelectAll = this.handleSelectAll.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
  }

  componentDidMount () {
    this.readUnifiedJobTemplates();
  }

  componentDidUpdate (prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      this.readUnifiedJobTemplates();
    }
  }

  handleSelectAll (isSelected) {
    const { templates } = this.state;
    const selected = isSelected ? [...templates] : [];
    this.setState({ selected });
  }

  handleSelect (template) {
    const { selected } = this.state;
    if (selected.some(s => s.id === template.id)) {
      this.setState({ selected: selected.filter(s => s.id !== template.id) });
    } else {
      this.setState({ selected: selected.concat(template) });
    }
  }

  async readUnifiedJobTemplates () {
    const { handleHttpError, location } = this.props;
    this.setState({ error: false, isLoading: true });
    const params = parseNamespacedQueryString(QS_CONFIG, location.search);

    try {
      const { data } = await UnifiedJobTemplatesAPI.read(params);
      const { count, results } = data;

      const stateToUpdate = {
        itemCount: count,
        templates: results,
        selected: [],
        isInitialized: true,
        isLoading: false,
      };
      this.setState(stateToUpdate);
    } catch (err) {
      handleHttpError(err) || this.setState({ error: true, isLoading: false });
    }
  }

  render () {
    const {
      error,
      isInitialized,
      isLoading,
      templates,
      itemCount,
      selected,
    } = this.state;
    const {
      match,
      i18n
    } = this.props;
    const isAllSelected = selected.length === templates.length;
    const { medium } = PageSectionVariants;
    return (
      <PageSection variant={medium}>
        <Card>
          {isInitialized && (
            <PaginatedDataList
              items={templates}
              itemCount={itemCount}
              itemName={i18n._(t`Template`)}
              qsConfig={QS_CONFIG}
              toolbarColumns={[
                { name: i18n._(t`Name`), key: 'name', isSortable: true },
                { name: i18n._(t`Modified`), key: 'modified', isSortable: true, isNumeric: true },
                { name: i18n._(t`Created`), key: 'created', isSortable: true, isNumeric: true },
              ]}
              renderToolbar={(props) => (
                <DatalistToolbar
                  {...props}
                  showSelectAll
                  showExpandCollapse
                  isAllSelected={isAllSelected}
                  onSelectAll={this.handleSelectAll}
                />
              )}
              renderItem={(template) => (
                <TemplateListItem
                  key={template.id}
                  value={template.name}
                  template={template}
                  detailUrl={`${match.url}/${template.type}/${template.id}`}
                  onSelect={() => this.handleSelect(template)}
                  isSelected={selected.some(row => row.id === template.id)}
                />
              )}
            />
          )}
          {isLoading ? <div>loading....</div> : ''}
          {error ? <div>error</div> : '' }
        </Card>
      </PageSection>
    );
  }
}
export { TemplatesList as _TemplatesList };
export default withI18n()(withNetwork(withRouter(TemplatesList)));
