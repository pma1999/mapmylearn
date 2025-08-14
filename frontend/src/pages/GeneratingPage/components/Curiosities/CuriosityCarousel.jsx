import React from 'react';
import PropTypes from 'prop-types';
import { Box, IconButton, Tooltip, useMediaQuery } from '@mui/material';
import { useTheme, styled } from '@mui/material/styles';
import { motion, AnimatePresence } from 'framer-motion';
import PauseIcon from '@mui/icons-material/Pause';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import CircleIcon from '@mui/icons-material/Circle';
import CuriosityCard from './CuriosityCard';
import CuriositySkeleton from './CuriositySkeleton';
import EngagementContent from './EngagementContent';

const CarouselContainer = styled(Box)(({ theme }) => ({
  position: 'relative',
  width: '100%',
  maxWidth: 720,
  margin: '0 auto',
}));

const ControlsRow = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: theme.spacing(0.5),
  marginTop: theme.spacing(1),
}));

const DotButton = styled(IconButton)(({ theme, active }) => ({
  width: 10,
  height: 10,
  padding: 0,
  opacity: active ? 1 : 0.4,
}));

const variants = {
  enter: (direction) => ({ x: direction > 0 ? 40 : -40, opacity: 0 }),
  center: { x: 0, opacity: 1 },
  exit: (direction) => ({ x: direction < 0 ? 40 : -40, opacity: 0 }),
};

const clampIndex = (index, length) => {
  if (length === 0) return 0;
  return ((index % length) + length) % length;
};

