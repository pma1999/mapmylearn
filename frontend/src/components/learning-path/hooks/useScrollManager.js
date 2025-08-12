import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Advanced scroll management hook for table of contents functionality
 * Provides smooth scrolling, active section detection, and scroll state management
 */
const useScrollManager = (options = {}) => {
  const {
    scrollOffset = 80,
    scrollBehavior = 'smooth',
    scrollDuration = 800,
    debounceDelay = 100,
    activeDetectionOffset = 100
  } = options;

  // State
  const [isScrolling, setIsScrolling] = useState(false);
  const [scrollDirection, setScrollDirection] = useState('down');
  const [lastScrollTop, setLastScrollTop] = useState(0);

  // Refs
  const scrollTimeoutRef = useRef(null);
  const debounceTimeoutRef = useRef(null);
  const isManualScrollRef = useRef(false);

  /**
   * Scrolls smoothly to a specific element by ID
   * @param {string} elementId - The ID of the target element
   * @param {Object} customOptions - Override default scroll options
   * @returns {Promise} - Resolves when scroll is complete
   */
  const scrollToElement = useCallback((elementId, customOptions = {}) => {
    return new Promise((resolve, reject) => {
      if (!elementId) {
        reject(new Error('Element ID is required'));
        return;
      }

      const element = document.getElementById(elementId);
      if (!element) {
        console.warn(`Element with ID "${elementId}" not found`);
        reject(new Error(`Element with ID "${elementId}" not found`));
        return;
      }

      // Mark as manual scroll to prevent active detection interference
      isManualScrollRef.current = true;
      setIsScrolling(true);

      const {
        offset = scrollOffset,
        behavior = scrollBehavior,
        duration = scrollDuration
      } = customOptions;

      try {
        // Calculate target position
        const elementRect = element.getBoundingClientRect();
        const currentScrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const targetPosition = currentScrollTop + elementRect.top - offset;

        // Use native smooth scrolling if supported and behavior is 'smooth'
        if (behavior === 'smooth' && 'scrollBehavior' in document.documentElement.style) {
          window.scrollTo({
            top: Math.max(0, targetPosition),
            behavior: 'smooth'
          });

          // Estimate completion time for native smooth scroll
          const scrollDistance = Math.abs(targetPosition - currentScrollTop);
          const estimatedDuration = Math.min(Math.max(scrollDistance / 3, 300), duration);

          scrollTimeoutRef.current = setTimeout(() => {
            setIsScrolling(false);
            isManualScrollRef.current = false;
            resolve();
          }, estimatedDuration);
        } else {
          // Fallback to manual animation for browsers without smooth scroll
          const startTime = performance.now();
          const startPosition = currentScrollTop;
          const distance = targetPosition - startPosition;

          const animateScroll = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function (ease-out-cubic)
            const easeOutCubic = 1 - Math.pow(1 - progress, 3);
            const currentPosition = startPosition + (distance * easeOutCubic);

            window.scrollTo(0, Math.max(0, currentPosition));

            if (progress < 1) {
              requestAnimationFrame(animateScroll);
            } else {
              setIsScrolling(false);
              isManualScrollRef.current = false;
              resolve();
            }
          };

          requestAnimationFrame(animateScroll);
        }
      } catch (error) {
        console.error('Error during scroll animation:', error);
        setIsScrolling(false);
        isManualScrollRef.current = false;
        reject(error);
      }
    });
  }, [scrollOffset, scrollBehavior, scrollDuration]);

  /**
   * Finds the currently active element based on scroll position
   * @param {Array} elementIds - Array of element IDs to check
   * @returns {string|null} - ID of the active element
   */
  const findActiveElement = useCallback((elementIds) => {
    if (!elementIds || elementIds.length === 0) return null;

    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const windowHeight = window.innerHeight;
    const documentHeight = document.documentElement.scrollHeight;

    // If near bottom of page, return last element
    if (scrollTop + windowHeight >= documentHeight - 50) {
      return elementIds[elementIds.length - 1];
    }

    let activeElement = null;
    let smallestDistance = Infinity;

    elementIds.forEach(elementId => {
      const element = document.getElementById(elementId);
      if (!element) return;

      const rect = element.getBoundingClientRect();
      const elementTop = rect.top + scrollTop;
      const distance = Math.abs(elementTop - (scrollTop + activeDetectionOffset));

      // Element is visible and closer than previous candidates
      if (rect.top <= activeDetectionOffset && distance < smallestDistance) {
        smallestDistance = distance;
        activeElement = elementId;
      }
    });

    // If no element is in the active zone, return the first one that's below viewport
    if (!activeElement) {
      for (const elementId of elementIds) {
        const element = document.getElementById(elementId);
        if (!element) continue;

        const rect = element.getBoundingClientRect();
        if (rect.top > activeDetectionOffset) {
          // Return previous element or first element
          const currentIndex = elementIds.indexOf(elementId);
          return currentIndex > 0 ? elementIds[currentIndex - 1] : elementIds[0];
        }
      }
      // If all elements are above viewport, return last one
      return elementIds[elementIds.length - 1];
    }

    return activeElement;
  }, [activeDetectionOffset]);

  /**
   * Handles scroll events with debouncing and direction detection
   */
  const handleScroll = useCallback(() => {
    // Skip if currently doing manual scroll
    if (isManualScrollRef.current) return;

    const currentScrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    // Detect scroll direction
    if (currentScrollTop > lastScrollTop) {
      setScrollDirection('down');
    } else if (currentScrollTop < lastScrollTop) {
      setScrollDirection('up');
    }
    
    setLastScrollTop(currentScrollTop);

    // Clear existing debounce timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    // Set debounced callback
    debounceTimeoutRef.current = setTimeout(() => {
      // Scroll has stopped, can now detect active element
      setIsScrolling(false);
    }, debounceDelay);
  }, [lastScrollTop, debounceDelay]);

  /**
   * Scroll to the top of the content area
   */
  const scrollToTop = useCallback(() => {
    return scrollToElement('top', { offset: 0 }).catch(() => {
      // Fallback if no element with ID 'top' exists
      window.scrollTo({ top: 0, behavior: scrollBehavior });
      return Promise.resolve();
    });
  }, [scrollToElement, scrollBehavior]);

  /**
   * Scroll to the bottom of the content area
   */
  const scrollToBottom = useCallback(() => {
    const documentHeight = document.documentElement.scrollHeight;
    const windowHeight = window.innerHeight;
    
    window.scrollTo({
      top: documentHeight - windowHeight,
      behavior: scrollBehavior
    });
  }, [scrollBehavior]);

  /**
   * Check if an element is currently visible in viewport
   */
  const isElementVisible = useCallback((elementId, threshold = 0.1) => {
    const element = document.getElementById(elementId);
    if (!element) return false;

    const rect = element.getBoundingClientRect();
    const windowHeight = window.innerHeight;
    
    const visibleHeight = Math.min(rect.bottom, windowHeight) - Math.max(rect.top, 0);
    const elementHeight = rect.height;
    
    return visibleHeight > 0 && (visibleHeight / elementHeight) >= threshold;
  }, []);

  // Set up scroll event listener
  useEffect(() => {
    let rafId;
    
    const throttledScrollHandler = () => {
      rafId = requestAnimationFrame(handleScroll);
    };

    window.addEventListener('scroll', throttledScrollHandler, { passive: true });

    return () => {
      window.removeEventListener('scroll', throttledScrollHandler);
      if (rafId) {
        cancelAnimationFrame(rafId);
      }
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, [handleScroll]);

  return {
    // Core scroll functions
    scrollToElement,
    scrollToTop,
    scrollToBottom,
    
    // Active element detection
    findActiveElement,
    isElementVisible,
    
    // Scroll state
    isScrolling,
    scrollDirection,
    lastScrollTop,
    
    // Utility functions
    setIsScrolling,
    
    // Configuration
    scrollOffset,
    activeDetectionOffset
  };
};

export default useScrollManager;
