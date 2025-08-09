import os
from unittest.mock import Mock, patch

import pytest

from server.engine import get_or_create_engine, initialize_engine


class TestEngine:
    """Test the AI engine initialization and management."""
    
    @pytest.mark.unit
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-openai-key"})
    @patch("server.engine.OpenAIEngine")
    def test_initialize_engine_openai(self, mock_openai_engine):
        """Test OpenAI engine initialization."""
        mock_engine = Mock()
        mock_openai_engine.return_value = mock_engine
        
        result = initialize_engine("OpenAI", "gpt-4")
        
        mock_openai_engine.assert_called_once_with(
            api_key="test-openai-key",
            model="gpt-4",
        )
        assert result == mock_engine
    
    @pytest.mark.unit
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-anthropic-key"})
    @patch("server.engine.AnthropicEngine")
    def test_initialize_engine_anthropic(self, mock_anthropic_engine):
        """Test Anthropic engine initialization."""
        mock_engine = Mock()
        mock_anthropic_engine.return_value = mock_engine
        
        result = initialize_engine("Anthropic", "claude-3-sonnet")
        
        mock_anthropic_engine.assert_called_once_with(
            api_key="test-anthropic-key",
            model="claude-3-sonnet",
        )
        assert result == mock_engine
    
    @pytest.mark.unit
    @patch.dict(os.environ, {"OPENAI_API_KEY": ""})
    def test_initialize_engine_openai_missing_key(self):
        """Test OpenAI engine initialization with missing API key."""
        with pytest.raises(ValueError, match="Missing OPENAI_API_KEY"):
            initialize_engine("OpenAI", "gpt-4")
    
    @pytest.mark.unit
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""})
    def test_initialize_engine_anthropic_missing_key(self):
        """Test Anthropic engine initialization with missing API key."""
        with pytest.raises(ValueError, match="Missing ANTHROPIC_API_KEY"):
            initialize_engine("Anthropic", "claude-3-sonnet")
    
    @pytest.mark.unit
    def test_initialize_engine_unsupported_type(self):
        """Test engine initialization with unsupported model type."""
        with pytest.raises(ValueError, match="Unsupported model type: InvalidModel"):
            initialize_engine("InvalidModel", "some-model")
    
    @pytest.mark.unit
    def test_get_or_create_engine_new_instance(self):
        """Test creating a new engine instance."""
        engine_instances = {}
        
        with patch("server.engine.initialize_engine") as mock_init:
            mock_engine = Mock()
            mock_init.return_value = mock_engine
            
            result = get_or_create_engine("OpenAI", "gpt-4", engine_instances)
            
            mock_init.assert_called_once_with("OpenAI", "gpt-4")
            assert result == mock_engine
            assert engine_instances[("OpenAI", "gpt-4")] == mock_engine
    
    @pytest.mark.unit
    def test_get_or_create_engine_existing_instance(self):
        """Test retrieving an existing engine instance."""
        engine_instances = {}
        mock_engine = Mock()
        engine_instances[("OpenAI", "gpt-4")] = mock_engine
        
        with patch("server.engine.initialize_engine") as mock_init:
            result = get_or_create_engine("OpenAI", "gpt-4", engine_instances)
            
            # Should not call initialize_engine again
            mock_init.assert_not_called()
            assert result == mock_engine
    
    @pytest.mark.unit
    def test_get_or_create_engine_multiple_models(self):
        """Test managing multiple engine instances."""
        engine_instances = {}
        
        with patch("server.engine.initialize_engine") as mock_init:
            mock_openai_engine = Mock()
            mock_anthropic_engine = Mock()
            
            mock_init.side_effect = [mock_openai_engine, mock_anthropic_engine]
            
            # Create OpenAI engine
            result1 = get_or_create_engine("OpenAI", "gpt-4", engine_instances)
            assert result1 == mock_openai_engine
            
            # Create Anthropic engine
            result2 = get_or_create_engine("Anthropic", "claude-3-sonnet", engine_instances)
            assert result2 == mock_anthropic_engine
            
            # Verify both are stored
            assert engine_instances[("OpenAI", "gpt-4")] == mock_openai_engine
            assert engine_instances[("Anthropic", "claude-3-sonnet")] == mock_anthropic_engine
            
            # Verify initialize_engine was called twice
            assert mock_init.call_count == 2
    
    @pytest.mark.unit
    def test_get_or_create_engine_same_model_different_instances(self):
        """Test that different engine instances don't interfere."""
        engine_instances1 = {}
        engine_instances2 = {}
        
        with patch("server.engine.initialize_engine") as mock_init:
            mock_engine1 = Mock()
            mock_engine2 = Mock()
            
            mock_init.side_effect = [mock_engine1, mock_engine2]
            
            # Create engines in different instances
            result1 = get_or_create_engine("OpenAI", "gpt-4", engine_instances1)
            result2 = get_or_create_engine("OpenAI", "gpt-4", engine_instances2)
            
            assert result1 == mock_engine1
            assert result2 == mock_engine2
            
            # Verify they're stored separately
            assert engine_instances1[("OpenAI", "gpt-4")] == mock_engine1
            assert engine_instances2[("OpenAI", "gpt-4")] == mock_engine2
    
    @pytest.mark.unit
    def test_engine_instances_isolation(self):
        """Test that engine instances are properly isolated between calls."""
        engine_instances = {}
        
        with patch("server.engine.initialize_engine") as mock_init:
            mock_engine = Mock()
            mock_init.return_value = mock_engine
            
            # First call
            result1 = get_or_create_engine("OpenAI", "gpt-4", engine_instances)
            
            # Second call with same parameters
            result2 = get_or_create_engine("OpenAI", "gpt-4", engine_instances)
            
            # Should be the same instance
            assert result1 is result2
            
            # Should only call initialize_engine once
            mock_init.assert_called_once()
    
    @pytest.mark.unit
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("server.engine.OpenAIEngine")
    def test_initialize_engine_with_csv_name(self, mock_openai_engine):
        """Test engine initialization with optional csv_name parameter."""
        mock_engine = Mock()
        mock_openai_engine.return_value = mock_engine
        
        # csv_name parameter is currently not used, but test it doesn't break
        result = initialize_engine("OpenAI", "gpt-4", "test.csv")
        
        mock_openai_engine.assert_called_once_with(
            api_key="test-key",
            model="gpt-4",
        )
        assert result == mock_engine
    
    @pytest.mark.unit
    def test_get_or_create_engine_logging(self):
        """Test that engine creation is logged."""
        engine_instances = {}
        
        with patch("server.engine.logger") as mock_logger, patch("server.engine.initialize_engine") as mock_init:
            mock_engine = Mock()
            mock_init.return_value = mock_engine
            
            get_or_create_engine("OpenAI", "gpt-4", engine_instances)
            
            mock_logger.info.assert_called_once_with(
                "Initializing Engine: Type=OpenAI, Model=gpt-4",
            )
    
    @pytest.mark.unit
    def test_get_or_create_engine_no_logging_for_existing(self):
        """Test that existing engines don't trigger logging."""
        engine_instances = {}
        mock_engine = Mock()
        engine_instances[("OpenAI", "gpt-4")] = mock_engine
        
        with patch("server.engine.logger") as mock_logger:
            get_or_create_engine("OpenAI", "gpt-4", engine_instances)
            
            # Should not log for existing engine
            mock_logger.info.assert_not_called()
