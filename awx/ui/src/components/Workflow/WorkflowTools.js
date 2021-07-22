import 'styled-components/macro';
import React, { useContext } from 'react';

import { t } from '@lingui/macro';
import styled from 'styled-components';
import { func, number } from 'prop-types';
import { Button, Tooltip } from '@patternfly/react-core';
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
import { WorkflowDispatchContext } from 'contexts/Workflow';

const Wrapper = styled.div`
  background-color: white;
  border: 1px solid #c7c7c7;
  height: 215px;
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
  onFitGraph,
  onPan,
  onPanToMiddle,
  onZoomChange,
  zoomPercentage,
}) {
  const dispatch = useContext(WorkflowDispatchContext);
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
        <b>{t`Tools`}</b>
        <Close onClick={() => dispatch({ type: 'TOGGLE_TOOLS' })} />
      </Header>
      <Tools>
        <Tooltip
          content={t`Fit the graph to the available screen size`}
          position="bottom"
        >
          <Button
            ouiaId="visualizer-zoom-to-fit-button"
            variant="tertiary"
            css="margin-right: 30px;"
            onClick={() => onFitGraph()}
          >
            <DesktopIcon />
          </Button>
        </Tooltip>
        <Tooltip content={t`Zoom Out`} position="bottom">
          <Button
            ouiaId="visualizer-zoom-out-button"
            variant="tertiary"
            css="margin-right: 10px;"
            onClick={() => zoomOut()}
          >
            <MinusIcon />
          </Button>
        </Tooltip>
        <input
          id="zoom-slider"
          max="200"
          min="10"
          onChange={(event) =>
            onZoomChange(parseInt(event.target.value, 10) / 100)
          }
          step="10"
          type="range"
          value={zoomPercentage}
        />
        <Tooltip content={t`Zoom In`} position="bottom">
          <Button
            ouiaId="visualizer-zoom-in-button"
            variant="tertiary"
            css="margin: 0px 25px 0px 10px;"
            onClick={() => zoomIn()}
          >
            <PlusIcon />
          </Button>
        </Tooltip>
        <Pan>
          <Tooltip content={t`Pan Left`} position="left">
            <Button
              ouiaId="visualizer-pan-left-button"
              variant="tertiary"
              css="margin-right: 10px;"
              onClick={() => onPan('left')}
            >
              <CaretLeftIcon />
            </Button>
          </Tooltip>
          <PanCenter>
            <Tooltip content={t`Pan Up`} position="top">
              <Button
                ouiaId="visualizer-pan-up-button"
                variant="tertiary"
                css="margin-bottom: 10px;"
                onClick={() => onPan('up')}
              >
                <CaretUpIcon />
              </Button>
            </Tooltip>
            <Tooltip
              content={t`Set zoom to 100% and center graph`}
              position="top"
            >
              <Button
                ouiaId="visualizer-pan-middle-button"
                variant="tertiary"
                onClick={() => onPanToMiddle()}
              >
                <HomeIcon />
              </Button>
            </Tooltip>
            <Tooltip content={t`Pan Down`} position="bottom">
              <Button
                ouiaId="visualizer-pan-down-button"
                variant="tertiary"
                css="margin-top: 10px;"
                onClick={() => onPan('down')}
              >
                <CaretDownIcon />
              </Button>
            </Tooltip>
          </PanCenter>
          <Tooltip content={t`Pan Right`} position="right">
            <Button
              ouiaId="visualizer-pan-right-button"
              variant="tertiary"
              css="margin-left: 10px;"
              onClick={() => onPan('right')}
            >
              <CaretRightIcon />
            </Button>
          </Tooltip>
        </Pan>
      </Tools>
    </Wrapper>
  );
}

WorkflowTools.propTypes = {
  onFitGraph: func.isRequired,
  onPan: func.isRequired,
  onPanToMiddle: func.isRequired,
  onZoomChange: func.isRequired,
  zoomPercentage: number.isRequired,
};

export default WorkflowTools;
