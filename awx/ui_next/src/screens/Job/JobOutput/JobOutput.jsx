import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useHistory, useLocation, withRouter } from 'react-router-dom';
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
import {
  Button,
  Toolbar as _Toolbar,
  ToolbarContent as _ToolbarContent,
  ToolbarItem,
  ToolbarToggleGroup,
  Tooltip,
} from '@patternfly/react-core';
import { SearchIcon } from '@patternfly/react-icons';

import AlertModal from '../../../components/AlertModal';
import { CardBody as _CardBody } from '../../../components/Card';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import ErrorDetail from '../../../components/ErrorDetail';
import Search from '../../../components/Search';
import StatusIcon from '../../../components/StatusIcon';

import JobEvent from './JobEvent';
import JobEventSkeleton from './JobEventSkeleton';
import PageControls from './PageControls';
import HostEventModal from './HostEventModal';
import { HostStatusBar, OutputToolbar } from './shared';
import getRowRangePageSize from './shared/jobOutputUtils';
import isJobRunning from '../../../util/jobs';
import useRequest, { useDismissableError } from '../../../util/useRequest';
import {
  encodeNonDefaultQueryString,
  parseQueryString,
  mergeParams,
  replaceParams,
  removeParams,
  getQSConfig,
} from '../../../util/qs';
import {
  JobsAPI,
  ProjectUpdatesAPI,
  SystemJobsAPI,
  WorkflowJobsAPI,
  InventoriesAPI,
  AdHocCommandsAPI,
} from '../../../api';

const QS_CONFIG = getQSConfig('job_output', {
  order_by: 'start_line',
});

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

const CardBody = styled(_CardBody)`
  display: flex;
  flex-flow: column;
  height: calc(100vh - 267px);
`;

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
  flex: 1 1 auto;
  font-family: monospace;
  font-size: 15px;
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

const Toolbar = styled(_Toolbar)`
  position: inherit;
`;

