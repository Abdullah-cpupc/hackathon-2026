'use client'

import { useRouter, useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { BlockPicker } from 'react-color'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { Bot, ArrowLeft, MessageCircle, X, ArrowDownLeft, ArrowDownRight } from 'lucide-react'
import { companyAPI, widgetAPI } from '@/lib/api'

const widgetSchema = z.object({
  name: z.string().min(1, 'Widget name is required'),
  position: z.enum(['bottom-left', 'bottom-right']),
  minimizedShape: z.enum(['circle', 'pill']),
  minimizedBgColor: z.string().regex(/^#([0-9a-fA-F]{3}){1,2}$/i, 'Must be a valid hex color'),
  maximizedStyle: z.enum(['solid', 'blurred'])
  , systemBubbleBgColor: z.string().regex(/^#([0-9a-fA-F]{3}){1,2}$/i, 'Must be a valid hex color')
  , userBubbleBgColor: z.string().regex(/^#([0-9a-fA-F]{3}){1,2}$/i, 'Must be a valid hex color')
})

type WidgetForm = z.infer<typeof widgetSchema>

export default function CreateWidgetPage() {
  const router = useRouter()
  const params = useParams()
  const companyId = params.id as string
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  const form = useForm<WidgetForm>({
    resolver: zodResolver(widgetSchema),
    defaultValues: { name: '', position: 'bottom-right', minimizedShape: 'circle', minimizedBgColor: '#2563eb', maximizedStyle: 'solid', systemBubbleBgColor: '#f3f4f6', userBubbleBgColor: '#2563eb' },
  })
  const widgetName = form.watch('name') || 'ChatBot'
  const position = form.watch('position')
  const minimizedShape = form.watch('minimizedShape')
  const minimizedBgColor = form.watch('minimizedBgColor')
  const maximizedStyle = form.watch('maximizedStyle')
  const systemBubbleBgColor = form.watch('systemBubbleBgColor')
  const userBubbleBgColor = form.watch('userBubbleBgColor')

  const onSubmit = async (values: WidgetForm) => {
    setLoading(true)
    try {
      // Transform the form data to match the backend schema
      const widgetData = {
        name: values.name,
        position: values.position,
        minimized_shape: values.minimizedShape,
        minimized_bg_color: values.minimizedBgColor,
        maximized_style: values.maximizedStyle,
        system_bubble_bg_color: values.systemBubbleBgColor,
        user_bubble_bg_color: values.userBubbleBgColor,
        is_active: true
      }

      await widgetAPI.createWidget(parseInt(companyId), widgetData)
      
      // Redirect to company page with success message
      router.push(`/dashboard/companies/${companyId}?widgetCreated=true`)
    } catch (error) {
      console.error('Failed to create widget:', error)
      // You could add a toast notification here
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const fetchCompany = async () => {
      try {
        const company = await companyAPI.getCompany(parseInt(companyId as string))
        const urls: string[] = company?.website_urls || []
        if (urls.length > 0) {
          const raw = urls[0].trim()
          const normalized = /^https?:\/\//i.test(raw) ? raw : `https://${raw}`
          setPreviewUrl(normalized)
        }
      } catch (e) {
        setPreviewUrl(null)
      }
    }
    if (companyId) {
      fetchCompany()
    }
  }, [companyId])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
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
            <Button asChild variant="ghost" size="sm">
              <Link href={`/dashboard/companies/${companyId}`}>
                <ArrowLeft className="w-4 h-4" />
                Back to Company
              </Link>
            </Button>
          </div>
        </div>
      </nav>

      <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 items-stretch min-h-[calc(100vh-10rem)] lg:min-h-[calc(100vh-8rem)]">
          {/* Left: Configuration Form */}
          <div className="lg:col-span-1 flex flex-col min-h-0">
            <Card className="border-0 shadow-xl h-full flex flex-col min-h-0">
              <CardHeader>
                <CardTitle className="text-2xl font-bold">Create Chat Widget</CardTitle>
                <CardDescription>Configure your website chat widget.</CardDescription>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto">
                <Form {...form}>
                  <form id="widget-form" onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                    <Accordion type="multiple" defaultValue={["basic"]}>
                      <AccordionItem value="basic">
                        <AccordionTrigger>Basic</AccordionTrigger>
                        <AccordionContent>
                          <div className="space-y-4">
                            <FormField
                              control={form.control}
                              name="name"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Widget Name</FormLabel>
                                  <FormControl>
                                    <Input placeholder="e.g. Main Site Widget" {...field} />
                                  </FormControl>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                            <FormField
                              control={form.control}
                              name="minimizedShape"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Minimized Shape</FormLabel>
                                  <div className="flex items-center gap-2">
                                    <Button
                                      type="button"
                                      variant="ghost"
                                      onClick={() => field.onChange('circle')}
                                      className={minimizedShape === 'circle' ? 'bg-blue-50 text-blue-700' : ''}
                                    >
                                      Circle
                                    </Button>
                                    <Button
                                      type="button"
                                      variant="ghost"
                                      onClick={() => field.onChange('pill')}
                                      className={minimizedShape === 'pill' ? 'bg-blue-50 text-blue-700' : ''}
                                    >
                                      Pill
                                    </Button>
                                  </div>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                      <AccordionItem value="positioning">
                        <AccordionTrigger>Positioning</AccordionTrigger>
                        <AccordionContent>
                          <div className="space-y-4">
                            <FormField
                            control={form.control}
                            name="position"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Widget Position</FormLabel>
                                <div className="flex items-center gap-2">
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    onClick={() => field.onChange('bottom-left')}
                                    className={position === 'bottom-left' ? 'bg-blue-50 text-blue-700' : ''}
                                  >
                                    <ArrowDownLeft className="mr-2 h-4 w-4" />
                                    Bottom Left
                                  </Button>
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    onClick={() => field.onChange('bottom-right')}
                                    className={position === 'bottom-right' ? 'bg-blue-50 text-blue-700' : ''}
                                  >
                                    <ArrowDownRight className="mr-2 h-4 w-4" />
                                    Bottom Right
                                  </Button>
                                </div>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                      <AccordionItem value="styling">
                        <AccordionTrigger>Styling & Color</AccordionTrigger>
                        <AccordionContent>
                          <div className="space-y-4">
                            <FormField
                              control={form.control}
                              name="systemBubbleBgColor"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>System Bubble Color</FormLabel>
                                  <div className="flex items-center justify-left">
                                    <BlockPicker
                                      color={field.value}
                                      width="300px"
                                      triangle="hide"
                                      onChangeComplete={(color: { hex: string }) => field.onChange(color.hex)}
                                      colors={[
                                        '#F3F4F6', '#E5E7EB', '#D1D5DB', '#9CA3AF', '#6B7280',
                                        '#FFF7ED', '#FEF3C7', '#FFEDD5', '#E0F2FE', '#DCFCE7',
                                      ]}
                                    />
                                  </div>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />

                            <FormField
                              control={form.control}
                              name="userBubbleBgColor"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>User Bubble Color</FormLabel>
                                  <div className="flex items-center justify-left">
                                    <BlockPicker
                                      color={field.value}
                                      width="300px"
                                      triangle="hide"
                                      onChangeComplete={(color: { hex: string }) => field.onChange(color.hex)}
                                      colors={[
                                        '#2563EB', '#3B82F6', '#6366F1', '#8B5CF6', '#22C55E',
                                        '#EF4444', '#F59E0B', '#14B8A6', '#10B981', '#EC4899',
                                      ]}
                                    />
                                  </div>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                            <FormField
                            control={form.control}
                            name="maximizedStyle"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Maximized Style</FormLabel>
                                <div className="flex items-center gap-2">
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    onClick={() => field.onChange('solid')}
                                    className={maximizedStyle === 'solid' ? 'bg-blue-50 text-blue-700' : ''}
                                  >
                                    Solid Color
                                  </Button>
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    onClick={() => field.onChange('blurred')}
                                    className={maximizedStyle === 'blurred' ? 'bg-blue-50 text-blue-700' : ''}
                                  >
                                    Blurred Background
                                  </Button>
                                </div>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                            <FormField
                            control={form.control}
                            name="minimizedBgColor"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Minimized Background Color</FormLabel>
                                <div className="flex items-center justify-left">
                                  <BlockPicker
                                    color={field.value}
                                    width="300px"
                                    triangle="hide"
                                    onChangeComplete={(color: { hex: string }) => field.onChange(color.hex)}
                                    colors={[
                                      '#3B82F6', '#6366F1', '#8B5CF6',
                                      '#EC4899', '#14B8A6', '#22C55E', '#EAB308', '#F97316', '#DC2626',
                                    ]}
                                  />
                                </div>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    </Accordion>
                    {/* actions moved to CardFooter below */}
                  </form>
                </Form>
              </CardContent>
              <CardFooter className="justify-end border-t">
                <Button asChild variant="outline" className="mr-2">
                  <Link href={`/dashboard/companies/${companyId}`}>Cancel</Link>
                </Button>
                <Button type="submit" form="widget-form" disabled={loading}>
                  {loading ? 'Creating...' : 'Create Widget'}
                </Button>
              </CardFooter>
            </Card>
          </div>

          {/* Right: Live Preview */}
          <div className="lg:col-span-3 flex flex-col min-h-0">
            <Card className="border-0 shadow-xl h-full flex flex-col min-h-0">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Live Preview</CardTitle>
                <CardDescription>See changes as you configure.</CardDescription>
              </CardHeader>
              <CardContent className="flex-1 min-h-0 overflow-hidden">
                <div className="relative h-full min-h-[400px] overflow-x-hidden">
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
                      className={`absolute bottom-4 ${position === 'bottom-right' ? 'right-4' : 'left-4'} ${minimizedShape === 'circle' ? 'size-14 rounded-full' : 'h-14 px-4 rounded-full'} text-white shadow-lg flex items-center justify-center transition-colors`}
                      style={{ backgroundColor: minimizedBgColor }}
                      aria-label="Open chat widget"
                    >
                      <MessageCircle className="size-6" />
                      {minimizedShape === 'pill' && (
                        <span className="ml-2 text-sm font-medium truncate max-w-[12rem]">{widgetName}</span>
                      )}
                    </button>
                  )}

                  {/* Overlay: expanded chat window */}
                  {isOpen && (
                    <div className={`absolute bottom-4 ${position === 'bottom-right' ? 'right-4' : 'left-4'} w-[380px] max-w-[calc(100%-2rem)] h-[560px] max-h-[calc(100%-2rem)] border rounded-xl shadow-2xl flex flex-col overflow-hidden overflow-x-hidden min-w-0 ${maximizedStyle === 'blurred' ? 'backdrop-blur-md bg-white/60' : 'bg-white'}`}>
                      <div className={`flex items-center justify-between px-3 py-2 border-b ${maximizedStyle === 'blurred' ? 'backdrop-blur-md bg-white/60' : 'bg-white'}`}>
                        <div className="flex items-center gap-2">
                          <div className="size-6 rounded-full bg-blue-600 text-white flex items-center justify-center">
                            <Bot className="size-4" />
                          </div>
                          <span className="text-sm font-medium text-gray-900">{widgetName}</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => setIsOpen(false)}
                          className="p-1 rounded-md hover:bg-gray-100 text-gray-500 hover:text-gray-700"
                          aria-label="Close chat widget"
                        >
                          <X className="size-4" />
                        </button>
                      </div>
                      <div className={`flex-1 ${maximizedStyle === 'blurred' ? 'backdrop-blur-md bg-white/10' : 'bg-white'}`}>
                        {/* Chat messages area with example bubbles */}
                          <div className="h-full overflow-y-auto overflow-x-hidden p-3 space-y-2 min-w-0">
                          {/* System/assistant bubble */}
                          <div className="flex items-start gap-2">
                            <div className="size-6 rounded-full bg-blue-600 text-white flex items-center justify-center shrink-0">
                              <Bot className="size-4" />
                            </div>
                            <div className="max-w-[80%] min-w-0 rounded-2xl rounded-tl-sm text-gray-900 px-3 py-2 text-sm break-words" style={{ backgroundColor: systemBubbleBgColor }}>
                              Hi! How can I help you today?
                            </div>
                          </div>

                          {/* User bubble */}
                          <div className="flex items-start gap-2 justify-end">
                            <div className="max-w-[80%] min-w-0 rounded-2xl rounded-tr-sm text-white px-3 py-2 text-sm break-words" style={{ backgroundColor: userBubbleBgColor }}>
                              I need information about pricing.
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="border-t p-2">
                        <div className="flex items-center gap-2">
                          <input
                            className="flex-1 rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-200"
                            placeholder="Type a message..."
                          />
                          <button
                            type="button"
                            className="rounded-md bg-blue-600 text-white text-sm px-3 py-2 hover:bg-blue-700"
                          >
                            Send
                          </button>
                        </div>
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
  )
}


