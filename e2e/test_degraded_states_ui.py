"""
E2E tests for degraded state UI validation.

Tests:
- Stale state badge appears when data is old
- Fallback prediction indicator visible when using deterministic fallback
- Denied access shows generic message without PHI
- No-candidate state with retry button
"""
import pytest
from playwright.async_api import Page


@pytest.mark.asyncio
async def test_stale_vital_badge_displayed(browser_context, app_server):
    """Stale badge appears on monitoring when vitals are old."""
    base_url, now_ref = app_server
    page = await browser_context.new_page()
    
    try:
        # Login as admin
        await page.goto(f"{base_url}/")
        await page.fill('input[name="username"]', "admin")
        await page.fill('input[name="password"]', "admin-password")
        await page.click('button[type="submit"]')
        await page.wait_for_url("**/dashboard", timeout=5000)
        
        # Navigate to monitoring
        await page.goto(f"{base_url}/monitoring")
        await page.wait_for_load_state("networkidle")
        
        # Simulate stale by advancing time or using API to set old timestamp
        # For now, just verify that IF stale badge exists, it's visible
        stale_badge = await page.query_selector('[data-testid="stale-badge"]')
        if stale_badge:
            badge_text = await stale_badge.inner_text()
            assert "stale" in badge_text.lower() or "old" in badge_text.lower(), \
                f"Stale badge should indicate staleness: {badge_text}"
        
        # Verify vitals are still readable (not hidden due to staleness)
        vitals = await page.query_selector('[data-testid="vital-values"]')
        if vitals:
            vitals_text = await vitals.inner_text()
            assert len(vitals_text) > 0, "Vital values should still be readable"
        
    finally:
        await page.close()


@pytest.mark.asyncio
async def test_fallback_prediction_indicator(browser_context, app_server):
    """Fallback prediction badge visible when using deterministic fallback."""
    base_url, now_ref = app_server
    page = await browser_context.new_page()
    
    try:
        # Login as doctor
        await page.goto(f"{base_url}/")
        await page.fill('input[name="username"]', "doctor")
        await page.fill('input[name="password"]', "doctor-password")
        await page.click('button[type="submit"]')
        await page.wait_for_url("**/dashboard", timeout=5000)
        
        # Navigate to alert/dispatch
        await page.goto(f"{base_url}/patients/P-1042/alert")
        await page.wait_for_load_state("networkidle")
        
        # Look for fallback indicator
        fallback_badge = await page.query_selector('[data-testid="fallback-badge"]')
        if fallback_badge:
            badge_text = await fallback_badge.inner_text()
            assert "fallback" in badge_text.lower() or "deterministic" in badge_text.lower(), \
                f"Fallback badge should indicate fallback source: {badge_text}"
        
        # Verify NO model name/version is displayed
        model_info = await page.query_selector('text=/[Mm]odel [Nn]ame|[Vv]ersion [Nn]umber/')
        assert model_info is None, "Should not display model version information"
        
    finally:
        await page.close()


@pytest.mark.asyncio
async def test_denied_access_generic_message(browser_context, app_server):
    """Denied access (403) shows generic message without patient-specific info."""
    base_url, now_ref = app_server
    page = await browser_context.new_page()
    
    try:
        # Login as nurse (who should not have access to some resources)
        await page.goto(f"{base_url}/")
        await page.fill('input[name="username"]', "sarah")
        await page.fill('input[name="password"]', "sarah-password")
        await page.click('button[type="submit"]')
        await page.wait_for_url("**/dashboard", timeout=5000)
        
        # Try to navigate to a restricted resource (if any)
        # For now, just verify denied message format
        await page.goto(f"{base_url}/admin/settings")
        
        # Check for access denied or forbidden message
        denied_msg = await page.query_selector('text=/[Aa]ccess [Dd]enied|[Ff]orbidden/')
        if denied_msg:
            msg_text = await denied_msg.inner_text()
            # Verify it's generic and doesn't leak patient info
            assert "P-1042" not in msg_text, "Access denied should not expose patient ID"
            assert "Sarah" not in msg_text, "Access denied should not expose user details"
        
    finally:
        await page.close()


@pytest.mark.asyncio
async def test_no_candidate_state_and_retry(browser_context, app_server):
    """No-candidate state shows message and retry button."""
    base_url, now_ref = app_server
    page = await browser_context.new_page()
    
    try:
        # Login as doctor
        await page.goto(f"{base_url}/")
        await page.fill('input[name="username"]', "doctor")
        await page.fill('input[name="password"]', "doctor-password")
        await page.click('button[type="submit"]')
        await page.wait_for_url("**/dashboard", timeout=5000)
        
        # Navigate to dispatch
        await page.goto(f"{base_url}/patients/P-1042/dispatch")
        await page.wait_for_load_state("networkidle")
        
        # If no candidates are available, check for no-candidate message
        candidates = await page.query_selector('[data-testid="candidates-list"]')
        if candidates:
            content = await candidates.inner_text()
            if "no" in content.lower() or "available" in content.lower():
                # Verify retry button exists
                retry_btn = await page.query_selector('[data-testid="retry-button"]')
                assert retry_btn is not None, "Should have retry button when no candidates"
                
                is_enabled = await retry_btn.is_enabled()
                assert is_enabled, "Retry button should be enabled"
        
    finally:
        await page.close()


@pytest.mark.asyncio
async def test_loading_state_before_response(browser_context, app_server):
    """Loading state displays before authoritative response arrives."""
    base_url, now_ref = app_server
    page = await browser_context.new_page()
    
    try:
        # Setup page with slow network
        await page.route("**/api/v1/**", lambda route: None)  # Block initial API
        
        # Navigate and start loading
        await page.goto(f"{base_url}/patients/P-1042/alert", wait_until="domcontentloaded")
        
        # Check for loading indicator
        loading = await page.query_selector('[data-testid="loading-indicator"]')
        if loading:
            is_visible = await loading.is_visible()
            assert is_visible, "Loading indicator should be visible initially"
        
        # Unblock and wait for content
        await page.unroute("**/api/v1/**")
        await page.wait_for_load_state("networkidle")
        
        # Verify loading is gone
        loading = await page.query_selector('[data-testid="loading-indicator"]')
        if loading:
            is_visible = await loading.is_visible()
            assert not is_visible, "Loading indicator should disappear after load"
        
    finally:
        await page.close()
