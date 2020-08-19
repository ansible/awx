import React, { Component } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import {
  AutoSizer,
  CellMeasurer,
  CellMeasurerCache,
  InfiniteLoader,
  List,
} from 'react-virtualized';

import AlertModal from '../../../components/AlertModal';
import { CardBody } from '../../../components/Card';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import ErrorDetail from '../../../components/ErrorDetail';
import StatusIcon from '../../../components/StatusIcon';

import JobEvent from './JobEvent';
import JobEventSkeleton from './JobEventSkeleton';
import PageControls from './PageControls';
import HostEventModal from './HostEventModal';
import { HostStatusBar, OutputToolbar } from './shared';
import {
  JobsAPI,
  ProjectUpdatesAPI,
  SystemJobsAPI,
  WorkflowJobsAPI,
  InventoriesAPI,
  AdHocCommandsAPI,
} from '../../../api';

const UNLOADED_EVENT = 'UNLOADED_EVENT';

const HeaderTitle = styled.div`
  display: inline-flex;
  align-items: center;
  h1 {
    margin-left: 10px;
    font-weight: var(--pf-global--FontWeight--bold);
  }
`;

const OutputHeader = styled.div`
  display: flex;
  justify-content: space-between;
`;

const OutputWrapper = styled.div`
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
  font-family: monospace;
  font-size: 15px;
  height: calc(100vh - 350px);
  outline: 1px solid #d7d7d7;
`;

const OutputFooter = styled.div`
  background-color: #ebebeb;
  border-right: 1px solid #d7d7d7;
  width: 75px;
  flex: 1;
`;

