'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { companyAPI } from '@/lib/api';
import { formatApiError } from '@/lib/errorUtils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { 
  ArrowLeft, 
  ArrowRight, 
  Building2, 
  MapPin, 
  Mail, 
  Phone, 
  Globe, 
  Upload, 
  FileText,
  Check,
  Bot,
  Image,
  X
} from 'lucide-react';

// Zod schema for form validation
const companyFormSchema = z.object({
  name: z.string().min(1, 'Company name is required'),
  description: z.string().optional(),
  address: z.string().optional(),
  contactEmail: z.string().email('Please enter a valid email address'),
  phone: z.string().optional(),
  industry: z.string().optional(),
  websiteUrls: z.array(z.string().url('Please enter a valid URL')).min(1, 'At least one website URL is required'),
});

type CompanyFormData = z.infer<typeof companyFormSchema>;

interface Step2Data {
  files: File[];
  descriptions: { [key: string]: string };
}

interface LogoData {
  file: File | null;
  preview: string | null;
}

export default function CreateCompanyPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [step2Data, setStep2Data] = useState<Step2Data>({
    files: [],
    descriptions: {},
  });
  const [logoData, setLogoData] = useState<LogoData>({
    file: null,
    preview: null,
  });

  const form = useForm<CompanyFormData>({
    resolver: zodResolver(companyFormSchema),
    defaultValues: {
      name: '',
      description: '',
      address: '',
      contactEmail: '',
      phone: '',
      industry: '',
      websiteUrls: [''],
    },
  });

  // Redirect if not authenticated
  if (!isAuthenticated) {
    router.push('/auth/login');
    return null;
  }

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
      setStep2Data(prev => ({
        ...prev,
        files: [...prev.files, ...validFiles]
      }));
      toast.success(`${validFiles.length} file(s) uploaded successfully`);
    }
  };

  const removeFile = (index: number) => {
    setStep2Data(prev => ({
      ...prev,
      files: prev.files.filter((_, i) => i !== index)
    }));
  };

  const handleFileDescriptionChange = (fileIndex: number, description: string) => {
    setStep2Data(prev => ({
      ...prev,
      descriptions: {
        ...prev.descriptions,
        [fileIndex]: description
      }
    }));
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

  const removeLogo = () => {
    setLogoData({
      file: null,
      preview: null,
    });
  };

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

  const handleNextStep = async () => {
    if (currentStep === 1) {
      const isValid = await form.trigger(['name', 'contactEmail']);
      if (isValid) {
        setCurrentStep(2);
      }
    }
  };

  const handlePrevStep = () => {
    setCurrentStep(1);
  };

  const handleSubmit = async () => {
    const isValid = await form.trigger(['websiteUrls']);
    if (!isValid) return;

    setLoading(true);

    try {
      const formData = form.getValues();
      
      // Create company with basic info and website URLs
      const validUrls = formData.websiteUrls.filter(url => url.trim() && url.includes('.'));
      const companyData = {
        name: formData.name,
        address: formData.address || undefined,
        phone: formData.phone || undefined,
        website_urls: validUrls,
        description: formData.description || `Contact: ${formData.contactEmail}${formData.phone ? ` | Phone: ${formData.phone}` : ''}`,
        industry: formData.industry || undefined
      };

      const company = await companyAPI.createCompany(companyData);

      // Upload logo if provided
      if (logoData.file) {
        await companyAPI.uploadLogo(company.id, logoData.file);
      }

      // Upload files if any
      if (step2Data.files.length > 0) {
        for (let i = 0; i < step2Data.files.length; i++) {
          const file = step2Data.files[i];
          const description = step2Data.descriptions[i] || `${file.name} - Knowledge base document`;
          await companyAPI.uploadFile(company.id, file, description);
        }
      }

      toast.success('Company created successfully!');
      setSuccess(true);
      setTimeout(() => {
        router.push('/dashboard');
      }, 2000);
    } catch (err: any) {
      toast.error(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md border-0 shadow-xl">
          <CardContent className="p-8 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Check className="w-8 h-8 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Company Created!</h2>
            <p className="text-gray-600 mb-6">
              Your company "{form.getValues('name')}" has been successfully created and is ready for AI chatbot setup.
            </p>
            <Button 
              onClick={() => router.push('/dashboard')}
            >
              Go to Dashboard
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
      </nav>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Progress Indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-center space-x-4">
            <div className={`flex items-center space-x-2 ${currentStep >= 1 ? 'text-blue-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${currentStep >= 1 ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>
                1
              </div>
              <span className="font-medium">Basic Info</span>
            </div>
            <div className={`w-16 h-1 ${currentStep >= 2 ? 'bg-blue-600' : 'bg-gray-200'}`}></div>
            <div className={`flex items-center space-x-2 ${currentStep >= 2 ? 'text-blue-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${currentStep >= 2 ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>
                2
              </div>
              <span className="font-medium">Knowledge Base</span>
            </div>
          </div>
        </div>

        <Card className="border-0 shadow-xl">
          <CardHeader>
            <CardTitle className="text-2xl font-bold text-center">
              {currentStep === 1 ? 'Company Information' : 'AI Knowledge Base'}
            </CardTitle>
            <CardDescription className="text-center">
              {currentStep === 1 
                ? 'Tell us about your company to get started' 
                : 'Add website and documents to train your AI chatbot'
              }
            </CardDescription>
          </CardHeader>
          <CardContent className="p-8">
            <Form {...form}>
              {currentStep === 1 && (
                <div className="space-y-6">
                  <FormField
                    control={form.control}
                    name="name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="flex items-center space-x-2">
                          <Building2 className="w-4 h-4" />
                          <span>Company Name *</span>
                        </FormLabel>
                        <FormControl>
                          <Input
                            placeholder="Enter your company name"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="description"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="flex items-center space-x-2">
                          <FileText className="w-4 h-4" />
                          <span>Company Description</span>
                        </FormLabel>
                        <FormControl>
                          <Textarea
                            placeholder="Describe your company, what you do, and your services..."
                            rows={4}
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="address"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="flex items-center space-x-2">
                          <MapPin className="w-4 h-4" />
                          <span>Company Address</span>
                        </FormLabel>
                        <FormControl>
                          <Textarea
                            placeholder="Enter your company address"
                            rows={3}
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="contactEmail"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="flex items-center space-x-2">
                          <Mail className="w-4 h-4" />
                          <span>Contact Email *</span>
                        </FormLabel>
                        <FormControl>
                          <Input
                            type="email"
                            placeholder="Enter your contact email"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="phone"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="flex items-center space-x-2">
                          <Phone className="w-4 h-4" />
                          <span>Phone Number</span>
                        </FormLabel>
                        <FormControl>
                          <Input
                            type="tel"
                            placeholder="Enter your phone number"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="space-y-4">
                    <Label className="flex items-center space-x-2">
                      <Image className="w-4 h-4" />
                      <span>Company Logo (Optional)</span>
                    </Label>
                    
                    {logoData.preview ? (
                      <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
                        <div className="relative">
                          <img
                            src={logoData.preview}
                            alt="Logo preview"
                            className="w-20 h-20 object-cover rounded-lg border"
                          />
                          <button
                            type="button"
                            onClick={removeLogo}
                            className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">{logoData.file?.name}</p>
                          <p className="text-xs text-gray-500">
                            {(logoData.file?.size && (logoData.file.size / 1024 / 1024).toFixed(1))}MB
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handleLogoChange}
                          className="hidden"
                          id="logo-upload"
                        />
                        <label htmlFor="logo-upload" className="cursor-pointer">
                          <Image className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                          <p className="text-sm text-gray-600 mb-1">
                            Click to upload company logo
                          </p>
                          <p className="text-xs text-gray-500">
                            Square images work best (JPEG, PNG, GIF, WebP - max 5MB)
                          </p>
                        </label>
                      </div>
                    )}
                  </div>

                  <div className="flex justify-end pt-6">
                    <Button 
                      onClick={handleNextStep}
                    >
                      Next Step
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </div>
                </div>
              )}

              {currentStep === 2 && (
                <div className="space-y-6">
                  <FormField
                    control={form.control}
                    name="industry"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="flex items-center space-x-2">
                          <Building2 className="w-4 h-4" />
                          <span>Industry</span>
                        </FormLabel>
                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                          <FormControl>
                            <SelectTrigger className="w-full">
                              <SelectValue placeholder="Select an industry..." />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {industryOptions.map((industry) => (
                              <SelectItem key={industry} value={industry}>
                                {industry}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="websiteUrls"
                    render={({ field }) => (
                      <FormItem>
                        <div className="flex items-center justify-between">
                          <FormLabel className="flex items-center space-x-2">
                            <Globe className="w-4 h-4" />
                            <span>Website URLs *</span>
                          </FormLabel>
                          <Button 
                            type="button" 
                            variant="outline" 
                            size="sm"
                            onClick={addWebsiteUrl}
                          >
                            Add URL
                          </Button>
                        </div>
                        
                        {field.value.map((url, index) => (
                          <div key={index} className="flex items-center space-x-2">
                            <Input
                              value={url}
                              onChange={(e) => handleWebsiteUrlChange(index, e.target.value)}
                              placeholder="https://yourcompany.com"
                              type="url"
                            />
                            {field.value.length > 1 && (
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => removeWebsiteUrl(index)}
                              >
                                Remove
                              </Button>
                            )}
                          </div>
                        ))}
                        
                        <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-md">
                          <div className="flex items-start space-x-2">
                            <div className="w-5 h-5 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                              <span className="text-blue-600 text-xs font-bold">i</span>
                            </div>
                            <div className="text-sm text-blue-800">
                              <p className="font-medium mb-1">Sitemap Required</p>
                              <p className="text-blue-700">
                                Your website should have a valid sitemap (usually at <code className="bg-blue-100 px-1 rounded">/sitemap.xml</code>) 
                                to help our AI better understand your site structure and content.
                              </p>
                            </div>
                          </div>
                        </div>
                        
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                <div className="space-y-4">
                  <Label className="flex items-center space-x-2">
                    <Upload className="w-4 h-4" />
                    <span>Knowledge Base Files</span>
                  </Label>
                  
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
                    <input
                      type="file"
                      multiple
                      accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.csv,.json"
                      onChange={handleFileChange}
                      className="hidden"
                      id="file-upload"
                    />
                    <label htmlFor="file-upload" className="cursor-pointer">
                      <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                      <p className="text-sm text-gray-600 mb-1">
                        Click to upload files or drag and drop
                      </p>
                      <p className="text-xs text-gray-500">
                        PDF, DOC, DOCX, XLS, XLSX, TXT, CSV, JSON (max 10MB each)
                      </p>
                    </label>
                  </div>

                  {step2Data.files.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="font-medium text-gray-900">Uploaded Files:</h4>
                      {step2Data.files.map((file, index) => (
                        <div key={index} className="flex items-center space-x-2 p-2 bg-gray-50 rounded-lg">
                          <FileText className="w-4 h-4 text-gray-500" />
                          <span className="flex-1 text-sm">{file.name}</span>
                          <span className="text-xs text-gray-500">
                            {(file.size / 1024 / 1024).toFixed(1)}MB
                          </span>
                          <Input
                            placeholder="Description (optional)"
                            value={step2Data.descriptions[index] || ''}
                            onChange={(e) => handleFileDescriptionChange(index, e.target.value)}
                            className="w-48 text-sm"
                          />
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => removeFile(index)}
                          >
                            Remove
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex justify-between pt-6">
                  <Button 
                    variant="outline"
                    onClick={handlePrevStep}
                  >
                    <ArrowLeft className="w-4 h-4" />
                    Previous Step
                  </Button>
                  <Button 
                    onClick={handleSubmit}
                    disabled={loading}
                  >
                    {loading ? 'Creating Company...' : 'Create Company'}
                  </Button>
                </div>
                </div>
              )}
            </Form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
