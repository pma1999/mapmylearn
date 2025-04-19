import React, { useMemo, useRef, useCallback, useState } from 'react';
import { Container, Paper, Divider, Grid, Snackbar, Alert, useMediaQuery, useTheme, Typography, Box } from '@mui/material';
import { FixedSizeGrid } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';

// Custom hooks
import useNotification from './hooks/useNotification';
import useHistoryFilters from './hooks/useHistoryFilters';
import useHistoryEntries from './hooks/useHistoryEntries';
import useHistoryActions from './hooks/useHistoryActions';

// Components
import PageHeader from './components/PageHeader';
import HistoryFilters from './components/HistoryFilters';
import HistoryEntryCard from './components/HistoryEntryCard';
import HistoryEntrySkeleton from './components/HistoryEntrySkeleton';
import EmptyState from './components/EmptyState';
import ImportDialog from './components/ImportDialog';
import ConfirmationDialog from './components/ConfirmationDialog';

// API Service
import * as api from '../../services/api';

/**
 * Virtualized grid cell renderer for history entries
 */
const EntryCell = ({ columnIndex, rowIndex, style, data }) => {
  const { entries, columnCount, onView, onDelete, onToggleFavorite, onUpdateTags, onDownloadPDF, onExport } = data;
  const index = rowIndex * columnCount + columnIndex;
  
  if (index >= entries.length) {
    return null; // Return empty for cells beyond our data
  }
  
  const entry = entries[index];
  
  return (
    <div style={{
      ...style,
      padding: '8px',
      boxSizing: 'border-box'
    }}>
      <HistoryEntryCard
        entry={entry}
        onView={onView}
        onDelete={onDelete}
        onToggleFavorite={onToggleFavorite}
        onUpdateTags={onUpdateTags}
        onDownloadPDF={onDownloadPDF}
        onExport={onExport}
        virtualized={true}
      />
    </div>
  );
};

/**
 * Performance statistics component
 */
const PerformanceStats = ({ stats, visible = false }) => {
  if (!visible || !stats) return null;
  
  // Only show stats when they're meaningful - not for background updates
  if (stats.fromCache && !stats.initialLoad) return null;
  
  return (
    <Box sx={{ mt: 1, mb: 2, px: 1, fontSize: '0.75rem', color: 'text.secondary' }}>
      <Typography variant="caption" component="div">
        Loaded {stats.total} items 
        {stats.fromCache ? ' (from cache)' : ` in ${Math.round(stats.loadTime)}ms`}
        {stats.serverTime ? ` • Server: ${stats.serverTime}ms` : ''}
      </Typography>
    </Box>
  );
};

/**
 * History page component for displaying and managing learning path history
 * @returns {JSX.Element} History page component
 */
