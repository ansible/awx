import React, { Component } from 'react';
import { I18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';
import {
  Button,
  Dropdown,
  DropdownDirection,
  DropdownItem,
  DropdownToggle,
  Level,
  LevelItem,
  TextInput,
  Split,
  SplitItem,
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
    const page_size = parseInt(target.innerText, 10);

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
    } = this.props;
    const { value, isOpen } = this.state;

    const opts = pageSizeOptions.slice().reverse().filter(o => o !== page_size);
    const isOnFirst = page === 1;
    const isOnLast = page === pageCount;

    const itemCount = isOnLast ? count % page_size : page_size;
    const itemMin = ((page - 1) * page_size) + 1;
    const itemMax = itemMin + itemCount - 1;

    const disabledStyle = {
      backgroundColor: '#EDEDED',
      border: '1px solid #C2C2CA',
      borderRadius: '0px',
      color: '#C2C2CA',
    };

    return (
      <I18n>
        {({ i18n }) => (
          <div className="awx-pagination">
            <Level>
              <LevelItem>
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
                <Trans> Per Page</Trans>
              </LevelItem>
              <LevelItem>
                <Split gutter="md" className="pf-u-display-flex pf-u-align-items-center">
                  <SplitItem>
                    <Trans>{`${itemMin} - ${itemMax} of ${count}`}</Trans>
                  </SplitItem>
                  <SplitItem>
                    <div className="pf-c-input-group">
                      <Button
                        variant="tertiary"
                        aria-label={i18n._(t`First`)}
                        style={isOnFirst ? disabledStyle : {}}
                        isDisabled={isOnFirst}
                        onClick={this.onFirst}
                      >
                        <i className="fas fa-angle-double-left" />
                      </Button>
                      <Button
                        variant="tertiary"
                        aria-label={i18n._(t`Previous`)}
                        style={isOnFirst ? disabledStyle : {}}
                        isDisabled={isOnFirst}
                        onClick={this.onPrevious}
                      >
                        <i className="fas fa-angle-left" />
                      </Button>
                    </div>
                  </SplitItem>
                  <SplitItem isMain>
                    <form onSubmit={this.onSubmit}>
                      <Trans>
                        {'Page '}
                        <TextInput
                          isDisabled={pageCount === 1}
                          aria-label={i18n._(t`Page Number`)}
                          style={{
                            height: '30px',
                            width: '30px',
                            textAlign: 'center',
                            padding: '0',
                            margin: '0',
                            ...(pageCount === 1 ? disabledStyle : {})
                          }}
                          value={value}
                          type="text"
                          onChange={this.onPageChange}
                        />
                        {' of '}
                        {pageCount}
                      </Trans>
                    </form>
                  </SplitItem>
                  <SplitItem>
                    <div className="pf-c-input-group">
                      <Button
                        variant="tertiary"
                        aria-label={i18n._(t`Next`)}
                        style={isOnLast ? disabledStyle : {}}
                        isDisabled={isOnLast}
                        onClick={this.onNext}
                      >
                        <i className="fas fa-angle-right" />
                      </Button>
                      <Button
                        variant="tertiary"
                        aria-label={i18n._(t`Last`)}
                        style={isOnLast ? disabledStyle : {}}
                        isDisabled={isOnLast}
                        onClick={this.onLast}
                      >
                        <i className="fas fa-angle-double-right" />
                      </Button>
                    </div>
                  </SplitItem>
                </Split>
              </LevelItem>
            </Level>
          </div>
        )}
      </I18n>
    );
  }
}

export default Pagination;
