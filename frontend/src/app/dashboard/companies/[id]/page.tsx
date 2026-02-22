'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { companyAPI, widgetAPI, aiAPI } from '@/lib/api';
import { formatApiError } from '@/lib/errorUtils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ChatWidgetsCard } from '@/components/ChatWidgetsCard';
import { QuickStatsCard } from '@/components/QuickStatsCard';
import { AIStatusCard } from '@/components/AIStatusCard';
import { AIChatModal } from '@/components/AIChatModal';
import { WidgetScriptModal } from '@/components/WidgetScriptModal';
import { toast } from 'sonner';
import { 
  ArrowLeft, 
  Edit,
  X,
  Bot,
  Trash2,
  Building2,
  FileText,
  MapPin,
  Phone,
  Globe
} from 'lucide-react';


interface Company {
  id: number;
  name: string;
  description?: string;
  address?: string;
  phone?: string;
  website_urls: string[];
  industry?: string;
  logo_url?: string;
  created_at: string;
  updated_at: string;
}

interface CompanyFile {
  id: number;
  filename: string;
  file_path: string;
  description?: string;
  file_size: number;
  uploaded_at: string;
}

interface Widget {
  id: number;
  company_id: number;
  name: string;
  widget_id: string;
  position: string;
  minimized_shape: string;
  minimized_bg_color: string;
  maximized_style: string;
  system_bubble_bg_color: string;
  user_bubble_bg_color: string;
  is_active: boolean;
  api_key?: string;
  allowed_domains?: string[];
  created_at: string;
  updated_at: string;
}


