import httpx

from app.config.settings import settings


class ZembraClient:

    async def fetch_reviews(
        self,
        network: str,
        slug: str,
        monitoring: str = "none"
    ) -> dict:

        headers = {
            "Authorization": f"Bearer {settings.zembra_api_token}",
            "Accept": "application/json"
        }

        payload = {
            "network": network,
            "slug": slug,
            "monitoring": monitoring
        }

        async with httpx.AsyncClient(timeout=120) as client:

            # Create review job
            response = await client.post(
                settings.zembra_api_url,
                headers=headers,
                json=payload
            )

            response.raise_for_status()

            job_data = response.json()

            # Extract job ID
            job_id = (
                job_data.get("data", {})
                .get("job", {})
                .get("jobId")
            )

            if not job_id:
                raise ValueError("Zembra did not return a job ID")

            # Retrieve collected reviews
            response = await client.get(
                settings.zembra_api_url,
                headers=headers,
                params={"jobId": job_id}
            )

            response.raise_for_status()

            return response.json()