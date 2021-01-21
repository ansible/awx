import React, { Component, Fragment } from 'react';
import { withRouter } from 'react-router-dom';
import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import {
  AutoSizer,
  CellMeasurer,
  CellMeasurerCache,
  InfiniteLoader,
  List,
} from 'react-virtualized';
import Ansi from 'ansi-to-html';
import hasAnsi from 'has-ansi';
import { AllHtmlEntities } from 'html-entities';

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

const EVENT_START_TASK = 'playbook_on_task_start';
const EVENT_START_PLAY = 'playbook_on_play_start';
const EVENT_STATS_PLAY = 'playbook_on_stats';
const TIME_EVENTS = [EVENT_START_TASK, EVENT_START_PLAY, EVENT_STATS_PLAY];

const ansi = new Ansi({
  stream: true,
  colors: {
    0: '#000',
    1: '#A30000',
    2: '#486B00',
    3: '#795600',
    4: '#00A',
    5: '#A0A',
    6: '#004368',
    7: '#AAA',
    8: '#555',
    9: '#F55',
    10: '#5F5',
    11: '#FF5',
    12: '#55F',
    13: '#F5F',
    14: '#5FF',
    15: '#FFF',
  },
});
const entities = new AllHtmlEntities();

function getTimestamp({ created }) {
  const date = new Date(created);

  const dateHours = date.getHours();
  const dateMinutes = date.getMinutes();
  const dateSeconds = date.getSeconds();

  const stampHours = dateHours < 10 ? `0${dateHours}` : dateHours;
  const stampMinutes = dateMinutes < 10 ? `0${dateMinutes}` : dateMinutes;
  const stampSeconds = dateSeconds < 10 ? `0${dateSeconds}` : dateSeconds;

  return `${stampHours}:${stampMinutes}:${stampSeconds}`;
}

const styleAttrPattern = new RegExp('style="[^"]*"', 'g');

function createStyleAttrHash(styleAttr) {
  let hash = 0;
  for (let i = 0; i < styleAttr.length; i++) {
    hash = (hash << 5) - hash; // eslint-disable-line no-bitwise
    hash += styleAttr.charCodeAt(i);
    hash &= hash; // eslint-disable-line no-bitwise
  }
  return `${hash}`;
}

function replaceStyleAttrs(html) {
  const allStyleAttrs = [...new Set(html.match(styleAttrPattern))];
  const cssMap = {};
  let result = html;
  for (let i = 0; i < allStyleAttrs.length; i++) {
    const styleAttr = allStyleAttrs[i];
    const cssClassName = `output-${createStyleAttrHash(styleAttr)}`;

    cssMap[cssClassName] = styleAttr.replace('style="', '').slice(0, -1);
    result = result.split(styleAttr).join(`class="${cssClassName}"`);
  }
  return { cssMap, result };
}

function getLineTextHtml({ created, event, start_line, stdout }) {
  const sanitized = entities.encode(stdout);
  let lineCssMap = {};
  const lineTextHtml = [];

  sanitized.split('\r\n').forEach((lineText, index) => {
    let html;
    if (hasAnsi(lineText)) {
      const { cssMap, result } = replaceStyleAttrs(ansi.toHtml(lineText));
      html = result;
      lineCssMap = { ...lineCssMap, ...cssMap };
    } else {
      html = lineText;
    }

    if (index === 1 && TIME_EVENTS.includes(event)) {
      const time = getTimestamp({ created });
      html += `<span class="time">${time}</span>`;
    }

    lineTextHtml.push({
      lineNumber: start_line + index,
      html,
    });
  });

  return {
    lineCssMap,
    lineTextHtml,
  };
}

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
  ${({ cssMap }) =>
    Object.keys(cssMap).map(className => `.${className}{${cssMap[className]}}`)}
`;

const OutputFooter = styled.div`
  background-color: #ebebeb;
  border-right: 1px solid #d7d7d7;
  width: 75px;
  flex: 1;
`;

let ws;
function connectJobSocket({ type, id }, onMessage) {
  ws = new WebSocket(
    `${window.location.protocol === 'http:' ? 'ws:' : 'wss:'}//${
      window.location.host
    }/websocket/`
  );

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
      cssMap: {},
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
    const { currentlyLoading, cssMap } = this.state;
    let shouldRecomputeRowHeights = false;
    prevState.currentlyLoading
      .filter(n => !currentlyLoading.includes(n))
      .forEach(n => {
        shouldRecomputeRowHeights = true;
        this.cache.clear(n);
      });
    if (Object.keys(cssMap).length !== Object.keys(prevState.cssMap).length) {
      shouldRecomputeRowHeights = true;
    }
    if (shouldRecomputeRowHeights) {
      if (this.listRef.recomputeRowHeights) {
        this.listRef.recomputeRowHeights();
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

    let actualLineTextHtml = [];
    if (results[index]) {
      const { lineTextHtml, lineCssMap } = getLineTextHtml(results[index]);
      this.setState(({ cssMap }) => ({ cssMap: { ...cssMap, ...lineCssMap } }));
      actualLineTextHtml = lineTextHtml;
    }

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
            lineTextHtml={actualLineTextHtml}
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
      if (this.listRef?.recomputeRowHeights) {
        this.listRef.recomputeRowHeights();
      }
    }
    this._previousWidth = width;
  }

  render() {
    const { job } = this.props;

    const {
      contentError,
      deletionError,
      hasContentLoading,
      hostEvent,
      isHostModalOpen,
      remoteRowCount,
      cssMap,
    } = this.state;

    if (hasContentLoading) {
      return <ContentLoading />;
    }

    if (contentError) {
      return <ContentError error={contentError} />;
    }

    return (
      <Fragment>
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
          />
          <OutputWrapper cssMap={cssMap}>
            <InfiniteLoader
              isRowLoaded={this.isRowLoaded}
              loadMoreRows={this.loadMoreRows}
              rowCount={remoteRowCount}
            >
              {({ onRowsRendered, registerChild }) => (
                <AutoSizer nonce={window.NONCE_ID} onResize={this.handleResize}>
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
        {deletionError && (
          <>
            <I18n>
              {({ i18n }) => (
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
            </I18n>
          </>
        )}
      </Fragment>
    );
  }
}

export { JobOutput as _JobOutput };
export default withRouter(JobOutput);
