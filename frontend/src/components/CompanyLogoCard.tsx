'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Image, Upload, X } from 'lucide-react';

interface Company {
  id: number;
  name: string;
  logo_url?: string;
}

interface LogoData {
  file: File | null;
  preview: string | null;
}

interface CompanyLogoCardProps {
  company: Company;
  logoData: LogoData;
  logoLoading: boolean;
  handleLogoChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  uploadLogo: () => void;
  removeLogo: () => void;
  cancelLogoUpload: () => void;
}

export function CompanyLogoCard({
  company,
  logoData,
  logoLoading,
  handleLogoChange,
  uploadLogo,
  removeLogo,
  cancelLogoUpload
}: CompanyLogoCardProps) {
  return (
    <Card className="border-0 shadow-xl">
      <CardHeader>
        <CardTitle className="text-lg font-bold">Company Logo</CardTitle>
        <CardDescription>
          Upload a logo for your company
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {company.logo_url ? (
            <div className="text-center">
              <div className="relative inline-block">
                <img
                  src={company.logo_url}
                  alt={`${company.name} logo`}
                  className="w-24 h-24 object-cover rounded-lg border mx-auto"
                />
                <button
                  onClick={removeLogo}
                  disabled={logoLoading}
                  className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors disabled:opacity-50"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2">Current logo</p>
            </div>
          ) : (
            <div className="text-center">
              <div className="w-24 h-24 bg-gray-100 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center mx-auto mb-2">
                <Image className="w-8 h-8 text-gray-400" />
              </div>
              <p className="text-xs text-gray-500">No logo uploaded</p>
            </div>
          )}

          {logoData.preview ? (
            <div className="space-y-3">
              <div className="text-center">
                <img
                  src={logoData.preview}
                  alt="Logo preview"
                  className="w-20 h-20 object-cover rounded-lg border mx-auto"
                />
                <p className="text-xs text-gray-500 mt-1">New logo preview</p>
              </div>
              <div className="flex space-x-2">
                <Button
                  size="sm"
                  onClick={uploadLogo}
                  disabled={logoLoading}
                  className="flex-1"
                >
                  {logoLoading ? 'Uploading...' : 'Upload'}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={cancelLogoUpload}
                  disabled={logoLoading}
                >
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-gray-400 transition-colors">
              <input
                type="file"
                accept="image/*"
                onChange={handleLogoChange}
                className="hidden"
                id="logo-upload-edit"
                disabled={logoLoading}
              />
              <label htmlFor="logo-upload-edit" className={`cursor-pointer ${logoLoading ? 'opacity-50 cursor-not-allowed' : ''}`}>
                <Upload className="w-6 h-6 mx-auto mb-2 text-gray-400" />
                <p className="text-sm text-gray-600 mb-1">
                  Upload new logo
                </p>
                <p className="text-xs text-gray-500">
                  Square images work best (max 5MB)
                </p>
              </label>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
