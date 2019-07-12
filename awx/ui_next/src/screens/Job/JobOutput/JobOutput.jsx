import React, { Component } from 'react';
import { CardBody } from '@patternfly/react-core';
import styled from 'styled-components';
import { JobsAPI } from '@api';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import MenuControls from './shared/MenuControls';
import { List, AutoSizer } from 'react-virtualized';

const OutputToolbar = styled.div`
  display: flex;
  justify-content: flex-end;
`;
const OutputWrapper = styled.div`
  height: calc(100vh - 325px);
  background-color: #fafafa;
  margin-top: 24px;
`;
const OutputRow = styled.div`
  display: flex;
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
  }

  componentDidMount() {
    this.loadJobEvents();
  }

  async loadJobEvents() {
    const { job } = this.props;

    try {
      const {
        data: { results = [] },
      } = await JobsAPI.readJobEvents(job.id);
      this.setState({ results, hasContentLoading: true });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  renderRow({ index, key, style }) {
    const { results } = this.state;
    return (
      <OutputRow key={key} style={style} className="row">
        <div className="id">{results[index].id}</div>
        <div className="content">{results[index].stdout}</div>
      </OutputRow>
    );
  }

  onRowsRendered = ({ startIndex, stopIndex }) => {
    this.setState({ startIndex, stopIndex });
  };

  handleScrollPrevious() {
    const { startIndex, stopIndex } = this.state;
    const index = startIndex - (stopIndex - startIndex);
    this.setState({ scrollToIndex: Math.max(0, index) });
  }

  handleScrollNext() {
    const { stopIndex } = this.state;
    this.setState({ scrollToIndex: stopIndex + 1});
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
      stopIndex
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
                  rowHeight={50}
                  rowRenderer={this.renderRow}
                  rowCount={results.length}
                  overscanRowCount={5}
                  scrollToIndex={scrollToIndex}
                  onRowsRendered={this.onRowsRendered}
                  scrollToAlignment="start"
                />
              );
            }}
          </AutoSizer>
        </OutputWrapper>
      </CardBody>
    );
  }
}

export default JobOutput;
