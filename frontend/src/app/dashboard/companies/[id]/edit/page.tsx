'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { companyAPI } from '@/lib/api';
import { formatApiError } from '@/lib/errorUtils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { CompanyInfoCard } from '@/components/CompanyInfoCard';
import { KnowledgeBaseFilesCard } from '@/components/KnowledgeBaseFilesCard';
import { CompanyLogoCard } from '@/components/CompanyLogoCard';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { 
  ArrowLeft, 
  Save,
  X,
  Bot,
  Upload,
  FileText
} from 'lucide-react';

// Zod schema for form validation
const companyFormSchema = z.object({
  name: z.string().min(1, 'Company name is required'),
  description: z.string().optional(),
  address: z.string().optional(),
  phone: z.string().optional(),
  industry: z.string().optional(),
  websiteUrls: z.array(z.string().url('Please enter a valid URL')).min(1, 'At least one website URL is required'),
});

type CompanyFormData = z.infer<typeof companyFormSchema>;

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

interface LogoData {
  file: File | null;
  preview: string | null;
}

const industryOptions = [
  'Education',
  'Technology',
  'Healthcare',
  'Finance',
  'Retail',
  'Manufacturing',
  'Real Estate',
  'Food & Beverage',
  'Travel & Tourism',
  'Professional Services',
  'Non-Profit',
  'Government',
  'Entertainment',
  'Sports & Fitness',
  'Beauty & Wellness',
  'Automotive',
  'Construction',
  'Agriculture',
  'Energy',
  'Other'
];

