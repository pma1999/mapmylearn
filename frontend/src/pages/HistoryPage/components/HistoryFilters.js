import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import {
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  InputAdornment,
  Box,
  Button,
  Chip
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import FilterListOffIcon from '@mui/icons-material/FilterListOff';
import useDebounce from '../../../hooks/useDebounce';

/**
 * Component for filtering and sorting history entries
 * @param {Object} props - Component props
 * @param {string} props.sortBy - Current sort option
 * @param {Function} props.onSortChange - Handler for sort option change
 * @param {string|null} props.filterSource - Current source filter
 * @param {Function} props.onFilterChange - Handler for source filter change
 * @param {string} props.search - Current search term
 * @param {Function} props.onSearchChange - Handler for search term change
 * @param {Function} props.clearFilters - Handler for clearing filters
 * @param {boolean} props.hasFilters - Whether any filters are applied
 * @param {boolean} props.isLoading - Whether the component is loading
 * @returns {JSX.Element} History filters component
 */
const HistoryFilters = ({ 
  sortBy, 
  onSortChange, 
  filterSource, 
  onFilterChange, 
  search, 
  onSearchChange,
  clearFilters,
  hasFilters,
  isLoading
}) => {
  const [inputValue, setInputValue] = useState(search);
  const debouncedInputValue = useDebounce(inputValue, 400);

  useEffect(() => {
    if (debouncedInputValue !== search) {
        onSearchChange(debouncedInputValue);
    }
  }, [debouncedInputValue, onSearchChange, search]);

  useEffect(() => {
    setInputValue(search);
  }, [search]);

  return (
    <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2 }}>
      <TextField
        placeholder="Search by topic..."
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        disabled={isLoading}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
        }}
        size="small"
        sx={{ flexGrow: 1 }}
      />
      
      <Box sx={{ display: 'flex', gap: 2, width: { xs: '100%', md: 'auto' } }}>
        <FormControl size="small" sx={{ minWidth: 150, flexGrow: { xs: 1, md: 0 } }} disabled={isLoading}>
          <InputLabel id="sort-by-label">Sort By</InputLabel>
          <Select
            labelId="sort-by-label"
            value={sortBy}
            label="Sort By"
            onChange={(e) => onSortChange(e.target.value)}
          >
            <MenuItem value="creation_date">Creation Date</MenuItem>
            <MenuItem value="last_modified_date">Last Modified</MenuItem>
            <MenuItem value="topic">Topic (A-Z)</MenuItem>
            <MenuItem value="favorite">Favorites First</MenuItem>
          </Select>
        </FormControl>
        
        <FormControl size="small" sx={{ minWidth: 120, flexGrow: { xs: 1, md: 0 } }} disabled={isLoading}>
          <InputLabel id="filter-source-label">Source</InputLabel>
          <Select
            labelId="filter-source-label"
            value={filterSource || ''}
            label="Source"
            onChange={(e) => onFilterChange(e.target.value || null)}
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="generated">Generated</MenuItem>
            <MenuItem value="imported">Imported</MenuItem>
          </Select>
        </FormControl>
      </Box>
      
      {hasFilters && (
          <Button 
            variant="text"
            size="small"
            startIcon={<FilterListOffIcon />}
            onClick={clearFilters}
            disabled={isLoading || !hasFilters}
            sx={{ flexShrink: 0, alignSelf: 'center' }}
          >
            Clear Filters
          </Button>
      )}
    </Box>
  );
};

HistoryFilters.propTypes = {
  sortBy: PropTypes.string.isRequired,
  onSortChange: PropTypes.func.isRequired,
  filterSource: PropTypes.string,
  onFilterChange: PropTypes.func.isRequired,
  search: PropTypes.string.isRequired,
  onSearchChange: PropTypes.func.isRequired,
  clearFilters: PropTypes.func.isRequired,
  hasFilters: PropTypes.bool.isRequired,
  isLoading: PropTypes.bool
};

export default HistoryFilters; 