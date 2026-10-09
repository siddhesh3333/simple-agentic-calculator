"""The Gemini agent and its calculator-tool loop."""

import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import google.genai as genai
from google.genai import errors, types

from tools import CalculatorError, calculate

PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

CALCULATOR_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="calculator",
            description=(
                "Perform one safe mathematical operation. Use percentage for "
                "a percent of b, such as 20 percent of 500."
            ),
            parameters={
                "type": "OBJECT",
                "properties": {
                    "operation": {
                        "type": "STRING",
                        "enum": [
                            "addition",
                            "subtraction",
                            "multiplication",
                            "division",
                            "percentage",
                            "power",
                            "square_root",
                        ],
                    },
                    "a": {"type": "NUMBER", "description": "First number."},
                    "b": {
                        "type": "NUMBER",
                        "description": (
                            "Second number. Required for every operation except "
                            "square_root."
                        ),
                    },
                },
                "required": ["operation", "a"],
            },
        )
    ]
)

SYSTEM_PROMPT = """You are SmartCalc AI, a clear and friendly calculator assistant.
Decide whether the user's request needs arithmetic. For arithmetic, always use
the calculator tool instead of doing the arithmetic yourself. For greetings or
non-mathematical questions, answer briefly without the tool. After receiving a
tool result, explain it in one simple sentence. Never invent a tool result."""


class AgentError(RuntimeError):
    """A user-friendly error from the agent boundary."""


def _client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise AgentError(
            "GEMINI_API_KEY is missing. Copy .env.example to .env and add your Gemini API key."
        )
    return genai.Client(api_key=api_key)


def _function_response_content(
    function_name: str, result: float | str
) -> types.Content:
    return types.Content(
        # Gemini represents a function response as the user's tool-result turn.
        role="user",
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    name=function_name,
                    response={"result": result},
                )
            )
        ],
    )


def run_agent(question: str) -> tuple[str, dict[str, Any]]:
    """Run one user question through the Gemini -> tool -> Gemini flow."""
    if not question or not question.strip():
        raise AgentError("Please enter a question.")

    client = _client()
    debug: dict[str, Any] = {
        "user_question": question.strip(),
        "agent_decision": "Waiting for Gemini",
        "tool_selected": None,
        "tool_input": None,
        "tool_result": None,
    }

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=question.strip(),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[CALCULATOR_TOOL],
            ),
        )
        function_calls = response.function_calls or []

        if not function_calls:
            debug["agent_decision"] = "No calculator required"
            return response.text or "I could not determine an answer.", debug

        function_call = function_calls[0]
        if function_call.name != "calculator":
            raise AgentError("Gemini requested an unsupported tool.")

        arguments = dict(function_call.args or {})
        debug["agent_decision"] = "Calculator required"
        debug["tool_selected"] = "calculator"
        debug["tool_input"] = arguments
        result = calculate(
            arguments.get("operation"), arguments.get("a"), arguments.get("b")
        )
        debug["tool_result"] = result
        logger.info("Calculator call: %s -> %s", arguments, result)

        if not response.candidates or not response.candidates[0].content:
            raise AgentError("Gemini returned an incomplete tool request.")

        final_response = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part(text=question.strip())],
                ),
                response.candidates[0].content,
                _function_response_content("calculator", result),
            ],
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
        )
        return final_response.text or str(result), debug
    except CalculatorError as error:
        debug["tool_result"] = f"Calculator error: {error}"
        raise AgentError(str(error)) from error
    except errors.ClientError as error:
        logger.exception("Gemini client error")
        if getattr(error, "code", None) in (401, 403):
            raise AgentError("The Gemini API key was rejected. Check your .env file.") from error
        if getattr(error, "code", None) == 429:
            raise AgentError("The Gemini API rate limit was reached. Please try again later.") from error
        if getattr(error, "code", None) == 404:
            raise AgentError(
                f"The Gemini model '{MODEL}' is unavailable for this API key. "
                "Update GEMINI_MODEL in .env to a model available in your Gemini account."
            ) from error
        raise AgentError("Gemini rejected the request. Check the model and API settings.") from error
    except errors.ServerError as error:
        logger.exception("Gemini server error")
        raise AgentError("Gemini is temporarily unavailable. Please try again later.") from error
    except (TimeoutError, ConnectionError) as error:
        logger.exception("Gemini connection error")
        raise AgentError("Could not connect to Gemini. Check your internet connection.") from error
    except (TypeError, ValueError, AttributeError) as error:
        logger.exception("Invalid response from Gemini")
        raise AgentError("Gemini returned an invalid response. Please try again.") from error
