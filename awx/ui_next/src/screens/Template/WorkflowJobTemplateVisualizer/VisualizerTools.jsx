import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { Tooltip } from '@patternfly/react-core';
import {
  CaretDownIcon,
  CaretLeftIcon,
  CaretRightIcon,
  CaretUpIcon,
  DesktopIcon,
  HomeIcon,
  MinusIcon,
  PlusIcon,
} from '@patternfly/react-icons';

const Wrapper = styled.div`
  border: 1px solid #c7c7c7;
  background-color: white;
  height: 135px;
`;

const Header = styled.div`
  padding: 10px;
  border-bottom: 1px solid #c7c7c7;
`;

const Pan = styled.div`
  display: flex;
  align-items: center;
`;

const PanCenter = styled.div`
  display: flex;
  flex-direction: column;
`;

const Tools = styled.div`
  display: flex;
  align-items: center;
  padding: 20px;
`;

function VisualizerTools({
  i18n,
  zoomPercentage,
  onZoomChange,
  onFitGraph,
  onPan,
  onPanToMiddle,
}) {
  const zoomIn = () => {
    const newScale =
      Math.ceil((zoomPercentage + 10) / 10) * 10 < 200
        ? Math.ceil((zoomPercentage + 10) / 10) * 10
        : 200;
    onZoomChange(newScale / 100);
  };

  const zoomOut = () => {
    const newScale =
      Math.floor((zoomPercentage - 10) / 10) * 10 > 10
        ? Math.floor((zoomPercentage - 10) / 10) * 10
        : 10;
    onZoomChange(newScale / 100);
  };

  return (
    <Wrapper>
      <Header>
        <b>{i18n._(t`Tools`)}</b>
      </Header>
      <Tools>
        <Tooltip
          content={i18n._(t`Fit the graph to the available screen size`)}
          position="bottom"
        >
          <DesktopIcon onClick={() => onFitGraph()} css="margin-right: 30px;" />
        </Tooltip>
        <Tooltip content={i18n._(t`Zoom Out`)} position="bottom">
          <MinusIcon onClick={() => zoomOut()} css="margin-right: 10px;" />
        </Tooltip>
        <input
          type="range"
          id="zoom-slider"
          value={zoomPercentage}
          min="10"
          max="200"
          step="10"
          onChange={event => onZoomChange(parseInt(event.target.value) / 100)}
        ></input>
        <Tooltip content={i18n._(t`Zoom In`)} position="bottom">
          <PlusIcon onClick={() => zoomIn()} css="margin: 0px 25px 0px 10px;" />
        </Tooltip>
        <Pan>
          <Tooltip content={i18n._(t`Pan Left`)} position="left">
            <CaretLeftIcon onClick={() => onPan('left')} />
          </Tooltip>
          <PanCenter>
            <Tooltip content={i18n._(t`Pan Up`)} position="top">
              <CaretUpIcon onClick={() => onPan('up')} />
            </Tooltip>
            <Tooltip
              content={i18n._(t`Set zoom to 100% and center graph`)}
              position="top"
            >
              <HomeIcon onClick={() => onPanToMiddle()} />
            </Tooltip>
            <Tooltip content={i18n._(t`Pan Down`)} position="bottom">
              <CaretDownIcon onClick={() => onPan('down')} />
            </Tooltip>
          </PanCenter>
          <Tooltip content={i18n._(t`Pan Right`)} position="right">
            <CaretRightIcon onClick={() => onPan('right')} />
          </Tooltip>
        </Pan>
      </Tools>
    </Wrapper>
  );
}

export default withI18n()(VisualizerTools);
