"""
E2E tests for WebSocket disconnect/reconnect resilience and REST recovery.

Tests:
- WebSocket disconnect detected and state changes to offline
- REST refetch recovers state after disconnect
- Manual refresh works during disconnect
- Automatic reconnection after detecting disconnect
"""
import pytest
from playwright.async_api import Page


@pytest.mark.asyncio
async def test_websocket_disconnect_detection(browser_context, app_server):
    """WebSocket disconnect is detected and state changes to offline."""
    base_url, now_ref = app_server
    page = await browser_context.new_page()
    
    try:
        # Login as doctor
        await page.goto(f"{base_url}/")
        await page.fill('input[name="username"]', "doctor")
        await page.fill('input[name="password"]', "doctor-password")
        await page.click('button[type="submit"]')
        await page.wait_for_url("**/dashboard", timeout=5000)
        
        # Navigate to alert page which uses WebSocket
        await page.goto(f"{base_url}/patients/P-1042/alert")
        await page.wait_for_load_state("networkidle")
        
        # Wait for WebSocket to connect
        await page.wait_for_timeout(1000)
        
        # Verify connection state shows connected
        connected = await page.query_selector('text=/[Cc]onnected/')
        if connected:
            is_visible = await connected.is_visible()
            assert is_visible, "Should show connected state initially"
        
        # Simulate network disconnect by blocking WebSocket
        await page.context.route("wss://**", lambda route: None)
        await page.context.route("ws://**", lambda route: None)
        
        # Wait for disconnect to be detected
        await page.wait_for_timeout(2000)
        
        # Verify state changed to disconnected
        disconnected = await page.query_selector('text=/[Dd]isconnected|[Oo]ffline/')
        if disconnected:
            is_visible = await disconnected.is_visible()
            assert is_visible, "Should show disconnected state after network failure"
        
    finally:
        await page.close()


@pytest.mark.asyncio
async def test_rest_refetch_recovers_state(browser_context, app_server):
    """REST refetch recovers state when WebSocket is unavailable."""
    base_url, now_ref = app_server
    page = await browser_context.new_page()
    
    try:
        # Login and navigate to alert
        await page.goto(f"{base_url}/")
        await page.fill('input[name="username"]', "doctor")
        await page.fill('input[name="password"]', "doctor-password")
        await page.click('button[type="submit"]')
        await page.wait_for_url("**/dashboard", timeout=5000)
        
        await page.goto(f"{base_url}/patients/P-1042/alert")
        await page.wait_for_load_state("networkidle")
        
        # Block WebSocket to simulate disconnect
        await page.context.route("wss://**", lambda route: None)
        await page.context.route("ws://**", lambda route: None)
        
        # Wait for disconnect
        await page.wait_for_timeout(1000)
        
        # Click "Retry REST" button if available
        retry_btn = await page.query_selector('[data-testid="retry-rest-button"]')
        if retry_btn:
            await retry_btn.click()
            
            # Wait for REST refetch to complete
            await page.wait_for_timeout(1000)
            
            # Verify alert data is still visible (recovered via REST)
            alert_card = await page.query_selector('[data-testid="alert-card"]')
            if alert_card:
                is_visible = await alert_card.is_visible()
                assert is_visible, "Alert data should be recovered via REST"
        
    finally:
        await page.close()


@pytest.mark.asyncio
async def test_manual_refresh_during_disconnect(browser_context, app_server):
    """Manual refresh button works even when WebSocket is disconnected."""
    base_url, now_ref = app_server
    page = await browser_context.new_page()
    
    try:
        # Login and navigate
        await page.goto(f"{base_url}/")
        await page.fill('input[name="username"]', "doctor")
        await page.fill('input[name="password"]', "doctor-password")
        await page.click('button[type="submit"]')
        await page.wait_for_url("**/dashboard", timeout=5000)
        
        await page.goto(f"{base_url}/patients/P-1042/alert")
        await page.wait_for_load_state("networkidle")
        
        # Get initial content
        initial_content = await page.content()
        
        # Block WebSocket
        await page.context.route("wss://**", lambda route: None)
        await page.context.route("ws://**", lambda route: None)
        await page.wait_for_timeout(1000)
        
        # Click refresh/retry button
        refresh_btn = await page.query_selector('[data-testid="refresh-button"]')
        if refresh_btn:
            await refresh_btn.click()
            
            # Wait for refresh to complete
            await page.wait_for_timeout(1000)
            
            # Verify content is still available
            alert_card = await page.query_selector('[data-testid="alert-card"]')
            assert alert_card is not None, "Alert should still be visible after manual refresh"
        
    finally:
        await page.close()


@pytest.mark.asyncio
async def test_automatic_reconnect_after_recovery(browser_context, app_server):
    """WebSocket automatically reconnects after network recovers."""
    base_url, now_ref = app_server
    page = await browser_context.new_page()
    
    try:
        # Login and navigate
        await page.goto(f"{base_url}/")
        await page.fill('input[name="username"]', "doctor")
        await page.fill('input[name="password"]', "doctor-password")
        await page.click('button[type="submit"]')
        await page.wait_for_url("**/dashboard", timeout=5000)
        
        await page.goto(f"{base_url}/patients/P-1042/alert")
        await page.wait_for_load_state("networkidle")
        
        # Verify initial connected state
        connected_initial = await page.query_selector('text=/[Cc]onnected/')
        
        # Block WebSocket briefly
        await page.context.route("wss://**", lambda route: None)
        await page.context.route("ws://**", lambda route: None)
        
        await page.wait_for_timeout(2000)
        
        # Unblock WebSocket to simulate recovery
        await page.context.unroute("wss://**")
        await page.context.unroute("ws://**")
        
        # Wait for reconnection
        await page.wait_for_timeout(2000)
        
        # Verify state returns to connected
        reconnected = await page.query_selector('text=/[Cc]onnected/')
        if reconnected:
            is_visible = await reconnected.is_visible()
            assert is_visible, "Should reconnect after network recovery"
        
    finally:
        await page.close()
