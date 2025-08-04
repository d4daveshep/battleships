"""
Input handling utilities for the TUI interface.
"""

import re
from typing import List, Optional, Tuple
from game.models import Coordinate, ShipType, Direction


class InputHandler:
    """Handles user input parsing and validation"""
    
    @staticmethod
    def parse_coordinate(input_str: str) -> Optional[Coordinate]:
        """Parse a coordinate string like 'A1' or 'J10'"""
        input_str = input_str.strip().upper()
        
        # Match pattern like A1, B5, J10
        match = re.match(r'^([A-J])([1-9]|10)$', input_str)
        if not match:
            return None
        
        row_char, col_str = match.groups()
        row = ord(row_char) - ord('A')
        col = int(col_str) - 1
        
        return Coordinate(row, col)
    
    @staticmethod
    def parse_coordinates_list(input_str: str) -> List[Coordinate]:
        """Parse a list of coordinates like 'A1 B2 C3' or 'A1,B2,C3'"""
        # Split by comma or space
        parts = re.split(r'[,\s]+', input_str.strip())
        coordinates = []
        
        for part in parts:
            if part:  # Skip empty parts
                coord = InputHandler.parse_coordinate(part)
                if coord:
                    coordinates.append(coord)
        
        return coordinates
    
    @staticmethod
    def parse_direction(input_str: str) -> Optional[Direction]:
        """Parse direction input"""
        input_str = input_str.strip().lower()
        
        direction_map = {
            'h': Direction.HORIZONTAL,
            'horizontal': Direction.HORIZONTAL,
            'v': Direction.VERTICAL,
            'vertical': Direction.VERTICAL,
            'ne': Direction.DIAGONAL_NE,
            'diagonal_ne': Direction.DIAGONAL_NE,
            'northeast': Direction.DIAGONAL_NE,
            'se': Direction.DIAGONAL_SE,
            'diagonal_se': Direction.DIAGONAL_SE,
            'southeast': Direction.DIAGONAL_SE,
        }
        
        return direction_map.get(input_str)
    
    @staticmethod
    def get_valid_coordinate(display, prompt: str, allow_empty: bool = False) -> Optional[Coordinate]:
        """Get a valid coordinate from user with error handling"""
        while True:
            user_input = display.input(prompt).strip()
            
            if allow_empty and not user_input:
                return None
            
            coord = InputHandler.parse_coordinate(user_input)
            if coord:
                return coord
            
            display.print_error("Invalid coordinate. Use format like 'A1', 'B5', 'J10'")
    
    @staticmethod
    def get_valid_coordinates_list(display, prompt: str, expected_count: int) -> List[Coordinate]:
        """Get a list of valid coordinates from user"""
        while True:
            user_input = display.input(prompt)
            
            coordinates = InputHandler.parse_coordinates_list(user_input)
            
            if len(coordinates) == expected_count:
                # Check for duplicates
                if len(set(coordinates)) == len(coordinates):
                    return coordinates
                else:
                    display.print_error("Duplicate coordinates are not allowed.")
            else:
                display.print_error(f"Please enter exactly {expected_count} coordinates.")
    
    @staticmethod
    def get_valid_direction(display, prompt: str) -> Direction:
        """Get a valid direction from user with error handling"""
        while True:
            user_input = display.input(prompt)
            
            direction = InputHandler.parse_direction(user_input)
            if direction:
                return direction
            
            display.print_error("Invalid direction. Use: h/horizontal, v/vertical, ne/northeast, se/southeast")
    
    @staticmethod
    def get_yes_no(display, prompt: str, default: bool = True) -> bool:
        """Get a yes/no answer from user"""
        default_text = "Y/n" if default else "y/N"
        
        while True:
            user_input = display.input(f"{prompt} [{default_text}]").strip().lower()
            
            if not user_input:
                return default
            
            if user_input in ['y', 'yes', 'true', '1']:
                return True
            elif user_input in ['n', 'no', 'false', '0']:
                return False
            
            display.print_error("Please enter 'y' for yes or 'n' for no.")
    
    @staticmethod
    def get_menu_choice(display, options: List[str], prompt: str = "Choose an option") -> int:
        """Get a menu choice from user"""
        while True:
            # Display options
            for i, option in enumerate(options, 1):
                display.print(f"{i}. {option}")
            
            try:
                choice = int(display.input(f"{prompt} (1-{len(options)})"))
                if 1 <= choice <= len(options):
                    return choice - 1  # Return 0-based index
                else:
                    display.print_error(f"Please enter a number between 1 and {len(options)}")
            except ValueError:
                display.print_error("Please enter a valid number")
    
    @staticmethod
    def get_ship_placement(display, ship_type: ShipType) -> Tuple[Coordinate, Direction]:
        """Get ship placement from user (position and direction)"""
        display.print(f"\nPlacing {ship_type.ship_name} (length {ship_type.length})")
        
        # Get starting position
        coord = InputHandler.get_valid_coordinate(
            display, 
            f"Enter starting position for {ship_type.ship_name} (e.g., A1)"
        )
        
        # Get direction
        direction = InputHandler.get_valid_direction(
            display,
            "Enter direction (h/v/ne/se)"
        )
        
        return coord, direction
    
    @staticmethod
    def validate_coordinate_format(coord_str: str) -> bool:
        """Validate coordinate format without parsing"""
        return bool(re.match(r'^[A-J]([1-9]|10)$', coord_str.upper().strip()))