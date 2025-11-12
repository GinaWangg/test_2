"""Vector search handler for Redis API."""

import os
from api_structure.core.timer import timed
from api_structure.src.clients.aiohttp_client import AiohttpClient


def _restructure_api_response(api_output: list) -> dict:
    """Restructure API response into numbered format.
    
    Args:
        api_output: List of FAQ results from API.
        
    Returns:
        Dictionary with numbered keys.
    """
    result = {}
    for i, item in enumerate(api_output, start=1):
        intent = (
            'Technical Support' 
            if item['type'] == 'question' 
            else item['type']
        )
        result[f'intent_{i}'] = intent
        result[f'kb_no_{i}'] = item['kb_no']
        result[f'cosineSimilarity_{i}'] = item['cosineSimilarity']
        result[f'key_{i}'] = item['key']
    return result


@timed(task_name="vector_search")
async def search_vector_kb(
        aiohttp_client: AiohttpClient,
        question: str,
        product_line: str,
        website: str
) -> tuple[dict, dict, dict]:
    """Search vector KB for intent and knowledge base matches.
    
    Args:
        aiohttp_client: Initialized aiohttp client.
        question: Question text to search.
        product_line: Product line identifier.
        website: Website code.
        
    Returns:
        Tuple of (api_response, intent_result, kb_result).
    """
    # Normalize website code
    if website == 'gb':
        website = 'uk'
    
    redis_url = os.getenv('MYAPP_VECTOR_API_URL')
    if not redis_url:
        raise ValueError("MYAPP_VECTOR_API_URL env var must be set.")
    
    # Prepare API request data
    data = [
        {
            "websiteCode": 'all',
            "keyword": question.lower(),
            "productLine": '',
            "version": "4.0",
            "n": 1,
            "hide_min": 0,
            "hide_max": 1999,
        },
        {
            "websiteCode": website,
            "keyword": question.lower(),
            "productLine": product_line,
            "version": "4.0",
            "n": 4,
            "hide_min": 0,
            "hide_max": 999,
        }
    ]
    
    headers = {
        'accept': 'text/plain',
        'Content-Type': 'application/json'
    }
    
    # Call API
    async with aiohttp_client.session.post(
        redis_url,
        json=data,
        headers=headers
    ) as resp:
        response_data = await resp.json()
    
    # Process response
    api_response = {
        "status": resp.status,
        "success": resp.status == 200,
        "output_data": response_data if resp.status == 200 else None,
        "error_message": None if resp.status == 200 else "API error"
    }
    
    try:
        ans_intent = response_data['result']['faqs']
        ans_kb = response_data['result']['faqs']
        
        # Pad KB results to 4 items if needed
        while len(ans_kb) < 4:
            default_item = {
                'kb_no': None,
                'websiteCode': None,
                'productLine': None,
                'key': None,
                'type': None,
                'hide': None,
                'cosineSimilarity': None
            }
            ans_kb.append(default_item)
        
        result_intent = _restructure_api_response(ans_intent)
        result_kb = _restructure_api_response(ans_kb)
    except Exception as e:
        api_response['success'] = False
        api_response['error_message'] = (
            f'Function vector_search error: {e}'
        )
        result_intent = {"error": "function search_vector_kb error"}
        result_kb = {"error": "function search_vector_kb error"}
    
    return api_response, result_intent, result_kb
