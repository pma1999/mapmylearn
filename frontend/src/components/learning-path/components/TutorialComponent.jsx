import React, { Suspense, lazy } from 'react';
import PropTypes from 'prop-types';
const Joyride = lazy(() => import('react-joyride'));

/**
 * Tutorial component wrapper for Joyride
 */
const TutorialComponent = ({
  steps,
  run,
  stepIndex,
  callback,
  theme,
  ...joyrideProps
}) => {
  const defaultStyles = {
    options: {
      arrowColor: theme.palette.background.paper,
      backgroundColor: theme.palette.background.paper,
      overlayColor: 'rgba(0, 0, 0, 0.6)',
      primaryColor: theme.palette.primary.main,
      textColor: theme.palette.text.primary,
      zIndex: theme.zIndex.tooltip + 1,
    },
    buttonNext: {
      backgroundColor: theme.palette.primary.main,
      borderRadius: theme.shape.borderRadius,
    },
    buttonBack: {
      color: theme.palette.primary.main,
    },
    buttonSkip: {
      color: theme.palette.text.secondary,
    },
    tooltip: {
      borderRadius: theme.shape.borderRadius,
    },
    tooltipContent: {
      padding: theme.spacing(2),
    },
  };

  return (
    <Suspense fallback={null}>
      <Joyride
        steps={steps}
        run={run}
        stepIndex={stepIndex}
        callback={callback}
        continuous={true}
        showProgress={true}
        showSkipButton={true}
        scrollToFirstStep={true}
        styles={defaultStyles}
        {...joyrideProps}
      />
    </Suspense>
  );
};

TutorialComponent.propTypes = {
  steps: PropTypes.array.isRequired,
  run: PropTypes.bool.isRequired,
  stepIndex: PropTypes.number.isRequired,
  callback: PropTypes.func.isRequired,
  theme: PropTypes.object.isRequired
};

export default TutorialComponent;
