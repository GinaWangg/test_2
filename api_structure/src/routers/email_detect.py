"""Email detection endpoint router."""

from fastapi import Request
from pydantic import BaseModel
from typing import Any, Optional
from api_structure.src.pipelines.email_detect_pipeline import (
    EmailDetectPipeline
)
from api_structure.core.exception_handlers import AbortException
import openai
import traceback


class EmailDetectInput(BaseModel):
    """Input model for email detection endpoint."""
    case_id: Any
    email: Any
    phone: Any
    case_date: Any
    site: Any
    product_type: Any
    email_content: Any
    product_model: Optional[str] = ''
    product_sn: Optional[str] = None
    problem_description_content: Optional[str] = None


def _validate_input_fields(input_model: EmailDetectInput) -> None:
    """Validate required input fields.
    
    Args:
        input_model: Pydantic input model.
        
    Raises:
        AbortException: If validation fails.
    """
    data_type_mappings = {
        'case_id': str,
        'email': str,
        'phone': str,
        'case_date': int,
        'site': str,
        'product_type': str,
        'email_content': str
    }
    
    for field, expected_type in data_type_mappings.items():
        value = getattr(input_model, field)
        if (
            not isinstance(value, expected_type) or
            value is None or
            value == ''
        ):
            raise AbortException(
                status=400,
                message=(
                    f"(Validation Error) The {field}({value}) field has "
                    "an incorrect format. Please recheck the input data."
                )
            )


async def email_detect_handler(
    input_data: EmailDetectInput,
    request: Request
) -> dict[str, Any]:
    """Handle email detection request.
    
    Args:
        input_data: Validated input data.
        request: FastAPI request object.
        
    Returns:
        Detection result dictionary.
        
    Raises:
        AbortException: On validation or processing errors.
    """
    # Validate inputs
    _validate_input_fields(input_data)
    
    # Get clients from app state
    gpt_client = request.app.state.gpt_client
    google_translate_client = request.app.state.google_translate_client
    aiohttp_client = request.app.state.aiohttp_client
    
    # Create pipeline
    pipeline = EmailDetectPipeline(
        gpt_client=gpt_client,
        google_translate_client=google_translate_client,
        aiohttp_client=aiohttp_client
    )
    
    try:
        # Run pipeline
        output = await pipeline.run(
            case_id=input_data.case_id,
            product_type=input_data.product_type,
            product_model=input_data.product_model or '',
            problem_description_content=(
                input_data.problem_description_content
            ),
            site=input_data.site.lower(),
            email_content=input_data.email_content
        )
        
        return output
        
    except openai.BadRequestError as e:
        # Handle GPT policy error with fallback
        summary = pipeline.summary or ""
        lang = pipeline.lang
        product_line = pipeline.product_line
        
        output = {
            "case_id": input_data.case_id,
            "gpt_extract": {
                "user_summary": summary,
                "type": 'unclear_description',
                "email_split_sentence": []
            },
            "check_info": {
                "start_time_ts": 0,
                "end_time_ts": 0,
                "lang": lang,
                "product_line": product_line,
                "email_split_info": []
            }
        }
        
        return output
        
    except KeyError as e:
        tb = traceback.format_exc()
        raise AbortException(
            status=400,
            message=str(e),
            message_detail=tb
        )
        
    except (TimeoutError, RuntimeError) as e:
        tb = traceback.format_exc()
        raise AbortException(
            status=400,
            message='ERROR',
            message_detail=tb
        )
        
    except Exception as e:
        tb = traceback.format_exc()
        raise AbortException(
            status=400,
            message='ERROR',
            message_detail=tb
        )
