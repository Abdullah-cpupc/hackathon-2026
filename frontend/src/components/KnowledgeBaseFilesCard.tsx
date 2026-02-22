'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Upload, FileText, Trash2 } from 'lucide-react';

interface CompanyFile {
  id: number;
  filename: string;
  file_path: string;
  description?: string;
  file_size: number;
  uploaded_at: string;
}

interface KnowledgeBaseFilesCardProps {
  files: CompanyFile[];
  fileLoading: boolean;
  handleFileChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  deleteFile: (fileId: number) => void;
}

export function KnowledgeBaseFilesCard({
  files,
  fileLoading,
  handleFileChange,
  deleteFile
}: KnowledgeBaseFilesCardProps) {
  return (
    <Card className="border-0 shadow-xl">
      <CardHeader>
        <CardTitle className="text-xl font-bold">Knowledge Base Files</CardTitle>
        <CardDescription>
          Upload documents to train your AI chatbot
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-gray-400 transition-colors">
            <input
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.csv,.json"
              onChange={handleFileChange}
              className="hidden"
              id="file-upload"
              disabled={fileLoading}
            />
            <label htmlFor="file-upload" className={`cursor-pointer ${fileLoading ? 'opacity-50 cursor-not-allowed' : ''}`}>
              <Upload className="w-6 h-6 mx-auto mb-2 text-gray-400" />
              <p className="text-sm text-gray-600 mb-1">
                Click to upload files or drag and drop
              </p>
              <p className="text-xs text-gray-500">
                PDF, DOC, DOCX, XLS, XLSX, TXT, CSV, JSON (max 10MB each)
              </p>
            </label>
          </div>

          {files.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium text-gray-900">Uploaded Files:</h4>
              {files.map((file) => (
                <div key={file.id} className="flex items-center space-x-2 p-2 bg-gray-50 rounded-lg">
                  <FileText className="w-4 h-4 text-gray-500" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{file.filename}</p>
                    <p className="text-xs text-gray-500">
                      {(file.file_size / 1024 / 1024).toFixed(1)}MB • {new Date(file.uploaded_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => deleteFile(file.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
