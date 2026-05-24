import base64
import logging
import config
import prompts

logger = logging.getLogger("ZinottiBot.AIService")

# Initialize clients if keys are present
openai_client = None
if config.OPENAI_API_KEY:
    try:
        from openai import AsyncOpenAI
        openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        logger.info("OpenAI Async client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")

claude_client = None
if config.CLAUDE_API_KEY:
    try:
        from anthropic import AsyncAnthropic
        # Ensure we set the API key properly in AsyncAnthropic
        claude_client = AsyncAnthropic(api_key=config.CLAUDE_API_KEY)
        logger.info("Claude Async client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Claude client: {e}")


def encode_image_base64(image_bytes: bytes) -> str:
    """Encode raw image bytes into base64 string."""
    return base64.b64encode(image_bytes).decode("utf-8")


async def call_openai_completion(model: str, messages: list, max_tokens: int, **kwargs) -> any:
    """
    Helper function to dynamically use max_tokens or max_completion_tokens based on the model name.
    Includes a fail-safe fallback to retry with the alternative parameter if a 400 bad request is thrown.
    """
    if not openai_client:
        raise RuntimeError("OpenAI client is not initialized.")
        
    params = {
        "model": model,
        "messages": messages,
        **kwargs
    }
    
    # Check if model requires modern max_completion_tokens (e.g. gpt-5 or o1/o3 family)
    model_lower = model.lower()
    if "gpt-5" in model_lower or model_lower.startswith("o1") or model_lower.startswith("o3"):
        params["max_completion_tokens"] = max_tokens
    else:
        params["max_tokens"] = max_tokens
        
    try:
        return await openai_client.chat.completions.create(**params)
    except Exception as e:
        err_str = str(e)
        # If API complains about the token parameter, swap and retry
        if "max_tokens" in err_str or "max_completion_tokens" in err_str or "unsupported_parameter" in err_str:
            logger.info("Swapping max_tokens / max_completion_tokens parameter and retrying OpenAI call...")
            if "max_tokens" in params:
                del params["max_tokens"]
                params["max_completion_tokens"] = max_tokens
            elif "max_completion_tokens" in params:
                del params["max_completion_tokens"]
                params["max_tokens"] = max_tokens
            return await openai_client.chat.completions.create(**params)
        raise e



async def generate_draft_transcript_from_photo(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """
    Generates a draft Kazakh transcript for the furniture in the photo.
    First tries OpenAI, then falls back to Claude if OpenAI fails or is unconfigured.
    """
    base64_image = encode_image_base64(image_bytes)
    
    # --- Try OpenAI first ---
    if openai_client:
        models_to_try = [config.OPENAI_CONTENT_MODEL, config.OPENAI_MODEL, "gpt-5.5", "gpt-4o"]
        for model in models_to_try:
            try:
                logger.info(f"Attempting OpenAI draft generation with model '{model}'...")
                response = await call_openai_completion(
                    model=model,
                    messages=[
                        {"role": "system", "content": prompts.TRANSCRIPT_SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompts.TRANSCRIPT_USER_PROMPT},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=1000
                )
                result = response.choices[0].message.content.strip()
                logger.info(f"OpenAI successfully generated transcript using model '{model}'")
                return result
            except Exception as e:
                logger.warning(f"OpenAI error with model '{model}': {e}")
                # Continue loop to try next model fallback

    # --- Try Claude as fallback ---
    if claude_client:
        models_to_try = [config.CLAUDE_MODEL, "claude-3-5-sonnet-20241022", "claude-3-7-sonnet-20250219"]
        for model in models_to_try:
            try:
                logger.info(f"Attempting Claude draft generation with model '{model}'...")
                # Anthropic API uses a specific vision format
                response = await claude_client.messages.create(
                    model=model,
                    system=prompts.TRANSCRIPT_SYSTEM_PROMPT,
                    max_tokens=1000,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": mime_type,
                                        "data": base64_image
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompts.TRANSCRIPT_USER_PROMPT
                                }
                            ]
                        }
                    ]
                )
                result = response.content[0].text.strip()
                logger.info(f"Claude successfully generated transcript using model '{model}'")
                return result
            except Exception as e:
                logger.warning(f"Claude error with model '{model}': {e}")

    raise RuntimeError("Both OpenAI and Claude services failed to process the image. Check API keys and network connection.")


