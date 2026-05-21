"""Async client for the Azure Retail Prices REST API."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

BASE_URL = "https://prices.azure.com/api/retail/prices"

# Default timeout for API requests (seconds)
REQUEST_TIMEOUT = 30.0


class AzurePricingClient:
    """Async client that wraps the Azure Retail Prices API.

    The API is public and requires no authentication.
    Docs: https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices
    """

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)

    async def close(self) -> None:
        await self._client.aclose()

    # ── Core query method ────────────────────────────────────────────

    async def query_prices(
        self,
        *,
        service_name: str | None = None,
        arm_region_name: str | None = None,
        sku_name: str | None = None,
        product_name: str | None = None,
        meter_name: str | None = None,
        price_type: str | None = None,
        currency_code: str = "USD",
        max_results: int = 100,
    ) -> list[dict[str, Any]]:
        """Query retail prices with optional OData filters.

        Returns up to *max_results* items across multiple pages.
        """
        filters = _build_filter(
            service_name=service_name,
            arm_region_name=arm_region_name,
            sku_name=sku_name,
            product_name=product_name,
            meter_name=meter_name,
            price_type=price_type,
        )
        params: dict[str, str] = {"currencyCode": currency_code}
        if filters:
            params["$filter"] = filters

        items: list[dict[str, Any]] = []
        url: str | None = BASE_URL

        while url and len(items) < max_results:
            resp = await self._client.get(url, params=params if url == BASE_URL else None)
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("Items", []):
                items.append(item)
                if len(items) >= max_results:
                    break

            url = data.get("NextPageLink")

        return items

    # ── Convenience helpers ──────────────────────────────────────────

    async def list_services(self, search: str | None = None) -> list[str]:
        """Return distinct service names. Optionally filter by substring."""
        items = await self.query_prices(max_results=1000)
        services = sorted({item["serviceName"] for item in items if "serviceName" in item})
        if search:
            search_lower = search.lower()
            services = [s for s in services if search_lower in s.lower()]
        return services

    async def list_regions(
        self, service_name: str | None = None
    ) -> list[str]:
        """Return distinct ARM region names, optionally scoped to a service."""
        items = await self.query_prices(service_name=service_name, max_results=1000)
        return sorted(
            {item["armRegionName"] for item in items if item.get("armRegionName")}
        )


# ── Private helpers ──────────────────────────────────────────────────


def _build_filter(
    *,
    service_name: str | None = None,
    arm_region_name: str | None = None,
    sku_name: str | None = None,
    product_name: str | None = None,
    meter_name: str | None = None,
    price_type: str | None = None,
) -> str:
    """Build an OData $filter string from keyword arguments."""
    clauses: list[str] = []

    if service_name:
        clauses.append(f"serviceName eq '{_escape(service_name)}'")
    if arm_region_name:
        clauses.append(f"armRegionName eq '{_escape(arm_region_name)}'")
    if sku_name:
        clauses.append(f"skuName eq '{_escape(sku_name)}'")
    if product_name:
        clauses.append(f"productName eq '{_escape(product_name)}'")
    if meter_name:
        clauses.append(f"meterName eq '{_escape(meter_name)}'")
    if price_type:
        clauses.append(f"priceType eq '{_escape(price_type)}'")

    return " and ".join(clauses)


def _escape(value: str) -> str:
    """Escape single quotes for OData filter values."""
    return value.replace("'", "''")