const HistoryPage = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  const isSmallScreen = useMediaQuery(theme.breakpoints.down('lg'));
  
  // Initialize notification hook
  const { 
    notification, 
    showNotification, 
    closeNotification 
  } = useNotification();
  
  // Initialize filters hook
  const {
    sortBy,
    filterSource,
    searchTerm,
    handleSortChange,
    handleFilterChange,
    handleSearchChange,
    clearFilters
  } = useHistoryFilters();
  
  // Initialize history entries hook with filter options
  const {
    entries,
    loading,
    error,
    stats,
    initialLoadComplete,
    refreshEntries
  } = useHistoryEntries(
    { sortBy, filterSource, searchTerm },
    showNotification
  );
  
  // State for dialogs and processing status
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
  const [isClearConfirmOpen, setIsClearConfirmOpen] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false); // Added for disabling buttons during actions

  // Placeholder handlers for PageHeader props - Updated Below
  // const handleImport = () => console.warn('Import functionality not implemented yet.');
  // const handleExportAll = () => console.warn('Export All functionality not implemented yet.');
  // const handleClearHistory = () => console.warn('Clear History functionality not implemented yet.');

  // Mock/Placeholder handler for individual entry export
  const handleExportEntry = (entryId) => console.warn(`Export for entry ${entryId} not implemented yet.`);

  // --- Updated Action Handlers ---

  const handleImport = () => {
    setIsImportDialogOpen(true);
  };

  const handlePerformImport = async (learningPathObject) => {
    setIsProcessing(true);
    setIsImportDialogOpen(false); // Close dialog immediately
    showNotification('Importing history...', 'info');
    try {
      // Prepare payload for saveToHistory (matches LearningPathCreate schema)
      const payload = {
        topic: learningPathObject.topic || 'Untitled Imported Path',
        language: learningPathObject.language || 'en', // Default or extract from object
        path_data: learningPathObject, // The entire object is the path_data
        favorite: learningPathObject.favorite || false,
        tags: learningPathObject.tags || [],
        source: 'imported' // Explicitly set source
      };
      
      // Call the correct backend API endpoint via api.saveToHistory
      const result = await api.saveToHistory(payload);
      
      if (result.success) {
        showNotification(`Learning path "${payload.topic}" imported successfully!`, 'success');
        refreshEntries(); // Refresh the list
      } else {
        // This path might not be reached if api throws error, but good practice
        throw new Error(result.error || 'Import failed due to an unknown reason.');
      }
    } catch (error) {
      console.error("Import failed:", error);
      showNotification(`Import failed: ${error.message || 'Could not process the import request.'}`, 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleExportAll = async () => {
    if (!entries.length) {
      showNotification('No history entries to export.', 'info');
      return;
    }
    setIsProcessing(true);
    showNotification('Exporting history...', 'info');
    try {
      // Call the placeholder for the backend API endpoint
      const exportedEntries = await api.exportAllHistoryAPI(); 
      
      // --- This download logic will execute only if the API call succeeds --- 
      // --- (which it won't until the backend endpoint is implemented) --- 
      if (!exportedEntries || exportedEntries.length === 0) {
        showNotification('No history entries found to export.', 'info');
        // No return here, proceed to finally
      } else {
        const jsonString = JSON.stringify(exportedEntries, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `learni_history_export_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showNotification('History exported successfully.', 'success');
      }
    } catch (error) {
      console.error("Export failed:", error);
      // Display the error from the API call (or the placeholder error)
      showNotification(`Export failed: ${error.message}`, 'error'); 
    } finally {
      setIsProcessing(false);
    }
  };

  const handleClearHistory = () => {
    setIsClearConfirmOpen(true);
  };

  const handlePerformClear = async () => {
    setIsClearConfirmOpen(false); // Close dialog immediately
    setIsProcessing(true);
    showNotification('Clearing history...', 'info');
    try {
       // Call the placeholder for the backend API endpoint
      await api.clearAllHistoryAPI();

      // --- This success logic will execute only if the API call succeeds --- 
      // --- (which it won't until the backend endpoint is implemented) --- 
      showNotification('History cleared successfully.', 'success');
      refreshEntries(); // Refresh the list
      
    } catch (error) {
      console.error("Clear history failed:", error);
      // Display the error from the API call (or the placeholder error)
      showNotification(`Failed to clear history: ${error.message}`, 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  // --- End Updated Action Handlers ---

  // Destructure actions from useHistoryActions
  const {
    handleViewLearningPath,
    handleDeleteLearningPath,
    handleToggleFavorite,
    handleUpdateTags,
    handleDownloadPDF,
  } = useHistoryActions(showNotification, refreshEntries);
  
  // Calculate grid dimensions based on screen size
  const columnCount = useMemo(() => {
    if (isMobile) return 1;
    if (isTablet) return 2;
    if (isSmallScreen) return 3;
    return 4;
  }, [isMobile, isTablet, isSmallScreen]);
  
  // Calculate row count based on entries length and column count
  const rowCount = useMemo(() => {
    return Math.ceil(entries.length / columnCount);
  }, [entries.length, columnCount]);
  
  // Compute item size based on screen size
  const itemWidth = useMemo(() => {
    if (isMobile) return 300;
    if (isTablet) return 280;
    if (isSmallScreen) return 260;
    return 270;
  }, [isMobile, isTablet, isSmallScreen]);
  
  const itemHeight = 320; // Fixed height for cards
  
  // Computed value to check if any filters are applied
  const hasFiltersApplied = !!filterSource || !!searchTerm || sortBy !== 'creation_date';
  
  // Virtualized list itemData - include onExport
  const itemData = useMemo(() => ({
    entries,
    columnCount,
    onView: handleViewLearningPath,
    onDelete: handleDeleteLearningPath,
    onToggleFavorite: handleToggleFavorite,
    onUpdateTags: handleUpdateTags,
    onDownloadPDF: handleDownloadPDF,
    onExport: handleExportEntry
  }), [
    entries, 
    columnCount, 
    handleViewLearningPath, 
    handleDeleteLearningPath, 
    handleToggleFavorite, 
    handleUpdateTags, 
    handleDownloadPDF,
    handleExportEntry
  ]);
  
  // Reference to AutoSizer for recalculating dimensions when entries change
  const autoSizerRef = useRef(null);
  
  // Handler for refreshing the grid size
  const refreshGridSize = useCallback(() => {
    if (autoSizerRef.current) {
      // Force a recalculation of the grid dimensions
      autoSizerRef.current.forceUpdate();
    }
  }, []);
  
  // Refresh grid size when entries change
  React.useEffect(() => {
    refreshGridSize();
  }, [entries.length, refreshGridSize]);
  
  return (
    <Container maxWidth="lg">
      <Paper elevation={3} sx={{ p: { xs: 2, sm: 3, md: 4 }, borderRadius: 2, mb: 4 }}>
        <PageHeader 
          hasEntries={entries.length > 0}
          isLoading={loading && !initialLoadComplete}
          isProcessing={isProcessing}
          onImport={handleImport}
          onExport={handleExportAll}
          onClear={handleClearHistory}
        />
        
        <Divider sx={{ mb: 3 }} />
        
        <HistoryFilters
          sortBy={sortBy}
          onSortChange={handleSortChange}
          filterSource={filterSource}
          onFilterChange={handleFilterChange}
          search={searchTerm}
          onSearchChange={handleSearchChange}
          disabled={loading && !initialLoadComplete}
        />
        
        <PerformanceStats 
          stats={stats} 
          visible={process.env.NODE_ENV === 'development' && initialLoadComplete} 
        />
        
        {loading && !initialLoadComplete ? (
          // Show skeletons only on initial load
          <Grid container spacing={2}>
            <HistoryEntrySkeleton count={8} />
          </Grid>
        ) : error ? (
          // Error state
          <Box sx={{ py: 4, textAlign: 'center' }}>
            <Typography color="error" gutterBottom>
              {error}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Please try refreshing the page or check your network connection.
            </Typography>
          </Box>
        ) : entries.length > 0 ? (
          // Virtualized grid for better performance with many entries
          <Box sx={{ height: Math.min(800, Math.max(400, rowCount * itemHeight / 2)), width: '100%' }}>
            <AutoSizer ref={autoSizerRef}>
              {({ height, width }) => (
                <FixedSizeGrid
                  columnCount={columnCount}
                  columnWidth={width / columnCount}
                  height={height}
                  rowCount={rowCount}
                  rowHeight={itemHeight}
                  width={width}
                  itemData={itemData}
                >
                  {EntryCell}
                </FixedSizeGrid>
              )}
            </AutoSizer>
          </Box>
        ) : (
          // Empty state
          <EmptyState 
            onClearFilters={hasFiltersApplied ? clearFilters : undefined}
            hasFilters={hasFiltersApplied}
          />
        )}
      </Paper>
      
      {/* Render Dialogs */}
      <ImportDialog 
        open={isImportDialogOpen} 
        onClose={() => !isProcessing && setIsImportDialogOpen(false)} // Prevent closing while processing
        onImport={handlePerformImport} // Pass the actual import handler
      />
      
      <ConfirmationDialog 
        open={isClearConfirmOpen} 
        title="Confirm Clear History" 
        message="Are you sure you want to delete ALL learning path history entries? This action cannot be undone." 
        onConfirm={handlePerformClear} 
        onCancel={() => !isProcessing && setIsClearConfirmOpen(false)} // Prevent closing while processing
      />

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={closeNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={closeNotification} severity={notification.severity} sx={{ width: '100%' }}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default HistoryPage; 