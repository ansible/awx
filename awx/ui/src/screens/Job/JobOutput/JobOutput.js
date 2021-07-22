import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useHistory, useLocation } from 'react-router-dom';
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
  Toolbar,
  ToolbarContent,
  ToolbarItem,
  ToolbarToggleGroup,
  Tooltip,
} from '@patternfly/react-core';
import { SearchIcon } from '@patternfly/react-icons';

import AlertModal from 'components/AlertModal';
import { CardBody as _CardBody } from 'components/Card';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import ErrorDetail from 'components/ErrorDetail';
import Search from 'components/Search';
import StatusIcon from 'components/StatusIcon';

import { getJobModel, isJobRunning } from 'util/jobs';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import useInterval from 'hooks/useInterval';
import {
  parseQueryString,
  mergeParams,
  removeParams,
  getQSConfig,
  updateQueryString,
} from 'util/qs';
import useIsMounted from 'hooks/useIsMounted';
import JobEvent from './JobEvent';
import JobEventSkeleton from './JobEventSkeleton';
import PageControls from './PageControls';
import HostEventModal from './HostEventModal';
import { HostStatusBar, OutputToolbar } from './shared';
import getRowRangePageSize from './shared/jobOutputUtils';

const QS_CONFIG = getQSConfig('job_output', {
  order_by: 'counter',
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
    Object.keys(cssMap).map(
      (className) => `.${className}{${cssMap[className]}}`
    )}
`;

const OutputFooter = styled.div`
  background-color: #ebebeb;
  border-right: 1px solid #d7d7d7;
  width: 75px;
  flex: 1;
`;

const SearchToolbar = styled(Toolbar)`
  position: inherit !important;
`;

const SearchToolbarContent = styled(ToolbarContent)`
  padding-left: 0px !important;
  padding-right: 0px !important;
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

  ws.onmessage = (e) => {
    onMessage(JSON.parse(e.data));
  };

  ws.onclose = (e) => {
    if (e.code !== 1000) {
      // eslint-disable-next-line no-console
      console.debug('Socket closed. Reconnecting...', e);
      setTimeout(() => {
        connectJobSocket({ type, id }, onMessage);
      }, 1000);
    }
  };

  ws.onerror = (err) => {
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

const getEventRequestParams = (job, remoteRowCount, requestRange) => {
  const [startIndex, stopIndex] = requestRange;
  if (isJobRunning(job?.status)) {
    return [
      { counter__gte: startIndex, limit: stopIndex - startIndex + 1 },
      range(startIndex, Math.min(stopIndex, remoteRowCount)),
      startIndex,
    ];
  }
  const { page, pageSize, firstIndex } = getRowRangePageSize(
    startIndex,
    stopIndex
  );
  const loadRange = range(
    firstIndex,
    Math.min(firstIndex + pageSize, remoteRowCount)
  );

  return [{ page, page_size: pageSize }, loadRange, firstIndex];
};

function JobOutput({ job, eventRelatedSearchableKeys, eventSearchableKeys }) {
  const location = useLocation();
  const listRef = useRef(null);
  const previousWidth = useRef(0);
  const jobSocketCounter = useRef(0);
  const isMounted = useIsMounted();
  const scrollTop = useRef(0);
  const scrollHeight = useRef(0);
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
  const [isFollowModeEnabled, setIsFollowModeEnabled] = useState(
    isJobRunning(job.status)
  );
  const [isMonitoringWebsocket, setIsMonitoringWebsocket] = useState(false);

  useInterval(
    () => {
      monitorJobSocketCounter();
    },
    isMonitoringWebsocket ? 5000 : null
  );

  useEffect(() => {
    loadJobEvents();

    if (isJobRunning(job.status)) {
      connectJobSocket(job, (data) => {
        if (data.group_name === 'job_events') {
          if (data.counter && data.counter > jobSocketCounter.current) {
            jobSocketCounter.current = data.counter;
          }
        }
        if (data.group_name === 'jobs' && data.unified_job_id === job.id) {
          if (data.final_counter) {
            jobSocketCounter.current = data.final_counter;
          }
          if (data.status) {
            setJobStatus(data.status);
          }
        }
      });
      setIsMonitoringWebsocket(true);
    }

    return function cleanup() {
      if (ws) {
        ws.close();
      }
      setIsMonitoringWebsocket(false);
      isMounted.current = false;
    };
  }, [location.search]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (listRef.current?.recomputeRowHeights) {
      listRef.current.recomputeRowHeights();
    }
  }, [currentlyLoading, cssMap, remoteRowCount]);

  useEffect(() => {
    if (jobStatus && !isJobRunning(jobStatus)) {
      if (jobSocketCounter.current > remoteRowCount && isMounted.current) {
        setRemoteRowCount(jobSocketCounter.current);
      }

      if (isMonitoringWebsocket) {
        setIsMonitoringWebsocket(false);
      }

      if (isFollowModeEnabled) {
        setTimeout(() => setIsFollowModeEnabled(false), 1000);
      }
    }
  }, [jobStatus]); // eslint-disable-line react-hooks/exhaustive-deps

  const {
    error: cancelError,
    isLoading: isCancelling,
    request: cancelJob,
  } = useRequest(
    useCallback(async () => {
      await getJobModel(job.type).cancel(job.id);
    }, [job.id, job.type]),
    {}
  );

  const { error: dismissableCancelError, dismissError: dismissCancelError } =
    useDismissableError(cancelError);

  const {
    request: deleteJob,
    isLoading: isDeleting,
    error: deleteError,
  } = useRequest(
    useCallback(async () => {
      await getJobModel(job.type).destroy(job.id);

      history.push('/jobs');
    }, [job.type, job.id, history])
  );

  const { error: dismissableDeleteError, dismissError: dismissDeleteError } =
    useDismissableError(deleteError);

  const monitorJobSocketCounter = () => {
    if (jobSocketCounter.current > remoteRowCount && isMounted.current) {
      setRemoteRowCount(jobSocketCounter.current);
    }
    if (
      jobSocketCounter.current === remoteRowCount &&
      !isJobRunning(job.status)
    ) {
      setIsMonitoringWebsocket(false);
    }
  };

  const loadJobEvents = async () => {
    const [params, loadRange] = getEventRequestParams(job, 50, [1, 50]);

    if (isMounted.current) {
      setHasContentLoading(true);
      setCurrentlyLoading((prevCurrentlyLoading) =>
        prevCurrentlyLoading.concat(loadRange)
      );
    }

    const eventPromise = getJobModel(job.type).readEvents(job.id, {
      ...params,
      ...parseQueryString(QS_CONFIG, location.search),
    });

    let countRequest;
    if (isJobRunning(job?.status)) {
      // If the job is running, it means we're using limit-offset pagination. Requests
      // with limit-offset pagination won't return a total event count for performance
      // reasons. In this situation, we derive the remote row count by using the highest
      // counter available in the database.
      countRequest = async () => {
        const {
          data: { results: lastEvents = [] },
        } = await getJobModel(job.type).readEvents(job.id, {
          order_by: '-counter',
          limit: 1,
        });
        return lastEvents.length >= 1 ? lastEvents[0].counter : 0;
      };
    } else {
      countRequest = async () => {
        const {
          data: { count: eventCount },
        } = await eventPromise;
        return eventCount;
      };
    }

    try {
      const [
        {
          data: { results: fetchedEvents = [] },
        },
        count,
      ] = await Promise.all([eventPromise, countRequest()]);

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
            (jobEvent) => jobEvent.counter === 1
          );
          if (firstIndex && fetchedEvents[firstIndex]?.stdout) {
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
        setCurrentlyLoading((prevCurrentlyLoading) =>
          prevCurrentlyLoading.filter((n) => !loadRange.includes(n))
        );
        loadRange.forEach((n) => {
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

  const handleHostEventClick = (hostEventToOpen) => {
    setHostEvent(hostEventToOpen);
    setIsHostModalOpen(true);
  };

  const handleHostModalClose = () => {
    setIsHostModalOpen(false);
  };

  const rowRenderer = ({ index, parent, key, style }) => {
    if (listRef.current && isFollowModeEnabled) {
      setTimeout(() => scrollToRow(remoteRowCount - 1), 0);
    }
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

    const [requestParams, loadRange, firstIndex] = getEventRequestParams(
      job,
      remoteRowCount,
      [startIndex, stopIndex]
    );

    if (isMounted.current) {
      setCurrentlyLoading((prevCurrentlyLoading) =>
        prevCurrentlyLoading.concat(loadRange)
      );
    }

    const params = {
      ...requestParams,
      ...parseQueryString(QS_CONFIG, location.search),
    };

    return getJobModel(job.type)
      .readEvents(job.id, params)
      .then((response) => {
        if (isMounted.current) {
          const newResults = {};
          let newResultsCssMap = {};
          response.data.results.forEach((jobEvent, index) => {
            newResults[firstIndex + index] = jobEvent;
            const { lineCssMap } = getLineTextHtml(jobEvent);
            newResultsCssMap = { ...newResultsCssMap, ...lineCssMap };
          });
          setResults((prevResults) => ({
            ...prevResults,
            ...newResults,
          }));
          setCssMap((prevCssMap) => ({
            ...prevCssMap,
            ...newResultsCssMap,
          }));
          setCurrentlyLoading((prevCurrentlyLoading) =>
            prevCurrentlyLoading.filter((n) => !loadRange.includes(n))
          );
          loadRange.forEach((n) => {
            cache.clear(n);
          });
        }
      });
  };

  const scrollToRow = (rowIndex) => {
    if (listRef.current) {
      listRef.current.scrollToRow(rowIndex);
    }
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
    scrollToRow(remoteRowCount - 1);
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
    const params = parseQueryString(QS_CONFIG, location.search);
    const qs = updateQueryString(
      QS_CONFIG,
      location.search,
      mergeParams(params, { [key]: value })
    );
    pushHistoryState(qs);
  };

  const handleReplaceSearch = (key, value) => {
    const qs = updateQueryString(QS_CONFIG, location.search, {
      [key]: value,
    });
    pushHistoryState(qs);
  };

  const handleRemoveSearchTerm = (key, value) => {
    const oldParams = parseQueryString(QS_CONFIG, location.search);
    const updatedParams = removeParams(QS_CONFIG, oldParams, {
      [key]: value,
    });
    const qs = updateQueryString(QS_CONFIG, location.search, updatedParams);
    pushHistoryState(qs);
  };

  const handleRemoveAllSearchTerms = () => {
    const oldParams = parseQueryString(QS_CONFIG, location.search);
    Object.keys(oldParams).forEach((key) => {
      oldParams[key] = null;
    });
    const qs = updateQueryString(QS_CONFIG, location.search, oldParams);
    pushHistoryState(qs);
  };

  const pushHistoryState = (qs) => {
    const { pathname } = history.location;
    history.push(qs ? `${pathname}?${qs}` : pathname);
  };

  const handleFollowToggle = () => {
    if (isFollowModeEnabled) {
      setIsFollowModeEnabled(false);
    } else {
      setIsFollowModeEnabled(true);
      scrollToRow(remoteRowCount - 1);
    }
  };

  const handleScroll = (e) => {
    if (
      isFollowModeEnabled &&
      scrollTop.current > e.scrollTop &&
      scrollHeight.current === e.scrollHeight
    ) {
      setIsFollowModeEnabled(false);
    }
    scrollTop.current = e.scrollTop;
    scrollHeight.current = e.scrollHeight;
  };

  const renderSearchComponent = () => (
    <Search
      qsConfig={QS_CONFIG}
      columns={[
        {
          name: t`Stdout`,
          key: 'stdout__icontains',
          isDefault: true,
        },
        {
          name: t`Event`,
          key: 'event',
          options: [
            ['runner_on_failed', t`Host Failed`],
            ['runner_on_start', t`Host Started`],
            ['runner_on_ok', t`Host OK`],
            ['runner_on_error', t`Host Failure`],
            ['runner_on_skipped', t`Host Skipped`],
            ['runner_on_unreachable', t`Host Unreachable`],
            ['runner_on_no_hosts', t`No Hosts Remaining`],
            ['runner_on_async_poll', t`Host Polling`],
            ['runner_on_async_ok', t`Host Async OK`],
            ['runner_on_async_failed', t`Host Async Failure`],
            ['runner_item_on_ok', t`Item OK`],
            ['runner_item_on_failed', t`Item Failed`],
            ['runner_item_on_skipped', t`Item Skipped`],
            ['runner_retry', t`Host Retry`],
            ['runner_on_file_diff', t`File Difference`],
            ['playbook_on_start', t`Playbook Started`],
            ['playbook_on_notify', t`Running Handlers`],
            ['playbook_on_include', t`Including File`],
            ['playbook_on_no_hosts_matched', t`No Hosts Matched`],
            ['playbook_on_no_hosts_remaining', t`No Hosts Remaining`],
            ['playbook_on_task_start', t`Task Started`],
            ['playbook_on_vars_prompt', t`Variables Prompted`],
            ['playbook_on_setup', t`Gathering Facts`],
            ['playbook_on_play_start', t`Play Started`],
            ['playbook_on_stats', t`Playbook Complete`],
            ['debug', t`Debug`],
            ['verbose', t`Verbose`],
            ['deprecated', t`Deprecated`],
            ['warning', t`Warning`],
            ['system_warning', t`System Warning`],
            ['error', t`Error`],
          ],
        },
        { name: t`Advanced`, key: 'advanced' },
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

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  return (
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
        <SearchToolbar
          id="job_output-toolbar"
          clearAllFilters={handleRemoveAllSearchTerms}
          collapseListedFiltersBreakpoint="lg"
          clearFiltersButtonText={t`Clear all filters`}
        >
          <SearchToolbarContent>
            <ToolbarToggleGroup toggleIcon={<SearchIcon />} breakpoint="lg">
              <ToolbarItem variant="search-filter">
                {isJobRunning(job.status) ? (
                  <Tooltip
                    content={t`Search is disabled while the job is running`}
                  >
                    {renderSearchComponent()}
                  </Tooltip>
                ) : (
                  renderSearchComponent()
                )}
              </ToolbarItem>
            </ToolbarToggleGroup>
            {isJobRunning(job.status) ? (
              <Button
                variant={isFollowModeEnabled ? 'secondary' : 'primary'}
                onClick={handleFollowToggle}
              >
                {isFollowModeEnabled ? t`Unfollow` : t`Follow`}
              </Button>
            ) : null}
          </SearchToolbarContent>
        </SearchToolbar>
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
                {({ width, height }) => (
                  <>
                    {hasContentLoading ? (
                      <div style={{ width }}>
                        <ContentLoading />
                      </div>
                    ) : (
                      <List
                        ref={(ref) => {
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
                        onScroll={handleScroll}
                      />
                    )}
                  </>
                )}
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
          title={t`Cancel Job`}
          label={t`Cancel Job`}
          actions={[
            <Button
              id="cancel-job-confirm-button"
              key="delete"
              variant="danger"
              isDisabled={isCancelling}
              aria-label={t`Cancel job`}
              onClick={cancelJob}
            >
              {t`Cancel job`}
            </Button>,
            <Button
              id="cancel-job-return-button"
              key="cancel"
              variant="secondary"
              aria-label={t`Return`}
              onClick={() => setShowCancelModal(false)}
            >
              {t`Return`}
            </Button>,
          ]}
        >
          {t`Are you sure you want to submit the request to cancel this job?`}
        </AlertModal>
      )}
      {dismissableDeleteError && (
        <AlertModal
          isOpen={dismissableDeleteError}
          variant="danger"
          onClose={dismissDeleteError}
          title={t`Job Delete Error`}
          label={t`Job Delete Error`}
        >
          <ErrorDetail error={dismissableDeleteError} />
        </AlertModal>
      )}
      {dismissableCancelError && (
        <AlertModal
          isOpen={dismissableCancelError}
          variant="danger"
          onClose={dismissCancelError}
          title={t`Job Cancel Error`}
          label={t`Job Cancel Error`}
        >
          <ErrorDetail error={dismissableCancelError} />
        </AlertModal>
      )}
    </>
  );
}

export { JobOutput as _JobOutput };
export default JobOutput;
