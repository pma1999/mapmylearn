import { useState } from 'react';

/**
 * Custom hook for managing history filtering, sorting and search
 * @returns {Object} Filter state and functions
 */
const useHistoryFilters = () => {
  // Filter states
  const [sortBy, setSortBy] = useState('creation_date');
  const [filterSource, setFilterSource] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  /**
   * Handle sort option change
   * @param {string} option - Sort option value
   */
  const handleSortChange = (option) => {
    setSortBy(option);
  };

  /**
   * Handle source filter change
   * @param {string|null} source - Source filter value
   */
  const handleFilterChange = (source) => {
    setFilterSource(source);
  };

  /**
   * Handle search term change
   * @param {string} term - Search term
   */
  const handleSearchChange = (term) => {
    setSearchTerm(term);
  };

  /**
   * Clear all applied filters
   */
  const clearFilters = () => {
    setSortBy('creation_date');
    setFilterSource(null);
    setSearchTerm('');
  };

  return {
    // Filter states
    sortBy,
    filterSource,
    searchTerm,
    
    // Filter handlers
    handleSortChange,
    handleFilterChange,
    handleSearchChange,
    clearFilters
  };
};

export default useHistoryFilters; 