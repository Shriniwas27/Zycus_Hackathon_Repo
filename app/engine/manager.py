from typing import Dict, Type
import logging

from .base import CommerceAdvisorStrategy
from .rule_based import RuleBasedCommerceAdvisor
from .ai_advisor import AIAdvisorCommerceAdvisor
from ..config import settings


logger = logging.getLogger(__name__)


class StrategyManager:
    """
    Manages the active commerce advisor strategy.
    Allows switching strategies at runtime without restart.
    """
    
    def __init__(self):
        self._strategies: Dict[str, Type[CommerceAdvisorStrategy]] = {
            "RULE_BASED": RuleBasedCommerceAdvisor,
            "AI_ADVISOR": AIAdvisorCommerceAdvisor
        }
        
        # Initialize with default strategy from settings
        default_strategy = settings.DEFAULT_STRATEGY
        if default_strategy not in self._strategies:
            raise ValueError(f"Unknown default strategy: {default_strategy}")
            
        self._active_strategy_name = default_strategy
        self._active_strategy_instance = self._strategies[default_strategy]()
        
    def get_active_strategy(self) -> CommerceAdvisorStrategy:
        """Get the currently active strategy instance."""
        return self._active_strategy_instance
    
    def switch_strategy(self, strategy_name: str) -> bool:
        """
        Switch to a different strategy at runtime.
        
        Args:
            strategy_name: Name of the strategy to switch to
            
        Returns:
            True if switch was successful, False otherwise
        """
        if strategy_name not in self._strategies:
            logger.warning(f"Unknown strategy: {strategy_name}")
            return False
            
        if strategy_name == self._active_strategy_name:
            # Already active, no change needed
            return True
            
        try:
            # Create new strategy instance
            new_strategy = self._strategies[strategy_name]()
            # Update active strategy
            self._active_strategy_name = strategy_name
            self._active_strategy_instance = new_strategy
            logger.info(f"Switched to strategy: {strategy_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to switch to strategy {strategy_name}: {str(e)}")
            return False
    
    def get_active_strategy_name(self) -> str:
        """Get the name of the currently active strategy."""
        return self._active_strategy_name
    
    def get_available_strategies(self) -> list[str]:
        """Get list of available strategy names."""
        return list(self._strategies.keys())


# Global singleton instance
strategy_manager = StrategyManager()