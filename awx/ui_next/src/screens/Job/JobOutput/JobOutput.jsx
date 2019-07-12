import styled from 'styled-components';
import { List, AutoSizer } from 'react-virtualized';

import React, { Component } from 'react';
import { CardBody } from '@patternfly/react-core';

import { JobsAPI } from '@api';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import JobEvent from './JobEvent';
import MenuControls from './shared/MenuControls';

const OutputToolbar = styled.div`
  display: flex;
  justify-content: flex-end;
`;
const OutputWrapper = styled.div`
  height: calc(100vh - 325px);
  background-color: #fafafa;
  margin-top: 24px;
  font-family: monospace;
  font-size: 15px;
  border: 1px solid #b7b7b7;
  display: flex;
  flex-direction: column;
`;
const OutputFooter = styled.div`
  background-color: #ebebeb;
  border-right: 1px solid #b7b7b7;
  width: 75px;
  flex: 1;
`;

class JobOutput extends Component {
  listRef = React.createRef();

  constructor(props) {
    super(props);

    this.state = {
      contentError: null,
      hasContentLoading: true,
      results: [],
      scrollToIndex: -1,
      startIndex: 0,
      stopIndex: 0,
    };

    this.loadJobEvents = this.loadJobEvents.bind(this);
    this.renderRow = this.renderRow.bind(this);
    this.handleScrollTop = this.handleScrollTop.bind(this);
    this.handleScrollBottom = this.handleScrollBottom.bind(this);
    this.handleScrollNext = this.handleScrollNext.bind(this);
    this.handleScrollPrevious = this.handleScrollPrevious.bind(this);
    this.onRowsRendered = this.onRowsRendered.bind(this);
  }

  componentDidMount() {
    this.loadJobEvents();
  }

  async loadJobEvents() {
    const { job } = this.props;

    this.setState({ hasContentLoading: true });
    try {
      const {
        data: { results = [] },
      } = await JobsAPI.readEvents(job.id, job.type, {
        page_size: 200,
        order_by: 'start_line',
      });
      this.setState({ results });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  renderRow({ index, key, style }) {
    const { results } = this.state;
    const { created, event, stdout, start_line } = results[index];
    return (
      <JobEvent
        className="row"
        key={key}
        style={style}
        created={created}
        event={event}
        start_line={start_line}
        stdout={stdout}
      />
    );
  }

  onRowsRendered({ startIndex, stopIndex }) {
    this.setState({ startIndex, stopIndex });
  }

  handleScrollPrevious() {
    const { startIndex, stopIndex } = this.state;
    const index = startIndex - (stopIndex - startIndex);
    this.setState({ scrollToIndex: Math.max(0, index) });
  }

  handleScrollNext() {
    const { stopIndex } = this.state;
    this.setState({ scrollToIndex: stopIndex + 1 });
  }

  handleScrollTop() {
    this.setState({ scrollToIndex: 0 });
  }

  handleScrollBottom() {
    const { results } = this.state;
    this.setState({ scrollToIndex: results.length - 1 });
  }

  render() {
    const { job } = this.props;
    const {
      results,
      hasContentLoading,
      contentError,
      scrollToIndex,
      startIndex,
      stopIndex,
    } = this.state;

    if (hasContentLoading) {
      return <ContentLoading />;
    }

    if (contentError) {
      return <ContentError error={contentError} />;
    }

    return (
      <CardBody>
        <b>{job.name}</b>
        <OutputToolbar>
          <MenuControls
            onScrollTop={this.handleScrollTop}
            onScrollBottom={this.handleScrollBottom}
            onScrollNext={this.handleScrollNext}
            onScrollPrevious={this.handleScrollPrevious}
          />
        </OutputToolbar>
        <OutputWrapper>
          <AutoSizer>
            {({ width, height }) => {
              console.log('scroll to index', scrollToIndex);
              console.log('start index', startIndex);
              console.log('stop index', stopIndex);
              return (
                <List
                  ref={this.listRef}
                  width={width}
                  height={height}
                  rowHeight={25}
                  rowRenderer={this.renderRow}
                  rowCount={results.length}
                  overscanRowCount={50}
                  scrollToIndex={scrollToIndex}
                  onRowsRendered={this.onRowsRendered}
                  scrollToAlignment="start"
                />
              );
            }}
          </AutoSizer>
          <OutputFooter />
        </OutputWrapper>
      </CardBody>
    );
  }
}

export default JobOutput;
