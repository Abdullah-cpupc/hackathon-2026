// Utility function to format API errors for display
export const formatApiError = (error: any): string => {
  console.error('API Error:', error);
  
  // Handle different error formats from FastAPI
  if (error.response?.data) {
    const data = error.response.data;
    
    // Handle validation errors (422) - array of error objects
    if (data.detail && Array.isArray(data.detail)) {
      return data.detail.map((err: any) => err.msg).join(', ');
    }
    
    // Handle simple detail message
    if (data.detail && typeof data.detail === 'string') {
      return data.detail;
    }
    
    // Handle other error formats
    if (typeof data === 'string') {
      return data;
    }
  }
  
  // Handle network errors or other issues
  if (error.message) {
    return error.message;
  }
  
  return 'An unexpected error occurred. Please try again.';
};
