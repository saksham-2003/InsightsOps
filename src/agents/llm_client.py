import os
import time

from dotenv import load_dotenv
from groq import Groq
from google import genai
from google.genai import types

load_dotenv(override=True)


def get_groq_client():
    """
    Create and return the Groq API client.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY was not found. Add it to the .env file."
        )
    return Groq(api_key=api_key)


def get_gemini_client():
    """
    Create and return the Gemini client.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY was not found. Add it to the .env file."
        )
    return genai.Client(api_key=api_key)


def get_llm_provider():
    """
    Returns the configured LLM provider.
    Defaults to Groq.
    """
    return os.getenv("LLM_PROVIDER", "groq").lower()


def get_llm_client():
    """
    Return the client for the configured provider.
    """
    provider = get_llm_provider()
    if provider == "gemini":
        return get_gemini_client()
    return get_groq_client()


def get_mapped_model(model_name: str) -> str:
    """
    Maps logical model aliases or legacy names to actual provider models.
    Supports aliases: planner, insight_generator, reasoning, vision, etc.
    """
    provider = get_llm_provider()
    
    if provider == "gemini":
        gemini_mapping = {
            "planner": os.getenv("GEMINI_PLANNER_MODEL", "gemini-3.5-flash"),
            "insight_generator": os.getenv("GEMINI_INSIGHT_MODEL", "gemini-3.5-flash"),
            "reasoning": os.getenv("GEMINI_REASONING_MODEL", "gemini-3.5-flash"),
            "vision": os.getenv("GEMINI_VISION_MODEL", "gemini-3.5-flash"),
            "openai/gpt-oss-20b": os.getenv("GEMINI_DEFAULT_MODEL", "gemini-3.5-flash"),
        }
        return gemini_mapping.get(model_name, model_name if not model_name.startswith("openai/") else "gemini-3.5-flash")
    
    else:
        groq_mapping = {
            "planner": "openai/gpt-oss-20b",
            "insight_generator": "openai/gpt-oss-20b",
            "reasoning": "openai/gpt-oss-20b",
            "vision": "openai/gpt-oss-20b",
        }
        return groq_mapping.get(model_name, model_name)


