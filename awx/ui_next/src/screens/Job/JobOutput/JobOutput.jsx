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
import JobEventSkeleton from './JobEventSkeleton';
import MenuControls from './MenuControls';
import HostEventModal from './HostEventModal';

const OutputHeader = styled.div`
  font-weight: var(--pf-global--FontWeight--bold);
`;
const OutputToolbar = styled.div`
  display: flex;
  justify-content: flex-end;
`;
const OutputWrapper = styled.div`
  height: calc(100vh - 350px);
  background-color: #fafafa;
  margin-top: 24px;
  font-family: monospace;
  font-size: 15px;
  outline: 1px solid #d7d7d7;
  display: flex;
  flex-direction: column;
`;
const OutputFooter = styled.div`
  background-color: #ebebeb;
  border-right: 1px solid #d7d7d7;
  width: 75px;
  flex: 1;
`;

function range(low, high) {
  const numbers = [];
  for (let n = low; n <= high; n++) {
    numbers.push(n);
  }
  return numbers;
}

class JobOutput extends Component {
  constructor(props) {
    super(props);
    this.listRef = React.createRef();
    this.state = {
      contentError: null,
      hasContentLoading: true,
      results: {},
      currentlyLoading: [],
      remoteRowCount: 0,
      isHostModalOpen: false,
      hostEvent: {},
    };

    this.cache = new CellMeasurerCache({
      fixedWidth: true,
      defaultHeight: 25,
    });

    this._isMounted = false;
    this.loadJobEvents = this.loadJobEvents.bind(this);
    this.rowRenderer = this.rowRenderer.bind(this);
    this.handleHostEventClick = this.handleHostEventClick.bind(this);
    this.handleHostModalClose = this.handleHostModalClose.bind(this);
    this.handleScrollFirst = this.handleScrollFirst.bind(this);
    this.handleScrollLast = this.handleScrollLast.bind(this);
    this.handleScrollNext = this.handleScrollNext.bind(this);
    this.handleScrollPrevious = this.handleScrollPrevious.bind(this);
    this.handleResize = this.handleResize.bind(this);
    this.isRowLoaded = this.isRowLoaded.bind(this);
    this.loadMoreRows = this.loadMoreRows.bind(this);
    this.scrollToRow = this.scrollToRow.bind(this);
  }

  componentDidMount() {
    this._isMounted = true;
    this.loadJobEvents();
  }

  componentDidUpdate(prevProps, prevState) {
    // recompute row heights for any job events that have transitioned
    // from loading to loaded
    const { currentlyLoading } = this.state;
    let shouldRecomputeRowHeights = false;
    prevState.currentlyLoading
      .filter(n => !currentlyLoading.includes(n))
      .forEach(n => {
        shouldRecomputeRowHeights = true;
        this.cache.clear(n);
      });
    if (shouldRecomputeRowHeights) {
      if (this.listRef.recomputeRowHeights) {
        this.listRef.recomputeRowHeights();
      }
    }
  }

  componentWillUnmount() {
    this._isMounted = false;
  }

  async loadJobEvents() {
    const { job, type } = this.props;

    const loadRange = range(1, 50);
    this._isMounted &&
      this.setState(({ currentlyLoading }) => ({
        hasContentLoading: true,
        currentlyLoading: currentlyLoading.concat(loadRange),
      }));
    try {
      const {
        data: { results: newResults = [], count },
      } = await JobsAPI.readEvents(job.id, type, {
        page_size: 50,
        order_by: 'start_line',
      });
      this._isMounted &&
        this.setState(({ results }) => {
          newResults.forEach(jobEvent => {
            results[jobEvent.counter] = jobEvent;
          });
          return { results, remoteRowCount: count + 1 };
        });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this._isMounted &&
        this.setState(({ currentlyLoading }) => ({
          hasContentLoading: false,
          currentlyLoading: currentlyLoading.filter(
            n => !loadRange.includes(n)
          ),
        }));
    }
  }

