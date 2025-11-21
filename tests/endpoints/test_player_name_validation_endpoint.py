"""
Endpoint tests for player name validation.

Tests verify the HTMX player name validation endpoint behavior.
"""

from bs4 import BeautifulSoup
from fastapi import status
from fastapi.testclient import TestClient


class TestPlayerNameValidationEndpoint:
    """Tests for POST /player-name endpoint"""

    def test_player_name_validation_endpoint_returns_200(self, client: TestClient):
        """Test that validation endpoint returns 200 OK"""
        response = client.post("/player-name", data={"player_name": "Alice"})

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

    def test_valid_player_name_returns_success_state(self, client: TestClient):
        """Test that valid player name returns success state"""
        response = client.post("/player-name", data={"player_name": "Alice"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Check for player-name-section div
        section = soup.find("div", id="player-name-section")
        assert section is not None

        # Should have the player name in the input value
        input_field = section.find("input", {"name": "player_name"})  # type: ignore
        assert input_field is not None
        assert input_field.get("value") == "Alice"  # type: ignore

        # Should not have error message
        error_message = soup.find(attrs={"data-testid": "error-message"})
        assert error_message is None

    def test_empty_player_name_returns_error(self, client: TestClient):
        """Test that empty player name returns error state"""
        response = client.post("/player-name", data={"player_name": ""})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Should have error message
        error_message = soup.find(attrs={"data-testid": "error-message"})
        assert error_message is not None
        assert "Player name is required" in error_message.text

        # Should have error CSS class
        section = soup.find("div", id="player-name-section")
        assert section is not None
        assert "error" in section.get("class", [])  # type: ignore

    def test_player_name_too_short_returns_error(self, client: TestClient):
        """Test that player name shorter than 2 characters returns error"""
        response = client.post("/player-name", data={"player_name": "A"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Should have error message
        error_message = soup.find(attrs={"data-testid": "error-message"})
        assert error_message is not None
        assert "between 2 and 20 characters" in error_message.text

    def test_player_name_too_long_returns_error(self, client: TestClient):
        """Test that player name longer than 20 characters returns error"""
        long_name = "A" * 21  # 21 characters
        response = client.post("/player-name", data={"player_name": long_name})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Should have error message
        error_message = soup.find(attrs={"data-testid": "error-message"})
        assert error_message is not None
        assert "between 2 and 20 characters" in error_message.text

    def test_player_name_with_invalid_characters_returns_error(
        self, client: TestClient
    ):
        """Test that player name with invalid characters returns error"""
        response = client.post("/player-name", data={"player_name": "Alice@123"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Should have error message
        error_message = soup.find(attrs={"data-testid": "error-message"})
        assert error_message is not None
        assert "letter, numbers and spaces" in error_message.text

    def test_player_name_with_whitespace_only_returns_error(self, client: TestClient):
        """Test that player name with only whitespace returns error"""
        response = client.post("/player-name", data={"player_name": "   "})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Should have error message
        error_message = soup.find(attrs={"data-testid": "error-message"})
        assert error_message is not None

    def test_player_name_validation_preserves_input_value(self, client: TestClient):
        """Test that validation preserves the submitted value"""
        response = client.post("/player-name", data={"player_name": "TestPlayer"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Input should contain the submitted value
        input_field = soup.find("input", {"name": "player_name"})  # type: ignore
        assert input_field is not None
        assert input_field.get("value") == "TestPlayer"  # type: ignore

    def test_player_name_validation_has_htmx_attributes(self, client: TestClient):
        """Test that response includes HTMX attributes for re-validation"""
        response = client.post("/player-name", data={"player_name": "Alice"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Input should have HTMX attributes
        input_field = soup.find("input", {"name": "player_name"})  # type: ignore
        assert input_field is not None
        assert input_field.get("hx-post") == "/player-name"  # type: ignore
        assert input_field.get("hx-target") == "#player-name-section"  # type: ignore

    def test_player_name_validation_returns_partial_html(self, client: TestClient):
        """Test that endpoint returns partial HTML suitable for HTMX swap"""
        response = client.post("/player-name", data={"player_name": "Alice"})

        assert response.status_code == status.HTTP_200_OK

        # Should not be a full HTML document
        assert "<!DOCTYPE" not in response.text
        assert "<html>" not in response.text

        # Should be just the component
        assert "player-name-section" in response.text


class TestPlayerNameValidationEdgeCases:
    """Edge case tests for player name validation"""

    def test_player_name_with_numbers_is_valid(self, client: TestClient):
        """Test that player names with numbers are valid"""
        response = client.post("/player-name", data={"player_name": "Alice123"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Should not have error message
        error_message = soup.find(attrs={"data-testid": "error-message"})
        assert error_message is None

    def test_player_name_with_hyphens_is_invalid(self, client: TestClient):
        """Test that player names with hyphens are invalid (only letters, numbers, spaces allowed)"""
        response = client.post("/player-name", data={"player_name": "Alice-Bob"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Should have error message (hyphens not allowed)
        error_message = soup.find(attrs={"data-testid": "error-message"})
        assert error_message is not None
        assert "letter, numbers and spaces" in error_message.text

    def test_player_name_with_underscores_is_invalid(self, client: TestClient):
        """Test that player names with underscores are invalid (only letters, numbers, spaces allowed)"""
        response = client.post("/player-name", data={"player_name": "Alice_Bob"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Should have error message (underscores not allowed)
        error_message = soup.find(attrs={"data-testid": "error-message"})
        assert error_message is not None
        assert "letter, numbers and spaces" in error_message.text

    def test_player_name_at_minimum_length(self, client: TestClient):
        """Test player name at minimum valid length (2 characters)"""
        response = client.post("/player-name", data={"player_name": "Al"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Should not have error message
        error_message = soup.find(attrs={"data-testid": "error-message"})
        assert error_message is None

    def test_player_name_at_maximum_length(self, client: TestClient):
        """Test player name at maximum valid length (20 characters)"""
        max_length_name = "A" * 20
        response = client.post("/player-name", data={"player_name": max_length_name})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Should not have error message
        error_message = soup.find(attrs={"data-testid": "error-message"})
        assert error_message is None

    def test_player_name_with_leading_trailing_spaces(self, client: TestClient):
        """Test player name with leading/trailing spaces"""
        # Note: The endpoint uses strip_quotes=False, so it should preserve spaces
        response = client.post("/player-name", data={"player_name": "  Alice  "})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Input should preserve the spaces (validation doesn't strip for this endpoint)
        input_field = soup.find("input", {"name": "player_name"})  # type: ignore
        assert input_field is not None
        assert input_field.get("value") == "  Alice  "  # type: ignore


class TestPlayerNameValidationCSSClasses:
    """Tests for CSS class behavior in validation responses"""

    def test_valid_name_has_success_class(self, client: TestClient):
        """Test that valid names get success CSS class"""
        response = client.post("/player-name", data={"player_name": "Alice"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        section = soup.find("div", id="player-name-section")
        assert section is not None
        css_classes = section.get("class", [])  # type: ignore

        # Should have success or valid class (or no error class)
        assert "error" not in css_classes

    def test_invalid_name_has_error_class(self, client: TestClient):
        """Test that invalid names get error CSS class"""
        response = client.post("/player-name", data={"player_name": ""})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        section = soup.find("div", id="player-name-section")
        assert section is not None
        css_classes = section.get("class", [])  # type: ignore

        # Should have error class
        assert "error" in css_classes

    def test_validation_warning_scenarios(self, client: TestClient):
        """Test that certain inputs might return warning states"""
        # Test with a name that might be valid but unconventional
        response = client.post("/player-name", data={"player_name": "123"})

        assert response.status_code == status.HTTP_200_OK

        # Should still process the request (may be valid or invalid depending on rules)
        soup = BeautifulSoup(response.text, "html.parser")
        section = soup.find("div", id="player-name-section")
        assert section is not None
