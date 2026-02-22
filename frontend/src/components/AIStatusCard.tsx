import React from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Bot, Zap, RefreshCw, Trash2, MessageCircle, Clock, CheckCircle, XCircle, File } from 'lucide-react';

interface AIBuildProgress {
  current_step?: string;
  message?: string;
  details?: {
    current_url?: string;
    url_index?: number;
    total_urls?: number;
    pages_scraped?: number;
    chunks_processed?: number;
    documents_added?: number;
    step?: string;
    [key: string]: any;
  };
  timestamp?: string;
}

interface AIStatus {
  company_id: number;
  ai_enabled: boolean;
  ai_build_status?: string;
  collection_name?: string;
  last_scraped_at?: string;
  document_count: number;
  error_message?: string;
  progress?: AIBuildProgress;
}

interface AIStatusCardProps {
  aiStatus: AIStatus | null;
  aiBuilding: boolean;
  onBuildAI: () => void;
  onScrapeWebsite: () => void;
  onDisableAI: () => void;
  onChatWithAI: () => void;
  companyId: number;
}

export function AIStatusCard({
  aiStatus,
  aiBuilding,
  onBuildAI,
  onScrapeWebsite,
  onDisableAI,
  onChatWithAI,
  companyId,
}: AIStatusCardProps) {
  const router = useRouter();

  const handleChatWithAI = () => {
    // Redirect to chat preview page instead of opening modal
    router.push(`/dashboard/companies/${companyId}/chat-preview`);
  };

  const getStatusBadge = () => {
    if (!aiStatus) {
      return (
        <Badge variant="secondary" className="bg-gray-100 text-gray-600">
          <Clock className="w-3 h-3 mr-1" />
          Not Built
        </Badge>
      );
    }

    switch (aiStatus.ai_build_status) {
      case 'not_started':
        return (
          <Badge variant="secondary" className="bg-gray-100 text-gray-600">
            <Clock className="w-3 h-3 mr-1" />
            Not Started
          </Badge>
        );
      case 'building':
        return (
          <Badge variant="default" className="bg-blue-100 text-blue-600">
            <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
            Building
          </Badge>
        );
      case 'ready':
        return (
          <Badge variant="default" className="bg-green-100 text-green-600">
            <CheckCircle className="w-3 h-3 mr-1" />
            Ready
          </Badge>
        );
      case 'failed':
        return (
          <Badge variant="destructive" className="bg-red-100 text-red-600">
            <XCircle className="w-3 h-3 mr-1" />
            Failed
          </Badge>
        );
      default:
        return (
          <Badge variant="secondary" className="bg-gray-100 text-gray-600">
            <Clock className="w-3 h-3 mr-1" />
            Unknown
          </Badge>
        );
    }
  };

  const getStatusDescription = () => {
    if (!aiStatus) return 'AI has not been built for this company yet.';

    switch (aiStatus.ai_build_status) {
      case 'not_started':
        return 'AI has not been built for this company yet. Click "Build AI" to get started.';
      case 'building':
        return 'AI is currently being built. This may take a few minutes...';
      case 'ready':
        return `AI is ready and has ${aiStatus.document_count} documents in its knowledge base.`;
      case 'failed':
        return `AI build failed: ${aiStatus.error_message || 'Unknown error'}`;
      default:
        return 'AI status is unknown.';
    }
  };

  const canBuildAI = !aiBuilding && (!aiStatus || aiStatus.ai_build_status !== 'building' && aiStatus.ai_build_status !== 'ready');
  const canScrapeWebsite = aiStatus?.ai_build_status === 'ready' && !aiBuilding;
  const canDisableAI = aiStatus?.ai_enabled && aiStatus?.ai_build_status === 'ready';
  const canChatWithAI = aiStatus?.ai_build_status === 'ready';

  return (
    <Card className="border-0 shadow-xl">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-xl font-bold flex items-center">
              <Bot className="w-5 h-5 text-purple-600" />
              AI Assistant
            </CardTitle>
            <CardDescription>
              Manage your company's AI knowledge base and chat capabilities
            </CardDescription>
          </div>
          <div className="flex-shrink-0">
            {getStatusBadge()}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Status Description */}
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">{getStatusDescription()}</p>
          </div>

          {/* AI Stats */}
          {aiStatus && (
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center space-x-2">
                <File className="w-4 h-4 text-blue-600" />
                <span className="text-gray-600">Documents:</span>
                <span className="font-medium">{aiStatus.document_count}</span>
              </div>
              {aiStatus.last_scraped_at && (
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-blue-600" />
                  <span className="text-gray-600">Last Updated:</span>
                  <span className="font-medium">
                    {new Date(aiStatus.last_scraped_at).toLocaleDateString('en-US', { 
                      month: 'short', 
                      day: 'numeric',
                      year: 'numeric'
                    })}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <div className="space-y-2">
            {canBuildAI && (
              <Button
              onClick={onBuildAI}
              disabled={!canBuildAI}
              className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white border-0"
            >
              <Zap className="w-4 h-4" />
              {aiBuilding ? 'Building...' : 'Build AI'}
            </Button>
            )}
            {(canScrapeWebsite || canChatWithAI || canDisableAI) && (
              <div className="flex flex-wrap gap-2">
                {canScrapeWebsite && (
                  <Button
                    onClick={onScrapeWebsite}
                    variant="outline"
                    size="sm"
                    className="border-blue-200 text-blue-600 hover:bg-blue-50"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Re-scrape
                  </Button>
                )}

                {canChatWithAI && (
                  <Button
                    onClick={handleChatWithAI}
                    variant="outline"
                    size="sm"
                    className="border-green-200 text-green-600 hover:bg-green-50"
                  >
                    <MessageCircle className="w-4 h-4" />
                    Preview Chat
                  </Button>
                )}

                {canDisableAI && (
                  <Button
                    onClick={onDisableAI}
                    variant="destructive"
                    size="sm"
                    className="bg-red-50 text-red-600 hover:bg-red-100 border-red-200"
                  >
                    <Trash2 className="w-4 h-4" />
                    Disable
                  </Button>
                )}
              </div>
            )}
          </div>

          {/* Error Message */}
          {aiStatus?.error_message && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">
                <strong>Error:</strong> {aiStatus.error_message}
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