let ws;
function connectJobSocket({ type, id }, onMessage) {
  ws = new WebSocket(`wss://${window.location.host}/websocket/`);

  ws.onopen = () => {
    const xrftoken = `; ${document.cookie}`
      .split('; csrftoken=')
      .pop()
      .split(';')
      .shift();
    const eventGroup = `${type}_events`;
    ws.send(
      JSON.stringify({
        xrftoken,
        groups: { jobs: ['summary', 'status_changed'], [eventGroup]: [id] },
      })
    );
  };

  ws.onmessage = e => {
    onMessage(JSON.parse(e.data));
  };

  ws.onclose = e => {
    // eslint-disable-next-line no-console
    console.debug('Socket closed. Reconnecting...', e);
    setTimeout(() => {
      connectJobSocket({ type, id }, onMessage);
    }, 1000);
  };

  ws.onerror = err => {
    // eslint-disable-next-line no-console
    console.debug('Socket error: ', err, 'Disconnecting...');
    ws.close();
  };
}

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
      deletionError: null,
      hasContentLoading: true,
      results: {},
      currentlyLoading: [],
      remoteRowCount: 0,
      isHostModalOpen: false,
      hostEvent: {},
      collapsedTaskUuids: [],
      collapsedPlayUuids: [],
      collapsedRowRanges: [],
    };

    this.cache = new CellMeasurerCache({
      fixedWidth: true,
      defaultHeight: 25,
    });

    this._isMounted = false;
    this.loadJobEvents = this.loadJobEvents.bind(this);
    this.handleDeleteJob = this.handleDeleteJob.bind(this);
    this.rowRenderer = this.rowRenderer.bind(this);
    this.handleHostEventClick = this.handleHostEventClick.bind(this);
    this.handleHostModalClose = this.handleHostModalClose.bind(this);
    this.handleScrollFirst = this.handleScrollFirst.bind(this);
    this.handleScrollLast = this.handleScrollLast.bind(this);
    this.handleScrollNext = this.handleScrollNext.bind(this);
    this.handleScrollPrevious = this.handleScrollPrevious.bind(this);
    this.handleTaskToggle = this.handleTaskToggle.bind(this);
    this.handlePlayToggle = this.handlePlayToggle.bind(this);
    this.handleResize = this.handleResize.bind(this);
    this.isRowLoaded = this.isRowLoaded.bind(this);
    this.loadMoreRows = this.loadMoreRows.bind(this);
    this.scrollToRow = this.scrollToRow.bind(this);
    this.monitorJobSocketCounter = this.monitorJobSocketCounter.bind(this);
  }

  componentDidMount() {
    const { job } = this.props;
    this._isMounted = true;
    this.loadJobEvents();

    connectJobSocket(job, data => {
      if (data.counter && data.counter > this.jobSocketCounter) {
        this.jobSocketCounter = data.counter;
      } else if (data.final_counter && data.unified_job_id === job.id) {
        this.jobSocketCounter = data.final_counter;
      }
    });
    this.interval = setInterval(() => this.monitorJobSocketCounter(), 5000);
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
        this.listRef.forceUpdateGrid();
      }
    }
  }

  componentWillUnmount() {
    if (ws) {
      ws.close();
    }
    clearInterval(this.interval);
    this._isMounted = false;
  }

  monitorJobSocketCounter() {
    const { remoteRowCount } = this.state;
    if (this.jobSocketCounter >= remoteRowCount) {
      this._isMounted &&
        this.setState({ remoteRowCount: this.jobSocketCounter + 1 });
    }
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

  async handleDeleteJob() {
    const { job, history } = this.props;
    try {
      switch (job.type) {
        case 'project_update':
          await ProjectUpdatesAPI.destroy(job.id);
          break;
        case 'system_job':
          await SystemJobsAPI.destroy(job.id);
          break;
        case 'workflow_job':
          await WorkflowJobsAPI.destroy(job.id);
          break;
        case 'ad_hoc_command':
          await AdHocCommandsAPI.destroy(job.id);
          break;
        case 'inventory_update':
          await InventoriesAPI.destroy(job.id);
          break;
        default:
          await JobsAPI.destroy(job.id);
      }
      history.push('/jobs');
    } catch (err) {
      this.setState({ deletionError: err });
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

  async handleTaskToggle(task_uuid) {
    if (!task_uuid) return;

    const { job, type } = this.props;
    const { collapsedTaskUuids, collapsedRowRanges, results } = this.state;

    // get array of our current rows sorted by counter
    const rows = [];
    Object.keys(results).forEach(key => {
      rows.push(results[key]);
    });
    rows.sort((a, b) => (a.counter > b.counter ? 1 : -1));

    const [taskRow] = rows.filter(r => r.uuid === task_uuid);
    let hasAllNestedEvents = false;
    rows.forEach(row => {
      if (!hasAllNestedEvents && row.counter > taskRow.counter) {
        if (row.event_level <= 2) {
          hasAllNestedEvents = true;
        }
      }
    });

    // make sure there are no missing events between toggled event and
    // next task or play event
    rows.forEach((row, index) => {
      if (row.counter > taskRow.counter) {
        if (row.counter !== rows[index - 1].counter + 1) {
          hasAllNestedEvents = false;
        }
      }
    });

    const [collapsedRange2] = collapsedRowRanges.filter(
      r => r[2] === task_uuid
    );

    // check if all events nested under that task have been downloaded
    if (!collapsedRange2 && hasAllNestedEvents) {
      if (collapsedTaskUuids.includes(task_uuid)) {
        this.setState({
          collapsedTaskUuids: collapsedTaskUuids.filter(u => u !== task_uuid),
        });
      } else {
        this.setState({
          collapsedTaskUuids: collapsedTaskUuids.concat(task_uuid),
        });
      }

      this.cache.clearAll();
      this.listRef.recomputeRowHeights();
      this.listRef.forceUpdateGrid();
    } else {
      // make an api request to figure out the range of events that _should_ be
      if (collapsedTaskUuids.includes(task_uuid)) {
        this.setState(currentState => {
          // results[counter] = { counter, event: UNLOADED_EVENT };
          const { results } = currentState;
          const [collapsedRange] = currentState.collapsedRowRanges.filter(
            r => r[2] === task_uuid
          );
          range(...collapsedRange).forEach(counter => {
            delete results[counter];
          });

          return {
            results,
            collapsedTaskUuids: collapsedTaskUuids.filter(u => u !== task_uuid),
            collapsedRowRanges: currentState.collapsedRowRanges.filter(
              r => r[2] !== task_uuid
            ),
          };
        });
        this.cache.clearAll();
        this.listRef.recomputeRowHeights();
        this.listRef.forceUpdateGrid();
        return;
      }
      const {
        data: { results: newResults = [] },
      } = await JobsAPI.readEvents(job.id, type, {
        counter__gt: taskRow.counter,
        event__in:
          'playbook_on_start,playbook_on_notify,playbook_on_include,playbook_on_no_hosts_matched,playbook_on_no_hosts_remaining,playbook_on_task_start,playbook_on_vars_prompt,playbook_on_setup,playbook_on_import_for_host,playbook_on_not_import_for_host,playbook_on_play_start,playbook_on_stats',
        order_by: '-counter',
      });

      // TODO: handle no results differently?
      if (newResults.length <= 0) return;

      const [nextUncollapsedEvent] = newResults;
      this.setState(currentState => {
        return {
          collapsedTaskUuids: currentState.collapsedTaskUuids.concat(task_uuid),
          collapsedRowRanges: currentState.collapsedRowRanges.concat([
            [taskRow.counter + 1, nextUncollapsedEvent.counter - 1, task_uuid],
          ]),
        };
      });

      this.cache.clearAll();
      this.listRef.recomputeRowHeights();
      this.listRef.forceUpdateGrid();
    }
  }

  handlePlayToggle(play_uuid) {
    const { collapsedPlayUuids, collapsedTaskUuids, results } = this.state;

    const isCollapsing = !collapsedPlayUuids.includes(play_uuid);

    if (isCollapsing) {
      if (!collapsedPlayUuids.includes(play_uuid)) {
        this.setState({
          collapsedPlayUuids: collapsedPlayUuids.concat(play_uuid),
        });
      }

      Object.values(results).forEach(result => {
        if (result.event_level === 2) {
          if (result.event_data.play_uuid === play_uuid) {
            if (!collapsedTaskUuids.includes(result.uuid)) {
              this.setState(currentState => {
                return {
                  collapsedTaskUuids: currentState.collapsedTaskUuids.concat(
                    result.uuid
                  ),
                };
              });
            }
          }
        }
      });
    } else {
      this.setState(currentState => {
        return {
          collapsedPlayUuids: currentState.collapsedPlayUuids.filter(
            u => u !== play_uuid
          ),
        };
      });
    }

    this.cache.clearAll();
    this.listRef.recomputeRowHeights();
    this.listRef.forceUpdateGrid();
  }

  rowRenderer({ index, parent, key, style }) {
    const { results, collapsedTaskUuids, collapsedPlayUuids } = this.state;

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

    const uuid = results[index]?.uuid;
    const taskUuid = results[index]?.event_data?.task_uuid;
    const playUuid = results[index]?.event_data?.play_uuid;
    const isTaskCollapsed = collapsedTaskUuids.includes(taskUuid);
    const isPlayCollapsed = collapsedPlayUuids.includes(playUuid);

    let cellContent = null;

    if (
      results[index]?.event !== UNLOADED_EVENT &&
      (!isTaskCollapsed || (uuid === taskUuid && !isPlayCollapsed))
    ) {
      cellContent = results[index] ? (
        <JobEvent
          isClickable={isHostEvent(results[index])}
          onJobEventClick={() => this.handleHostEventClick(results[index])}
          className="row"
          style={style}
          onPlayToggle={() => this.handlePlayToggle(playUuid)}
          onTaskToggle={() => this.handleTaskToggle(taskUuid)}
          isCollapsed={isTaskCollapsed || isPlayCollapsed}
          {...results[index]}
        />
      ) : (
        <JobEventSkeleton
          className="row"
          style={style}
          counter={index}
          contentLength={80}
        />
      );
    } else {
      cellContent = (
        <div style={{ lineHeight: 0, height: 0, visibility: 'hidden' }} />
      );
    }

    return (
      <CellMeasurer
        key={key}
        cache={this.cache}
        parent={parent}
        rowIndex={index}
        columnIndex={0}
      >
        {cellContent}
      </CellMeasurer>
    );
  }

  loadMoreRows({ startIndex, stopIndex }) {
    if (startIndex === 0 && stopIndex === 0) {
      return Promise.resolve(null);
    }
    const { job, type } = this.props;
    const { collapsedRowRanges } = this.state;

    // check if the wanted rows are unloaded but collapsed
    let isRangeCollapsed = false;
    let collapsedRange = null;
    collapsedRowRanges.forEach(eventRange => {
      if (startIndex >= eventRange[0] && stopIndex <= eventRange[1]) {
        isRangeCollapsed = true;
        collapsedRange = eventRange;
      }
    });

    if (isRangeCollapsed) {
      this.setState(({ results, currentlyLoading }) => {
        range(...collapsedRange).forEach(counter => {
          results[counter] = { counter, event: UNLOADED_EVENT };
        });
        return {
          results,
        };
      });
      this.cache.clearAll();
      this.listRef.recomputeRowHeights();
      this.listRef.forceUpdateGrid();
      return;
    }

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
      if (!this._isMounted) return;
      const { collapsedPlayUuids } = this.state;

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

      const newCollapsedTaskUuids = [];
      response.data.results.forEach(jobEvent => {
        if (jobEvent.event_level === 2) {
          if (collapsedPlayUuids.includes(jobEvent.event_data.play_uuid)) {
            newCollapsedTaskUuids.push(jobEvent.uuid);
          }
        }
      });

      if (newCollapsedTaskUuids.length <= 0) {
        return;
      }

      this.setState(({ collapsedTaskUuids }) => {
        const updatedCollapsedTaskUuids = collapsedTaskUuids.concat(
          newCollapsedTaskUuids
        );
        return {
          collapsedTaskUuids: [...new Set(updatedCollapsedTaskUuids)],
        };
      });
      this.cache.clearAll();
      this.listRef.recomputeRowHeights();
      this.listRef.forceUpdateGrid();
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
    const { job, i18n } = this.props;

    const {
      contentError,
      deletionError,
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
        <OutputHeader>
          <HeaderTitle>
            <StatusIcon status={job.status} />
            <h1>{job.name}</h1>
          </HeaderTitle>
          <OutputToolbar job={job} onDelete={this.handleDeleteJob} />
        </OutputHeader>
        <HostStatusBar counts={job.host_status_counts} />
        <PageControls
          onScrollFirst={this.handleScrollFirst}
          onScrollLast={this.handleScrollLast}
          onScrollNext={this.handleScrollNext}
          onScrollPrevious={this.handleScrollPrevious}
          onPlusClick={this.handlePlusClick}
        />
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
        {deletionError && (
          <AlertModal
            isOpen={deletionError}
            variant="danger"
            onClose={() => this.setState({ deletionError: null })}
            title={i18n._(t`Job Delete Error`)}
            label={i18n._(t`Job Delete Error`)}
          >
            <ErrorDetail error={deletionError} />
          </AlertModal>
        )}
      </CardBody>
    );
  }
}

export { JobOutput as _JobOutput };
export default withI18n()(withRouter(JobOutput));
