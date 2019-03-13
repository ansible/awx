import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { I18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';
import {
  Button,
  Dropdown,
  DropdownDirection,
  DropdownItem,
  DropdownToggle,
  TextInput
} from '@patternfly/react-core';

class Pagination extends Component {
  constructor (props) {
    super(props);

    const { page } = props;
    this.state = { value: page, isOpen: false };

    this.onPageChange = this.onPageChange.bind(this);
    this.onSubmit = this.onSubmit.bind(this);
    this.onFirst = this.onFirst.bind(this);
    this.onPrevious = this.onPrevious.bind(this);
    this.onNext = this.onNext.bind(this);
    this.onLast = this.onLast.bind(this);
    this.onTogglePageSize = this.onTogglePageSize.bind(this);
    this.onSelectPageSize = this.onSelectPageSize.bind(this);
  }

  componentDidUpdate (prevProps) {
    const { page } = this.props;

    if (prevProps.page !== page) {
      this.onPageChange(page);
    }
  }

  onPageChange (value) {
    this.setState({ value });
  }

  onSubmit (event) {
    const { onSetPage, page, pageCount, page_size } = this.props;
    const { value } = this.state;

    event.preventDefault();

    // eslint-disable-next-line no-bitwise
    const isPositiveInteger = value >>> 0 === parseFloat(value) && parseInt(value, 10) > 0;
    const isValid = isPositiveInteger && parseInt(value, 10) <= pageCount;

    if (isValid) {
      onSetPage(value, page_size);
    } else {
      this.setState({ value: page });
    }
  }

  onFirst () {
    const { onSetPage, page_size } = this.props;

    onSetPage(1, page_size);
  }

  onPrevious () {
    const { onSetPage, page, page_size } = this.props;
    const previousPage = page - 1;

    onSetPage(previousPage, page_size);
  }

  onNext () {
    const { onSetPage, page, page_size } = this.props;
    const nextPage = page + 1;

    onSetPage(nextPage, page_size);
  }

  onLast () {
    const { onSetPage, pageCount, page_size } = this.props;

    onSetPage(pageCount, page_size);
  }

  onTogglePageSize (isOpen) {
    this.setState({ isOpen });
  }

  onSelectPageSize ({ target }) {
    const { onSetPage } = this.props;
    const page = 1;
    const page_size = parseInt(target.innerText || target.textContent, 10);

    this.setState({ isOpen: false });

    onSetPage(page, page_size);
  }

  render () {
    const { up } = DropdownDirection;
    const {
      count,
      page,
      pageCount,
      page_size,
      pageSizeOptions,
      showPageSizeOptions,
      style
    } = this.props;
    const { value, isOpen } = this.state;
    let opts;
    if (pageSizeOptions) {
      opts = pageSizeOptions.slice().reverse().filter(o => o !== page_size);
    }
    const isOnFirst = page === 1;
    const isOnLast = page === pageCount;

    let itemCount;
    if (!isOnLast || count === page_size) {
      itemCount = page_size;
    } else {
      itemCount = count % page_size;
    }
    const itemMin = ((page - 1) * page_size) + 1;
    const itemMax = itemMin + itemCount - 1;

    return (
      <I18n>
        {({ i18n }) => (
          <div className="awx-pagination" style={style}>
            {showPageSizeOptions && (
              <div className="awx-pagination__page-size-selection">
                <Trans>Items Per Page</Trans>
                <Dropdown
                  onToggle={this.onTogglePageSize}
                  onSelect={this.onSelectPageSize}
                  direction={up}
                  isOpen={isOpen}
                  toggle={(
                    <DropdownToggle
                      className="togglePageSize"
                      onToggle={this.onTogglePageSize}
                    >
                      {page_size}
                    </DropdownToggle>
                  )}
                >
                  {opts.map(option => (
                    <DropdownItem
                      key={option}
                      component="button"
                    >
                      {option}
                    </DropdownItem>
                  ))}
                </Dropdown>
              </div>
            )}
            <div className="awx-pagination__counts">
              <div className="awx-pagination__item-count">
                <Trans>{`Items ${itemMin} – ${itemMax} of ${count}`}</Trans>
              </div>
              {pageCount !== 1 && (
                <div className="awx-pagination__page-count">
                  <div className="pf-c-input-group pf-m-previous">
                    <Button
                      className="awx-pagination__page-button"
                      variant="tertiary"
                      aria-label={i18n._(t`First`)}
                      isDisabled={isOnFirst}
                      onClick={this.onFirst}
                    >
                      <i className="fas fa-angle-double-left" />
                    </Button>
                    <Button
                      className="awx-pagination__page-button"
                      variant="tertiary"
                      aria-label={i18n._(t`Previous`)}
                      isDisabled={isOnFirst}
                      onClick={this.onPrevious}
                    >
                      <i className="fas fa-angle-left" />
                    </Button>
                  </div>
                  <form
                    className="awx-pagination__page-input-form"
                    onSubmit={this.onSubmit}
                  >
                    <Trans>
                      {'Page '}
                      <TextInput
                        className="awx-pagination__page-input"
                        aria-label={i18n._(t`Page Number`)}
                        value={value}
                        type="text"
                        onChange={this.onPageChange}
                      />
                      {' of '}
                      {pageCount}
                    </Trans>
                  </form>
                  <div className="pf-c-input-group">
                    <Button
                      className="awx-pagination__page-button"
                      variant="tertiary"
                      aria-label={i18n._(t`Next`)}
                      isDisabled={isOnLast}
                      onClick={this.onNext}
                    >
                      <i className="fas fa-angle-right" />
                    </Button>
                    <Button
                      className="awx-pagination__page-button"
                      variant="tertiary"
                      aria-label={i18n._(t`Last`)}
                      isDisabled={isOnLast}
                      onClick={this.onLast}
                    >
                      <i className="fas fa-angle-double-right" />
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </I18n>
    );
  }
}

Pagination.propTypes = {
  count: PropTypes.number,
  onSetPage: PropTypes.func.isRequired,
  page: PropTypes.number.isRequired,
  pageCount: PropTypes.number,
  pageSizeOptions: PropTypes.arrayOf(PropTypes.number),
  page_size: PropTypes.number.isRequired,
  showPageSizeOptions: PropTypes.bool
};

Pagination.defaultProps = {
  count: null,
  pageCount: null,
  pageSizeOptions: [5, 10, 25, 50],
  showPageSizeOptions: true
};

export default Pagination;
