/**
 * Format a date string into a localized date and time format
 * @param {string} dateString - ISO date string
 * @param {boolean} includeTime - Whether to include time in the formatted string
 * @returns {string} Formatted date string
 */
export const formatDate = (dateString, includeTime = true) => {
  if (!dateString) return '';
  
  try {
    const date = new Date(dateString);
    
    // Format the date part
    const dateOptions = { year: 'numeric', month: 'short', day: 'numeric' };
    const formattedDate = date.toLocaleDateString('es-ES', dateOptions);
    
    // Return date only if includeTime is false
    if (!includeTime) {
      return formattedDate;
    }
    
    // Format the time part
    const timeOptions = { hour: '2-digit', minute: '2-digit' };
    const formattedTime = date.toLocaleTimeString('es-ES', timeOptions);
    
    // Combine date and time
    return `${formattedDate}, ${formattedTime}`;
  } catch (error) {
    console.error('Error formatting date:', error);
    return dateString;
  }
};

/**
 * Get a relative time string (e.g., "2 hours ago", "yesterday")
 * @param {string} dateString - ISO date string
 * @returns {string} Relative time string
 */
export const getRelativeTime = (dateString) => {
  if (!dateString) return '';
  
  try {
    const date = new Date(dateString);
    const now = new Date();
    
    // Calculate time difference in milliseconds
    const diffMs = now - date;
    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    // Format based on time difference
    if (diffSeconds < 60) {
      return 'hace unos segundos';
    } else if (diffMinutes < 60) {
      return `hace ${diffMinutes} ${diffMinutes === 1 ? 'minuto' : 'minutos'}`;
    } else if (diffHours < 24) {
      return `hace ${diffHours} ${diffHours === 1 ? 'hora' : 'horas'}`;
    } else if (diffDays < 7) {
      return `hace ${diffDays} ${diffDays === 1 ? 'día' : 'días'}`;
    } else {
      // For older dates, just return the formatted date
      return formatDate(dateString, false);
    }
  } catch (error) {
    console.error('Error calculating relative time:', error);
    return dateString;
  }
}; 