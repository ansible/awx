import React, { Component } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Card,
  PageSection,
  PageSectionVariants,
} from '@patternfly/react-core';
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
      contentError: false,
      contentLoading: true,
      selected: [],
      templates: [],
      itemCount: 0,
    };
    this.loadUnifiedJobTemplates = this.loadUnifiedJobTemplates.bind(this);
    this.handleSelectAll = this.handleSelectAll.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
  }

  componentDidMount () {
    this.loadUnifiedJobTemplates();
  }

  componentDidUpdate (prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      this.loadUnifiedJobTemplates();
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

  async loadUnifiedJobTemplates () {
    const { location } = this.props;
    const params = parseNamespacedQueryString(QS_CONFIG, location.search);

    this.setState({ contentError: false, contentLoading: true });
    try {
      const { data: { count, results } } = await UnifiedJobTemplatesAPI.read(params);
      this.setState({
        itemCount: count,
        templates: results,
        selected: [],
      });
    } catch (err) {
      this.setState({ contentError: true });
    } finally {
      this.setState({ contentLoading: false });
    }
  }

  render () {
    const {
      contentError,
      contentLoading,
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
          <PaginatedDataList
            contentError={contentError}
            contentLoading={contentLoading}
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
        </Card>
      </PageSection>
    );
  }
}

export { TemplatesList as _TemplatesList };
export default withI18n()(withRouter(TemplatesList));
