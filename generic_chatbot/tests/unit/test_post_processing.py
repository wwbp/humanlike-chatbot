import pytest

from chatbot.services.post_processing import human_like_chunks


class TestPostProcessing:
    """Test the post-processing service for message chunking."""
    
    @pytest.mark.unit
    def test_human_like_chunks_simple_sentence(self):
        """Test that short sentences are returned as single chunks."""
        text = "Hello there."
        chunks = human_like_chunks(text)
        assert chunks == ["Hello there."]
    
    @pytest.mark.unit
    def test_human_like_chunks_multiple_sentences(self):
        """Test that multiple sentences are chunked appropriately."""
        text = "This is the first sentence. This is the second sentence. And a third one."
        chunks = human_like_chunks(text)
        # Each sentence becomes its own chunk due to the algorithm's natural behavior
        assert len(chunks) == 3
        assert chunks[0] == "This is the first sentence."
        assert chunks[1] == "This is the second sentence."
        assert chunks[2] == "And a third one."
    
    @pytest.mark.unit
    def test_human_like_chunks_with_question(self):
        """Test that questions at the end are separated into their own chunk."""
        text = "Here is some information. And here is more. Do you understand?"
        chunks = human_like_chunks(text)
        # Each sentence becomes its own chunk, including the question
        assert len(chunks) == 3
        assert chunks[0] == "Here is some information."
        assert chunks[1] == "And here is more."
        assert chunks[2] == "Do you understand?"
    
    @pytest.mark.unit
    def test_human_like_chunks_short_sentences(self):
        """Test that very short sentences are handled correctly."""
        text = "Hi. How are you? Good."
        chunks = human_like_chunks(text)
        assert len(chunks) == 3
        assert chunks == ["Hi.", "How are you?", "Good."]
    
    @pytest.mark.unit
    def test_human_like_chunks_long_text(self):
        """Test chunking of longer text with multiple sentences."""
        text = (
            "This is a longer piece of text. It contains multiple sentences. "
            "Each sentence should be processed correctly. We want to create "
            "natural chunks. This makes the conversation feel more human."
        )
        chunks = human_like_chunks(text)
        # The algorithm intelligently groups some sentences together
        assert len(chunks) == 4
        assert chunks[0] == "This is a longer piece of text. It contains multiple sentences."
        assert chunks[1] == "Each sentence should be processed correctly."
        assert chunks[2] == "We want to create natural chunks."
        assert chunks[3] == "This makes the conversation feel more human."
    
    @pytest.mark.unit
    def test_human_like_chunks_empty_string(self):
        """Test handling of empty string input."""
        text = ""
        chunks = human_like_chunks(text)
        assert chunks == []
    
    @pytest.mark.unit
    def test_human_like_chunks_single_word(self):
        """Test handling of single word input."""
        text = "Hello"
        chunks = human_like_chunks(text)
        assert chunks == ["Hello"]
    
    @pytest.mark.unit
    def test_human_like_chunks_with_ellipsis(self):
        """Test handling of text with ellipsis."""
        text = "This is a sentence... And another one."
        chunks = human_like_chunks(text)
        # NLTK doesn't recognize ellipsis as sentence boundary, so it's treated as one sentence
        assert len(chunks) == 1
        assert chunks[0] == "This is a sentence... And another one."
    
    @pytest.mark.unit
    def test_human_like_chunks_with_exclamation(self):
        """Test handling of text with exclamation marks."""
        text = "Wow! This is amazing! How cool is this?"
        chunks = human_like_chunks(text)
        assert len(chunks) == 3
        assert chunks == ["Wow!", "This is amazing!", "How cool is this?"]
    
    @pytest.mark.unit
    def test_human_like_chunks_complex_scenario(self):
        """Test a complex real-world scenario."""
        text = (
            "I understand your concern. Let me explain the process step by step. "
            "First, we'll need to gather some information. Then we can proceed. "
            "Does that sound good to you? Let me know if you have questions."
        )
        chunks = human_like_chunks(text)
        # The algorithm intelligently groups some sentences together
        assert len(chunks) == 5
        assert chunks[0] == "I understand your concern."
        assert chunks[1] == "Let me explain the process step by step. First, we'll need to gather some information."
        assert chunks[2] == "Then we can proceed."
        assert chunks[3] == "Does that sound good to you?"
        assert chunks[4] == "Let me know if you have questions."
    
    @pytest.mark.unit
    def test_human_like_chunks_preserves_whitespace(self):
        """Test that whitespace is preserved appropriately."""
        text = "  Hello there.  How are you?  "
        chunks = human_like_chunks(text)
        assert chunks == ["Hello there.", "How are you?"]
    
    @pytest.mark.unit
    def test_human_like_chunks_with_numbers(self):
        """Test handling of text with numbers and punctuation."""
        text = "The answer is 42. That's correct. Isn't it amazing?"
        chunks = human_like_chunks(text)
        # Each sentence becomes its own chunk
        assert len(chunks) == 3
        assert chunks[0] == "The answer is 42."
        assert chunks[1] == "That's correct."
        assert chunks[2] == "Isn't it amazing?"
