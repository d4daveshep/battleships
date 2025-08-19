from services.auth_service import PlayerNameValidation


class TestAuthService:
    # Unit tests for AuthService - extracted from main.py validation logic
    
    def test_valid_player_name(self, auth_service):
        # Test valid player name validation
        result = auth_service.validate_player_name("John", strip_quotes=False)
        
        assert result.is_valid is True
        assert result.error_message == ""
        assert result.css_class == "valid"
    
    def test_valid_player_name_with_spaces(self, auth_service):
        # Test valid player name with spaces
        result = auth_service.validate_player_name("John Doe", strip_quotes=False)
        
        assert result.is_valid is True
        assert result.error_message == ""
        assert result.css_class == "valid"
    
    def test_valid_player_name_with_numbers(self, auth_service):
        # Test valid player name with numbers
        result = auth_service.validate_player_name("Player123", strip_quotes=False)
        
        assert result.is_valid is True
        assert result.error_message == ""
        assert result.css_class == "valid"
    
    def test_empty_player_name(self, auth_service):
        # Test empty player name validation
        result = auth_service.validate_player_name("", strip_quotes=False)
        
        assert result.is_valid is False
        assert result.error_message == "Player name is required"
        assert result.css_class == "error"
    
    def test_whitespace_only_player_name(self, auth_service):
        # Test whitespace-only player name validation
        result = auth_service.validate_player_name("   ", strip_quotes=False)
        
        assert result.is_valid is False
        assert result.error_message == "Player name is required"
        assert result.css_class == "error"
    
    def test_player_name_too_short(self, auth_service):
        # Test player name too short validation
        result = auth_service.validate_player_name("A", strip_quotes=False)
        
        assert result.is_valid is False
        assert result.error_message == "Player name must be between 2 and 20 characters"
        assert result.css_class == "error"
    
    def test_player_name_too_long(self, auth_service):
        # Test player name too long validation
        long_name = "A" * 21
        result = auth_service.validate_player_name(long_name, strip_quotes=False)
        
        assert result.is_valid is False
        assert result.error_message == "Player name must be between 2 and 20 characters"
        assert result.css_class == "error"
    
    def test_player_name_at_min_length(self, auth_service):
        # Test player name at minimum length (2 chars)
        result = auth_service.validate_player_name("AB", strip_quotes=False)
        
        assert result.is_valid is True
        assert result.error_message == ""
        assert result.css_class == "valid"
    
    def test_player_name_at_max_length(self, auth_service):
        # Test player name at maximum length (20 chars)
        max_name = "A" * 20
        result = auth_service.validate_player_name(max_name, strip_quotes=False)
        
        assert result.is_valid is True
        assert result.error_message == ""
        assert result.css_class == "valid"
    
    def test_player_name_with_special_characters(self, auth_service):
        # Test player name with special characters (should fail)
        result = auth_service.validate_player_name("Player@123", strip_quotes=False)
        
        assert result.is_valid is False
        assert result.error_message == "Player name can only contain letter, numbers and spaces"
        assert result.css_class == "error"
    
    def test_player_name_with_quotes_no_strip(self, auth_service):
        # Test player name with quotes when strip_quotes=False
        result = auth_service.validate_player_name('"Player"', strip_quotes=False)
        
        assert result.is_valid is False
        assert result.error_message == "Player name can only contain letter, numbers and spaces"
        assert result.css_class == "error"
    
    def test_player_name_with_quotes_strip_enabled(self, auth_service):
        # Test player name with quotes when strip_quotes=True
        result = auth_service.validate_player_name('"Player"', strip_quotes=True)
        
        assert result.is_valid is True
        assert result.error_message == ""
        assert result.css_class == "valid"
    
    def test_player_name_with_single_quotes_strip_enabled(self, auth_service):
        # Test player name with single quotes when strip_quotes=True
        result = auth_service.validate_player_name("'Player'", strip_quotes=True)
        
        assert result.is_valid is True
        assert result.error_message == ""
        assert result.css_class == "valid"
    
    def test_player_name_with_mixed_quotes_strip_enabled(self, auth_service):
        # Test player name with mixed quotes when strip_quotes=True
        result = auth_service.validate_player_name('"Player\'', strip_quotes=True)
        
        assert result.is_valid is True
        assert result.error_message == ""
        assert result.css_class == "valid"
    
    def test_quoted_empty_name_strip_enabled(self, auth_service):
        # Test empty quoted name when strip_quotes=True
        result = auth_service.validate_player_name('""', strip_quotes=True)
        
        assert result.is_valid is False
        assert result.error_message == "Player name is required"
        assert result.css_class == "error"
    
    def test_whitespace_with_strip_quotes(self, auth_service):
        # Test whitespace handling with strip_quotes=True
        result = auth_service.validate_player_name('  "Player"  ', strip_quotes=True)
        
        assert result.is_valid is True
        assert result.error_message == ""
        assert result.css_class == "valid"