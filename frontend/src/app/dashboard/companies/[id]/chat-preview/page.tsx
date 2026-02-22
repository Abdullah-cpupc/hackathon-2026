'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { companyAPI, widgetAPI, aiAPI } from '@/lib/api';
import { formatApiError } from '@/lib/errorUtils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import { 
  ArrowLeft, 
  Bot, 
  MessageCircle, 
  X, 
  ExternalLink,
  Globe,
  Settings,
  RefreshCw,
  Send,
  User,
  Loader2,
  Link as LinkIcon
} from 'lucide-react';

interface Company {
  id: number;
  name: string;
  website_urls: string[];
  description?: string;
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

interface AIStatus {
  company_id: number;
  ai_enabled: boolean;
  ai_build_status?: string;
  collection_name?: string;
  last_scraped_at?: string;
  document_count: number;
  error_message?: string;
}

export default function ChatPreviewPage() {
  const router = useRouter();
  const params = useParams();
  const { isAuthenticated } = useAuth();
  const companyId = parseInt(params.id as string);
  
  const [company, setCompany] = useState<Company | null>(null);
  const [widgets, setWidgets] = useState<Widget[]>([]);
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedWidget, setSelectedWidget] = useState<Widget | null>(null);
  const [messages, setMessages] = useState<Array<{id: string, role: 'user' | 'assistant', content: string, timestamp: Date}>>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  // Default widget styles
  const defaultWidget = {
    name: 'AI Assistant',
    position: 'bottom-right' as const,
    minimized_shape: 'circle' as const,
    minimized_bg_color: '#2563eb',
    maximized_style: 'solid' as const,
    system_bubble_bg_color: '#f3f4f6',
    user_bubble_bg_color: '#2563eb',
  };