const ToolbarContent = styled(_ToolbarContent)`
  padding-left: 0px;
  padding-right: 0px;
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

function isHostEvent(jobEvent) {
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
}

const cache = new CellMeasurerCache({
  fixedWidth: true,
  defaultHeight: 25,
});

function JobOutput({
  job,
  type,
  eventRelatedSearchableKeys,
  eventSearchableKeys,
}) {
  const location = useLocation();
  const listRef = useRef(null);
  const isMounted = useRef(false);
  const previousWidth = useRef(0);
  const jobSocketCounter = useRef(0);
  const interval = useRef(null);
  const history = useHistory();
  const [contentError, setContentError] = useState(null);
  const [cssMap, setCssMap] = useState({});
  const [currentlyLoading, setCurrentlyLoading] = useState([]);
  const [hasContentLoading, setHasContentLoading] = useState(true);
  const [hostEvent, setHostEvent] = useState({});
  const [isHostModalOpen, setIsHostModalOpen] = useState(false);
  const [jobStatus, setJobStatus] = useState(job.status ?? 'waiting');
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [remoteRowCount, setRemoteRowCount] = useState(0);
  const [results, setResults] = useState({});

  useEffect(() => {
    isMounted.current = true;
    loadJobEvents();

    if (isJobRunning(job.status)) {
      connectJobSocket(job, data => {
        if (data.group_name === 'job_events') {
          if (data.counter && data.counter > jobSocketCounter.current) {
            jobSocketCounter.current = data.counter;
          }
        }
        if (data.group_name === 'jobs' && data.unified_job_id === job.id) {
          if (data.final_counter) {
            jobSocketCounter.current = data.final_counter;
          }
          if (job.status) {
            setJobStatus(job.status);
          }
        }
      });
      interval.current = setInterval(() => monitorJobSocketCounter(), 5000);
    }

    return function cleanup() {
      if (ws) {
        ws.close();
      }
      clearInterval(interval.current);
      isMounted.current = false;
    };
  }, [location.search]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (listRef.current?.recomputeRowHeights) {
      listRef.current.recomputeRowHeights();
    }
  }, [currentlyLoading, cssMap, remoteRowCount]);

  const {
    error: cancelError,
    isLoading: isCancelling,
    request: cancelJob,
  } = useRequest(
    useCallback(async () => {
      await JobsAPI.cancel(job.id, type);
    }, [job.id, type]),
    {}
  );

  const {
    error: dismissableCancelError,
    dismissError: dismissCancelError,
  } = useDismissableError(cancelError);

  const {
    request: deleteJob,
    isLoading: isDeleting,
    error: deleteError,
  } = useRequest(
    useCallback(async () => {
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
    }, [job, history])
  );

  const {
    error: dismissableDeleteError,
    dismissError: dismissDeleteError,
  } = useDismissableError(deleteError);

  const monitorJobSocketCounter = () => {
    if (jobSocketCounter.current === remoteRowCount) {
      clearInterval(interval.current);
    }
    if (jobSocketCounter.current > remoteRowCount && isMounted.current) {
      setRemoteRowCount(jobSocketCounter.current);
    }
  };

  const loadJobEvents = async () => {
    const loadRange = range(1, 50);

    if (isMounted.current) {
      setHasContentLoading(true);
      setCurrentlyLoading(prevCurrentlyLoading =>
        prevCurrentlyLoading.concat(loadRange)
      );
    }

    try {
      const {
        data: { results: fetchedEvents = [], count },
      } = await JobsAPI.readEvents(job.id, type, {
        page: 1,
        page_size: 50,
        ...parseQueryString(QS_CONFIG, location.search),
      });

      if (isMounted.current) {
        let countOffset = 0;
        if (job?.result_traceback) {
          const tracebackEvent = {
            counter: 1,
            created: null,
            event: null,
            type: null,
            stdout: job?.result_traceback,
            start_line: 0,
          };
          const firstIndex = fetchedEvents.findIndex(
            jobEvent => jobEvent.counter === 1
          );
          if (firstIndex && fetchedResults[firstIndex]?.stdout) {
            const stdoutLines = fetchedEvents[firstIndex].stdout.split('\r\n');
            stdoutLines[0] = tracebackEvent.stdout;
            fetchedEvents[firstIndex].stdout = stdoutLines.join('\r\n');
          } else {
            countOffset += 1;
            fetchedEvents.unshift(tracebackEvent);
          }
        }

        const newResults = {};
        let newResultsCssMap = {};
        fetchedEvents.forEach((jobEvent, index) => {
          newResults[index] = jobEvent;
          const { lineCssMap } = getLineTextHtml(jobEvent);
          newResultsCssMap = { ...newResultsCssMap, ...lineCssMap };
        });
        setResults(newResults);
        setRemoteRowCount(count + countOffset);
        setCssMap(newResultsCssMap);
      }
    } catch (err) {
      setContentError(err);
    } finally {
      if (isMounted.current) {
        setHasContentLoading(false);
        setCurrentlyLoading(prevCurrentlyLoading =>
          prevCurrentlyLoading.filter(n => !loadRange.includes(n))
        );
        loadRange.forEach(n => {
          cache.clear(n);
        });
      }
    }
  };

  const isRowLoaded = ({ index }) => {
    if (results[index]) {
      return true;
    }
    return currentlyLoading.includes(index);
  };

  const handleHostEventClick = hostEventToOpen => {
    setHostEvent(hostEventToOpen);
    setIsHostModalOpen(true);
  };

  const handleHostModalClose = () => {
    setIsHostModalOpen(false);
  };

  const rowRenderer = ({ index, parent, key, style }) => {
    let actualLineTextHtml = [];
    if (results[index]) {
      const { lineTextHtml } = getLineTextHtml(results[index]);
      actualLineTextHtml = lineTextHtml;
    }

    return (
      <CellMeasurer
        key={key}
        cache={cache}
        parent={parent}
        rowIndex={index}
        columnIndex={0}
      >
        {results[index] ? (
          <JobEvent
            isClickable={isHostEvent(results[index])}
            onJobEventClick={() => handleHostEventClick(results[index])}
            className="row"
            style={style}
            lineTextHtml={actualLineTextHtml}
            index={index}
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
  };

  const loadMoreRows = ({ startIndex, stopIndex }) => {
    if (startIndex === 0 && stopIndex === 0) {
      return Promise.resolve(null);
    }

    if (stopIndex > startIndex + 50) {
      stopIndex = startIndex + 50;
    }

    const { page, pageSize, firstIndex } = getRowRangePageSize(
      startIndex,
      stopIndex
    );

    const loadRange = range(
      firstIndex,
      Math.min(firstIndex + pageSize, remoteRowCount)
    );

    if (isMounted.current) {
      setCurrentlyLoading(prevCurrentlyLoading =>
        prevCurrentlyLoading.concat(loadRange)
      );
    }

    const params = {
      page,
      page_size: pageSize,
      ...parseQueryString(QS_CONFIG, location.search),
    };

    return JobsAPI.readEvents(job.id, type, params).then(response => {
      if (isMounted.current) {
        const newResults = {};
        let newResultsCssMap = {};
        response.data.results.forEach((jobEvent, index) => {
          newResults[firstIndex + index] = jobEvent;
          const { lineCssMap } = getLineTextHtml(jobEvent);
          newResultsCssMap = { ...newResultsCssMap, ...lineCssMap };
        });
        setResults(prevResults => ({
          ...prevResults,
          ...newResults,
        }));
        setCssMap(prevCssMap => ({
          ...prevCssMap,
          ...newResultsCssMap,
        }));
        setCurrentlyLoading(prevCurrentlyLoading =>
          prevCurrentlyLoading.filter(n => !loadRange.includes(n))
        );
        loadRange.forEach(n => {
          cache.clear(n);
        });
      }
    });
  };

  const scrollToRow = rowIndex => {
    listRef.current.scrollToRow(rowIndex);
  };

  const handleScrollPrevious = () => {
    const startIndex = listRef.current.Grid._renderedRowStartIndex;
    const stopIndex = listRef.current.Grid._renderedRowStopIndex;
    const scrollRange = stopIndex - startIndex + 1;
    scrollToRow(Math.max(0, startIndex - scrollRange));
  };

  const handleScrollNext = () => {
    const stopIndex = listRef.current.Grid._renderedRowStopIndex;
    scrollToRow(stopIndex - 1);
  };

  const handleScrollFirst = () => {
    scrollToRow(0);
  };

  const handleScrollLast = () => {
    scrollToRow(remoteRowCount);
  };

  const handleResize = ({ width }) => {
    if (width !== previousWidth) {
      cache.clearAll();
      if (listRef.current?.recomputeRowHeights) {
        listRef.current.recomputeRowHeights();
      }
    }
    previousWidth.current = width;
  };

  const handleSearch = (key, value) => {
    let params = parseQueryString(QS_CONFIG, location.search);
    params = mergeParams(params, { [key]: value });
    pushHistoryState(params);
  };

  const handleReplaceSearch = (key, value) => {
    const oldParams = parseQueryString(QS_CONFIG, location.search);
    pushHistoryState(replaceParams(oldParams, { [key]: value }));
  };

  const handleRemoveSearchTerm = (key, value) => {
    let oldParams = parseQueryString(QS_CONFIG, location.search);
    if (parseInt(value, 10)) {
      oldParams = removeParams(QS_CONFIG, oldParams, {
        [key]: parseInt(value, 10),
      });
    }
    pushHistoryState(removeParams(QS_CONFIG, oldParams, { [key]: value }));
  };

  const handleRemoveAllSearchTerms = () => {
    const oldParams = parseQueryString(QS_CONFIG, location.search);
    pushHistoryState(removeParams(QS_CONFIG, oldParams, { ...oldParams }));
  };

  const pushHistoryState = params => {
    const { pathname } = history.location;
    const encodedParams = encodeNonDefaultQueryString(QS_CONFIG, params);
    history.push(encodedParams ? `${pathname}?${encodedParams}` : pathname);
  };

  const renderSearchComponent = i18n => (
    <Search
      qsConfig={QS_CONFIG}
      columns={[
        {
          name: i18n._(t`Stdout`),
          key: 'stdout__icontains',
          isDefault: true,
        },
        {
          name: i18n._(t`Event`),
          key: 'event',
          options: [
            ['runner_on_failed', i18n._(t`Host Failed`)],
            ['runner_on_start', i18n._(t`Host Started`)],
            ['runner_on_ok', i18n._(t`Host OK`)],
            ['runner_on_error', i18n._(t`Host Failure`)],
            ['runner_on_skipped', i18n._(t`Host Skipped`)],
            ['runner_on_unreachable', i18n._(t`Host Unreachable`)],
            ['runner_on_no_hosts', i18n._(t`No Hosts Remaining`)],
            ['runner_on_async_poll', i18n._(t`Host Polling`)],
            ['runner_on_async_ok', i18n._(t`Host Async OK`)],
            ['runner_on_async_failed', i18n._(t`Host Async Failure`)],
            ['runner_item_on_ok', i18n._(t`Item OK`)],
            ['runner_item_on_failed', i18n._(t`Item Failed`)],
            ['runner_item_on_skipped', i18n._(t`Item Skipped`)],
            ['runner_retry', i18n._(t`Host Retry`)],
            ['runner_on_file_diff', i18n._(t`File Difference`)],
            ['playbook_on_start', i18n._(t`Playbook Started`)],
            ['playbook_on_notify', i18n._(t`Running Handlers`)],
            ['playbook_on_include', i18n._(t`Including File`)],
            ['playbook_on_no_hosts_matched', i18n._(t`No Hosts Matched`)],
            ['playbook_on_no_hosts_remaining', i18n._(t`No Hosts Remaining`)],
            ['playbook_on_task_start', i18n._(t`Task Started`)],
            ['playbook_on_vars_prompt', i18n._(t`Variables Prompted`)],
            ['playbook_on_setup', i18n._(t`Gathering Facts`)],
            ['playbook_on_play_start', i18n._(t`Play Started`)],
            ['playbook_on_stats', i18n._(t`Playbook Complete`)],
            ['debug', i18n._(t`Debug`)],
            ['verbose', i18n._(t`Verbose`)],
            ['deprecated', i18n._(t`Deprecated`)],
            ['warning', i18n._(t`Warning`)],
            ['system_warning', i18n._(t`System Warning`)],
            ['error', i18n._(t`Error`)],
          ],
        },
        { name: i18n._(t`Advanced`), key: 'advanced' },
      ]}
      searchableKeys={eventSearchableKeys}
      relatedSearchableKeys={eventRelatedSearchableKeys}
      onSearch={handleSearch}
      onReplaceSearch={handleReplaceSearch}
      onShowAdvancedSearch={() => {}}
      onRemove={handleRemoveSearchTerm}
      isDisabled={isJobRunning(job.status)}
    />
  );

  if (hasContentLoading) {
    return <ContentLoading />;
  }

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  return (
    <I18n>
      {({ i18n }) => (
        <>
          <CardBody>
            {isHostModalOpen && (
              <HostEventModal
                onClose={handleHostModalClose}
                isOpen={isHostModalOpen}
                hostEvent={hostEvent}
              />
            )}
            <OutputHeader>
              <HeaderTitle>
                <StatusIcon status={job.status} />
                <h1>{job.name}</h1>
              </HeaderTitle>
              <OutputToolbar
                job={job}
                jobStatus={jobStatus}
                onCancel={() => setShowCancelModal(true)}
                onDelete={deleteJob}
                isDeleteDisabled={isDeleting}
              />
            </OutputHeader>
            <HostStatusBar counts={job.host_status_counts} />
            <Toolbar
              id="job_output-toolbar"
              clearAllFilters={handleRemoveAllSearchTerms}
              collapseListedFiltersBreakpoint="lg"
              clearFiltersButtonText={i18n._(t`Clear all filters`)}
            >
              <ToolbarContent>
                <ToolbarToggleGroup toggleIcon={<SearchIcon />} breakpoint="lg">
                  <ToolbarItem variant="search-filter">
                    {isJobRunning(job.status) ? (
                      <Tooltip
                        content={i18n._(
                          t`Search is disabled while the job is running`
                        )}
                      >
                        {renderSearchComponent(i18n)}
                      </Tooltip>
                    ) : (
                      renderSearchComponent(i18n)
                    )}
                  </ToolbarItem>
                </ToolbarToggleGroup>
              </ToolbarContent>
            </Toolbar>
            <PageControls
              onScrollFirst={handleScrollFirst}
              onScrollLast={handleScrollLast}
              onScrollNext={handleScrollNext}
              onScrollPrevious={handleScrollPrevious}
            />
            <OutputWrapper cssMap={cssMap}>
              <InfiniteLoader
                isRowLoaded={isRowLoaded}
                loadMoreRows={loadMoreRows}
                rowCount={remoteRowCount}
              >
                {({ onRowsRendered, registerChild }) => (
                  <AutoSizer nonce={window.NONCE_ID} onResize={handleResize}>
                    {({ width, height }) => {
                      return (
                        <List
                          ref={ref => {
                            registerChild(ref);
                            listRef.current = ref;
                          }}
                          deferredMeasurementCache={cache}
                          height={height || 1}
                          onRowsRendered={onRowsRendered}
                          rowCount={remoteRowCount}
                          rowHeight={cache.rowHeight}
                          rowRenderer={rowRenderer}
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
          {showCancelModal && isJobRunning(job.status) && (
            <AlertModal
              isOpen={showCancelModal}
              variant="danger"
              onClose={() => setShowCancelModal(false)}
              title={i18n._(t`Cancel Job`)}
              label={i18n._(t`Cancel Job`)}
              actions={[
                <Button
                  id="cancel-job-confirm-button"
                  key="delete"
                  variant="danger"
                  isDisabled={isCancelling}
                  aria-label={i18n._(t`Cancel job`)}
                  onClick={cancelJob}
                >
                  {i18n._(t`Cancel job`)}
                </Button>,
                <Button
                  id="cancel-job-return-button"
                  key="cancel"
                  variant="secondary"
                  aria-label={i18n._(t`Return`)}
                  onClick={() => setShowCancelModal(false)}
                >
                  {i18n._(t`Return`)}
                </Button>,
              ]}
            >
              {i18n._(
                t`Are you sure you want to submit the request to cancel this job?`
              )}
            </AlertModal>
          )}
          {dismissableDeleteError && (
            <AlertModal
              isOpen={dismissableDeleteError}
              variant="danger"
              onClose={dismissDeleteError}
              title={i18n._(t`Job Delete Error`)}
              label={i18n._(t`Job Delete Error`)}
            >
              <ErrorDetail error={dismissableDeleteError} />
            </AlertModal>
          )}
          {dismissableCancelError && (
            <AlertModal
              isOpen={dismissableCancelError}
              variant="danger"
              onClose={dismissCancelError}
              title={i18n._(t`Job Cancel Error`)}
              label={i18n._(t`Job Cancel Error`)}
            >
              <ErrorDetail error={dismissableCancelError} />
            </AlertModal>
          )}
        </>
      )}
    </I18n>
  );
}

export { JobOutput as _JobOutput };
export default withRouter(JobOutput);
