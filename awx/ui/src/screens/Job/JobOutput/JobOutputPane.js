import React, { useState, useRef } from 'react';
import styled from 'styled-components';
import { useLocation } from 'react-router-dom';
import {
  AutoSizer,
  CellMeasurer,
  InfiniteLoader,
  List,
} from 'react-virtualized';
import ContentLoading from 'components/ContentLoading';
import { parseQueryString } from 'util/qs';
import { getJobModel } from 'util/jobs';
import useIsMounted from 'hooks/useIsMounted';
import PageControls from './PageControls';
import JobOutputSearch from './JobOutputSearch';
import JobEvent from './JobEvent';
import JobEventSkeleton from './JobEventSkeleton';
import HostEventModal from './HostEventModal';
import getLineTextHtml from './getLineTextHtml';

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

export default function JobOutputPane({
  qsConfig,
  job,
  eventRelatedSearchableKeys,
  eventSearchableKeys,
  results,
  setResults,
  currentlyLoading,
  setCurrentlyLoading,
  hasContentLoading,
  listRef,
  remoteRowCount,
  isFollowModeEnabled,
  setIsFollowModeEnabled,
  cache,
  cssMap,
  setCssMap,
  getEventRequestParams,
}) {
  const previousWidth = useRef(0);
  const scrollTop = useRef(0);
  const scrollHeight = useRef(0);
  const isMounted = useIsMounted();
  const location = useLocation();

  const [hostEvent, setHostEvent] = useState({});
  const [isHostModalOpen, setIsHostModalOpen] = useState(false);

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

  const scrollToRow = (rowIndex) => {
    if (listRef.current) {
      listRef.current.scrollToRow(rowIndex);
    }
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
      ...parseQueryString(qsConfig, location.search),
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

  return (
    <>
      <JobOutputSearch
        qsConfig={qsConfig}
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
        {isHostModalOpen && (
          <HostEventModal
            onClose={() => setIsHostModalOpen(false)}
            isOpen={isHostModalOpen}
            hostEvent={hostEvent}
          />
        )}
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
    </>
  );
}