async def refine_transcript_with_details(draft: str, sizes: str, materials: str) -> str:
    """
    Refines the Kazakh transcript draft with exact user-provided sizes and materials.
    First tries OpenAI, then falls back to Claude.
    """
    user_prompt = prompts.TRANSCRIPT_REFINEMENT_PROMPT.format(
        draft_transcript=draft,
        sizes=sizes,
        materials=materials
    )

    # --- Try OpenAI first ---
    if openai_client:
        models_to_try = [config.OPENAI_CONTENT_MODEL, config.OPENAI_MODEL, "gpt-5.5", "gpt-4o"]
        for model in models_to_try:
            try:
                logger.info(f"Attempting OpenAI refinement with model '{model}'...")
                response = await call_openai_completion(
                    model=model,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=1000
                )
                result = response.choices[0].message.content.strip()
                logger.info(f"OpenAI successfully refined transcript using model '{model}'")
                return result
            except Exception as e:
                logger.warning(f"OpenAI refinement error with model '{model}': {e}")

    # --- Try Claude as fallback ---
    if claude_client:
        models_to_try = [config.CLAUDE_MODEL, "claude-3-5-sonnet-20241022", "claude-3-7-sonnet-20250219"]
        for model in models_to_try:
            try:
                logger.info(f"Attempting Claude refinement with model '{model}'...")
                response = await claude_client.messages.create(
                    model=model,
                    max_tokens=1000,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )
                result = response.content[0].text.strip()
                logger.info(f"Claude successfully refined transcript using model '{model}'")
                return result
            except Exception as e:
                logger.warning(f"Claude refinement error with model '{model}': {e}")

    raise RuntimeError("Both OpenAI and Claude services failed to refine the transcript.")


def format_scenario_response(raw: str) -> str:
    """Normalize LLM output: trim and collapse excessive blank lines."""
    lines = [line.rstrip() for line in raw.strip().splitlines()]
    result = []
    blank_count = 0
    for line in lines:
        if not line.strip():
            blank_count += 1
            if blank_count <= 1:
                result.append("")
        else:
            blank_count = 0
            result.append(line)
    return "\n".join(result).strip()


async def generate_content_scenarios(product: str, vibe: str, features: str, image_bytes: bytes = None, mime_type: str = "image/jpeg") -> str:
    """
    Generates Marketing & Psychological video scenarios (Entertainment & Lifehacks)
    using the Golden Prompt rules.
    """
    user_prompt = prompts.SCENARIO_USER_PROMPT.format(
        product=product,
        vibe=vibe,
        features=features
    )

    # --- Try OpenAI first ---
    if openai_client:
        models_to_try = [config.OPENAI_CONTENT_MODEL, config.OPENAI_MODEL, "gpt-5.5", "gpt-4o"]
        for model in models_to_try:
            try:
                logger.info(f"Attempting OpenAI scenario generation with model '{model}'...")
                
                content_list = [{"type": "text", "text": user_prompt}]
                if image_bytes:
                    base64_image = encode_image_base64(image_bytes)
                    content_list.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    })

                response = await call_openai_completion(
                    model=model,
                    messages=[
                        {"role": "system", "content": prompts.SCENARIO_SYSTEM_PROMPT},
                        {"role": "user", "content": content_list}
                    ],
                    max_tokens=1000,
                    temperature=0.7,
                )
                result = format_scenario_response(response.choices[0].message.content.strip())
                logger.info(f"OpenAI successfully generated scenario using model '{model}'")
                return result
            except Exception as e:
                logger.warning(f"OpenAI scenario error with model '{model}': {e}")

    # --- Try Claude as fallback ---
    if claude_client:
        models_to_try = [config.CLAUDE_MODEL, "claude-3-5-sonnet-20241022", "claude-3-7-sonnet-20250219"]
        for model in models_to_try:
            try:
                logger.info(f"Attempting Claude scenario generation with model '{model}'...")
                
                content_list = []
                if image_bytes:
                    base64_image = encode_image_base64(image_bytes)
                    content_list.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": base64_image
                        }
                    })
                content_list.append({"type": "text", "text": user_prompt})

                response = await claude_client.messages.create(
                    model=model,
                    system=prompts.SCENARIO_SYSTEM_PROMPT,
                    max_tokens=1000,
                    temperature=0.7,
                    messages=[
                        {"role": "user", "content": content_list}
                    ]
                )
                result = format_scenario_response(response.content[0].text.strip())
                logger.info(f"Claude successfully generated scenario using model '{model}'")
                return result
            except Exception as e:
                logger.warning(f"Claude scenario error with model '{model}': {e}")

    raise RuntimeError("Both OpenAI and Claude services failed to generate the scenario.")

