"""
Gemini AI client for the inbuilt MCP server.
"""
import logging
from typing import Optional, List, Dict, Any
import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Client for interacting with Google's Gemini AI API.
    
    Provides methods for:
    - Chat completion
    - Text summarization
    - Content analysis
    - Code explanation
    """
    
    def __init__(self):
        self._configured = False
        self._model = None
    
    def configure(self):
        """Configure the Gemini API client."""
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set, Gemini features will be disabled")
            return False
        
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._model = genai.GenerativeModel(settings.GEMINI_MODEL)
            self._configured = True
            logger.info(f"Gemini client configured with model: {settings.GEMINI_MODEL}")
            return True
        except Exception as e:
            logger.error(f"Failed to configure Gemini client: {e}")
            return False
    
    @property
    def is_configured(self) -> bool:
        """Check if the client is properly configured."""
        return self._configured
    
    async def chat(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a chat response using Gemini.
        
        Args:
            message: The user's message
            conversation_history: Optional list of previous messages
            system_prompt: Optional system prompt for context
        
        Returns:
            Dict with 'response' text and 'success' boolean
        """
        if not self._configured:
            return {
                "success": False,
                "response": "Gemini AI is not configured. Please set GEMINI_API_KEY.",
                "error": "not_configured"
            }
        
        try:
            # Build the prompt with context
            full_prompt = ""
            
            if system_prompt:
                full_prompt += f"System: {system_prompt}\n\n"
            
            if conversation_history:
                for msg in conversation_history[-10:]:  # Last 10 messages for context
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    full_prompt += f"{role.capitalize()}: {content}\n"
            
            full_prompt += f"User: {message}\n\nAssistant:"
            
            # Generate response
            response = await self._model.generate_content_async(full_prompt)
            
            # Safe text extraction
            text_response = ""
            try:
                text_response = response.text
            except Exception:
                if response.candidates:
                    finish_reason = response.candidates[0].finish_reason
                    text_response = f"No text content returned. (Finish Reason: {finish_reason})"
                else:
                    text_response = "No response candidates returned."

            return {
                "success": True,
                "response": text_response,
                "model": settings.GEMINI_MODEL
            }
            
        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            return {
                "success": False,
                "response": f"Error generating response: {str(e)}",
                "error": str(e)
            }
    
    async def summarize(self, text: str, max_length: Optional[int] = None) -> Dict[str, Any]:
        """
        Summarize the given text.
        
        Args:
            text: Text to summarize
            max_length: Optional maximum length for summary
        
        Returns:
            Dict with 'summary' and 'success' boolean
        """
        if not self._configured:
            return {
                "success": False,
                "summary": "Gemini AI is not configured.",
                "error": "not_configured"
            }
        
        try:
            length_instruction = ""
            if max_length:
                length_instruction = f" Keep the summary under {max_length} words."
            
            prompt = f"""Please provide a clear and concise summary of the following text.{length_instruction}

Text to summarize:
{text}

Summary:"""
            
            response = await self._model.generate_content_async(prompt)
            
            # Safe text extraction
            text_summary = ""
            try:
                text_summary = response.text
            except Exception:
                 text_summary = "Unable to generate summary (Empty response)."

            return {
                "success": True,
                "summary": text_summary,
                "original_length": len(text),
                "model": settings.GEMINI_MODEL
            }
            
        except Exception as e:
            logger.error(f"Gemini summarize error: {e}")
            return {
                "success": False,
                "summary": f"Error summarizing: {str(e)}",
                "error": str(e)
            }
    
    async def analyze(self, content: str, analysis_type: str = "general") -> Dict[str, Any]:
        """
        Analyze content and provide insights.
        
        Args:
            content: Content to analyze
            analysis_type: Type of analysis (general, sentiment, key_points, etc.)
        
        Returns:
            Dict with 'analysis' and 'success' boolean
        """
        if not self._configured:
            return {
                "success": False,
                "analysis": "Gemini AI is not configured.",
                "error": "not_configured"
            }
        
        try:
            analysis_prompts = {
                "general": "Provide a comprehensive analysis of the following content, including main themes, key points, and any notable observations.",
                "sentiment": "Analyze the sentiment of the following content. Identify the overall tone, emotional undertones, and any mixed sentiments.",
                "key_points": "Extract and list the key points from the following content in a clear, organized manner.",
                "structured": "Analyze the following content and provide a structured breakdown with categories, themes, and insights."
            }
            
            prompt_instruction = analysis_prompts.get(analysis_type, analysis_prompts["general"])
            
            prompt = f"""{prompt_instruction}

Content:
{content}

Analysis:"""
            
            response = await self._model.generate_content_async(prompt)
            
            # Safe text extraction
            text_analysis = ""
            try:
                text_analysis = response.text
            except Exception:
                 text_analysis = "Unable to generate analysis (Empty response)."

            return {
                "success": True,
                "analysis": text_analysis,
                "analysis_type": analysis_type,
                "model": settings.GEMINI_MODEL
            }
            
        except Exception as e:
            logger.error(f"Gemini analyze error: {e}")
            return {
                "success": False,
                "analysis": f"Error analyzing: {str(e)}",
                "error": str(e)
            }
    
    async def explain_code(
        self,
        code: str,
        language: Optional[str] = None,
        detail_level: str = "medium"
    ) -> Dict[str, Any]:
        """
        Explain a code snippet.
        
        Args:
            code: Code to explain
            language: Programming language (optional, will be auto-detected)
            detail_level: Level of detail (brief, medium, detailed)
        
        Returns:
            Dict with 'explanation' and 'success' boolean
        """
        if not self._configured:
            return {
                "success": False,
                "explanation": "Gemini AI is not configured.",
                "error": "not_configured"
            }
        
        try:
            lang_hint = f" (written in {language})" if language else ""
            
            detail_instructions = {
                "brief": "Provide a brief, high-level explanation.",
                "medium": "Provide a clear explanation covering the main logic and purpose.",
                "detailed": "Provide a detailed, line-by-line explanation of what the code does."
            }
            
            detail_instruction = detail_instructions.get(detail_level, detail_instructions["medium"])
            
            prompt = f"""Explain the following code{lang_hint}. {detail_instruction}

```
{code}
```

Explanation:"""
            
            response = await self._model.generate_content_async(prompt)
            
            # Safe text extraction
            text_explanation = ""
            try:
                text_explanation = response.text
            except Exception:
                 text_explanation = "Unable to explain code (Empty response)."

            return {
                "success": True,
                "explanation": text_explanation,
                "language": language or "auto-detected",
                "detail_level": detail_level,
                "model": settings.GEMINI_MODEL
            }
            
        except Exception as e:
            logger.error(f"Gemini code explain error: {e}")
            return {
                "success": False,
                "explanation": f"Error explaining code: {str(e)}",
                "error": str(e)
            }


# Global Gemini client instance
gemini_client = GeminiClient()


def get_gemini_client() -> GeminiClient:
    """Get the Gemini client instance."""
    return gemini_client
