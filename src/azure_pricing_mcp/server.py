"""Azure Pricing MCP Server — tools for querying Azure retail prices."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from azure_pricing_mcp.azure_api import AzurePricingClient

# ── Server setup ─────────────────────────────────────────────────────

mcp = FastMCP(
    "Azure Pricing",
    instructions=(
        "MCP server for querying Azure service pricing using the public "
        "Azure Retail Prices API. Use these tools to search prices, estimate "
        "monthly costs, compare regions, and discover available services/regions."
    ),
)

_client = AzurePricingClient()

# Hours in a typical month (24 × 365 / 12 ≈ 730)
DEFAULT_HOURS_PER_MONTH = 730.0


# ── Formatting helpers ───────────────────────────────────────────────


def _format_price_item(item: dict[str, Any]) -> str:
    """Format a single price item into a readable string."""
    lines = [
        f"  Product: {item.get('productName', 'N/A')}",
        f"  SKU: {item.get('skuName', 'N/A')}",
        f"  ARM SKU: {item.get('armSkuName', 'N/A')}",
        f"  Meter: {item.get('meterName', 'N/A')}",
        f"  Region: {item.get('armRegionName', 'N/A')}",
        f"  Retail Price: {item.get('retailPrice', 'N/A')} {item.get('currencyCode', '')}",
        f"  Unit: {item.get('unitOfMeasure', 'N/A')}",
        f"  Price Type: {item.get('type', 'N/A')}",
    ]
    return "\n".join(lines)


# ── MCP Tools ────────────────────────────────────────────────────────


@mcp.tool()
async def search_prices(
    service_name: str | None = None,
    arm_region_name: str | None = None,
    arm_sku_name: str | None = None,
    sku_name: str | None = None,
    product_name: str | None = None,
    price_type: str | None = None,
    currency_code: str = "USD",
    max_results: int = 10,
) -> str:
    """Search Azure retail prices by service, region, SKU, or product name.

    Args:
        service_name: Azure service name (e.g. "Virtual Machines", "Storage")
        arm_region_name: Azure region (e.g. "eastus", "westeurope", "brazilsouth")
        arm_sku_name: ARM SKU name for exact match (e.g. "Standard_D8s_v5", "Standard_B2s")
        sku_name: SKU display name (e.g. "D2 v3", "Standard_LRS"). Use arm_sku_name for exact VM matching.
        product_name: Product name (e.g. "Virtual Machines Dv3 Series")
        price_type: Price type filter: "Consumption" (pay-as-you-go), "Reservation" (reserved instances), or "DevTestConsumption"
        currency_code: Currency code (default: USD). Examples: USD, EUR, BRL, GBP
        max_results: Maximum number of results to return (default: 10, max: 50)
    """
    max_results = min(max_results, 50)

    if not any([service_name, arm_region_name, arm_sku_name, sku_name, product_name]):
        return "Error: Please provide at least one filter (service_name, arm_region_name, arm_sku_name, sku_name, or product_name)."

    items = await _client.query_prices(
        service_name=service_name,
        arm_region_name=arm_region_name,
        arm_sku_name=arm_sku_name,
        sku_name=sku_name,
        product_name=product_name,
        price_type=price_type,
        currency_code=currency_code,
        max_results=max_results,
    )

    if not items:
        return "No pricing data found for the specified filters."

    results = [f"Found {len(items)} result(s):\n"]
    for i, item in enumerate(items, 1):
        results.append(f"[{i}]")
        results.append(_format_price_item(item))
        results.append("")

    return "\n".join(results)


@mcp.tool()
async def estimate_cost(
    service_name: str,
    arm_sku_name: str | None = None,
    sku_name: str | None = None,
    arm_region_name: str | None = None,
    quantity: float = 1.0,
    hours_per_month: float = DEFAULT_HOURS_PER_MONTH,
    currency_code: str = "USD",
) -> str:
    """Estimate monthly cost for an Azure service based on quantity and usage hours.

    The estimation multiplies the unit retail price by the quantity and hours.
    For storage or data services priced per GB/month, set hours_per_month to 1.

    Args:
        service_name: Azure service name (e.g. "Virtual Machines")
        arm_sku_name: ARM SKU name for exact match (e.g. "Standard_D8s_v5")
        sku_name: SKU display name to narrow down (e.g. "D2 v3")
        arm_region_name: Azure region (e.g. "eastus")
        quantity: Number of units (e.g. VM instances, GB of storage). Default: 1
        hours_per_month: Usage hours per month (default: 730 = 24/7). Set to 1 for flat monthly rates.
        currency_code: Currency code (default: USD)
    """
    items = await _client.query_prices(
        service_name=service_name,
        arm_sku_name=arm_sku_name,
        sku_name=sku_name,
        arm_region_name=arm_region_name,
        currency_code=currency_code,
        price_type="Consumption",
        max_results=20,
    )

    if not items:
        return "No pricing data found. Try adjusting service_name, sku_name, or arm_region_name."

    results = [f"Cost estimate for {service_name} (qty={quantity}, {hours_per_month} hrs/month):\n"]

    for item in items:
        retail_price = item.get("retailPrice", 0)
        unit = item.get("unitOfMeasure", "")

        # Determine if price is hourly or monthly/flat
        is_hourly = "hour" in unit.lower() or "/hour" in unit.lower()
        if is_hourly:
            monthly_cost = retail_price * hours_per_month * quantity
        else:
            monthly_cost = retail_price * quantity

        results.append(
            f"  {item.get('productName', 'N/A')} | {item.get('skuName', 'N/A')} | "
            f"{item.get('meterName', 'N/A')}\n"
            f"    Region: {item.get('armRegionName', 'N/A')}\n"
            f"    Unit Price: {retail_price} {currency_code}/{unit}\n"
            f"    Est. Monthly Cost: {monthly_cost:.4f} {currency_code}\n"
        )

    return "\n".join(results)


@mcp.tool()
async def compare_regions(
    service_name: str,
    arm_sku_name: str | None = None,
    sku_name: str | None = None,
    product_name: str | None = None,
    regions: list[str] | None = None,
    currency_code: str = "USD",
) -> str:
    """Compare prices for an Azure service/SKU across multiple regions.

    Results are sorted by price (cheapest first).

    Args:
        service_name: Azure service name (e.g. "Virtual Machines")
        arm_sku_name: ARM SKU name for exact match (e.g. "Standard_D8s_v5")
        sku_name: SKU display name (e.g. "D2 v3")
        product_name: Product name for more specific filtering
        regions: List of region names to compare. If omitted, shows all available regions.
        currency_code: Currency code (default: USD)
    """
    items = await _client.query_prices(
        service_name=service_name,
        arm_sku_name=arm_sku_name,
        sku_name=sku_name,
        product_name=product_name,
        currency_code=currency_code,
        price_type="Consumption",
        max_results=500,
    )

    if not items:
        return "No pricing data found. Try adjusting filters."

    # Group by region, keeping the lowest price per region
    region_prices: dict[str, dict[str, Any]] = {}
    for item in items:
        region = item.get("armRegionName", "")
        if not region:
            continue
        if regions and region not in regions:
            continue

        price = item.get("retailPrice", 0)
        if region not in region_prices or price < region_prices[region]["retailPrice"]:
            region_prices[region] = item

    if not region_prices:
        return "No regional pricing data found for the specified filters."

    sorted_regions = sorted(region_prices.items(), key=lambda x: x[1].get("retailPrice", 0))

    results = [
        f"Price comparison across {len(sorted_regions)} region(s) for {service_name}"
        + (f" ({sku_name})" if sku_name else "")
        + f" in {currency_code}:\n"
    ]
    results.append(f"{'Region':<25} {'Unit Price':>12} {'Unit':<20} {'SKU'}")
    results.append("-" * 80)

    for region, item in sorted_regions:
        results.append(
            f"{region:<25} {item.get('retailPrice', 0):>12.6f} "
            f"{item.get('unitOfMeasure', 'N/A'):<20} {item.get('skuName', 'N/A')}"
        )

    return "\n".join(results)


@mcp.tool()
async def list_services(
    search: str | None = None,
) -> str:
    """List available Azure services in the pricing API.

    Args:
        search: Optional text to filter service names (case-insensitive substring match)
    """
    services = await _client.list_services(search=search)

    if not services:
        return "No services found" + (f" matching '{search}'" if search else "") + "."

    header = f"Found {len(services)} Azure service(s)"
    if search:
        header += f" matching '{search}'"
    header += ":\n"

    return header + "\n".join(f"  • {s}" for s in services)


@mcp.tool()
async def list_regions(
    service_name: str | None = None,
) -> str:
    """List available Azure regions.

    Args:
        service_name: If provided, only show regions where this service is available
    """
    regions = await _client.list_regions(service_name=service_name)

    if not regions:
        return "No regions found" + (f" for '{service_name}'" if service_name else "") + "."

    header = f"Found {len(regions)} Azure region(s)"
    if service_name:
        header += f" for '{service_name}'"
    header += ":\n"

    return header + "\n".join(f"  • {r}" for r in regions)


# ── Entry point ──────────────────────────────────────────────────────


def main() -> None:
    """Run the Azure Pricing MCP server (stdio transport)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
