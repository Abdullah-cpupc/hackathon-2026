'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MessageCircle, Eye, EyeOff, Copy, Trash2, Edit } from 'lucide-react';

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

interface ChatWidgetsCardProps {
  companyId: number;
  widgets: Widget[];
  widgetsLoading: boolean;
  toggleWidget: (widgetId: string) => void;
  copyWidgetScript: (widget: Widget) => void;
  openScriptModal: (widget: Widget) => void;
  deleteWidget: (widgetId: string) => void;
}

export function ChatWidgetsCard({
  companyId,
  widgets,
  widgetsLoading,
  toggleWidget,
  copyWidgetScript,
  openScriptModal,
  deleteWidget
}: ChatWidgetsCardProps) {
  return (
    <Card className="border-0 shadow-xl">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-xl font-bold">Chat Widgets</CardTitle>
            <CardDescription>
              Manage your website chat widgets
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {widgets.length === 0 ? (
            <div className="text-center py-6">
              <MessageCircle className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-500 mb-3">No widgets created yet</p>
              <Button asChild size="sm" variant="outline">
                <Link href={`/dashboard/companies/${companyId}/widgets/create`}>
                  Create Your First Widget
                </Link>
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {widgets.map((widget) => (
                <div key={widget.id} className="p-3 border rounded-lg bg-gray-50 items-center">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-medium text-gray-900">{widget.name}</h4>
                      <Badge variant={widget.is_active ? "default" : "secondary"}>
                        {widget.is_active ? "Active" : "Inactive"}
                      </Badge>
                      <Badge variant="outline">
                        {new Date(widget.created_at).toLocaleDateString()}
                      </Badge>
                    </div>
                            <div className="flex items-center space-x-1">
                              <button
                                onClick={() => toggleWidget(widget.widget_id)}
                                disabled={widgetsLoading}
                                className="p-1 hover:bg-gray-200 rounded transition-colors"
                                title={widget.is_active ? "Deactivate" : "Activate"}
                              >
                                {widget.is_active ? (
                                  <Eye className="w-4 h-4 text-green-600" />
                                ) : (
                                  <EyeOff className="w-4 h-4 text-gray-400" />
                                )}
                              </button>
                              <Link
                                href={`/dashboard/companies/${companyId}/widgets/${widget.widget_id}/edit`}
                                className="p-1 hover:bg-gray-200 rounded transition-colors"
                                title="Edit widget"
                              >
                                <Edit className="w-4 h-4 text-blue-600" />
                              </Link>
                              <button
                                onClick={() => openScriptModal(widget)}
                                className="p-1 hover:bg-gray-200 rounded transition-colors"
                                title="Get widget script"
                              >
                                <Copy className="w-4 h-4 text-blue-600" />
                              </button>
                              <button
                                onClick={() => deleteWidget(widget.widget_id)}
                                disabled={widgetsLoading}
                                className="p-1 hover:bg-red-100 rounded transition-colors"
                                title="Delete widget"
                              >
                                <Trash2 className="w-4 h-4 text-red-600" />
                              </button>
                            </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
