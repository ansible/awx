import 'styled-components/macro';
import React, { useContext } from 'react';
import { withI18n } from '@lingui/react';
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
import { WorkflowDispatchContext } from '../../contexts/Workflow';

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
  i18n,
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
        <b>{i18n._(t`Tools`)}</b>
        <Close onClick={() => dispatch({ type: 'TOGGLE_TOOLS' })} />
      </Header>
      <Tools>
        <Tooltip
          content={i18n._(t`Fit the graph to the available screen size`)}
          position="bottom"
        >
          <Button
            variant="tertiary"
            css="margin-right: 30px;"
            onClick={() => onFitGraph()}
          >
            <DesktopIcon />
          </Button>
        </Tooltip>
        <Tooltip content={i18n._(t`Zoom Out`)} position="bottom">
          <Button
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
          onChange={event =>
            onZoomChange(parseInt(event.target.value, 10) / 100)
          }
          step="10"
          type="range"
          value={zoomPercentage}
        />
        <Tooltip content={i18n._(t`Zoom In`)} position="bottom">
          <Button
            variant="tertiary"
            css="margin: 0px 25px 0px 10px;"
            onClick={() => zoomIn()}
          >
            <PlusIcon />
          </Button>
        </Tooltip>
        <Pan>
          <Tooltip content={i18n._(t`Pan Left`)} position="left">
            <Button
              variant="tertiary"
              css="margin-right: 10px;"
              onClick={() => onPan('left')}
            >
              <CaretLeftIcon />
            </Button>
          </Tooltip>
          <PanCenter>
            <Tooltip content={i18n._(t`Pan Up`)} position="top">
              <Button
                variant="tertiary"
                css="margin-bottom: 10px;"
                onClick={() => onPan('up')}
              >
                <CaretUpIcon />
              </Button>
            </Tooltip>
            <Tooltip
              content={i18n._(t`Set zoom to 100% and center graph`)}
              position="top"
            >
              <Button variant="tertiary" onClick={() => onPanToMiddle()}>
                <HomeIcon />
              </Button>
            </Tooltip>
            <Tooltip content={i18n._(t`Pan Down`)} position="bottom">
              <Button
                variant="tertiary"
                css="margin-top: 10px;"
                onClick={() => onPan('down')}
              >
                <CaretDownIcon />
              </Button>
            </Tooltip>
          </PanCenter>
          <Tooltip content={i18n._(t`Pan Right`)} position="right">
            <Button
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

export default withI18n()(WorkflowTools);
