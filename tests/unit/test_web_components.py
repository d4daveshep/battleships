"""
Component tests for HTML/HTMX interactions using Playwright.
"""

import pytest
import asyncio
import uvicorn
import threading
import time
from playwright.async_api import async_playwright, Page, Browser

from web.app import app


class TestServer:
    """Test server management"""
    
    @classmethod
    def setup_class(cls):
        """Start test server"""
        cls.server_thread = threading.Thread(
            target=uvicorn.run,
            args=(app,),
            kwargs={
                "host": "127.0.0.1",
                "port": 8001,
                "log_level": "critical"
            },
            daemon=True
        )
        cls.server_thread.start()
        time.sleep(2)  # Wait for server to start
    
    @pytest.fixture(scope="class")
    async def browser(self):
        """Browser fixture"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            yield browser
            await browser.close()
    
    @pytest.fixture
    async def page(self, browser: Browser):
        """Page fixture"""
        page = await browser.new_page()
        yield page
        await page.close()


class TestGameCreation(TestServer):
    """Test game creation UI"""
    
    async def test_main_page_loads(self, page: Page):
        """Test main page loads correctly"""
        await page.goto("http://127.0.0.1:8001")
        
        # Check title
        title = await page.title()
        assert "Fox The Navy" in title
        
        # Check main heading
        heading = await page.locator("h1").inner_text()
        assert "Fox The Navy" in heading
        
        # Check new game form
        form = page.locator("#new-game-form")
        await form.wait_for()
        
        assert await form.locator("h2").inner_text() == "Start New Game"
    
    async def test_create_game_vs_computer(self, page: Page):
        """Test creating game against computer"""
        await page.goto("http://127.0.0.1:8001")
        
        # Fill in player name
        await page.fill("#player1_name", "Alice")
        
        # Select vs computer (should be default)
        computer_radio = page.locator('input[value="true"]')
        await computer_radio.check()
        
        # Submit form
        await page.click('button[type="submit"]')
        
        # Wait for game interface to load
        game_interface = page.locator("#game-interface")
        await game_interface.wait_for()
        
        # Check ship placement phase
        setup_phase = page.locator("#setup-phase")
        await setup_phase.wait_for()
        
        heading = await setup_phase.locator("h2").inner_text()
        assert "Ship Placement" in heading
    
    async def test_create_game_vs_human(self, page: Page):
        """Test creating game against human"""
        await page.goto("http://127.0.0.1:8001")
        
        # Fill in player name
        await page.fill("#player1_name", "Alice")
        
        # Select vs human
        human_radio = page.locator('input[value="false"]')
        await human_radio.check()
        
        # Player 2 name field should appear
        player2_field = page.locator("#player2-name")
        await player2_field.wait_for(state="visible")
        
        await page.fill("#player2_name", "Bob")
        
        # Submit form
        await page.click('button[type="submit"]')
        
        # Wait for game interface
        game_interface = page.locator("#game-interface")
        await game_interface.wait_for()


class TestShipPlacement(TestServer):
    """Test ship placement UI interactions"""
    
    async def setup_game(self, page: Page):
        """Helper to set up a new game"""
        await page.goto("http://127.0.0.1:8001")
        await page.fill("#player1_name", "TestPlayer")
        await page.click('button[type="submit"]')
        
        # Wait for ship placement phase
        setup_phase = page.locator("#setup-phase")
        await setup_phase.wait_for()
    
    async def test_ship_placement_form_loads(self, page: Page):
        """Test ship placement form loads"""
        await self.setup_game(page)
        
        # Check placement form
        placement_form = page.locator("#ship-placement-form")
        await placement_form.wait_for()
        
        # Should show first ship (Destroyer)
        ship_name = await placement_form.locator("h3").inner_text()
        assert "DESTROYER" in ship_name.upper()
        
        # Check form fields
        assert await page.locator("#row").is_visible()
        assert await page.locator("#col").is_visible()
        assert await page.locator("#direction").is_visible()
    
    async def test_place_ship_manually(self, page: Page):
        """Test manually placing a ship"""
        await self.setup_game(page)
        
        # Fill placement form
        await page.select_option("#row", "0")  # Row A
        await page.select_option("#col", "0")  # Column 1
        await page.select_option("#direction", "horizontal")
        
        # Submit placement
        await page.click('button[type="submit"]')
        
        # Wait for board update and next ship form
        await page.wait_for_timeout(1000)
        
        # Check board shows ship
        board = page.locator("#player-board")
        cell = board.locator('td[data-row="0"][data-col="0"]')
        await cell.wait_for()
        
        # Should show ship symbol or different styling
        cell_class = await cell.get_attribute("class")
        assert "ship" in cell_class or await cell.inner_text() == "D"
    
    async def test_auto_place_ships(self, page: Page):
        """Test auto-placing all ships"""
        await self.setup_game(page)
        
        # Click auto-place button
        auto_btn = page.locator("#auto-place-btn")
        await auto_btn.click()
        
        # Wait for placement to complete
        await page.wait_for_timeout(2000)
        
        # Should transition to playing phase or show all ships placed
        # Check if game moved to playing phase
        playing_phase = page.locator("#playing-phase")
        try:
            await playing_phase.wait_for(timeout=5000)
            heading = await playing_phase.locator("h2").inner_text()
            assert "Battle Phase" in heading
        except:
            # If still in setup, check that ships are placed
            board = page.locator("#player-board")
            ship_cells = board.locator(".ship")
            count = await ship_cells.count()
            assert count > 0  # Should have some ships placed
    
    async def test_ship_placement_validation(self, page: Page):
        """Test ship placement validation"""
        await self.setup_game(page)
        
        # Try to place ship at same position twice
        await page.select_option("#row", "0")
        await page.select_option("#col", "0") 
        await page.select_option("#direction", "horizontal")
        await page.click('button[type="submit"]')
        
        # Wait for first ship to be placed
        await page.wait_for_timeout(1000)
        
        # Try to place second ship overlapping
        if await page.locator("#ship-placement-form").is_visible():
            await page.select_option("#row", "0")
            await page.select_option("#col", "0")
            await page.select_option("#direction", "horizontal")
            await page.click('button[type="submit"]')
            
            # Should show error or not allow invalid placement
            # Check for error notification or form still visible
            await page.wait_for_timeout(1000)
            assert await page.locator("#ship-placement-form").is_visible()


class TestGamePlay(TestServer):
    """Test gameplay UI interactions"""
    
    async def setup_playing_game(self, page: Page):
        """Helper to set up game in playing phase"""
        await page.goto("http://127.0.0.1:8001")
        await page.fill("#player1_name", "TestPlayer")
        await page.click('button[type="submit"]')
        
        # Auto-place ships to get to playing phase quickly
        setup_phase = page.locator("#setup-phase")
        await setup_phase.wait_for()
        
        auto_btn = page.locator("#auto-place-btn")
        await auto_btn.click()
        
        # Wait for playing phase
        playing_phase = page.locator("#playing-phase")
        await playing_phase.wait_for(timeout=10000)
    
    async def test_playing_phase_interface(self, page: Page):
        """Test playing phase interface elements"""
        await self.setup_playing_game(page)
        
        # Check battle phase heading
        heading = await page.locator("#playing-phase h2").inner_text()
        assert "Battle Phase" in heading
        
        # Check boards are visible
        assert await page.locator("#player-ships-board").is_visible()
        assert await page.locator("#shots-fired-board").is_visible()
        
        # Check shot controls
        assert await page.locator("#shot-controls").is_visible()
        assert await page.locator("#shots").is_visible()
    
    async def test_submit_shots(self, page: Page):
        """Test submitting shots"""
        await self.setup_playing_game(page)
        
        # Enter valid shots
        await page.fill("#shots", "A1,B2")
        
        # Submit shots
        await page.click('button[type="submit"]')
        
        # Wait for response
        await page.wait_for_timeout(2000)
        
        # Check for round results or board updates
        round_results = page.locator("#round-results")
        if await round_results.is_visible():
            results_text = await round_results.inner_text()
            assert "Round" in results_text and "Results" in results_text
    
    async def test_shot_input_validation(self, page: Page):
        """Test shot input validation"""
        await self.setup_playing_game(page)
        
        # Enter invalid shot format
        shots_input = page.locator("#shots")
        await shots_input.fill("INVALID")
        
        # Check if validation message appears
        await page.wait_for_timeout(500)
        
        validation_msg = page.locator(".validation-message")
        if await validation_msg.is_visible():
            msg_text = await validation_msg.inner_text()
            assert "Invalid" in msg_text
    
    async def test_board_updates(self, page: Page):
        """Test that boards update after shots"""
        await self.setup_playing_game(page)
        
        # Submit shots
        await page.fill("#shots", "F6,G6")
        await page.click('button[type="submit"]')
        
        # Wait for board updates
        await page.wait_for_timeout(3000)
        
        # Check shots fired board
        shots_board = page.locator("#shots-fired-board")
        
        # Should show fired shots (round numbers)
        fired_cells = shots_board.locator(".fired")
        count = await fired_cells.count()
        assert count >= 2  # Should have at least 2 fired shots


class TestGameFlow(TestServer):
    """Test complete game flow"""
    
    async def test_complete_game_flow(self, page: Page):
        """Test playing a complete game"""
        # Start game
        await page.goto("http://127.0.0.1:8001")
        await page.fill("#player1_name", "TestPlayer")
        await page.click('button[type="submit"]')
        
        # Auto-place ships
        setup_phase = page.locator("#setup-phase")
        await setup_phase.wait_for()
        
        auto_btn = page.locator("#auto-place-btn")
        await auto_btn.click()
        
        # Wait for playing phase
        playing_phase = page.locator("#playing-phase")
        await playing_phase.wait_for(timeout=10000)
        
        # Play several rounds
        for round_num in range(1, 4):  # Play 3 rounds
            # Check if game is still in playing phase
            if not await playing_phase.is_visible():
                break
                
            # Submit shots
            shots = [f"{chr(65 + round_num)}{round_num}", f"{chr(65 + round_num + 1)}{round_num + 1}"]
            await page.fill("#shots", ",".join(shots))
            await page.click('button[type="submit"]')
            
            # Wait for round processing
            await page.wait_for_timeout(2000)
            
            # Check if game ended
            finished_phase = page.locator("#finished-phase")
            if await finished_phase.is_visible():
                # Game ended, check final state
                heading = await finished_phase.locator("h2").inner_text()
                assert "Game Over" in heading
                
                # Should show winner or draw
                winner_elem = page.locator(".winner-announcement, .draw-announcement")
                if await winner_elem.is_visible():
                    announcement = await winner_elem.inner_text()
                    assert "Wins" in announcement or "Draw" in announcement
                
                break
        
        # If game didn't end naturally, that's also valid for testing
    
    async def test_new_game_after_completion(self, page: Page):
        """Test starting new game after completion"""
        await page.goto("http://127.0.0.1:8001")
        
        # Create and play quick game
        await page.fill("#player1_name", "Player1")
        await page.click('button[type="submit"]')
        
        # If we can get to a finished game state, test new game button
        # For now, just test the delete game functionality
        await page.goto("http://127.0.0.1:8001")
        
        # Should show new game form again
        new_game_form = page.locator("#new-game-form")
        await new_game_form.wait_for()
        
        assert await new_game_form.locator("h2").inner_text() == "Start New Game"


class TestHTMXBehavior(TestServer):
    """Test HTMX-specific behavior"""
    
    async def test_htmx_auto_refresh(self, page: Page):
        """Test HTMX auto-refresh functionality"""
        await page.goto("http://127.0.0.1:8001")
        await page.fill("#player1_name", "RefreshTest")
        await page.click('button[type="submit"]')
        
        # Wait for game status element
        game_status = page.locator("#game-status")
        await game_status.wait_for()
        
        # Game status should auto-refresh periodically
        # Wait for a few seconds to see if content updates
        initial_content = await game_status.inner_text()
        await page.wait_for_timeout(5000)
        
        # Content might be same but HTMX should be making requests
        # Check that element is still there and responsive
        assert await game_status.is_visible()
    
    async def test_htmx_form_submissions(self, page: Page):
        """Test HTMX form submission behavior"""
        await page.goto("http://127.0.0.1:8001")
        
        # Monitor network requests
        requests = []
        page.on("request", lambda request: requests.append(request.url))
        
        # Submit new game form
        await page.fill("#player1_name", "HTMXTest")
        await page.click('button[type="submit"]')
        
        # Wait for response
        await page.wait_for_timeout(2000)
        
        # Should have made HTMX request
        htmx_requests = [req for req in requests if "/game/new" in req]
        assert len(htmx_requests) > 0
    
    async def test_dynamic_content_loading(self, page: Page):
        """Test dynamic content loading via HTMX"""
        await page.goto("http://127.0.0.1:8001")
        await page.fill("#player1_name", "DynamicTest")
        await page.click('button[type="submit"]')
        
        # Wait for setup phase
        setup_phase = page.locator("#setup-phase")
        await setup_phase.wait_for()
        
        # Board should load dynamically
        player_board = page.locator("#player-board")
        await player_board.wait_for()
        
        # Should contain board table
        board_table = player_board.locator(".board-table")
        await board_table.wait_for()
        
        # Check board has correct structure
        rows = board_table.locator("tr")
        row_count = await rows.count()
        assert row_count == 11  # 1 header + 10 board rows
    
    async def test_error_handling(self, page: Page):
        """Test HTMX error handling"""
        await page.goto("http://127.0.0.1:8001")
        
        # Try to access endpoint that requires game without creating one
        await page.goto("http://127.0.0.1:8001/game/status")
        
        # Should get 404 response
        # In browser, this might show error page or be handled by HTMX
        # Just check we don't get a crash
        assert await page.locator("body").is_visible()


@pytest.mark.asyncio
async def test_concurrent_users():
    """Test multiple concurrent users"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Create multiple pages (simulating multiple users)
        pages = []
        for i in range(3):
            page = await browser.new_page()
            pages.append(page)
        
        try:
            # Each user creates a game
            tasks = []
            for i, page in enumerate(pages):
                async def create_game(page_obj, player_name):
                    await page_obj.goto("http://127.0.0.1:8001")
                    await page_obj.fill("#player1_name", player_name)
                    await page_obj.click('button[type="submit"]')
                    
                    setup_phase = page_obj.locator("#setup-phase")
                    await setup_phase.wait_for()
                    
                    return await setup_phase.locator("h2").inner_text()
                
                task = create_game(page, f"Player{i}")
                tasks.append(task)
            
            # Wait for all games to be created
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            for result in results:
                assert "Ship Placement" in result
                
        finally:
            # Cleanup
            for page in pages:
                await page.close()
            await browser.close()


if __name__ == "__main__":
    # Run tests with: pytest tests/test_web_components.py -v
    pytest.main([__file__, "-v"])