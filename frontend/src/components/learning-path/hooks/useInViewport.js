import { useEffect, useState } from 'react';

/**
 * useInViewport - observes if a target element is visible within an optional scroll root.
 *
 * @param {React.RefObject<Element>} targetRef - The element to observe.
 * @param {Object} options
 * @param {Element|null} [options.root=null] - The scroll container to use as root. Defaults to viewport if null.
 * @param {string} [options.rootMargin='0px'] - Margin around the root.
 * @param {number|number[]} [options.threshold=0] - Intersection threshold(s).
 * @returns {boolean} inView - Whether the element is currently in view within the root.
 */
export default function useInViewport(targetRef, options = {}) {
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const element = targetRef && 'current' in targetRef ? targetRef.current : null;

    // If no element yet, assume not in view and wait for next render
    if (!element) {
      setInView(false);
      return;
    }

    // SSR or unsupported environment fallback
    if (typeof window === 'undefined' || typeof IntersectionObserver === 'undefined') {
      setInView(true);
      return;
    }

    const { root = null, rootMargin = '0px', threshold = 0 } = options;

    let cancelled = false;
    const observer = new IntersectionObserver(
      (entries) => {
        if (cancelled) return;
        const entry = entries[0];
        if (entry) {
          // Consider visible if intersecting with a positive ratio
          setInView(entry.isIntersecting && entry.intersectionRatio > 0);
        }
      },
      { root, rootMargin, threshold }
    );

    observer.observe(element);

    return () => {
      cancelled = true;
      try {
        observer.unobserve(element);
      } catch (e) {
        // no-op
      }
      observer.disconnect();
    };
    // Re-run when the element or observing parameters change
  }, [targetRef, options]);

  return inView;
}
