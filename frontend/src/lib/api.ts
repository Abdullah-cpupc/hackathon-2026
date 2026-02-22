import axios from 'axios';
import Cookies from 'js-cookie';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Log API URL in development (helps debug configuration issues)
// if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
//   console.log('🔗 API Base URL:', API_BASE_URL);
// }

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = Cookies.get('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token expiration
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid, clear cookies and redirect to login
      Cookies.remove('access_token');
      Cookies.remove('user');
      if (typeof window !== 'undefined') {
        window.location.href = '/auth/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth API functions
export const authAPI = {
  // Register user
  register: async (userData: {
    email: string;
    username: string;
    password: string;
  }) => {
    const response = await apiClient.post('/auth/register', userData);
    return response.data;
  },

  // Login user
  login: async (credentials: {
    username: string;
    password: string;
  }) => {
    const response = await apiClient.post('/auth/login', credentials);
    return response.data;
  },

  // Get current user
  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },
};

// Company API functions
export const companyAPI = {
  // Get user's companies
  getCompanies: async () => {
    const response = await apiClient.get('/companies/');
    return response.data;
  },

  // Create company
  createCompany: async (companyData: {
    name: string;
    address?: string;
    phone?: string;
    website_urls: string[];
    description?: string;
    industry?: string;
    logo_url?: string;
  }) => {
    const response = await apiClient.post('/companies/', companyData);
    return response.data;
  },

  // Get company by ID
  getCompany: async (companyId: number) => {
    const response = await apiClient.get(`/companies/${companyId}`);
    return response.data;
  },

  // Update company
  updateCompany: async (companyId: number, companyData: {
    name?: string;
    address?: string;
    phone?: string;
    website_urls?: string[];
    description?: string;
    industry?: string;
    logo_url?: string;
  }) => {
    const response = await apiClient.put(`/companies/${companyId}`, companyData);
    return response.data;
  },

  // Delete company
  deleteCompany: async (companyId: number) => {
    const response = await apiClient.delete(`/companies/${companyId}`);
    return response.data;
  },

  // Upload file to company
  uploadFile: async (companyId: number, file: File, description?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (description) {
      formData.append('description', description);
    }
    
    const response = await apiClient.post(`/companies/${companyId}/files`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Get company files
  getCompanyFiles: async (companyId: number) => {
    const response = await apiClient.get(`/companies/${companyId}/files`);
    return response.data;
  },

  // Delete file
  deleteFile: async (companyId: number, fileId: number) => {
    const response = await apiClient.delete(`/companies/${companyId}/files/${fileId}`);
    return response.data;
  },

  // Upload logo
  uploadLogo: async (companyId: number, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post(`/companies/${companyId}/logo`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Delete logo
  deleteLogo: async (companyId: number) => {
    const response = await apiClient.delete(`/companies/${companyId}/logo`);
    return response.data;
  },
};

// Widget API functions
export const widgetAPI = {
  // Create widget
  createWidget: async (companyId: number, widgetData: {
    name: string;
    position: string;
    minimized_shape: string;
    minimized_bg_color: string;
    maximized_style: string;
    system_bubble_bg_color: string;
    user_bubble_bg_color: string;
    is_active?: boolean;
  }) => {
    const response = await apiClient.post(`/widgets/?company_id=${companyId}`, widgetData);
    return response.data;
  },

  // Get company widgets
  getCompanyWidgets: async (companyId: number) => {
    const response = await apiClient.get(`/widgets/company/${companyId}`);
    return response.data;
  },

  // Get widget by ID
  getWidget: async (widgetId: string) => {
    const response = await apiClient.get(`/widgets/${widgetId}`);
    return response.data;
  },

  // Update widget
  updateWidget: async (widgetId: string, widgetData: {
    name?: string;
    position?: string;
    minimized_shape?: string;
    minimized_bg_color?: string;
    maximized_style?: string;
    system_bubble_bg_color?: string;
    user_bubble_bg_color?: string;
    is_active?: boolean;
  }) => {
    const response = await apiClient.put(`/widgets/${widgetId}`, widgetData);
    return response.data;
  },

  // Toggle widget active status
  toggleWidget: async (widgetId: string) => {
    const response = await apiClient.patch(`/widgets/${widgetId}/toggle`);
    return response.data;
  },

  // Delete widget
  deleteWidget: async (widgetId: string) => {
    const response = await apiClient.delete(`/widgets/${widgetId}`);
    return response.data;
  },
};

// AI API functions
export const aiAPI = {
  // Build AI for a company
  buildAI: async (companyId: number, websiteUrls?: string[]) => {
    const response = await apiClient.post(`/ai/build/${companyId}`, {
      website_urls: websiteUrls
    });
    return response.data;
  },

  // Re-scrape website for AI
  scrapeWebsite: async (companyId: number, websiteUrls?: string[]) => {
    const response = await apiClient.post(`/ai/scrape/${companyId}`, {
      website_urls: websiteUrls
    });
    return response.data;
  },

  // Get AI status for a company
  getAIStatus: async (companyId: number) => {
    const response = await apiClient.get(`/ai/status/${companyId}`);
    return response.data;
  },

  // Chat with AI
  chatWithAI: async (companyId: number, message: string, nResults?: number) => {
    const response = await apiClient.post(`/ai/chat/${companyId}`, {
      message,
      n_results: nResults || 5
    });
    return response.data;
  },

  // Disable AI for a company
  disableAI: async (companyId: number) => {
    const response = await apiClient.delete(`/ai/disable/${companyId}`);
    return response.data;
  },
};

export default apiClient;
