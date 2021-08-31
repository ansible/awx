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
import { Button } from '@patternfly/react-core';

import AlertModal from 'components/AlertModal';
import { CardBody as _CardBody } from 'components/Card';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import ErrorDetail from 'components/ErrorDetail';
import StatusIcon from 'components/StatusIcon';

import { getJobModel, isJobRunning } from 'util/jobs';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import useInterval from 'hooks/useInterval';
import { parseQueryString, getQSConfig } from 'util/qs';
import useIsMounted from 'hooks/useIsMounted';
import JobEvent from './JobEvent';
import JobEventSkeleton from './JobEventSkeleton';
import PageControls from './PageControls';
import HostEventModal from './HostEventModal';
import JobOutputSearch from './JobOutputSearch';
import { HostStatusBar, OutputToolbar } from './shared';
import getLineTextHtml from './getLineTextHtml';
import connectJobSocket, { closeWebSocket } from './connectJobSocket';
import getEventRequestParams from './getEventRequestParams';
import isHostEvent from './isHostEvent';
import { fetchCount, normalizeEvents } from './loadJobEvents';

const QS_CONFIG = getQSConfig('job_output', {
  order_by: 'counter',
});

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

const cache = new CellMeasurerCache({
  fixedWidth: true,
  defaultHeight: 25,
});

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
      closeWebSocket();
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

    try {
      const [
        {
          data: { results: fetchedEvents = [] },
        },
        count,
      ] = await Promise.all([eventPromise, fetchCount(job, eventPromise)]);

      if (!isMounted.current) {
        return;
      }
      const { events, countOffset } = normalizeEvents(job, fetchedEvents);

      const newResults = {};
      let newResultsCssMap = {};
      events.forEach((jobEvent, index) => {
        newResults[index] = jobEvent;
        const { lineCssMap } = getLineTextHtml(jobEvent);
        newResultsCssMap = { ...newResultsCssMap, ...lineCssMap };
      });
      setResults(newResults);
      setRemoteRowCount(count + countOffset);
      setCssMap(newResultsCssMap);
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
        if (!isMounted.current) {
          return;
        }

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
        <JobOutputSearch
          qsConfig={QS_CONFIG}
          job={job}
          eventRelatedSearchableKeys={eventRelatedSearchableKeys}
          eventSearchableKeys={eventSearchableKeys}
          remoteRowCount={remoteRowCount}
          scrollToRow={scrollToRow}
          isFollowModeEnabled={isFollowModeEnabled}
          setIsFollowModeEnabled={setIsFollowModeEnabled}
        />
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

export default JobOutput;
