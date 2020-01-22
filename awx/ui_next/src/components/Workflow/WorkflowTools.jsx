import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { func, number } from 'prop-types';
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
  TimesIcon,
} from '@patternfly/react-icons';

const Wrapper = styled.div`
  background-color: white;
  border: 1px solid #c7c7c7;
  height: 135px;
  position: relative;
`;

const Header = styled.div`
  border-bottom: 1px solid #c7c7c7;
  padding: 10px;
`;

const Pan = styled.div`
  align-items: center;
  display: flex;
`;

const PanCenter = styled.div`
  display: flex;
  flex-direction: column;
`;

const Tools = styled.div`
  align-items: center;
  display: flex;
  padding: 20px;
`;

const Close = styled(TimesIcon)`
  cursor: pointer;
  position: absolute;
  right: 10px;
  top: 15px;
`;

function WorkflowTools({
  i18n,
  onClose,
  onFitGraph,
  onPan,
  onPanToMiddle,
  onZoomChange,
  zoomPercentage,
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
        <Close onClick={onClose} />
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
          id="zoom-slider"
          max="200"
          min="10"
          onChange={event =>
            onZoomChange(parseInt(event.target.value, 10) / 100)
          }
          step="10"
          type="range"
          value={zoomPercentage}
        />
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

WorkflowTools.propTypes = {
  onClose: func.isRequired,
  onFitGraph: func.isRequired,
  onPan: func.isRequired,
  onPanToMiddle: func.isRequired,
  onZoomChange: func.isRequired,
  zoomPercentage: number.isRequired,
};

export default withI18n()(WorkflowTools);
