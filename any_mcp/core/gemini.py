import google.generativeai as genai
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass 
class GeminiMessage:
    """Simple message structure to match Claude's interface"""
    content: str
    role: str = "user"


class Gemini:
    """
    Gemini API service class that provides a similar interface to Claude class.
    Supports text generation with tools and conversation management.
    """
    
    def __init__(self, model: str = "gemini-1.5-pro", api_key: str = None):
        self.model = model
        if api_key:
            genai.configure(api_key=api_key)
        
        # Initialize the model
        self.client = genai.GenerativeModel(model)
        
    def add_user_message(self, messages: List[Dict], message: Any):
        """Add a user message to the conversation"""
        content = message.content if hasattr(message, 'content') else str(message)
        user_message = {
            "role": "user", 
            "content": content
        }
        messages.append(user_message)
        
    def add_assistant_message(self, messages: List[Dict], message: Any):
        """Add an assistant message to the conversation"""
        content = message.content if hasattr(message, 'content') else str(message)
        assistant_message = {
            "role": "assistant",
            "content": content
        }
        messages.append(assistant_message)
        
    def text_from_message(self, response) -> str:
        """Extract text from Gemini response"""
        if hasattr(response, 'text'):
            return response.text
        elif hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
    
    def _convert_messages_to_gemini_format(self, messages: List[Dict]) -> List[Dict]:
        """Convert messages to Gemini's expected format"""
        gemini_messages = []
        
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model" 
            gemini_messages.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
            
        return gemini_messages
    
    def _convert_tools_to_gemini_format(self, tools: Optional[List[Dict]]) -> Optional[List[Dict]]:
        """Convert tools from Claude format to Gemini format if needed"""
        if not tools:
            return None
            
        # For now, return None to disable tools - can be enhanced later
        # Gemini has a different tool calling format than Claude
        return None
    
    def chat(
        self,
        messages: List[Dict],
        system: Optional[str] = None,
        temperature: float = 1.0,
        stop_sequences: List[str] = None,
        tools: Optional[List[Dict]] = None,
        thinking: bool = False,
        thinking_budget: int = 1024,
    ) -> GeminiMessage:
        """
        Generate a response using Gemini API
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system: System prompt (will be prepended to conversation)
            temperature: Controls randomness (0.0 to 2.0)
            stop_sequences: List of sequences to stop generation 
            tools: List of tools (not implemented yet)
            thinking: Enable thinking mode (not supported by Gemini)
            thinking_budget: Thinking budget (not supported by Gemini)
            
        Returns:
            GeminiMessage with the response
        """
        try:
            # Convert messages to Gemini format
            gemini_messages = self._convert_messages_to_gemini_format(messages)
            
            # Prepare the conversation
            conversation_parts = []
            
            # Add system message if provided
            if system:
                conversation_parts.append(f"System: {system}\n\n")
            
            # Add conversation history
            for msg in messages:
                role_label = "Human" if msg["role"] == "user" else "Assistant"
                conversation_parts.append(f"{role_label}: {msg['content']}\n\n")
            
            # Combine into a single prompt for now (simpler approach)
            full_prompt = "".join(conversation_parts)
            
            # Generate response
            response = self.client.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=8000,
                    stop_sequences=stop_sequences or []
                )
            )
            
            # Return response in Claude-compatible format
            return GeminiMessage(
                content=response.text,
                role="assistant"
            )
            
        except Exception as e:
            # Return error message in expected format
            return GeminiMessage(
                content=f"Error generating response: {str(e)}",
                role="assistant"
            )
    
    async def chat_async(
        self,
        messages: List[Dict],
        system: Optional[str] = None,
        temperature: float = 1.0,
        stop_sequences: List[str] = None,
        tools: Optional[List[Dict]] = None,
    ) -> GeminiMessage:
        """Async version of chat method"""
        # For now, run sync version in thread pool
        # Can be improved with native async when Gemini supports it better
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.chat,
            messages, system, temperature, stop_sequences, tools
        )