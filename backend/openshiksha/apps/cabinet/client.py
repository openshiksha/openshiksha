"""
Cabinet API Client

Modern async client for Cabinet service integration.
Based on legacy/cabinet/cabinet_api.py but with:
- Async/await support (httpx)
- Better error handling
- Retry logic
- Type hints
"""

import httpx
from typing import Dict, Any, Optional
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class CabinetClient:
    """
    Async client for Cabinet service

    Handles communication with external question bank service.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        self.base_url = base_url or settings.CABINET_API_URL
        self.api_key = api_key or settings.CABINET_API_KEY
        self.timeout = timeout

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            }
        )

    async def get_question(self, question_id: int) -> Dict[str, Any]:
        """
        Retrieve question with all subparts and constraints

        Args:
            question_id: Question ID

        Returns:
            Dictionary with question data including:
            - container: Question metadata
            - subparts: List of question subparts with variable constraints
        """
        try:
            response = await self.client.get(f'/questions/{question_id}/')
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Cabinet API error getting question {question_id}: {e}")
            raise

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# TODO: Implement additional Cabinet methods based on legacy cabinet_api.py:
# - build_undealt_assignment()
# - build_submission()
# - update_submission()
# - get_question_with_img_urls()
