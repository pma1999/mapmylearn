import { useState, useEffect, useMemo, useCallback } from 'react';
import { parseMarkdownHeaders, hasMarkdownHeaders } from '../utils/markdownParser';

/**
 * Custom hook for managing markdown table of contents functionality
 * Extracts headers from markdown content and provides navigation state management
 * 
 * @param {string} markdownContent - Raw markdown content to parse
 * @param {Object} options - Configuration options
 * @returns {Object} TOC state and handlers
 */
const useMarkdownTOC = (markdownContent, options = {}) => {
  const {
    enableActiveDetection = true, // Enable automatic active header detection
    scrollOffset = 80, // Offset for scroll-to-section to account for fixed headers
    debounceDelay = 100 // Debounce delay for scroll event handling
  } = options;

  // Core state
  const [activeHeaderId, setActiveHeaderId] = useState(null);
  const [isScrolling, setIsScrolling] = useState(false);
  const [tocVisible, setTocVisible] = useState(false);

  // Parse headers from markdown content and create ID mapping
  const { headers, headerIdMap } = useMemo(() => {
    if (!markdownContent) return { headers: [], headerIdMap: new Map() };
    
    const parsedHeaders = parseMarkdownHeaders(markdownContent);
    const idMap = new Map();
    
    // Create mapping of header text to ID for MarkdownRenderer
    parsedHeaders.forEach(header => {
      idMap.set(header.title, header.id);
    });
    
    return { headers: parsedHeaders, headerIdMap: idMap };
  }, [markdownContent]);

  // Check if content has headers
  const hasHeaders = useMemo(() => {
    return hasMarkdownHeaders(markdownContent);
  }, [markdownContent]);

  // Set initial active header when headers change
  useEffect(() => {
    if (headers.length > 0 && !activeHeaderId) {
      setActiveHeaderId(headers[0].id);
    }
  }, [headers, activeHeaderId]);

  // Scroll to specific header section
  const scrollToHeader = useCallback((headerId) => {
    if (!headerId) return;

    // Add debug info
    console.log(`Attempting to scroll to header with ID: "${headerId}"`);
    console.log('Available elements with IDs starting with "heading":', 
      Array.from(document.querySelectorAll('[id^="heading"]')).map(el => el.id));

    const element = document.getElementById(headerId);
    if (!element) {
      console.warn(`Header element with ID "${headerId}" not found`);
      return;
    }

    setIsScrolling(true);
    setActiveHeaderId(headerId);

    // Smooth scroll to element with offset
    const elementPosition = element.getBoundingClientRect().top + window.pageYOffset;
    const offsetPosition = elementPosition - scrollOffset;

    window.scrollTo({
      top: Math.max(0, offsetPosition),
      behavior: 'smooth'
    });

    // Reset scrolling state after animation completes
    setTimeout(() => {
      setIsScrolling(false);
    }, 1000); // Smooth scroll typically takes ~700ms, add buffer
  }, [scrollOffset]);

  // Navigate to next header
  const goToNextHeader = useCallback(() => {
    if (!activeHeaderId || headers.length === 0) return;

    const currentIndex = headers.findIndex(h => h.id === activeHeaderId);
    if (currentIndex !== -1 && currentIndex < headers.length - 1) {
      const nextHeader = headers[currentIndex + 1];
      scrollToHeader(nextHeader.id);
    }
  }, [activeHeaderId, headers, scrollToHeader]);

  // Navigate to previous header
  const goToPreviousHeader = useCallback(() => {
    if (!activeHeaderId || headers.length === 0) return;

    const currentIndex = headers.findIndex(h => h.id === activeHeaderId);
    if (currentIndex > 0) {
      const prevHeader = headers[currentIndex - 1];
      scrollToHeader(prevHeader.id);
    }
  }, [activeHeaderId, headers, scrollToHeader]);

  // Get header by ID
  const getHeaderById = useCallback((headerId) => {
    return headers.find(h => h.id === headerId);
  }, [headers]);

  // Get current header index
  const getCurrentHeaderIndex = useCallback(() => {
    if (!activeHeaderId) return -1;
    return headers.findIndex(h => h.id === activeHeaderId);
  }, [activeHeaderId, headers]);

  // Check if there's a next header
  const hasNextHeader = useMemo(() => {
    const currentIndex = getCurrentHeaderIndex();
    return currentIndex !== -1 && currentIndex < headers.length - 1;
  }, [getCurrentHeaderIndex, headers.length]);

  // Check if there's a previous header
  const hasPreviousHeader = useMemo(() => {
    const currentIndex = getCurrentHeaderIndex();
    return currentIndex > 0;
  }, [getCurrentHeaderIndex]);

  // Auto-detect active header based on scroll position (intersection observer)
  useEffect(() => {
    if (!enableActiveDetection || headers.length === 0 || isScrolling) {
      return;
    }

    const observerOptions = {
      rootMargin: `-${scrollOffset}px 0px -50% 0px`,
      threshold: 0
    };

    const intersectionObserver = new IntersectionObserver((entries) => {
      // Find the first intersecting header
      const intersectingEntry = entries.find(entry => entry.isIntersecting);
      
      if (intersectingEntry) {
        const headerId = intersectingEntry.target.id;
        if (headerId && headerId !== activeHeaderId) {
          setActiveHeaderId(headerId);
        }
      }
    }, observerOptions);

    // Observe all header elements
    headers.forEach(header => {
      const element = document.getElementById(header.id);
      if (element) {
        intersectionObserver.observe(element);
      }
    });

    return () => {
      intersectionObserver.disconnect();
    };
  }, [headers, enableActiveDetection, scrollOffset, activeHeaderId, isScrolling]);

  // Toggle TOC visibility (for mobile)
  const toggleTocVisibility = useCallback(() => {
    setTocVisible(prev => !prev);
  }, []);

  // Hide TOC (for mobile)
  const hideToc = useCallback(() => {
    setTocVisible(false);
  }, []);

  // Show TOC (for mobile)
  const showToc = useCallback(() => {
    setTocVisible(true);
  }, []);

  // Reset TOC state
  const resetToc = useCallback(() => {
    setActiveHeaderId(headers.length > 0 ? headers[0].id : null);
    setIsScrolling(false);
    setTocVisible(false);
  }, [headers]);

  return {
    // Core data
    headers,
    hasHeaders,
    activeHeaderId,
    headerIdMap, // Map of header text to ID for MarkdownRenderer
    
    // State
    isScrolling,
    tocVisible,
    
    // Navigation methods
    scrollToHeader,
    goToNextHeader,
    goToPreviousHeader,
    
    // Utility methods
    getHeaderById,
    getCurrentHeaderIndex,
    
    // State queries
    hasNextHeader,
    hasPreviousHeader,
    
    // Visibility controls
    toggleTocVisibility,
    hideToc,
    showToc,
    
    // Reset
    resetToc,
    
    // Manual state setters (for advanced use cases)
    setActiveHeaderId,
    setTocVisible
  };
};

export default useMarkdownTOC;
