import os
import time

from dotenv import load_dotenv
from groq import Groq


load_dotenv(override=True)


def get_groq_client():
    """
    Create and return the Groq API client.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY was not found. "
            "Add it to the .env file."
        )

    return Groq(
        api_key=api_key
    )


def create_chat_completion_with_retry(
    client,
    max_retries=3,
    retry_delay=3,
    **kwargs
):
    """
    Call the chat completion API with simple retry logic.

    Retries temporary rate-limit errors.
    """

    last_error = None


    for attempt in range(max_retries):

        try:

            return client.chat.completions.create(
                **kwargs
            )


        except Exception as error:

            last_error = error

            error_text = str(error).lower()


            is_rate_limit = (
                "429" in error_text
                or
                "rate limit" in error_text
                or
                "rate_limit_exceeded" in error_text
            )


            if not is_rate_limit:

                raise


            if attempt < max_retries - 1:

                wait_time = (
                    retry_delay
                    * (attempt + 1)
                )

                print(
                    f"Rate limit reached. "
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)


    raise last_error