import React from 'react';
import PropTypes from 'prop-types';
import {
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  InputAdornment
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';

/**
 * Component for filtering and sorting history entries
 * @param {Object} props - Component props
 * @param {string} props.sortBy - Current sort option
 * @param {Function} props.onSortChange - Handler for sort option change
 * @param {string|null} props.filterSource - Current source filter
 * @param {Function} props.onFilterChange - Handler for source filter change
 * @param {string} props.search - Current search term
 * @param {Function} props.onSearchChange - Handler for search term change
 * @returns {JSX.Element} History filters component
 */
const HistoryFilters = ({ 
  sortBy, 
  onSortChange, 
  filterSource, 
  onFilterChange, 
  search, 
  onSearchChange 
}) => {
  return (
    <Grid container spacing={2} sx={{ mb: 3 }}>
      <Grid item xs={12} sm={12} md={5}>
        <TextField
          fullWidth
          placeholder="Search by topic..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          size="small"
        />
      </Grid>
      <Grid item xs={6} sm={6} md={4}>
        <FormControl fullWidth size="small">
          <InputLabel id="sort-by-label">Sort By</InputLabel>
          <Select
            labelId="sort-by-label"
            value={sortBy}
            label="Sort By"
            onChange={(e) => onSortChange(e.target.value)}
          >
            <MenuItem value="creation_date">Creation Date</MenuItem>
            <MenuItem value="last_modified_date">Last Modified</MenuItem>
            <MenuItem value="topic">Topic</MenuItem>
            <MenuItem value="favorite">Favorites First</MenuItem>
          </Select>
        </FormControl>
      </Grid>
      <Grid item xs={6} sm={6} md={3}>
        <FormControl fullWidth size="small">
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
      </Grid>
    </Grid>
  );
};

HistoryFilters.propTypes = {
  sortBy: PropTypes.string.isRequired,
  onSortChange: PropTypes.func.isRequired,
  filterSource: PropTypes.string,
  onFilterChange: PropTypes.func.isRequired,
  search: PropTypes.string.isRequired,
  onSearchChange: PropTypes.func.isRequired
};

export default HistoryFilters; 