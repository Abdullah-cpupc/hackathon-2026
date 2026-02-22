'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { FileText, Bot, Globe, Calendar, Clock, Zap } from 'lucide-react';

interface Company {
  created_at: string;
  updated_at: string;
  website_urls: string[];
}

interface CompanyFile {
  id: number;
  file_size: number;
}

interface Widget {
  id: number;
  is_active: boolean;
}

interface QuickStatsCardProps {
  company: Company;
  files: CompanyFile[];
  widgets: Widget[];
}

export function QuickStatsCard({ company, files, widgets }: QuickStatsCardProps) {
  const activeWidgets = widgets.filter(w => w.is_active).length;
  const totalFileSize = files.reduce((sum, file) => sum + file.file_size, 0);
  const fileSizeInMB = (totalFileSize / (1024 * 1024)).toFixed(1);

  return (
    <Card className="border-0 shadow-xl">
      <CardHeader>
        <CardTitle className="text-lg font-bold">Quick Stats</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Files Uploaded */}
          <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <FileText className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500">Files</p>
              <p className="text-lg font-bold text-gray-900">{files.length}</p>
              <p className="text-xs text-gray-500">{fileSizeInMB}MB</p>
            </div>
          </div>

          {/* Total Widgets */}
          <div className="flex items-center space-x-3 p-3 bg-purple-50 rounded-lg">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <Bot className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500">Total Widgets</p>
              <p className="text-lg font-bold text-gray-900">{widgets.length}</p>
              <p className="text-xs text-gray-500">Created</p>
            </div>
          </div>

          {/* Active Widgets */}
          <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500">Active</p>
              <p className="text-lg font-bold text-gray-900">{activeWidgets}</p>
              <p className="text-xs text-gray-500">Widgets</p>
            </div>
          </div>

          {/* Website URLs */}
          <div className="flex items-center space-x-3 p-3 bg-orange-50 rounded-lg">
            <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
              <Globe className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500">Websites</p>
              <p className="text-lg font-bold text-gray-900">{company.website_urls.length}</p>
              <p className="text-xs text-gray-500">Connected</p>
            </div>
          </div>

          {/* Created Date */}
          <div className="flex items-center space-x-3 p-3 bg-indigo-50 rounded-lg">
            <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
              <Calendar className="w-5 h-5 text-indigo-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500">Created</p>
              <p className="text-sm font-semibold text-gray-900">
                {new Date(company.created_at).toLocaleDateString('en-US', { 
                  month: 'short', 
                  day: 'numeric',
                  year: 'numeric'
                })}
              </p>
            </div>
          </div>

          {/* Last Updated */}
          <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
            <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
              <Clock className="w-5 h-5 text-gray-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500">Updated</p>
              <p className="text-sm font-semibold text-gray-900">
                {new Date(company.updated_at).toLocaleDateString('en-US', { 
                  month: 'short', 
                  day: 'numeric',
                  year: 'numeric'
                })}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
