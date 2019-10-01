import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import PaginatedDataList from '../PaginatedDataList';
import DataListToolbar from '../DataListToolbar';
import CheckboxListItem from '../CheckboxListItem';
import SelectedList from '../SelectedList';
import { getQSConfig, parseQueryString } from '../../util/qs';

class SelectResourceStep extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      isInitialized: false,
      count: null,
      error: false,
      resources: [],
    };

    this.qsConfig = getQSConfig('resource', {
      page: 1,
      page_size: 5,
      order_by: props.sortedColumnKey,
    });
  }

  componentDidMount() {
    this.readResourceList();
  }

  componentDidUpdate(prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      this.readResourceList();
    }
  }

  async readResourceList() {
    const { onSearch, location } = this.props;
    const queryParams = parseQueryString(this.qsConfig, location.search);

    this.setState({
      isLoading: true,
      error: false,
    });
    try {
      const { data } = await onSearch(queryParams);
      const { count, results } = data;

      this.setState({
        resources: results,
        count,
        isInitialized: true,
        isLoading: false,
        error: false,
      });
    } catch (err) {
      this.setState({
        isLoading: false,
        error: true,
      });
    }
  }

  render() {
    const { isInitialized, isLoading, count, error, resources } = this.state;

    const {
      columns,
      displayKey,
      onRowClick,
      selectedLabel,
      selectedResourceRows,
      i18n,
    } = this.props;

    return (
      <Fragment>
        {isLoading && <div>{i18n._(t`Loading...`)}</div>}
        {isInitialized && (
          <Fragment>
            <div>
              {i18n._(
                t`Choose the resources that will be receiving new roles.  You'll be able to select the roles to apply in the next step.  Note that the resources chosen here will receive all roles chosen in the next step.`
              )}
            </div>
            {selectedResourceRows.length > 0 && (
              <SelectedList
                displayKey={displayKey}
                label={selectedLabel}
                onRemove={onRowClick}
                selected={selectedResourceRows}
                showOverflowAfter={5}
              />
            )}
            <PaginatedDataList
              items={resources}
              itemCount={count}
              qsConfig={this.qsConfig}
              toolbarColumns={columns}
              renderItem={item => (
                <CheckboxListItem
                  isSelected={selectedResourceRows.some(i => i.id === item.id)}
                  itemId={item.id}
                  key={item.id}
                  name={item[displayKey]}
                  label={item[displayKey]}
                  onSelect={() => onRowClick(item)}
                />
              )}
              renderToolbar={props => <DataListToolbar {...props} fillWidth />}
              showPageSizeOptions={false}
            />
          </Fragment>
        )}
        {error ? <div>error</div> : ''}
      </Fragment>
    );
  }
}

SelectResourceStep.propTypes = {
  columns: PropTypes.arrayOf(PropTypes.object).isRequired,
  displayKey: PropTypes.string,
  onRowClick: PropTypes.func,
  onSearch: PropTypes.func.isRequired,
  selectedLabel: PropTypes.string,
  selectedResourceRows: PropTypes.arrayOf(PropTypes.object),
  sortedColumnKey: PropTypes.string,
};

SelectResourceStep.defaultProps = {
  displayKey: 'name',
  onRowClick: () => {},
  selectedLabel: null,
  selectedResourceRows: [],
  sortedColumnKey: 'name',
};

export { SelectResourceStep as _SelectResourceStep };
export default withI18n()(withRouter(SelectResourceStep));