const prefersReducedMotion = () => {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

const CuriosityCarousel = ({
  items = [],
  autoplay = true,
  intervalMs = 7000,
  pauseOnHover = true,
  pauseOnFocus = true,
  initialIndex = 0,
  onIndexChange,
  onInteract,
  onCopy,
  ariaLabel = 'Engagement content carousel',
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const reduced = prefersReducedMotion();

  const [index, setIndex] = React.useState(0);
  const [direction, setDirection] = React.useState(0);
  const [paused, setPaused] = React.useState(false);
  const [visible, setVisible] = React.useState(true);
  const timerRef = React.useRef(null);
  const interactTimeoutRef = React.useRef(null);

  React.useEffect(() => {
    setIndex(clampIndex(initialIndex, items.length));
  }, [initialIndex, items.length]);

  React.useEffect(() => {
    const onVisibility = () => setVisible(document.visibilityState === 'visible');
    document.addEventListener('visibilitychange', onVisibility);
    return () => document.removeEventListener('visibilitychange', onVisibility);
  }, []);

  const clearTimer = () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  const scheduleNext = React.useCallback(() => {
    clearTimer();
    if (!autoplay || paused || !visible || reduced || items.length <= 1) return;
    timerRef.current = setTimeout(() => {
      navigate(1, true);
    }, intervalMs);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoplay, paused, visible, reduced, items.length, intervalMs]);

  React.useEffect(() => {
    scheduleNext();
    return clearTimer;
  }, [index, scheduleNext]);

  const markInteracted = () => {
    if (onInteract) onInteract({ type: 'interact', index });
    setPaused(true);
    if (interactTimeoutRef.current) clearTimeout(interactTimeoutRef.current);
    interactTimeoutRef.current = setTimeout(() => setPaused(false), 15000);
  };

  const navigate = (delta, auto = false) => {
    const newIndex = clampIndex(index + delta, items.length);
    setDirection(delta);
    setIndex(newIndex);
    if (onIndexChange) onIndexChange(newIndex);
    if (!auto) markInteracted();
  };

  const handleKeyDown = (e) => {
    if (!items.length) return;
    if (e.key === 'ArrowRight') { e.preventDefault(); navigate(1); }
    if (e.key === 'ArrowLeft')  { e.preventDefault(); navigate(-1); }
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      setPaused((p) => !p);
      if (onInteract) onInteract({ type: 'pause_toggle', index });
    }
  };

  const handleHover = (isHovering) => {
    if (!pauseOnHover) return;
    setPaused(isHovering);
  };

  const handleFocus = (isFocus) => {
    if (!pauseOnFocus) return;
    setPaused(isFocus);
  };

  if (!items || items.length === 0) {
    return (
      <CarouselContainer aria-label={ariaLabel}>
        <CuriositySkeleton />
      </CarouselContainer>
    );
  }

  const current = items[index] || items[0];

  return (
    <CarouselContainer
      role="region"
      aria-label={ariaLabel}
      aria-live="polite"
      onKeyDown={handleKeyDown}
      tabIndex={0}
      onMouseEnter={() => handleHover(true)}
      onMouseLeave={() => handleHover(false)}
      onFocus={() => handleFocus(true)}
      onBlur={() => handleFocus(false)}
    >
      <Box sx={{ position: 'relative' }}>
        <AnimatePresence initial={false} custom={direction}>
          <motion.div
            key={index}
            custom={direction}
            variants={reduced ? {} : variants}
            initial={reduced ? false : 'enter'}
            animate={reduced ? 'center' : 'center'}
            exit={reduced ? false : 'exit'}
            transition={reduced ? { duration: 0 } : { type: 'spring', stiffness: 300, damping: 30 }}
            drag={isMobile && !reduced ? 'x' : false}
            dragConstraints={{ left: 0, right: 0 }}
            dragElastic={0.2}
            onDragEnd={(e, info) => {
              const velocity = info.velocity.x;
              const offset = info.offset.x;
              if (Math.abs(offset) > 60 || Math.abs(velocity) > 500) {
                if (offset < 0) navigate(1); else navigate(-1);
                if (onInteract) onInteract({ type: 'swipe', index });
              }
            }}
          >
            <EngagementContent 
              item={current} 
              onCopy={onCopy}
              onInteract={(interactionData) => {
                if (onInteract) {
                  onInteract({ 
                    ...interactionData, 
                    index, 
                    contentType: current?.type || 'unknown' 
                  });
                }
              }}
            />
          </motion.div>
        </AnimatePresence>

        {/* Side controls (desktop) */}
        {!isMobile && items.length > 1 && (
          <>
            <Box sx={{ position: 'absolute', top: '50%', left: -8, transform: 'translateY(-50%)' }}>
              <Tooltip title="Previous">
                <IconButton size="small" onClick={() => navigate(-1)} aria-label="Previous curiosity">
                  <ChevronLeftIcon />
                </IconButton>
              </Tooltip>
            </Box>
            <Box sx={{ position: 'absolute', top: '50%', right: -8, transform: 'translateY(-50%)' }}>
              <Tooltip title="Next">
                <IconButton size="small" onClick={() => navigate(1)} aria-label="Next curiosity">
                  <ChevronRightIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </>
        )}
      </Box>

      {/* Bottom controls */}
      <ControlsRow>
        {items.length > 1 && (
          <>
            {items.map((_, i) => (
              <DotButton key={i} active={i === index ? 1 : 0} onClick={() => navigate(i - index)} aria-label={`Go to item ${i + 1}`}>
                <CircleIcon fontSize="inherit" sx={{ fontSize: 8 }} />
              </DotButton>
            ))}
          </>
        )}
        <Box sx={{ width: 8 }} />
        <Tooltip title={paused ? 'Play' : 'Pause'}>
          <IconButton size="small" onClick={() => setPaused((p) => !p)} aria-label={paused ? 'Play auto-rotation' : 'Pause auto-rotation'}>
            {paused ? <PlayArrowIcon /> : <PauseIcon />}
          </IconButton>
        </Tooltip>
      </ControlsRow>
    </CarouselContainer>
  );
};

CuriosityCarousel.propTypes = {
  items: PropTypes.arrayOf(PropTypes.shape({ text: PropTypes.string, category: PropTypes.string })),
  autoplay: PropTypes.bool,
  intervalMs: PropTypes.number,
  pauseOnHover: PropTypes.bool,
  pauseOnFocus: PropTypes.bool,
  initialIndex: PropTypes.number,
  onIndexChange: PropTypes.func,
  onInteract: PropTypes.func,
  onCopy: PropTypes.func,
  ariaLabel: PropTypes.string,
};

export default CuriosityCarousel;