export default function CompanyEditPage() {
  const router = useRouter();
  const params = useParams();
  const { isAuthenticated } = useAuth();
  const companyId = parseInt(params.id as string);
  
  const [company, setCompany] = useState<Company | null>(null);
  const [files, setFiles] = useState<CompanyFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [saveLoading, setSaveLoading] = useState(false);
  const [fileLoading, setFileLoading] = useState(false);
  const [logoData, setLogoData] = useState<LogoData>({
    file: null,
    preview: null,
  });
  const [logoLoading, setLogoLoading] = useState(false);

  const form = useForm<CompanyFormData>({
    resolver: zodResolver(companyFormSchema),
    defaultValues: {
      name: '',
      description: '',
      address: '',
      phone: '',
      industry: '',
      websiteUrls: [''],
    },
  });

  useEffect(() => {
    // Redirect if not authenticated
    if (!isAuthenticated) {
      router.push('/auth/login');
      return;
    }

    if (companyId) {
      fetchCompanyData();
      fetchCompanyFiles();
    }
  }, [isAuthenticated, companyId, router]);

  const fetchCompanyData = async () => {
    try {
      const companyData = await companyAPI.getCompany(companyId);
      setCompany(companyData);
      
      // Update form with company data
      form.reset({
        name: companyData.name,
        description: companyData.description || '',
        address: companyData.address || '',
        phone: companyData.phone || '',
        industry: companyData.industry || '',
        websiteUrls: companyData.website_urls.length > 0 ? companyData.website_urls : [''],
      });
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

  const handleWebsiteUrlChange = (index: number, value: string) => {
    const currentUrls = form.getValues('websiteUrls');
    const newUrls = [...currentUrls];
    newUrls[index] = value;
    form.setValue('websiteUrls', newUrls);
  };

  const addWebsiteUrl = () => {
    const currentUrls = form.getValues('websiteUrls');
    form.setValue('websiteUrls', [...currentUrls, '']);
  };

  const removeWebsiteUrl = (index: number) => {
    const currentUrls = form.getValues('websiteUrls');
    if (currentUrls.length > 1) {
      const newUrls = currentUrls.filter((_, i) => i !== index);
      form.setValue('websiteUrls', newUrls);
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/plain',
      'text/csv',
      'application/json'
    ];

    const validFiles = files.filter(file => {
      if (!allowedTypes.includes(file.type)) {
        toast.error(`File type ${file.type} is not allowed. Please upload PDF, DOC, DOCX, XLS, XLSX, TXT, CSV, or JSON files.`);
        return false;
      }
      if (file.size > 10 * 1024 * 1024) { // 10MB limit
        toast.error(`File ${file.name} is too large. Maximum size is 10MB.`);
        return false;
      }
      return true;
    });

    if (validFiles.length > 0) {
      uploadFiles(validFiles);
    }
  };

  const uploadFiles = async (filesToUpload: File[]) => {
    setFileLoading(true);
    try {
      for (const file of filesToUpload) {
        const description = `${file.name} - Knowledge base document`;
        await companyAPI.uploadFile(companyId, file, description);
      }
      toast.success(`${filesToUpload.length} file(s) uploaded successfully`);
      fetchCompanyFiles(); // Refresh files list
    } catch (err: any) {
      toast.error(formatApiError(err));
    } finally {
      setFileLoading(false);
    }
  };

  const deleteFile = async (fileId: number) => {
    try {
      await companyAPI.deleteFile(companyId, fileId);
      toast.success('File deleted successfully');
      fetchCompanyFiles(); // Refresh files list
    } catch (err: any) {
      toast.error(formatApiError(err));
    }
  };

  const handleLogoChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file type
      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
      if (!allowedTypes.includes(file.type)) {
        toast.error('Please upload a valid image file (JPEG, PNG, GIF, or WebP)');
        return;
      }
      
      // Validate file size (5MB limit)
      if (file.size > 5 * 1024 * 1024) {
        toast.error('Logo file is too large. Maximum size is 5MB.');
        return;
      }
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setLogoData({
          file: file,
          preview: e.target?.result as string,
        });
      };
      reader.readAsDataURL(file);
    }
  };

  const uploadLogo = async () => {
    if (!logoData.file) return;
    
    setLogoLoading(true);
    try {
      await companyAPI.uploadLogo(companyId, logoData.file);
      toast.success('Logo uploaded successfully');
      fetchCompanyData(); // Refresh company data
      setLogoData({ file: null, preview: null }); // Clear the form
    } catch (err: any) {
      toast.error(formatApiError(err));
    } finally {
      setLogoLoading(false);
    }
  };

  const removeLogo = async () => {
    setLogoLoading(true);
    try {
      await companyAPI.deleteLogo(companyId);
      toast.success('Logo deleted successfully');
      fetchCompanyData(); // Refresh company data
    } catch (err: any) {
      toast.error(formatApiError(err));
    } finally {
      setLogoLoading(false);
    }
  };

  const cancelLogoUpload = () => {
    setLogoData({ file: null, preview: null });
  };

  const handleSave = async () => {
    const isValid = await form.trigger();
    if (!isValid) return;

    setSaveLoading(true);
    try {
      const formData = form.getValues();
      const validUrls = formData.websiteUrls.filter(url => url.trim() && url.includes('.'));
      
      const updateData = {
        name: formData.name,
        description: formData.description || undefined,
        address: formData.address || undefined,
        phone: formData.phone || undefined,
        industry: formData.industry || undefined,
        website_urls: validUrls,
      };

      const updatedCompany = await companyAPI.updateCompany(companyId, updateData);
      setCompany(updatedCompany);
      toast.success('Company updated successfully');
      
      // Navigate back to company details
      router.push(`/dashboard/companies/${companyId}`);
    } catch (err: any) {
      toast.error(formatApiError(err));
    } finally {
      setSaveLoading(false);
    }
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
                asChild
              >
                <Link href={`/dashboard/companies/${companyId}`}>
                  <ArrowLeft className="w-4 h-4" />
                  Back to Company
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Edit {company.name}</h1>
              <p className="text-gray-600 mt-1">
                Update your company information, logo, and knowledge base files
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <Button 
                variant="outline" 
                onClick={() => router.push(`/dashboard/companies/${companyId}`)}
              >
                <X className="w-4 h-4" />
                Cancel
              </Button>
              <Button 
                onClick={handleSave} 
                disabled={saveLoading}
              >
                <Save className="w-4 h-4" />
                {saveLoading ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            <CompanyInfoCard
              form={form}
              editMode={true}
              industryOptions={industryOptions}
              handleWebsiteUrlChange={handleWebsiteUrlChange}
              addWebsiteUrl={addWebsiteUrl}
              removeWebsiteUrl={removeWebsiteUrl}
            />

            <KnowledgeBaseFilesCard
              files={files}
              fileLoading={fileLoading}
              handleFileChange={handleFileChange}
              deleteFile={deleteFile}
            />
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <CompanyLogoCard
              company={company}
              logoData={logoData}
              logoLoading={logoLoading}
              handleLogoChange={handleLogoChange}
              uploadLogo={uploadLogo}
              removeLogo={removeLogo}
              cancelLogoUpload={cancelLogoUpload}
            />

            {/* Quick Tips Card */}
            <Card className="border-0 shadow-xl">
              <CardHeader>
                <CardTitle className="text-lg font-bold flex items-center">
                  <FileText className="w-5 h-5 mr-2 text-blue-600" />
                  Editing Tips
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm text-gray-600">
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                    <p>Make sure your company name and website URLs are accurate</p>
                  </div>
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                    <p>Upload a square logo for best results (PNG, JPG, or WebP)</p>
                  </div>
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                    <p>Knowledge base files help train your AI chatbot</p>
                  </div>
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                    <p>Changes are saved automatically when you click "Save Changes"</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
