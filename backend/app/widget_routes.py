from fastapi import APIRouter, Depends, HTTPException, status, Response, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import json
import secrets
import logging
from urllib.parse import urlparse

from .database import get_db, User, Company, Widget
from .schemas import (
    WidgetCreate, WidgetResponse, WidgetUpdate, WidgetToggleResponse
)
from .auth import get_current_user
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create widget router
widget_router = APIRouter(prefix="/widgets", tags=["widgets"])

def normalize_domain_from_url(url: str) -> Optional[str]:
    """
    Extract and normalize domain from a URL.
    Removes port numbers and www. prefix for consistent comparison.
    
    Args:
        url: URL string
        
    Returns:
        Normalized domain (without www. and port) or None if invalid
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove port number
        if ':' in domain:
            domain = domain.split(':')[0]
        # Remove www. prefix for normalization
        domain = domain.replace('www.', '')
        return domain if domain else None
    except Exception as e:
        logger.warning(f"Failed to normalize domain from URL {url}: {e}")
        return None

def get_allowed_domains_from_company(company: Company) -> List[str]:
    """
    Extract and normalize allowed domains from company website URLs.
    
    Args:
        company: Company object with website_urls
        
    Returns:
        List of normalized domain names
    """
    allowed_domains = []
    if not company.website_urls:
        return allowed_domains
    
    try:
        website_urls = json.loads(company.website_urls)
        for url in website_urls:
            domain = normalize_domain_from_url(url)
            if domain and domain not in allowed_domains:
                allowed_domains.append(domain)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse company website_urls: {e}")
    
    return allowed_domains

# Widget routes
@widget_router.post("/", response_model=WidgetResponse)
def create_widget(
    company_id: int,
    widget: WidgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify company exists and belongs to user
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.owner_id == current_user.id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Generate unique widget ID
    widget_id = f"widget_{company_id}_{uuid.uuid4().hex[:12]}"
    
    # Generate API key
    api_key = f"ak_{secrets.token_urlsafe(32)}"
    
    # Get allowed domains from company website URLs and normalize them
    allowed_domains = get_allowed_domains_from_company(company)
    
    # Create widget
    db_widget = Widget(
        company_id=company_id,
        name=widget.name,
        widget_id=widget_id,
        position=widget.position,
        minimized_shape=widget.minimized_shape,
        minimized_bg_color=widget.minimized_bg_color,
        maximized_style=widget.maximized_style,
        system_bubble_bg_color=widget.system_bubble_bg_color,
        user_bubble_bg_color=widget.user_bubble_bg_color,
        is_active=widget.is_active,
        api_key=api_key,
        allowed_domains=json.dumps(allowed_domains) if allowed_domains else None
    )
    
    db.add(db_widget)
    db.commit()
    db.refresh(db_widget)
    
    return db_widget

@widget_router.get("/company/{company_id}", response_model=List[WidgetResponse])
def get_company_widgets(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify company exists and belongs to user
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.owner_id == current_user.id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    widgets = db.query(Widget).filter(Widget.company_id == company_id).all()
    return widgets

@widget_router.get("/{widget_id}", response_model=WidgetResponse)
def get_widget(
    widget_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    widget = db.query(Widget).filter(Widget.widget_id == widget_id).first()
    
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    # Verify company belongs to user
    company = db.query(Company).filter(
        Company.id == widget.company_id,
        Company.owner_id == current_user.id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    return widget

@widget_router.put("/{widget_id}", response_model=WidgetResponse)
def update_widget(
    widget_id: str,
    widget_update: WidgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    widget = db.query(Widget).filter(Widget.widget_id == widget_id).first()
    
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    # Verify company belongs to user
    company = db.query(Company).filter(
        Company.id == widget.company_id,
        Company.owner_id == current_user.id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    # Update fields
    update_data = widget_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(widget, field, value)
    
    # If company website URLs were updated, refresh allowed domains
    # Check if we need to update allowed domains (this would be triggered if company was updated)
    # For now, we'll keep the existing allowed_domains unless widget is being reactivated
    # In a future enhancement, we could add an endpoint to refresh allowed domains
    
    db.commit()
    db.refresh(widget)
    
    return widget

@widget_router.patch("/{widget_id}/toggle", response_model=WidgetToggleResponse)
def toggle_widget(
    widget_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    widget = db.query(Widget).filter(Widget.widget_id == widget_id).first()
    
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    # Verify company belongs to user
    company = db.query(Company).filter(
        Company.id == widget.company_id,
        Company.owner_id == current_user.id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    # Toggle active status
    widget.is_active = not widget.is_active
    db.commit()
    
    return {
        "message": f"Widget {'activated' if widget.is_active else 'deactivated'} successfully",
        "is_active": widget.is_active
    }

@widget_router.delete("/{widget_id}")
def delete_widget(
    widget_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    widget = db.query(Widget).filter(Widget.widget_id == widget_id).first()
    
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    # Verify company belongs to user
    company = db.query(Company).filter(
        Company.id == widget.company_id,
        Company.owner_id == current_user.id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    db.delete(widget)
    db.commit()
    
    return {"message": "Widget deleted successfully"}

@widget_router.post("/{widget_id}/refresh-domains")
def refresh_widget_domains(
    widget_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh allowed domains for a widget based on company's current website URLs.
    Useful when company website URLs are updated.
    """
    widget = db.query(Widget).filter(Widget.widget_id == widget_id).first()
    
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    # Verify company belongs to user
    company = db.query(Company).filter(
        Company.id == widget.company_id,
        Company.owner_id == current_user.id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    # Get updated allowed domains from company
    allowed_domains = get_allowed_domains_from_company(company)
    
    # Update widget's allowed domains
    widget.allowed_domains = json.dumps(allowed_domains) if allowed_domains else None
    db.commit()
    db.refresh(widget)
    
    logger.info(f"Refreshed allowed domains for widget {widget_id}: {allowed_domains}")
    
    return {
        "message": "Widget domains refreshed successfully",
        "allowed_domains": allowed_domains,
        "widget_id": widget_id
    }

@widget_router.get("/{widget_id}/script.js")
def get_widget_script(
    widget_id: str, 
    api_key: str = Query(..., description="Widget API key"),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Serve the widget JavaScript file with embedded configuration.
    Requires API key and validates domain.
    """
    widget = db.query(Widget).filter(Widget.widget_id == widget_id).first()
    
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    if not widget.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget is not active"
        )
    
    # Validate API key
    if not api_key or widget.api_key != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    
    # Validate domain using referer or origin header (more lenient for script loading)
    # Allow script loading from any domain, but the chat endpoint will validate
    # This allows the script to be loaded for preview/testing, but chat requests are secured
    origin = request.headers.get('origin') if request else None
    referer = request.headers.get('referer') if request else None
    source_url = origin or referer
    
    if source_url:
        try:
            parsed_source = urlparse(source_url)
            source_domain = parsed_source.netloc.lower()
            # Remove port number
            if ':' in source_domain:
                source_domain = source_domain.split(':')[0]
            
            # Allow localhost/127.0.0.1 for development/preview
            if source_domain in ['localhost', '127.0.0.1', '0.0.0.0']:
                pass  # Allow script loading from localhost
            else:
                # For production, we could validate here, but it's more important to validate at chat endpoint
                # For now, allow script loading (the chat endpoint will enforce domain validation)
                allowed_domains = json.loads(widget.allowed_domains) if widget.allowed_domains else []
                if allowed_domains:
                    source_domain_normalized = source_domain.replace('www.', '')
                    domain_allowed = False
                    for allowed_domain in allowed_domains:
                        allowed_domain_normalized = allowed_domain.replace('www.', '').lower()
                        if source_domain_normalized == allowed_domain_normalized:
                            domain_allowed = True
                            break
                    # Log but don't block script loading (chat endpoint will enforce)
                    if not domain_allowed:
                        logger.warning(f"⚠️ Script loaded from non-allowed domain: {source_domain} (allowed: {allowed_domains})")
        except Exception as e:
            logger.warning(f"Error parsing source URL for script: {e}")
            # Don't block script loading on parse errors
    
    # Get company info
    company = db.query(Company).filter(Company.id == widget.company_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Generate JavaScript with embedded config
    config = {
        "widgetId": widget.widget_id,
        "companyId": widget.company_id,
        "companyName": company.name,
        "widgetName": widget.name,  # Add widget name
        "position": widget.position,
        "minimizedShape": widget.minimized_shape,
        "minimizedBgColor": widget.minimized_bg_color,
        "maximizedStyle": widget.maximized_style,
        "systemBubbleBgColor": widget.system_bubble_bg_color,
        "userBubbleBgColor": widget.user_bubble_bg_color,
        "apiBaseUrl": settings.base_url,
        "apiKey": widget.api_key,
        "isActive": widget.is_active
    }
    
    # Generate the widget script
    script_content = generate_widget_script(config)
    
    return Response(
        content=script_content,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=3600",  # 1 hour cache
            "Access-Control-Allow-Origin": "*"
        }
    )

def generate_widget_script(config):
    """
    Generate the JavaScript widget code with embedded configuration.
    Matches the preview design exactly.
    """
    widget_name = config.get('widgetName', config.get('companyName', 'ChatBot'))
    position = config.get('position', 'bottom-right')
    minimized_shape = config.get('minimizedShape', 'circle')
    minimized_bg_color = config.get('minimizedBgColor', '#2563eb')
    maximized_style = config.get('maximizedStyle', 'solid')
    system_bubble_bg_color = config.get('systemBubbleBgColor', '#f3f4f6')
    user_bubble_bg_color = config.get('userBubbleBgColor', '#2563eb')
    
    # Position styles
    position_bottom = '16px'  # bottom-4 = 1rem = 16px
    position_side = '16px'    # right-4 or left-4 = 1rem = 16px
    position_css = f'bottom: {position_bottom}; {position}: {position_side};'
    chat_position_css = f'{position}: {position_side};'  # Align with button
    
    # Minimized button styles
    if minimized_shape == 'pill':
        minimized_button_css = 'height: 56px; padding: 0 16px; border-radius: 28px; display: flex; align-items: center; justify-content: center; gap: 8px;'
    else:  # circle
        minimized_button_css = 'width: 56px; height: 56px; border-radius: 50%; display: flex; align-items: center; justify-content: center;'
    
    # Chat window styles
    if maximized_style == 'solid':
        chat_window_bg = 'background: white;'
        header_bg = 'background: white;'
        messages_bg = 'background: white;'
    else:  # blurred
        chat_window_bg = 'background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);'
        header_bg = 'background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);'
        messages_bg = 'background: rgba(255, 255, 255, 0.1);'
    
    # SVG icons for bot and user (inline to avoid external dependencies) - Lucide icons
    bot_icon_svg = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="10" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>'
    user_icon_svg = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
    message_icon_svg = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>'
    x_icon_svg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18M6 6l12 12"/></svg>'
    send_icon_svg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>'
    
    return f"""
(function() {{
    'use strict';
    
    // Widget configuration
    const CONFIG = {json.dumps(config)};
    
    // Widget class
    class AIChatWidget {{
        constructor() {{
            this.config = CONFIG;
            this.isOpen = false;
            this.messages = [];
            this.isLoading = false;
            this.init();
        }}
        
        init() {{
            this.createWidget();
            this.attachEventListeners();
            // Show welcome message
            if (this.messages.length === 0) {{
                this.addWelcomeMessage();
            }}
        }}
        
        createWidget() {{
            // Create widget container
            this.container = document.createElement('div');
            this.container.id = 'ai-chat-widget';
            this.container.style.cssText = `
                position: fixed;
                {position_css}
                z-index: 999999;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            `;
            
            // Create minimized button
            this.minimizedButton = document.createElement('button');
            this.minimizedButton.type = 'button';
            this.minimizedButton.setAttribute('aria-label', 'Open chat widget');
            this.minimizedButton.style.cssText = `
                {minimized_button_css}
                background-color: {minimized_bg_color};
                color: white;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
                cursor: pointer;
                border: none;
                transition: all 0.2s ease;
                font-size: 0;
            `;
            this.minimizedButton.onmouseenter = () => {{ this.minimizedButton.style.opacity = '0.9'; }};
            this.minimizedButton.onmouseleave = () => {{ this.minimizedButton.style.opacity = '1'; }};
            
            // Add icon to minimized button
            const iconWrapper = document.createElement('div');
            iconWrapper.style.cssText = 'display: flex; align-items: center; justify-content: center;';
            iconWrapper.innerHTML = '{message_icon_svg}';
            this.minimizedButton.appendChild(iconWrapper);
            
            // Add widget name for pill shape
            if ('{minimized_shape}' === 'pill') {{
                const nameSpan = document.createElement('span');
                nameSpan.textContent = '{widget_name}';
                nameSpan.style.cssText = 'margin-left: 8px; font-size: 14px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 192px;';
                this.minimizedButton.appendChild(nameSpan);
            }}
            
            // Create chat window
            this.chatWindow = document.createElement('div');
            this.chatWindow.style.cssText = `
                position: absolute;
                bottom: 72px;
                {chat_position_css}
                width: 380px;
                max-width: calc(100vw - 2rem);
                height: 560px;
                max-height: calc(100vh - 2rem);
                {chat_window_bg}
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 12px;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                display: none;
                flex-direction: column;
                overflow: hidden;
            `;
            
            // Create chat header
            const header = document.createElement('div');
            header.style.cssText = `
                {header_bg}
                padding: 12px 16px;
                border-bottom: 1px solid rgba(0, 0, 0, 0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-shrink: 0;
            `;
            
            const headerLeft = document.createElement('div');
            headerLeft.style.cssText = 'display: flex; align-items: center; gap: 8px;';
            
            const botIcon = document.createElement('div');
            botIcon.style.cssText = 'width: 24px; height: 24px; border-radius: 50%; background-color: #2563eb; color: white; display: flex; align-items: center; justify-content: center; flex-shrink: 0;';
            botIcon.innerHTML = '{bot_icon_svg}';
            
            const widgetNameSpan = document.createElement('span');
            widgetNameSpan.textContent = '{widget_name}';
            widgetNameSpan.style.cssText = 'font-size: 14px; font-weight: 500; color: #111827;';
            
            headerLeft.appendChild(botIcon);
            headerLeft.appendChild(widgetNameSpan);
            
            const headerRight = document.createElement('div');
            headerRight.style.cssText = 'display: flex; align-items: center; gap: 4px;';
            
            const closeButton = document.createElement('button');
            closeButton.type = 'button';
            closeButton.setAttribute('aria-label', 'Close chat widget');
            closeButton.id = 'widget-close-btn';
            closeButton.style.cssText = 'padding: 4px; border-radius: 6px; border: none; background: none; cursor: pointer; color: #6b7280; display: flex; align-items: center; justify-content: center; transition: background 0.2s;';
            closeButton.onmouseenter = () => {{ closeButton.style.background = '#f3f4f6'; closeButton.style.color = '#374151'; }};
            closeButton.onmouseleave = () => {{ closeButton.style.background = 'none'; closeButton.style.color = '#6b7280'; }};
            closeButton.innerHTML = '{x_icon_svg}';
            
            headerRight.appendChild(closeButton);
            header.appendChild(headerLeft);
            header.appendChild(headerRight);
            
            // Create messages area
            this.messagesArea = document.createElement('div');
            this.messagesArea.style.cssText = `
                flex: 1;
                {messages_bg}
                overflow-y: auto;
                padding: 12px;
                display: flex;
                flex-direction: column;
                gap: 8px;
                min-height: 0;
            `;
            
            // Create input area
            const inputArea = document.createElement('div');
            inputArea.style.cssText = `
                border-top: 1px solid rgba(0, 0, 0, 0.1);
                padding: 8px;
                background: white;
                flex-shrink: 0;
            `;
            
            const inputWrapper = document.createElement('div');
            inputWrapper.style.cssText = 'display: flex; align-items: center; gap: 8px;';
            
            this.messageInput = document.createElement('input');
            this.messageInput.type = 'text';
            this.messageInput.placeholder = 'Ask me anything...';
            this.messageInput.id = 'widget-message-input';
            this.messageInput.style.cssText = `
                flex: 1;
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                background: white;
                color: #111827;
                font-size: 14px;
                outline: none;
                transition: border-color 0.2s, box-shadow 0.2s;
            `;
            this.messageInput.onfocus = () => {{
                this.messageInput.style.borderColor = '#93c5fd';
                this.messageInput.style.boxShadow = '0 0 0 3px rgba(147, 197, 253, 0.1)';
            }};
            this.messageInput.onblur = () => {{
                this.messageInput.style.borderColor = '#d1d5db';
                this.messageInput.style.boxShadow = 'none';
            }};
            
            const sendButton = document.createElement('button');
            sendButton.type = 'button';
            sendButton.id = 'widget-send-btn';
            sendButton.style.cssText = `
                padding: 8px;
                background: #2563eb;
                border: none;
                border-radius: 6px;
                color: white;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.2s;
                flex-shrink: 0;
            `;
            sendButton.onmouseenter = () => {{ sendButton.style.background = '#1d4ed8'; }};
            sendButton.onmouseleave = () => {{ sendButton.style.background = '#2563eb'; }};
            sendButton.innerHTML = '{send_icon_svg}';
            
            inputWrapper.appendChild(this.messageInput);
            inputWrapper.appendChild(sendButton);
            inputArea.appendChild(inputWrapper);
            
            // Assemble chat window
            this.chatWindow.appendChild(header);
            this.chatWindow.appendChild(this.messagesArea);
            this.chatWindow.appendChild(inputArea);
            
            // Assemble container
            this.container.appendChild(this.minimizedButton);
            this.container.appendChild(this.chatWindow);
            
            // Add to page
            document.body.appendChild(this.container);
        }}
        
        attachEventListeners() {{
            this.minimizedButton.addEventListener('click', () => this.toggleWidget());
            document.getElementById('widget-close-btn').addEventListener('click', () => this.toggleWidget());
            document.getElementById('widget-send-btn').addEventListener('click', () => this.sendMessage());
            
            this.messageInput.addEventListener('keypress', (e) => {{
                if (e.key === 'Enter' && !e.shiftKey) {{
                    e.preventDefault();
                    this.sendMessage();
                }}
            }});
        }}
        
        toggleWidget() {{
            this.isOpen = !this.isOpen;
            this.chatWindow.style.display = this.isOpen ? 'flex' : 'none';
            
            if (this.isOpen) {{
                this.messageInput.focus();
                this.scrollToBottom();
            }}
        }}
        
        addWelcomeMessage() {{
            const welcomeMsg = "Hi! I'm your AI assistant. How can I help you today?";
            this.addMessage(welcomeMsg, false);
        }}
        
        async sendMessage() {{
            const message = this.messageInput.value.trim();
            if (!message || this.isLoading) return;
            
            // Add user message to UI
            this.addMessage(message, true);
            this.messageInput.value = '';
            this.messageInput.disabled = true;
            this.isLoading = true;
            
            // Show loading indicator
            const loadingId = this.addLoadingMessage();
            
            try {{
                const response = await fetch(`${{this.config.apiBaseUrl}}/api/v1/ai/chat/${{this.config.companyId}}/widget`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'X-API-Key': this.config.apiKey
                    }},
                    body: JSON.stringify({{
                        message: message,
                        n_results: 5
                    }})
                }});
                
                if (!response.ok) {{
                    const errorData = await response.json().catch(() => ({{}}));
                    throw new Error(errorData.detail || 'Failed to get response');
                }}
                
                const data = await response.json();
                
                // Remove loading message
                this.removeMessage(loadingId);
                
                // Add AI response
                this.addMessage(data.response, false);
                
            }} catch (error) {{
                console.error('Chat error:', error);
                this.removeMessage(loadingId);
                this.addMessage('Sorry, I encountered an error. Please try again.', false);
            }} finally {{
                this.isLoading = false;
                this.messageInput.disabled = false;
                this.messageInput.focus();
            }}
        }}
        
        addLoadingMessage() {{
            const messageId = 'msg_loading_' + Date.now();
            const messageWrapper = document.createElement('div');
            messageWrapper.id = messageId;
            messageWrapper.style.cssText = 'display: flex; justify-content: flex-start; width: 100%;';
            
            const messageContainer = document.createElement('div');
            messageContainer.style.cssText = 'display: flex; items-start: flex-start; gap: 8px; max-width: 80%;';
            
            const iconWrapper = document.createElement('div');
            iconWrapper.style.cssText = 'width: 24px; height: 24px; border-radius: 50%; background-color: #2563eb; color: white; display: flex; align-items: center; justify-content: center; flex-shrink: 0;';
            iconWrapper.innerHTML = '{bot_icon_svg}';
            
            const bubble = document.createElement('div');
            bubble.style.cssText = `
                border-radius: 16px 16px 16px 4px;
                padding: 12px;
                background-color: {system_bubble_bg_color};
                color: #111827;
                font-size: 14px;
                display: flex;
                align-items: center;
                gap: 8px;
            `;
            
            const spinner = document.createElement('div');
            spinner.style.cssText = 'width: 12px; height: 12px; border: 2px solid #93c5fd; border-top-color: #2563eb; border-radius: 50%; animation: spin 0.6s linear infinite;';
            
            const loadingText = document.createTextNode('AI is thinking...');
            
            bubble.appendChild(spinner);
            bubble.appendChild(loadingText);
            messageContainer.appendChild(iconWrapper);
            messageContainer.appendChild(bubble);
            messageWrapper.appendChild(messageContainer);
            this.messagesArea.appendChild(messageWrapper);
            this.scrollToBottom();
            
            // Add spin animation if not already present
            if (!document.getElementById('widget-spin-animation')) {{
                const style = document.createElement('style');
                style.id = 'widget-spin-animation';
                style.textContent = '@keyframes spin {{ to {{ transform: rotate(360deg); }} }}';
                document.head.appendChild(style);
            }}
            
            return messageId;
        }}
        
        addMessage(content, isUser) {{
            const messageId = 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            const messageWrapper = document.createElement('div');
            messageWrapper.id = messageId;
            messageWrapper.style.cssText = `display: flex; justify-content: ${{isUser ? 'flex-end' : 'flex-start'}}; width: 100%;`;
            
            const messageContainer = document.createElement('div');
            messageContainer.style.cssText = `display: flex; align-items: flex-start; gap: 8px; max-width: 80%; flex-direction: ${{isUser ? 'row-reverse' : 'row'}};`;
            
            // Icon
            const iconWrapper = document.createElement('div');
            iconWrapper.style.cssText = 'width: 24px; height: 24px; border-radius: 50%; background-color: #2563eb; color: white; display: flex; align-items: center; justify-content: center; flex-shrink: 0;';
            iconWrapper.innerHTML = isUser ? '{user_icon_svg}' : '{bot_icon_svg}';
            
            // Bubble
            const bubble = document.createElement('div');
            const bubbleColor = isUser ? '{user_bubble_bg_color}' : '{system_bubble_bg_color}';
            const textColor = isUser ? 'white' : '#111827';
            const borderRadius = isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px';
            
            bubble.style.cssText = `
                border-radius: ${{borderRadius}};
                padding: 12px;
                background-color: ${{bubbleColor}};
                color: ${{textColor}};
                font-size: 14px;
                line-height: 1.5;
                word-wrap: break-word;
                white-space: pre-wrap;
            `;
            bubble.textContent = content;
            
            messageContainer.appendChild(iconWrapper);
            messageContainer.appendChild(bubble);
            messageWrapper.appendChild(messageContainer);
            this.messagesArea.appendChild(messageWrapper);
            this.scrollToBottom();
            
            return messageId;
        }}
        
        removeMessage(messageId) {{
            const messageElement = document.getElementById(messageId);
            if (messageElement) {{
                messageElement.remove();
            }}
        }}
        
        scrollToBottom() {{
            setTimeout(() => {{
                this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
            }}, 100);
        }}
    }}
    
    // Initialize widget when DOM is ready
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', () => new AIChatWidget());
    }} else {{
        new AIChatWidget();
    }}
}})();
"""

# Export router
__all__ = ["widget_router"]
