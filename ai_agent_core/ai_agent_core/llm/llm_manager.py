"""
Shared LLM Manager for reusing LLM instances across the application.
Supports multiple providers via LangChain.
"""

from typing import Dict, Any, Optional

try:
    from langchain_core.callbacks import StreamingStdOutCallbackHandler
except ImportError:
    StreamingStdOutCallbackHandler = None

# Using Any for return type hints since LangChain might not be installed in all environments
# The underlying return type is langchain_core.language_models.chat_models.BaseChatModel

class LLMManager:
    """
    Manages shared LLM instances to avoid creating multiple identical clients.
    """
    _instances: Dict[str, Any] = {}

    @classmethod
    def get_llm(cls, name: str = "default", config: Optional[Dict[str, Any]] = None) -> Any:
        """
        Retrieves an existing LLM instance by name, or creates a new one based on the configuration.
        """
        if name in cls._instances:
            return cls._instances[name]
        
        if config is None:
            from ai_agent_core.config.settings import DEFAULT_LLM_CONFIG
            config = DEFAULT_LLM_CONFIG

        provider = config.get("provider", "openai").lower()
        model_name = config.get("model", "gpt-4o-mini")
        temperature = config.get("temperature", 0.0)
        api_key = config.get("api_key")
        streaming = config.get("streaming", False)
        callbacks = config.get("callbacks", [])
        base_url = config.get("base_url")
        
        if streaming and StreamingStdOutCallbackHandler:
            callbacks.append(StreamingStdOutCallbackHandler())

        # Lazy loading LangChain dependencies
        if provider == "openai":
            from langchain_openai import ChatOpenAI
            kwargs = {"model": model_name, "temperature": temperature, "streaming": streaming, "callbacks": callbacks}
            if api_key: kwargs["api_key"] = api_key
            llm = ChatOpenAI(**kwargs)
        elif provider == "cerebras":
            from langchain_cerebras import ChatCerebras
            kwargs = {"model": model_name, "temperature": temperature, "streaming": streaming, "callbacks": callbacks}
            if api_key: kwargs["api_key"] = api_key
            llm = ChatCerebras(**kwargs)
        elif provider == "groq":
            from langchain_groq import ChatGroq
            kwargs = {"model": model_name, "temperature": temperature, "streaming": streaming, "callbacks": callbacks}
            if api_key: kwargs["api_key"] = api_key
            llm = ChatGroq(**kwargs)
        elif provider == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI
            kwargs = {"model": model_name, "temperature": temperature, "streaming": streaming, "callbacks": callbacks}
            if api_key: kwargs["api_key"] = api_key
            llm = ChatGoogleGenerativeAI(**kwargs)
        elif provider == "local":
            # Using modern langchain-ollama if available, fallback to community
            try:
                from langchain_ollama import ChatOllama
            except ImportError:
                from langchain_community.chat_models import ChatOllama
            
            kwargs = {"model": model_name, "temperature": temperature, "callbacks": callbacks}
            if base_url:
                kwargs["base_url"] = base_url
            llm = ChatOllama(**kwargs)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        cls._instances[name] = llm
        return llm