export default function CompanyDetailsPage() {
  const router = useRouter();
  const params = useParams();
  const { isAuthenticated } = useAuth();
  const companyId = parseInt(params.id as string);
  
  const [company, setCompany] = useState<Company | null>(null);
  const [files, setFiles] = useState<CompanyFile[]>([]);
  const [widgets, setWidgets] = useState<Widget[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [widgetsLoading, setWidgetsLoading] = useState(false);
  const [aiBuilding, setAiBuilding] = useState(false);
  const [aiStatus, setAiStatus] = useState<any>(null);
  const [chatModalOpen, setChatModalOpen] = useState(false);

  useEffect(() => {
    // Redirect if not authenticated
    if (!isAuthenticated) {
      router.push('/auth/login');
      return;
    }

    if (companyId) {
      fetchCompanyData();
      fetchCompanyFiles();
      fetchCompanyWidgets();
      fetchAIStatus();
    }
  }, [isAuthenticated, companyId, router]);

  const fetchCompanyData = async () => {
    try {
      const companyData = await companyAPI.getCompany(companyId);
      setCompany(companyData);
    } catch (err: any) {
      toast.error(formatApiError(err));
      router.push('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const fetchCompanyFiles = async () => {
    try {
      const filesData = await companyAPI.getCompanyFiles(companyId);
      setFiles(filesData);
    } catch (err: any) {
      console.error('Error fetching files:', err);
    }
  };

  const fetchCompanyWidgets = async () => {
    try {
      const widgetsData = await widgetAPI.getCompanyWidgets(companyId);
      setWidgets(widgetsData || []);
    } catch (err: any) {
      console.error('Error fetching widgets:', err);
      // Handle network errors gracefully - default to empty array
      if (err.message?.includes('Network Error') || err.code === 'ERR_NETWORK') {
        console.warn('Network error: Backend may not be reachable. Check NEXT_PUBLIC_API_URL environment variable.');
        setWidgets([]); // Default to empty array so UI doesn't break
      } else {
        setWidgets([]); // Default to empty array on any error
      }
    }
  };

  const fetchAIStatus = async () => {
    try {
      const status = await aiAPI.getAIStatus(companyId);
      setAiStatus(status);
    } catch (err: any) {
      console.error('Error fetching AI status:', err);
    }
  };


  const toggleWidget = async (widgetId: string) => {
    setWidgetsLoading(true);
    try {
      await widgetAPI.toggleWidget(widgetId);
      toast.success('Widget status updated');
      fetchCompanyWidgets(); // Refresh widgets list
    } catch (err: any) {
      toast.error(formatApiError(err));
    } finally {
      setWidgetsLoading(false);
    }
  };

  const deleteWidget = async (widgetId: string) => {
    if (!confirm('Are you sure you want to delete this widget? This action cannot be undone.')) {
      return;
    }

    setWidgetsLoading(true);
    try {
      await widgetAPI.deleteWidget(widgetId);
      toast.success('Widget deleted successfully');
      fetchCompanyWidgets(); // Refresh widgets list
    } catch (err: any) {
      toast.error(formatApiError(err));
    } finally {
      setWidgetsLoading(false);
    }
  };

  const [showScriptModal, setShowScriptModal] = useState(false);
  const [selectedWidget, setSelectedWidget] = useState<Widget | null>(null);

  const openScriptModal = (widget: Widget) => {
    setSelectedWidget(widget);
    setShowScriptModal(true);
  };

  const copyWidgetScript = (widget: Widget) => {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    const script = `<script src="${apiBaseUrl}/widgets/${widget.widget_id}/script.js?api_key=${widget.api_key}"></script>`;
    navigator.clipboard.writeText(script).then(() => {
      toast.success('Widget script copied to clipboard');
    }).catch(() => {
      toast.error('Failed to copy script');
    });
  };


  const handleDelete = async () => {
    setDeleteLoading(true);
    try {
      await companyAPI.deleteCompany(companyId);
      toast.success('Company deleted successfully');
      router.push('/dashboard');
    } catch (err: any) {
      toast.error(formatApiError(err));
    } finally {
      setDeleteLoading(false);
    }
  };

  const buildAI = async () => {
    if (!company) return;
    
    setAiBuilding(true);
    try {
      const result = await aiAPI.buildAI(companyId, company.website_urls);
      toast.success('AI build initiated successfully! This may take a few minutes.');
      
      // Start polling for AI status
      pollAIStatus();
    } catch (err: any) {
      toast.error(formatApiError(err));
    } finally {
      setAiBuilding(false);
    }
  };

  const pollAIStatus = async () => {
    try {
      const status = await aiAPI.getAIStatus(companyId);
      setAiStatus(status);
      
      // Continue polling if still building
      if (status.ai_build_status === 'building') {
        setTimeout(pollAIStatus, 2500); // Poll every 2.5 seconds when building for more responsive updates
      } else if (status.ai_build_status === 'ready') {
        toast.success('AI build completed successfully!');
      } else if (status.ai_build_status === 'failed') {
        toast.error(`AI build failed: ${status.error_message || 'Unknown error'}`);
      }
    } catch (err: any) {
      console.error('Error polling AI status:', err);
      // Continue polling even on error, but with longer interval
      if (aiStatus?.ai_build_status === 'building') {
        setTimeout(pollAIStatus, 5000);
      }
    }
  };

  const scrapeWebsite = async () => {
    if (!company) return;
    
    setAiBuilding(true);
    try {
      const result = await aiAPI.scrapeWebsite(companyId, company.website_urls);
      toast.success('Website re-scraping initiated successfully!');
      
      // Start polling for AI status
      pollAIStatus();
    } catch (err: any) {
      toast.error(formatApiError(err));
    } finally {
      setAiBuilding(false);
    }
  };

  const disableAI = async () => {
    try {
      await aiAPI.disableAI(companyId);
      toast.success('AI has been disabled successfully!');
      await fetchAIStatus(); // Refresh AI status
    } catch (err: any) {
      toast.error(formatApiError(err));
    }
  };

  const chatWithAI = () => {
    setChatModalOpen(true);
  };


  if (loading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 bg-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading company details...</p>
        </div>
      </div>
    );
  }

  if (!company) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 flex items-center justify-center">
        <Card className="w-full max-w-md border-0 shadow-xl">
          <CardContent className="p-8 text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <X className="w-8 h-8 text-red-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Company Not Found</h2>
            <p className="text-gray-600 mb-6">
              The company you're looking for doesn't exist or you don't have permission to view it.
            </p>
            <Button onClick={() => router.push('/dashboard')}>
              Back to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      {/* Navigation */}
      <nav className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                ChatBotAI
              </span>
            </div>
            
            <div className="flex items-center space-x-3">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => router.push('/dashboard')}
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Dashboard
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{company.name}</h1>
              {/* <p className="text-gray-600 mt-1">
                Created {new Date(company.created_at).toLocaleDateString()}
              </p> */}
            </div>
            <div className="flex items-center space-x-3">
              <Button 
                asChild
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white border-0 shadow-lg"
              >
                <Link href={`/dashboard/companies/${company.id}/widgets/create`}>
                  Create Chat Widget
                </Link>
              </Button>
              <div className="h-8 w-px bg-gray-300"></div>
              <Button asChild>
                <Link href={`/dashboard/companies/${company.id}/edit`}>
                  <Edit className="w-4 h-4" />
                  Edit Company
                </Link>
              </Button>
              <Button 
                variant="destructive" 
                onClick={() => setShowDeleteConfirm(true)}
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </Button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-3 space-y-6">
            <QuickStatsCard
              company={company}
              files={files}
              widgets={widgets}
            />

            <AIStatusCard
              aiStatus={aiStatus}
              aiBuilding={aiBuilding}
              onBuildAI={buildAI}
              onScrapeWebsite={scrapeWebsite}
              onDisableAI={disableAI}
              onChatWithAI={chatWithAI}
              companyId={companyId}
            />

            <ChatWidgetsCard
              companyId={companyId}
              widgets={widgets}
              widgetsLoading={widgetsLoading}
              toggleWidget={toggleWidget}
              copyWidgetScript={copyWidgetScript}
              openScriptModal={openScriptModal}
              deleteWidget={deleteWidget}
            />
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Company Information - Read Only */}
            <Card className="border-0 shadow-xl">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Company Information</CardTitle>
                <CardDescription>
                  Your company's details
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center space-x-3">
                    <Building2 className="w-4 h-4" />
                    <div>
                      <p className="text-xs text-gray-500">Company Name</p>
                      <p className="text-sm font-medium">{company.name}</p>
                    </div>
                  </div>

                  {company.description && (
                    <div className="flex items-start space-x-3">
                      <FileText className="w-4 h-4 mt-1" />
                      <div>
                        <p className="text-xs text-gray-500">Description</p>
                        <p className="text-xs text-gray-700 line-clamp-3">{company.description}</p>
                      </div>
                    </div>
                  )}

                  {company.address && (
                    <div className="flex items-start space-x-3">
                      <MapPin className="w-4 h-4 mt-1" />
                      <div>
                        <p className="text-xs text-gray-500">Address</p>
                        <p className="text-xs text-gray-700 line-clamp-2">{company.address}</p>
                      </div>
                    </div>
                  )}

                  {company.phone && (
                    <div className="flex items-center space-x-3">
                      <Phone className="w-4 h-4" />
                      <div>
                        <p className="text-xs text-gray-500">Phone</p>
                        <p className="text-sm font-medium">{company.phone}</p>
                      </div>
                    </div>
                  )}

                  {company.industry && (
                    <div className="flex items-center space-x-3">
                      <Building2 className="w-4 h-4" />
                      <div>
                        <p className="text-xs text-gray-500">Industry</p>
                        <p className="text-sm font-medium">{company.industry}</p>
                      </div>
                    </div>
                  )}

                  <div className="flex items-start space-x-3">
                    <Globe className="w-4 h-4 mt-1" />
                    <div>
                      <p className="text-xs text-gray-500">Website URLs</p>
                      <div className="space-y-1">
                        {company.website_urls.slice(0, 2).map((url, index) => (
                          <a
                            key={index}
                            href={url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs hover:text-blue-800 underline block truncate"
                          >
                            {url}
                          </a>
                        ))}
                        {company.website_urls.length > 2 && (
                          <p className="text-xs text-gray-500">+{company.website_urls.length - 2} more</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <Card className="w-full max-w-md mx-4 border-0 shadow-xl">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg font-semibold text-red-600">
                  Delete Company
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowDeleteConfirm(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <p className="text-gray-600">
                  Are you sure you want to delete <strong>"{company.name}"</strong>? 
                  This action cannot be undone and will remove all associated data including files and chatbot configurations.
                </p>
                <div className="flex justify-end space-x-3">
                  <Button
                    variant="outline"
                    onClick={() => setShowDeleteConfirm(false)}
                    disabled={deleteLoading}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={handleDelete}
                    disabled={deleteLoading}
                  >
                    {deleteLoading ? 'Deleting...' : 'Delete Company'}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* AI Chat Modal */}
      {company && (
        <AIChatModal
          isOpen={chatModalOpen}
          onClose={() => setChatModalOpen(false)}
          companyId={companyId}
          companyName={company.name}
        />
      )}

      {/* Widget Script Modal */}
      <WidgetScriptModal
        isOpen={showScriptModal}
        onClose={() => setShowScriptModal(false)}
        widget={selectedWidget}
      />
    </div>
  );
}
