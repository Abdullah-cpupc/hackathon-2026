'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { X, Copy, Check, ExternalLink, Code, Globe, Smartphone, Monitor } from 'lucide-react';
import { toast } from 'sonner';

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

interface WidgetScriptModalProps {
  isOpen: boolean;
  onClose: () => void;
  widget: Widget | null;
}

export function WidgetScriptModal({ isOpen, onClose, widget }: WidgetScriptModalProps) {
  const [copiedScript, setCopiedScript] = useState(false);
  const [copiedUrl, setCopiedUrl] = useState(false);

  if (!isOpen || !widget) return null;

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
  const scriptTag = `<script src="${apiBaseUrl}/widgets/${widget.widget_id}/script.js?api_key=${widget.api_key}"></script>`;
  const scriptUrl = `${apiBaseUrl}/widgets/${widget.widget_id}/script.js?api_key=${widget.api_key}`;

  const copyScript = async () => {
    try {
      await navigator.clipboard.writeText(scriptTag);
      setCopiedScript(true);
      toast.success('Script tag copied to clipboard!');
      setTimeout(() => setCopiedScript(false), 2000);
    } catch (err) {
      toast.error('Failed to copy script');
    }
  };

  const copyUrl = async () => {
    try {
      await navigator.clipboard.writeText(scriptUrl);
      setCopiedUrl(true);
      toast.success('Script URL copied to clipboard!');
      setTimeout(() => setCopiedUrl(false), 2000);
    } catch (err) {
      toast.error('Failed to copy URL');
    }
  };

  const testWidget = () => {
    window.open(`/test_widget.html?widget=${widget.widget_id}`, '_blank');
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-4xl max-h-[90vh] overflow-hidden border-0 shadow-xl">
        <CardHeader className="">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl font-bold">Widget Installation</CardTitle>
              <CardDescription>
                Get the script tag for "{widget.name}" widget
              </CardDescription>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </Button>
          </div>
        </CardHeader>

        <CardContent className="space-y-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {/* Widget Status */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <div 
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: widget.minimized_bg_color }}
              />
              <div>
                <h3 className="font-medium">{widget.name}</h3>
                <p className="text-sm text-gray-600">Widget ID: {widget.widget_id}</p>
              </div>
            </div>
            <Badge variant={widget.is_active ? "default" : "secondary"}>
              {widget.is_active ? "Active" : "Inactive"}
            </Badge>
          </div>

          {/* API Key */}
          {widget.api_key && (
            <div className="space-y-3">
              <h3 className="text-lg font-semibold flex items-center space-x-2">
                <Code className="w-5 h-5" />
                <span>API Key</span>
              </h3>
              <div className="relative">
                <input
                  type="text"
                  value={widget.api_key}
                  readOnly
                  className="w-full p-3 bg-gray-100 border rounded-lg text-sm font-mono"
                />
              </div>
              <p className="text-xs text-gray-600">
                This API key is required for the widget to function. Keep it secure and don't share it publicly.
              </p>
            </div>
          )}

          {/* Allowed Domains */}
          {widget.allowed_domains && widget.allowed_domains.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-lg font-semibold flex items-center space-x-2">
                <Globe className="w-5 h-5" />
                <span>Allowed Domains</span>
              </h3>
              <div className="space-y-2">
                {widget.allowed_domains.map((domain, index) => (
                  <div key={index} className="p-2 bg-gray-100 rounded text-sm font-mono">
                    {domain}
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-600">
                The widget can only be used on these domains for security.
              </p>
            </div>
          )}

          {/* Script Tag */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold flex items-center space-x-2">
                <Code className="w-5 h-5" />
                <span>Script Tag</span>
              </h3>
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={copyScript}
                  className="flex items-center space-x-2"
                >
                  {copiedScript ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  <span>{copiedScript ? 'Copied!' : 'Copy'}</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={testWidget}
                  className="flex items-center space-x-2"
                >
                  <ExternalLink className="w-4 h-4" />
                  <span>Test</span>
                </Button>
              </div>
            </div>
            
            <div className="relative">
              <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
                <code>{scriptTag}</code>
              </pre>
            </div>
          </div>

          {/* Script URL */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold flex items-center space-x-2">
                <Globe className="w-5 h-5" />
                <span>Direct URL</span>
              </h3>
              <Button
                variant="outline"
                size="sm"
                onClick={copyUrl}
                className="flex items-center space-x-2"
              >
                {copiedUrl ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                <span>{copiedUrl ? 'Copied!' : 'Copy URL'}</span>
              </Button>
            </div>
            
            <div className="relative">
              <input
                type="text"
                value={scriptUrl}
                readOnly
                className="w-full p-3 bg-gray-100 border rounded-lg text-sm font-mono"
              />
            </div>
          </div>

          {/* Installation Instructions */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold flex items-center space-x-2">
              <Monitor className="w-5 h-5" />
              <span>Installation Instructions</span>
            </h3>

            <div className="space-y-4">
              <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">Method 1: HTML Script Tag</h4>
                <ol className="list-decimal list-inside space-y-2 text-sm text-gray-700">
                  <li>Copy the script tag above</li>
                  <li>Paste it before the closing <code className="bg-gray-200 px-1 rounded">&lt;/body&gt;</code> tag in your HTML</li>
                  <li>Save and publish your website</li>
                  <li>The chat widget will appear automatically</li>
                </ol>
              </div>

              <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">Method 2: Content Management Systems</h4>
                <div className="space-y-3 text-sm text-gray-700">
                  <div>
                    <strong>WordPress:</strong> Add the script tag to your theme's footer.php file or use a plugin like "Insert Headers and Footers"
                  </div>
                  <div>
                    <strong>Shopify:</strong> Add the script to your theme.liquid file in the <code className="bg-gray-200 px-1 rounded">&lt;/body&gt;</code> section
                  </div>
                  <div>
                    <strong>Squarespace:</strong> Use Code Injection in Settings → Advanced → Code Injection → Footer
                  </div>
                  <div>
                    <strong>Wix:</strong> Add an HTML element and paste the script tag
                  </div>
                </div>
              </div>

              <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">Method 3: Dynamic Loading</h4>
                <div className="space-y-2 text-sm text-gray-700">
                  <p>For dynamic websites or SPAs, you can load the widget programmatically:</p>
                  <pre className="bg-gray-100 p-3 rounded text-xs overflow-x-auto border">
                    <code>{`const script = document.createElement('script');
script.src = '${scriptUrl}';
document.body.appendChild(script);`}</code>
                  </pre>
                </div>
              </div>
            </div>
          </div>

          {/* Widget Features */}
          {/* <div className="space-y-4">
            <h3 className="text-lg font-semibold flex items-center space-x-2">
              <Smartphone className="w-5 h-5" />
              <span>Widget Features</span>
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-sm mb-2">Position</h4>
                <p className="text-sm text-gray-600 capitalize">{widget.position.replace('-', ' ')}</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-sm mb-2">Shape</h4>
                <p className="text-sm text-gray-600 capitalize">{widget.minimized_shape}</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-sm mb-2">Background Color</h4>
                <div className="flex items-center space-x-2">
                  <div 
                    className="w-4 h-4 rounded border"
                    style={{ backgroundColor: widget.minimized_bg_color }}
                  />
                  <span className="text-sm text-gray-600 font-mono">{widget.minimized_bg_color}</span>
                </div>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-sm mb-2">Style</h4>
                <p className="text-sm text-gray-600 capitalize">{widget.maximized_style}</p>
              </div>
            </div>
          </div> */}

          {/* Important Notes */}
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <h4 className="font-semibold text-gray-900 mb-2">Important Notes</h4>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
              <li>The widget must be active to appear on websites</li>
              <li>Changes to widget settings take effect immediately</li>
              <li>The widget is responsive and works on all devices</li>
              <li>No additional CSS or JavaScript files are required</li>
              <li>The widget automatically handles cross-origin requests</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