  isRowLoaded({ index }) {
    const { results, currentlyLoading } = this.state;
    if (results[index]) {
      return true;
    }
    return currentlyLoading.includes(index);
  }

  handleHostEventClick(hostEvent) {
    this.setState({
      isHostModalOpen: true,
      hostEvent,
    });
  }

  handleHostModalClose() {
    this.setState({
      isHostModalOpen: false,
    });
  }

  rowRenderer({ index, parent, key, style }) {
    const { results } = this.state;

    const isHostEvent = jobEvent => {
      const { event, event_data, host, type } = jobEvent;
      let isHost;
      if (typeof host === 'number' || (event_data && event_data.res)) {
        isHost = true;
      } else if (
        type === 'project_update_event' &&
        event !== 'runner_on_skipped' &&
        event_data.host
      ) {
        isHost = true;
      } else {
        isHost = false;
      }
      return isHost;
    };

    return (
      <CellMeasurer
        key={key}
        cache={this.cache}
        parent={parent}
        rowIndex={index}
        columnIndex={0}
      >
        {results[index] ? (
          <JobEvent
            isClickable={isHostEvent(results[index])}
            onJobEventClick={() => this.handleHostEventClick(results[index])}
            className="row"
            style={style}
            {...results[index]}
          />
        ) : (
          <JobEventSkeleton
            className="row"
            style={style}
            counter={index}
            contentLength={80}
          />
        )}
      </CellMeasurer>
    );
  }

  loadMoreRows({ startIndex, stopIndex }) {
    if (startIndex === 0 && stopIndex === 0) {
      return Promise.resolve(null);
    }
    const { job, type } = this.props;

    const loadRange = range(startIndex, stopIndex);
    this._isMounted &&
      this.setState(({ currentlyLoading }) => ({
        currentlyLoading: currentlyLoading.concat(loadRange),
      }));
    const params = {
      counter__gte: startIndex,
      counter__lte: stopIndex,
      order_by: 'start_line',
    };

    return JobsAPI.readEvents(job.id, type, params).then(response => {
      this._isMounted &&
        this.setState(({ results, currentlyLoading }) => {
          response.data.results.forEach(jobEvent => {
            results[jobEvent.counter] = jobEvent;
          });
          return {
            results,
            currentlyLoading: currentlyLoading.filter(
              n => !loadRange.includes(n)
            ),
          };
        });
    });
  }

  scrollToRow(rowIndex) {
    this.listRef.scrollToRow(rowIndex);
  }

  handleScrollPrevious() {
    const startIndex = this.listRef.Grid._renderedRowStartIndex;
    const stopIndex = this.listRef.Grid._renderedRowStopIndex;
    const scrollRange = stopIndex - startIndex + 1;
    this.scrollToRow(Math.max(0, startIndex - scrollRange));
  }

  handleScrollNext() {
    const stopIndex = this.listRef.Grid._renderedRowStopIndex;
    this.scrollToRow(stopIndex - 1);
  }

  handleScrollFirst() {
    this.scrollToRow(0);
  }

  handleScrollLast() {
    const { remoteRowCount } = this.state;
    this.scrollToRow(remoteRowCount - 1);
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
      contentError,
      hasContentLoading,
      hostEvent,
      isHostModalOpen,
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
        {isHostModalOpen && (
          <HostEventModal
            onClose={this.handleHostModalClose}
            isOpen={isHostModalOpen}
            hostEvent={hostEvent}
          />
        )}
        <OutputHeader>{job.name}</OutputHeader>
        <OutputToolbar>
          <MenuControls
            onScrollFirst={this.handleScrollFirst}
            onScrollLast={this.handleScrollLast}
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
                      height={height || 1}
                      onRowsRendered={onRowsRendered}
                      rowCount={remoteRowCount}
                      rowHeight={this.cache.rowHeight}
                      rowRenderer={this.rowRenderer}
                      scrollToAlignment="start"
                      width={width || 1}
                      overscanRowCount={20}
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
