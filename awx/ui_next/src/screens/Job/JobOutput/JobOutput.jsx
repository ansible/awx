import styled from 'styled-components';
import {
  AutoSizer,
  CellMeasurer,
  CellMeasurerCache,
  InfiniteLoader,
  List,
} from 'react-virtualized';

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
      loadedRowCount: 0,
      loadedRowsMap: {},
      loadingRowCount: 0,
      remoteRowCount: 0,
    };

    this.cache = new CellMeasurerCache({
      fixedWidth: true,
      defaultHeight: 25,
    });

    this.loadJobEvents = this.loadJobEvents.bind(this);
    this.rowRenderer = this.rowRenderer.bind(this);
    this.handleScrollTop = this.handleScrollTop.bind(this);
    this.handleScrollBottom = this.handleScrollBottom.bind(this);
    this.handleScrollNext = this.handleScrollNext.bind(this);
    this.handleScrollPrevious = this.handleScrollPrevious.bind(this);
    this.handleResize = this.handleResize.bind(this);
    this.isRowLoaded = this.isRowLoaded.bind(this);
    this.loadMoreRows = this.loadMoreRows.bind(this);
  }

  componentDidMount() {
    this.loadJobEvents();
  }

  async loadJobEvents() {
    const { job } = this.props;

    this.setState({ hasContentLoading: true });
    try {
      const {
        data: { results = [], count },
      } = await JobsAPI.readEvents(job.id, job.type, {
        page_size: 50,
        order_by: 'start_line',
      });
      this.setState({ results, remoteRowCount: count + 1 });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  isRowLoaded({ index }) {
    const { results } = this.state;
    return !!results[index];
  }

  rowRenderer({ index, parent, key, style }) {
    const { results } = this.state;
    if (!results[index]) {
      return;
    }
    const { created, event, stdout, start_line } = results[index];
    return (
      <CellMeasurer
        key={key}
        cache={this.cache}
        parent={parent}
        rowIndex={index}
        columnIndex={0}
      >
        <JobEvent
          className="row"
          style={style}
          created={created}
          event={event}
          start_line={start_line}
          stdout={stdout}
        />
      </CellMeasurer>
    );
  }

  async loadMoreRows({ startIndex, stopIndex }) {
    const { job } = this.props;
    const { results } = this.state;

    let params = {
      counter__gte: startIndex,
      counter__lte: stopIndex,
      order_by: 'start_line',
    };

    return await JobsAPI.readEvents(job.id, job.type, params).then(response => {
      this.setState({ results: [...results, ...response.data.results] });
    });
  }

  handleScrollPrevious() {
    const startIndex = this.listRef.Grid._renderedRowStartIndex;
    const stopIndex = this.listRef.Grid._renderedRowStopIndex;
    const range = stopIndex - startIndex + 1;
    this.listRef.scrollToRow(Math.max(0, startIndex - range));
  }

  handleScrollNext() {
    const stopIndex = this.listRef.Grid._renderedRowStopIndex;
    this.listRef.scrollToRow(stopIndex - 1);
  }

  handleScrollTop() {
    this.listRef.scrollToRow(0);
  }

  handleScrollBottom() {
    const { remoteRowCount } = this.state;
    this.listRef.scrollToRow(remoteRowCount - 1);
  }

  handleResize({ width }) {
    if (width !== this._previousWidth) {
      this.cache.clearAll();
      this.listRef.recomputeRowHeights();
    }
    this._previousWidth = width;
  }

  render() {
    const { job } = this.props;
    const {
      hasContentLoading,
      contentError,
      scrollToIndex,
      remoteRowCount,
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
          <InfiniteLoader
            isRowLoaded={this.isRowLoaded}
            loadMoreRows={this.loadMoreRows}
            rowCount={remoteRowCount}
          >
            {({ onRowsRendered, registerChild }) => (
              <AutoSizer onResize={this.handleResize}>
                {({ width, height }) => {
                  return (
                    <List
                      ref={ref => {
                        this.listRef = ref;
                        registerChild(ref);
                      }}
                      deferredMeasurementCache={this.cache}
                      height={height}
                      onRowsRendered={onRowsRendered}
                      rowCount={remoteRowCount}
                      rowHeight={this.cache.rowHeight}
                      rowRenderer={this.rowRenderer}
                      scrollToAlignment="start"
                      scrollToIndex={scrollToIndex}
                      width={width}
                    />
                  );
                }}
              </AutoSizer>
            )}
          </InfiniteLoader>
          <OutputFooter />
        </OutputWrapper>
      </CardBody>
    );
  }
}

export default JobOutput;
