import React, { useMemo, useRef, useCallback, useState } from 'react';
import { Container, Paper, Divider, Grid, useMediaQuery, useTheme, Typography, Box, Pagination, Stack } from '@mui/material';
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
import ActiveGenerationCard from './components/ActiveGenerationCard';
import EmptyState from './components/EmptyState';
import ImportDialog from './components/ImportDialog';
import ConfirmationDialog from './components/ConfirmationDialog';

// API Service
import * as api from '../../services/api';

/**
 * Virtualized grid cell renderer for history entries and skeletons
 */
const EntryCell = ({ columnIndex, rowIndex, style, data }) => {
  const { 
    entries, 
    columnCount, 
    onView, 
    onDelete, 
    onToggleFavorite, 
    onUpdateTags, 
    onDownloadPDF, 
    onExport, 
    onTogglePublic, 
    onCopyShareLink,
    isLoading // Added isLoading flag
  } = data;
  const index = rowIndex * columnCount + columnIndex;
  
  // If loading, render skeleton if index is within skeleton count
  if (isLoading) {
     if (index < data.skeletonCount) {
        return (
          <div style={{ ...style, padding: '8px', boxSizing: 'border-box' }}>
            <HistoryEntrySkeleton index={index} />
          </div>
        );
     } else {
        return null; // Don't render anything beyond skeleton count
     }
  }
  
  // If not loading, render actual entry if index is valid
  if (index >= entries.length) {
    return null; // Return empty for cells beyond real data
  }
  
  const entry = entries[index];
  
  return (
    <div style={{ ...style, padding: '8px', boxSizing: 'border-box' }}>
      {entry.isActive ? (
        <ActiveGenerationCard 
          entry={entry} 
          virtualized={true} 
        />
      ) : (
        <HistoryEntryCard
          entry={entry}
          onView={onView}
          onDelete={onDelete}
          onToggleFavorite={onToggleFavorite}
          onUpdateTags={onUpdateTags}
          onDownloadPDF={onDownloadPDF}
          onExport={onExport}
          onTogglePublic={onTogglePublic}
          onCopyShareLink={onCopyShareLink}
          virtualized={true}
        />
      )}
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
  const isLargeScreen = useMediaQuery(theme.breakpoints.up('lg'));
  
  const [page, setPage] = useState(1);
  const ITEMS_PER_PAGE = 12;

  // Initialize notification hook
  const { showNotification } = useNotification();
  
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
  
  // Fetch entries with pagination
  const {
    entries,
    pagination,
    loading,
    error,
    stats,
    initialLoadComplete,
    refreshEntries
  } = useHistoryEntries(
    { sortBy, filterSource, searchTerm, page, perPage: ITEMS_PER_PAGE },
    showNotification
  );
  
  // State for dialogs and processing status
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
  const [isClearConfirmOpen, setIsClearConfirmOpen] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  // Mock/Placeholder handler for individual entry export
  const handleExportEntry = (entryId) => console.warn(`Export for entry ${entryId} not implemented yet.`);

  // --- Updated Action Handlers ---

  const handleImport = () => {
    setIsImportDialogOpen(true);
  };

  const handlePerformImport = async (learningPathObject) => {
    setIsProcessing(true);
    setIsImportDialogOpen(false); // Close dialog immediately
    showNotification('Importing learning path...', { severity: 'info' });
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
        showNotification(`"${payload.topic}" imported successfully!`, { severity: 'success' });
        refreshEntries(); // Refresh the list
      } else {
        // This path might not be reached if api throws error, but good practice
        throw new Error(result.error || 'Import failed due to an unknown reason.');
      }
    } catch (error) {
      console.error("Import failed:", error);
      showNotification(`Import failed: ${error.message || 'Could not process the import request.'}`, { severity: 'error' });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleExportAll = async () => {
    if (!entries.length) {
      showNotification('No history entries to export.', { severity: 'info' });
      return;
    }
    setIsProcessing(true);
    showNotification('Exporting all history...', { severity: 'info' });
    try {
      // Call the placeholder for the backend API endpoint
      const exportedEntries = await api.exportAllHistoryAPI(); 
      
      // --- This download logic will execute only if the API call succeeds --- 
      // --- (which it won't until the backend endpoint is implemented) --- 
      if (!exportedEntries || exportedEntries.length === 0) {
        showNotification('No history entries found to export.', { severity: 'info' });
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
        
        showNotification('History exported successfully.', { severity: 'success' });
      }
    } catch (error) {
      console.error("Export failed:", error);
      // Display the error from the API call (or the placeholder error)
      showNotification(`Export failed: ${error.message}`, { severity: 'error' }); 
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
    showNotification('Clearing all history...', { severity: 'info' });
    try {
       // Call the placeholder for the backend API endpoint
      await api.clearAllHistoryAPI();

      // --- This success logic will execute only if the API call succeeds --- 
      // --- (which it won't until the backend endpoint is implemented) --- 
      showNotification('History cleared successfully.', { severity: 'success' });
      refreshEntries(); // Refresh the list
      
    } catch (error) {
      console.error("Clear history failed:", error);
      // Display the error from the API call (or the placeholder error)
      showNotification(`Failed to clear history: ${error.message}`, { severity: 'error' });
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
    handleTogglePublic,
    handleCopyShareLink
  } = useHistoryActions(showNotification, refreshEntries);
  
  const handlePageChange = (event, newPage) => {
    setPage(newPage);
    // The useHistoryEntries hook should re-fetch data when 'page' changes
  };

  const hasFiltersApplied = useMemo(() => {
      return searchTerm !== '' || filterSource !== null || sortBy !== 'creation_date';
  }, [searchTerm, filterSource, sortBy]);

  // Calculate grid parameters
  const columnCount = isMobile ? 1 : isTablet ? 2 : isLargeScreen ? 4 : 3;
  const isLoadingSkeletons = loading && !initialLoadComplete;
  // Use ITEMS_PER_PAGE for skeletons, actual entries length for data
  const displayData = isLoadingSkeletons ? Array(ITEMS_PER_PAGE).fill({ isSkeleton: true }) : entries;
  const rowCount = Math.ceil(displayData.length / columnCount);
  const cardHeight = 380;

  // Memoize itemData for react-window, include loading state and skeleton count
  const itemData = useMemo(() => ({
    entries: displayData, // Use potentially skeleton-filled array
    columnCount,
    onView: handleViewLearningPath,
    onDelete: handleDeleteLearningPath,
    onToggleFavorite: handleToggleFavorite,
    onUpdateTags: handleUpdateTags,
    onDownloadPDF: handleDownloadPDF,
    onExport: handleExportEntry,
    onTogglePublic: handleTogglePublic,
    onCopyShareLink: handleCopyShareLink,
    isLoading: isLoadingSkeletons, // Pass loading flag
    skeletonCount: ITEMS_PER_PAGE // Pass expected skeleton count (used by EntryCell)
  }), [
    displayData, // Depends on loading state
    columnCount, 
    handleViewLearningPath, 
    handleDeleteLearningPath, 
    handleToggleFavorite, 
    handleUpdateTags, 
    handleDownloadPDF, 
    handleExportEntry, 
    handleTogglePublic, 
    handleCopyShareLink,
    isLoadingSkeletons // Add dependency
  ]);
  
  // Render Logic
  const renderContent = () => {
    // Check for EmptyState AFTER checking for loading, otherwise it might flash empty state briefly
    if (!isLoadingSkeletons && entries.length === 0) {
      return (
        <EmptyState 
          hasFilters={hasFiltersApplied}
          onClearFilters={clearFilters} 
        />
      );
    }
    
    // Always render the grid: it shows skeletons when loading, entries when loaded
    return (
        <Box sx={{ height: 'calc(100vh - 250px)', width: '100%' }}> {/* Adjust height */} 
            <AutoSizer>
            {({
                height,
                width
            }) => {
                const cardWidth = width / columnCount;
                const effectiveRowCount = Math.max(1, rowCount);
                return (
                <FixedSizeGrid
                    columnCount={columnCount}
                    columnWidth={cardWidth}
                    height={height}
                    rowCount={effectiveRowCount} 
                    rowHeight={cardHeight}
                    width={width}
                    itemData={itemData}
                    style={{ overflowX: 'hidden'}}
                >
                    {EntryCell}
                </FixedSizeGrid>
                );
            }}
            </AutoSizer>
        </Box>
    );
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <PageHeader
        hasEntries={entries.length > 0}
        onImport={handleImport}
        onExport={handleExportAll}
        onClear={handleClearHistory}
        isLoading={loading && !initialLoadComplete}
        isProcessing={isProcessing}
      />
      
      <Paper elevation={0} sx={{ p: { xs: 1.5, sm: 2 }, mb: 3, border: '1px solid', borderColor: 'divider' }}>
        <HistoryFilters
          sortBy={sortBy}
          onSortChange={handleSortChange}
          filterSource={filterSource}
          onFilterChange={handleFilterChange}
          search={searchTerm}
          onSearchChange={handleSearchChange}
          clearFilters={clearFilters}
          hasFilters={hasFiltersApplied}
        />
      </Paper>
      
      {renderContent()}
      
      {!isLoadingSkeletons && pagination && pagination.total > 0 && pagination.total > ITEMS_PER_PAGE && (
        <Stack spacing={2} sx={{ mt: 3, alignItems: 'center' }}>
            <Typography variant="body2" color="text.secondary">
                Showing {entries.length} of {pagination.total} paths
            </Typography>
            <Pagination 
                count={Math.ceil(pagination.total / ITEMS_PER_PAGE)}
                page={page}
                onChange={handlePageChange}
                color="primary"
                showFirstButton 
                showLastButton 
                sx={{ 
                  '& .MuiPaginationItem-root': {
                    fontSize: '0.875rem'
                  }
                }}
            />
        </Stack>
      )}

      <PerformanceStats stats={stats} visible={process.env.NODE_ENV === 'development'} />

      <ImportDialog
        open={isImportDialogOpen}
        onClose={() => setIsImportDialogOpen(false)}
        onImport={handlePerformImport}
      />
      <ConfirmationDialog
        open={isClearConfirmOpen}
        title="Clear All History"
        message="Are you sure you want to delete ALL learning paths from your history? This action cannot be undone."
        onConfirm={handlePerformClear}
        onCancel={() => setIsClearConfirmOpen(false)}
        isDestructive={true}
      />
    </Container>
  );
};

export default HistoryPage; 