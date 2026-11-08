import asyncio
import json
import logging

import httpx

from app.config.settings import settings

logger = logging.getLogger(__name__)


class ZembraTimeout(TimeoutError):
    """The job was created but didn't finish in time.

    Poll this job_id again instead of creating a new job.
    """

    def __init__(self, job_id: str, attempts: int):
        super().__init__(
            f"Zembra job {job_id} not finished after {attempts} polls"
        )
        self.job_id = job_id


def _save_debug_copy(result: dict) -> None:
    """Keep the last good response so mapper bugs can be tested offline."""
    try:
        with open("last_zembra_response.json", "w") as f:
            json.dump(result, f)
    except OSError:
        pass


class ZembraClient:

    async def fetch_reviews(
        self,
        network: str,
        slug: str,
        monitoring: str = "none",
        max_attempts: int = 12,
        poll_interval: int = 5,
    ) -> dict:

        headers = {
            "Authorization": f"Bearer {settings.zembra_api_token}",
            "Accept": "application/json",
        }

        payload = {
            "network": network,
            "slug": slug,
            "monitoring": monitoring,
        }

        async with httpx.AsyncClient(timeout=60) as client:

            # Step 1: create the review job (this is the step that costs credits)
            response = await client.post(
                settings.zembra_api_url,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            job_data = response.json()

            job_id = (job_data.get("data") or {}).get("job", {}).get("jobId")
            if not job_id:
                raise ValueError("Zembra did not return a job ID")

            logger.info("Zembra job created: %s", job_id)

            # Step 2: poll the same job until it finishes
            for attempt in range(max_attempts):
                try:
                    response = await client.get(
                        settings.zembra_api_url,
                        headers=headers,
                        params={"jobId": job_id},
                    )
                    response.raise_for_status()
                except httpx.TransportError as exc:
                    # transient network problem: try the next poll, never a new job
                    logger.warning("Poll %s failed: %s", attempt + 1, exc)
                else:
                    result = response.json()

                    if result.get("status") != "SUCCESS":
                        raise ValueError(
                            result.get("message", "Zembra polling failed")
                        )

                    message = (result.get("message") or "").lower()
                    if "in progress" not in message:
                        # balance is only returned when the job is created
                        result.setdefault("balance", job_data.get("balance"))
                        _save_debug_copy(result)
                        return result

                if attempt < max_attempts - 1:
                    await asyncio.sleep(poll_interval)

        raise ZembraTimeout(job_id, max_attempts)