def create_chat_completion_with_retry(
    client,
    max_retries=3,
    retry_delay=3,
    **kwargs
):
    """
    Create a chat completion using the configured LLM provider.
    Supports both Groq and Gemini with complete parameter and role preservation.
    Automatically falls back from Gemini to Groq if rate-limited, exhausted, unavailable, or timed out.
    """
    provider = get_llm_provider()
    print(f"\n========== USING LLM PROVIDER: {provider.upper()} ==========\n")
    last_error = None

    for attempt in range(max_retries):
        try:
            if provider == "groq":
                if "model" in kwargs:
                    kwargs["model"] = get_mapped_model(kwargs["model"])
                return client.chat.completions.create(**kwargs)

            elif provider == "gemini":
                model_name = get_mapped_model(kwargs.get("model", "gemini-3.5-flash"))
                messages = kwargs.get("messages", [])
                temperature = kwargs.get("temperature", 0.1)
                
                system_instruction = None
                gemini_contents = []

                for message in messages:
                    role = message.get("role")
                    content = message.get("content", "")
                    
                    if role == "system":
                        system_instruction = content
                    elif role == "user":
                        gemini_contents.append(
                            types.Content(
                                role="user",
                                parts=[types.Part.from_text(text=str(content))]
                            )
                        )
                    elif role == "assistant" or role == "model":
                        gemini_contents.append(
                            types.Content(
                                role="model",
                                parts=[types.Part.from_text(text=str(content))]
                            )
                        )
                    else:
                        gemini_contents.append(
                            types.Content(
                                role="user",
                                parts=[types.Part.from_text(text=str(content))]
                            )
                        )

                config_kwargs = {
                    "temperature": temperature,
                }

                if system_instruction:
                    config_kwargs["system_instruction"] = system_instruction

                response_format = kwargs.get("response_format")
                if response_format and isinstance(response_format, dict):
                    if response_format.get("type") == "json_object":
                        config_kwargs["response_mime_type"] = "application/json"

                config = types.GenerateContentConfig(**config_kwargs)

                print("Using model:", model_name)

                try:
                    return client.models.generate_content(
                        model=model_name,
                        contents=gemini_contents if gemini_contents else "",
                        config=config
                    )
                except Exception as gemini_err:
                    err_text = str(gemini_err).lower()
                    # Check if error matches fallback trigger criteria
                    is_fallback_trigger = any(
                        keyword in err_text for keyword in [
                            "429",
                            "503",
                            "resource_exhausted",
                            "resource exhausted",
                            "unavailable",
                            "timeout",
                            "timed out",
                            "rate limit"
                        ]
                    )

                    if is_fallback_trigger:
                        print(f"Gemini encountered transient limit/error ({gemini_err}). Automatically falling back to Groq...")
                        
                        # Create a NEW Groq client using get_groq_client() as requested
                        groq_client = get_groq_client()
                        
                        # Resolve the incoming model alias or name explicitly using Groq's mapping rules
                        raw_model = kwargs.get("model", "planner")
                        groq_mapping = {
                            "planner": "openai/gpt-oss-20b",
                            "insight_generator": "openai/gpt-oss-20b",
                            "reasoning": "openai/gpt-oss-20b",
                            "vision": "openai/gpt-oss-20b",
                        }
                        mapped_groq_model = groq_mapping.get(raw_model, raw_model)
                        
                        # Build a clean dictionary containing only parameters accepted by Groq
                        fallback_kwargs = {
                            "model": mapped_groq_model,
                            "messages": messages,
                        }
                        if "temperature" in kwargs:
                            fallback_kwargs["temperature"] = kwargs["temperature"]
                        if response_format:
                            fallback_kwargs["response_format"] = response_format
                            
                        # Execute Groq completion request using the new client and clean payload
                        return groq_client.chat.completions.create(**fallback_kwargs)
                    
                    # If not a fallback trigger, re-raise to handle standard retries/exceptions
                    raise gemini_err

            else:
                raise ValueError(
                    f"Unsupported provider: {provider}"
                )

        except Exception as error:
            last_error = error
            error_text = str(error).lower()

            is_retryable = (
                "429" in error_text
                or "503" in error_text
                or "unavailable" in error_text
                or "rate limit" in error_text
                or "resource_exhausted" in error_text
                or "resource exhausted" in error_text
            )

            if not is_retryable:
                raise

            if attempt < max_retries - 1:
                wait_time = retry_delay * (attempt + 1)
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

    raise last_error


def extract_response_text(response):
    """
    Extract text from the response, supporting Groq response structures,
    Gemini native structures, and fallback-parsed Groq completions returned during Gemini failure.
    """
    # 1. Check if the response object has Groq completion structure (.choices)
    if hasattr(response, "choices") and response.choices:
        try:
            return response.choices[0].message.content
        except Exception:
            pass

    # 2. Check standard Gemini response text attribute or candidates structure
    try:
        if hasattr(response, "text") and response.text:
            return response.text
    except Exception:
        pass

    try:
        if hasattr(response, "candidates") and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, "content") and candidate.content:
                    if hasattr(candidate.content, "parts") and candidate.content.parts:
                        text_parts = [
                            part.text for part in candidate.content.parts 
                            if hasattr(part, "text") and part.text
                        ]
                        if text_parts:
                            return "".join(text_parts)
    except Exception:
        pass

    if hasattr(response, "text") and response.text:
        return response.text

    # Fallback to configured provider check if structure evaluation fails
    provider = get_llm_provider()
    if provider == "groq":
        try:
            return response.choices[0].message.content
        except Exception as e:
            raise ValueError(f"Failed to extract response text from Groq response structure: {e}")

    raise ValueError("Failed to extract response text from response structure.")