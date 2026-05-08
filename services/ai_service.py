import os
from core.config import settings
import logging
import asyncio

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.provider = settings.AI_PROVIDER.lower()
        self.openai_client = None
        self.ollama_client = None
        self.genai = None # For Gemini
        self._initialized = False

    def _initialize_provider(self):
        """
        🔥 LAZY INITIALIZATION: Only load heavy libraries and configure providers 
        when the service is actually used for the first time.
        """
        if self._initialized:
            return

        self.provider = settings.AI_PROVIDER.lower()
        logger.info(f"🚀 [AI] Initializing {self.provider} provider...")

        if self.provider == "openai":
            try:
                from openai import OpenAI
                if settings.OPENAI_API_KEY:
                    self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                    self.model = "gpt-4o-mini"
                else:
                    logger.warning("OPENAI_API_KEY not configured.")
            except ImportError:
                logger.error("openai package not installed.")

        elif self.provider == "gemini":
            try:
                import google.generativeai as genai
                self.genai = genai
                if settings.GEMINI_API_KEY:
                    genai.configure(api_key=settings.GEMINI_API_KEY)
                    # Use model from settings with a stable default
                    self.model = getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")
                    logger.info(f"Gemini provider initialized with model: {self.model}")
                else:
                    logger.warning("GEMINI_API_KEY not configured.")
            except ImportError:
                logger.error("google-generativeai package not installed.")

        elif self.provider == "ollama":
            try:
                import ollama
                self.model = settings.OLLAMA_MODEL
                headers = {}
                if settings.OLLAMA_API_KEY:
                    headers["Authorization"] = f"Bearer {settings.OLLAMA_API_KEY}"
                
                self.ollama_client = ollama.Client(
                    host=settings.OLLAMA_BASE_URL,
                    headers=headers
                )
                logger.info(f"Ollama provider initialized with model: {self.model} at {settings.OLLAMA_BASE_URL}")
            except ImportError:
                logger.error("ollama package not installed.")
        
        self._initialized = True

    async def generate_reply(self, prompt: str, device_id: str = "default") -> str:
        """Generate a reply using the configured provider"""
        # 🔥 Safety: Don't run if chatbot is disabled (unless it's a SYSTEM request)
        if not settings.ENABLE_AI_CHATBOT and device_id != "SYSTEM":
            return "AI Chatbot is currently disabled in settings."

        # Ensure provider is initialized
        if not self._initialized or self.provider != settings.AI_PROVIDER.lower():
            self._initialized = False # Force re-init if provider changed
            self._initialize_provider()

        if self.provider == "openai":
            return await self._generate_openai_reply(prompt, device_id)
        elif self.provider == "gemini":
            return await self._generate_gemini_reply(prompt, device_id)
        elif self.provider == "ollama":
            return await self._generate_ollama_reply(prompt, device_id)
        else:
            return f"Error: Unknown AI provider '{self.provider}'"

    async def _generate_openai_reply(self, prompt: str, device_id: str) -> str:
        if not self.openai_client:
            return "OpenAI client not initialized. Please check your API key."
        
        try:
            from fastapi.concurrency import run_in_threadpool
            def sync_call():
                return self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000,
                    temperature=0.7
                )
            response = await run_in_threadpool(sync_call)
            if response and response.choices:
                return response.choices[0].message.content.strip()
            return "I'm sorry, I couldn't generate a response from OpenAI."
        except Exception as e:
            logger.error(f"❌ [OPENAI ERROR] Device {device_id}: {str(e)}")
            return f"OpenAI error: {str(e)[:100]}"

    async def _generate_gemini_reply(self, prompt: str, device_id: str) -> str:
        if not settings.GEMINI_API_KEY or not self.genai:
            return "Gemini API key not configured or package not loaded."
        
        try:
            model = self.genai.GenerativeModel(self.model)
            from fastapi.concurrency import run_in_threadpool
            def sync_call():
                return model.generate_content(prompt)
            response = await run_in_threadpool(sync_call)
            if response and response.text:
                return response.text.strip()
            return "I'm sorry, I couldn't generate a response from Gemini."
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ [GEMINI ERROR] Device {device_id}: {error_msg}")
            
            if "429" in error_msg or "quota" in error_msg.lower():
                # Extract wait time if present (e.g., "Please retry in 41.4s")
                import re
                wait_match = re.search(r"retry in (\d+\.?\d*)s", error_msg)
                wait_time = f" ({wait_match.group(1)}s)" if wait_match else ""
                return f"❌ AI Quota Exceeded. Please wait a moment{wait_time} or check your Google AI Studio plan limits."
                
            if "404" in error_msg or "models" in error_msg.lower():
                try:
                    models = [m.name for m in self.genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    logger.info(f"Available Gemini models: {models}")
                except:
                    pass
            return f"Gemini error: {error_msg[:100]}"

    async def _generate_ollama_reply(self, prompt: str, device_id: str) -> str:
        if not self.ollama_client:
            return "Ollama client not initialized."
        try:
            from fastapi.concurrency import run_in_threadpool
            def sync_call():
                return self.ollama_client.chat(
                    model=self.model,
                    messages=[{'role': 'user', 'content': prompt}]
                )
            response = await run_in_threadpool(sync_call)
            if response and 'message' in response:
                return response['message']['content'].strip()
            return "I'm sorry, I couldn't generate a response from Ollama."
        except Exception as e:
            logger.error(f"❌ [OLLAMA ERROR] Device {device_id}: {str(e)}")
            return f"Ollama error: Ensure Ollama is running at {settings.OLLAMA_BASE_URL} and model '{self.model}' is pulled."

# Singleton instance
ai_service = AIService()