  const currentWidget = selectedWidget || defaultWidget;

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login');
      return;
    }

    if (companyId) {
      fetchCompanyData();
      fetchWidgets();
      fetchAIStatus();
    }
  }, [isAuthenticated, companyId, router]);

  const fetchCompanyData = async () => {
    try {
      const companyData = await companyAPI.getCompany(companyId);
      setCompany(companyData);
      
      // Set preview URL
      const urls: string[] = companyData?.website_urls || [];
      if (urls.length > 0) {
        const raw = urls[0].trim();
        const normalized = /^https?:\/\//i.test(raw) ? raw : `https://${raw}`;
        setPreviewUrl(normalized);
      }
    } catch (err: any) {
      toast.error(formatApiError(err));
      router.push('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const fetchWidgets = async () => {
    try {
      const widgetsData = await widgetAPI.getCompanyWidgets(companyId);
      setWidgets(widgetsData);
      
      // Select the first active widget, or the first widget if none are active
      const activeWidget = widgetsData.find((w: Widget) => w.is_active) || widgetsData[0];
      if (activeWidget) {
        setSelectedWidget(activeWidget);
      }
    } catch (err: any) {
      console.error('Error fetching widgets:', err);
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

  const refreshPreview = () => {
    fetchCompanyData();
    fetchWidgets();
    fetchAIStatus();
  };

  const openScriptModal = () => {
    if (selectedWidget) {
      // Open the widget script modal from the company page
      router.push(`/dashboard/companies/${companyId}?showScriptModal=true&widgetId=${selectedWidget.widget_id}`);
    }
  };

  const testWidget = () => {
    if (selectedWidget) {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      window.open(`/test_widget.html?widget=${selectedWidget.widget_id}&api_key=${selectedWidget.api_key}`, '_blank');
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading || !canChat) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: inputMessage.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await aiAPI.chatWithAI(companyId, userMessage.content);

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: response.response,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: 'I apologize, but I encountered an error while processing your request. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Parse message content to extract sources and render as links
  const renderMessageContent = (content: string, role: 'user' | 'assistant') => {
    // Check if there's a Sources section (case-insensitive, handles "Source:" or "Sources:")
    const sourcesRegex = /Sources?:\s*([\s\S]+?)(?:\n\n|$)/i;
    const sourcesMatch = content.match(sourcesRegex);
    
    if (!sourcesMatch) {
      // No sources section, return content as-is
      return <p className="whitespace-pre-wrap">{content}</p>;
    }

    // Split content into main text and sources
    const sourcesIndex = content.toLowerCase().lastIndexOf('source');
    const mainContent = content.substring(0, sourcesIndex).trim();
    const sourcesText = sourcesMatch[1].trim();

    // Extract URLs and text from sources
    // Pattern: URLs (http/https) - more comprehensive, also handles domain-only references
    const urlPattern = /(https?:\/\/[^\s\)\]\>]+)/gi;
    const domainPattern = /([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}/g;
    
    // Process sources more intelligently
    // Split by lines and process sequentially, combining domain + path
    const lines = sourcesText.split(/\n/).map(s => s.trim()).filter(s => s.length > 0);
    const processedSources: Array<{ url: string; text: string }> = [];
    let pendingDomain: string | null = null;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Check if line contains a full URL
      const urlMatch = line.match(urlPattern);
      if (urlMatch) {
        // Complete URL found
        const url = urlMatch[0];
        const text = line.replace(urlPattern, '').trim();
        processedSources.push({ 
          url, 
          text: text || url 
        });
        pendingDomain = null;
        continue;
      }
      
      // Check if line is just a domain (e.g., gradschool.wsu.edu)
      const domainMatch = line.match(/^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$/);
      if (domainMatch) {
        pendingDomain = domainMatch[0];
        // Check if next line might be a path
        const nextLine = i + 1 < lines.length ? lines[i + 1] : '';
        // If next line looks like a path continuation, combine them
        if (nextLine && (nextLine.startsWith('/') || nextLine.match(/^[a-z0-9\-\/\s]+$/i))) {
          // Skip next line, we'll process it together
          continue;
        } else {
          // Just a domain, create URL
          processedSources.push({ 
            url: `https://${pendingDomain}`, 
            text: pendingDomain 
          });
          pendingDomain = null;
        }
        continue;
      }
      
      // Check if this line might be a path continuation of a pending domain
      if (pendingDomain && (line.startsWith('/') || line.match(/^[a-z0-9\-\/\s]+$/i))) {
        // Combine domain with path
        const path = line.replace(/^\s*and\s+/i, '').trim(); // Remove "and " prefix if present
        const fullUrl = `https://${pendingDomain}/${path.replace(/^\//, '')}`;
        processedSources.push({ 
          url: fullUrl, 
          text: `${pendingDomain}/${path}` 
        });
        pendingDomain = null;
        continue;
      }
      
      // If we have a pending domain but this doesn't look like a path, save the domain
      if (pendingDomain) {
        processedSources.push({ 
          url: `https://${pendingDomain}`, 
          text: pendingDomain 
        });
        pendingDomain = null;
      }
      
      // Standalone text (not a URL or domain)
      // Only add if it's meaningful (not just punctuation or very short)
      if (line.length > 2 && !line.match(/^[^\w]+$/)) {
        processedSources.push({ url: '', text: line });
      }
    }
    
    // Don't forget any pending domain
    if (pendingDomain) {
      processedSources.push({ 
        url: `https://${pendingDomain}`, 
        text: pendingDomain 
      });
    }

    return (
      <div>
        {mainContent && (
          <p className="whitespace-pre-wrap mb-3">{mainContent}</p>
        )}
        <div className="mt-3 pt-3 border-t" style={{ borderColor: role === 'user' ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.1)' }}>
          <p className="text-xs font-semibold mb-2" style={{ color: role === 'user' ? 'rgba(255,255,255,0.8)' : 'rgba(0,0,0,0.6)' }}>
            Sources:
          </p>
          <div className="space-y-1.5">
            {processedSources.map((source, index) => {
              if (source.url) {
                // Has a URL - make it a link
                let displayText = source.text;
                if (!displayText || displayText === source.url) {
                  try {
                    const urlObj = new URL(source.url);
                    displayText = urlObj.hostname + urlObj.pathname;
                  } catch {
                    displayText = source.url;
                  }
                }
                
                return (
                  <a
                    key={index}
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-xs hover:underline transition-colors break-all"
                    style={{ 
                      color: role === 'user' ? 'rgba(255,255,255,0.9)' : '#2563eb'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.opacity = '0.8';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.opacity = '1';
                    }}
                  >
                    <LinkIcon className="w-3 h-3 flex-shrink-0" />
                    <span className="truncate max-w-[250px]">{displayText}</span>
                    <ExternalLink className="w-3 h-3 opacity-60 flex-shrink-0" />
                  </a>
                );
              }
              
              // Plain text source (no URL found)
              return (
                <div 
                  key={index} 
                  className="text-xs"
                  style={{ color: role === 'user' ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.6)' }}
                >
                  {source.text}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  if (loading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 bg-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading chat preview...</p>
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

  const canChat = aiStatus?.ai_build_status === 'ready' && aiStatus?.ai_enabled;

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
                onClick={refreshPreview}
                className="text-gray-600 hover:text-gray-900"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </Button>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => router.push(`/dashboard/companies/${companyId}`)}
              >
              <ArrowLeft className="w-4 h-4" />
                Back to Company
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8 h-[calc(100vh-8rem)] overflow-x-hidden">
        <div className="h-full overflow-x-hidden">
          {/* Full-width Live Preview */}
          <div className="w-full h-full overflow-x-hidden">
            <Card className="border-0 shadow-xl h-full">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg font-bold">Live Chat Preview</CardTitle>
                    <CardDescription>
                      See how your chat widget will appear to customers
                    </CardDescription>
                  </div>
                  <div className="flex items-center space-x-2">
                    {canChat ? (
                      <Badge className="bg-green-100 text-green-600">
                        <Bot className="w-3 h-3 mr-1" />
                        AI Ready
                      </Badge>
                    ) : (
                      <Badge variant="secondary" className="bg-orange-100 text-orange-600">
                        <Bot className="w-3 h-3 mr-1" />
                        AI Not Ready
                      </Badge>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="h-full">
                <div className="relative h-full">
                  {previewUrl ? (
                    <iframe
                      src={previewUrl}
                      className="w-full h-full rounded-md border"
                      sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
                    />
                  ) : (
                    <div className="h-full bg-white border rounded-md flex items-center justify-center text-sm text-gray-500">
                      No website URL available to preview
                    </div>
                  )}
                  
                  {/* Overlay: chat widget trigger */}
                  {!isOpen && (
                    <button
                      type="button"
                      onClick={() => setIsOpen(true)}
                      className={`absolute bottom-4 ${
                        currentWidget.position === 'bottom-right' ? 'right-4' : 'left-4'
                      } ${
                        currentWidget.minimized_shape === 'circle' 
                          ? 'size-14 rounded-full' 
                          : 'h-14 px-4 rounded-full'
                      } text-white shadow-lg flex items-center justify-center transition-colors hover:opacity-90`}
                      style={{ backgroundColor: currentWidget.minimized_bg_color }}
                      aria-label="Open chat widget"
                    >
                      <MessageCircle className="size-6" />
                      {currentWidget.minimized_shape === 'pill' && (
                        <span className="ml-2 text-sm font-medium truncate max-w-[12rem]">
                          {currentWidget.name}
                        </span>
                      )}
                    </button>
                  )}

                  {/* Overlay: expanded chat window */}
                  {isOpen && (
                    <div className={`absolute bottom-4 ${
                      currentWidget.position === 'bottom-right' ? 'right-4' : 'left-4'
                    } w-[380px] max-w-[calc(100%-2rem)] h-[560px] max-h-[calc(100%-2rem)] border rounded-xl shadow-2xl flex flex-col overflow-hidden overflow-x-hidden min-w-0 ${
                      currentWidget.maximized_style === 'blurred' 
                        ? 'backdrop-blur-md bg-white/60' 
                        : 'bg-white'
                    }`}>
                      <div className={`flex items-center justify-between px-3 py-2 border-b ${
                        currentWidget.maximized_style === 'blurred' 
                          ? 'backdrop-blur-md bg-white/60' 
                          : 'bg-white'
                      }`}>
                        <div className="flex items-center gap-2">
                          <div className="size-6 rounded-full bg-blue-600 text-white flex items-center justify-center">
                            <Bot className="size-4" />
                          </div>
                          <span className="text-sm font-medium text-gray-900">
                            {currentWidget.name}
                          </span>
                          {canChat && (
                            <Badge className="bg-green-100 text-green-600 text-xs">
                              AI Ready
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            onClick={clearChat}
                            className="p-1 rounded-md hover:bg-gray-100 text-gray-500 hover:text-gray-700"
                            aria-label="Clear chat"
                            title="Clear chat"
                          >
                            <RefreshCw className="size-4" />
                          </button>
                          <button
                            type="button"
                            onClick={() => setIsOpen(false)}
                            className="p-1 rounded-md hover:bg-gray-100 text-gray-500 hover:text-gray-700"
                            aria-label="Close chat widget"
                          >
                            <X className="size-4" />
                          </button>
                        </div>
                      </div>
                      
                      <div className={`flex-1 overflow-hidden ${
                        currentWidget.maximized_style === 'blurred' 
                          ? 'backdrop-blur-md bg-white/10' 
                          : 'bg-white'
                      }`}>
                        {/* Chat messages area */}
                        <div className="h-full overflow-y-auto overflow-x-hidden p-3 space-y-2 scroll-smooth min-w-0">
                          {messages.length === 0 && (
                            <div className="flex items-start gap-2">
                              <div className="size-6 rounded-full bg-blue-600 text-white flex items-center justify-center shrink-0">
                                <Bot className="size-4" />
                              </div>
                              <div 
                                className="max-w-[80%] rounded-2xl rounded-tl-sm text-gray-900 px-3 py-2 text-sm" 
                                style={{ backgroundColor: currentWidget.system_bubble_bg_color }}
                              >
                                {canChat 
                                  ? "Hi! I'm your AI assistant. How can I help you today?" 
                                  : "Hello! I'm your chat assistant. Please configure AI to enable smart responses."
                                }
                              </div>
                            </div>
                          )}
                          
                          {messages.map((message) => (
                            <div
                              key={message.id}
                              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                              <div
                                className={`flex items-start gap-2 max-w-[80%] min-w-0 ${
                                  message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                                }`}
                              >
                                <div
                                  className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${
                                    message.role === 'user'
                                      ? 'bg-blue-600 text-white'
                                      : 'bg-blue-600 text-white'
                                  }`}
                                >
                                  {message.role === 'user' ? (
                                    <User className="w-3 h-3" />
                                  ) : (
                                    <Bot className="w-3 h-3" />
                                  )}
                                </div>
                                <div
                                  className={`rounded-2xl px-3 py-2 text-sm break-words min-w-0 ${
                                    message.role === 'user'
                                      ? 'rounded-tr-sm text-white'
                                      : 'rounded-tl-sm text-gray-900'
                                  }`}
                                  style={{ 
                                    backgroundColor: message.role === 'user' 
                                      ? currentWidget.user_bubble_bg_color 
                                      : currentWidget.system_bubble_bg_color 
                                  }}
                                >
                                  {message.role === 'assistant' 
                                    ? renderMessageContent(message.content, message.role)
                                    : <p className="whitespace-pre-wrap">{message.content}</p>
                                  }
                                  <p
                                    className={`text-xs mt-1 ${
                                      message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                                    }`}
                                  >
                                    {message.timestamp.toLocaleTimeString()}
                                  </p>
                                </div>
                              </div>
                            </div>
                          ))}
                          
                          {/* Loading indicator */}
                          {isLoading && (
                            <div className="flex justify-start">
                              <div className="flex items-start gap-2 max-w-[80%]">
                                <div className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center shrink-0">
                                  <Bot className="w-3 h-3" />
                                </div>
                                <div 
                                  className="rounded-2xl rounded-tl-sm px-3 py-2 text-sm" 
                                  style={{ backgroundColor: currentWidget.system_bubble_bg_color }}
                                >
                                  <div className="flex items-center space-x-2">
                                    <Loader2 className="w-3 h-3 animate-spin text-blue-600" />
                                    <span className="text-gray-600">AI is thinking...</span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}
                          <div ref={messagesEndRef} />
                        </div>
                      </div>
                      
                      <div className="border-t p-2">
                        <div className="flex items-center gap-2">
                          <Input
                            value={inputMessage}
                            onChange={(e) => setInputMessage(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder={canChat ? "Ask me anything..." : "Configure AI to enable smart responses"}
                            disabled={!canChat || isLoading}
                            className="flex-1 text-sm"
                          />
                          <Button
                            onClick={sendMessage}
                            disabled={!inputMessage.trim() || !canChat || isLoading}
                            size="sm"
                            className="bg-blue-600 hover:bg-blue-700 text-white"
                          >
                            <Send className="w-4 h-4" />
                          </Button>
                        </div>
                        {!canChat && (
                          <p className="text-xs text-orange-600 mt-1 px-1">
                            Build AI first to enable smart chat responses
                          </p>
                        )}
                        {canChat && (
                          <p className="text-xs text-gray-500 mt-1 px-1">
                            Press Enter to send, Shift+Enter for new line
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
