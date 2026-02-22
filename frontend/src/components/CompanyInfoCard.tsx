'use client';

import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Building2, FileText, MapPin, Phone, Globe } from 'lucide-react';

interface CompanyInfoCardProps {
  form: any;
  editMode: boolean;
  industryOptions: string[];
  handleWebsiteUrlChange: (index: number, value: string) => void;
  addWebsiteUrl: () => void;
  removeWebsiteUrl: (index: number) => void;
}

export function CompanyInfoCard({
  form,
  editMode,
  industryOptions,
  handleWebsiteUrlChange,
  addWebsiteUrl,
  removeWebsiteUrl
}: CompanyInfoCardProps) {
  return (
    <Card className="border-0 shadow-xl">
      <CardHeader>
        <CardTitle className="text-xl font-bold">Company Information</CardTitle>
        <CardDescription>
          {editMode ? 'Edit your company details below' : 'View your company information'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <div className="space-y-6">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="flex items-center space-x-0">
                    <Building2 className="w-4 h-4" />
                    <span>Company Name *</span>
                  </FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Enter your company name"
                      disabled={!editMode}
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
                  <FormLabel className="flex items-center space-x-0">
                    <FileText className="w-4 h-4" />
                    <span>Company Description</span>
                  </FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Describe your company, what you do, and your services..."
                      rows={4}
                      disabled={!editMode}
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
                  <FormLabel className="flex items-center space-x-0">
                    <MapPin className="w-4 h-4" />
                    <span>Company Address</span>
                  </FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Enter your company address"
                      rows={3}
                      disabled={!editMode}
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
                  <FormLabel className="flex items-center space-x-0">
                    <Phone className="w-4 h-4" />
                    <span>Phone Number</span>
                  </FormLabel>
                  <FormControl>
                    <Input
                      type="tel"
                      placeholder="Enter your phone number"
                      disabled={!editMode}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="industry"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="flex items-center space-x-0">
                    <Building2 className="w-4 h-4" />
                    <span>Industry</span>
                  </FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value} disabled={!editMode}>
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
                          <FormLabel className="flex items-center space-x-0">
                            <Globe className="w-4 h-4" />
                            <span>Website URLs *</span>
                          </FormLabel>
                    {editMode && (
                      <Button 
                        type="button" 
                        variant="outline" 
                        size="sm"
                        onClick={addWebsiteUrl}
                      >
                        Add URL
                      </Button>
                    )}
                  </div>
                  
                  {field.value.map((url: string, index: number) => (
                    <div key={index} className="flex items-center space-x-2">
                      <Input
                        value={url}
                        onChange={(e) => handleWebsiteUrlChange(index, e.target.value)}
                        placeholder="https://yourcompany.com"
                        type="url"
                        disabled={!editMode}
                      />
                      {editMode && field.value.length > 1 && (
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
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        </Form>
      </CardContent>
    </Card>
  );
}
