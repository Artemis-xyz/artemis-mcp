import os
from typing import List
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("artemis_plugins")

# Simplified prompt template focusing on formula generation
PROMPT_TEMPLATE = """The assistant's goal is to help users generate Artemis formulas for Artemis Sheets.
<mcp>
Tools:
- "generate-art-formula": Generates an ART formula for retrieving crypto prices, fees, revenue, and other time-series data.
- "generate-artinfo-formula": Generates an ARTINFO formula for asset classifications, available metrics, market cap rankings, and metadata.
  - If the user asks for **market cap rankings, supported metrics, or asset information**, use `generate-artinfo-formula`.
  - If the user asks for **price, fees, revenue, or historical data**, use `generate-art-formula`.
</mcp>

<workflow>
1. Formula Generation:
   - For time-series data (ART formula):
     - If the user wants price, fees, revenue, or historical data, use `generate-art-formula`
     - Basic format: `ART(symbols, metrics, [startDate], [endDate], [order], [showDates], [hideWeekends])`
   
   - For asset information (ARTINFO formula):
     - If the user wants market cap rankings, asset information, supported metrics, or metadata, use `generate-artinfo-formula`
     - Main formats:
       - `ARTINFO("ALL", "SYMBOLS")` for all asset symbols
       - `ARTINFO("ALL", "METRICS")` for all available metrics
       - `ARTINFO("ALL", "TOPn-SYMBOLS")` for top n assets by market cap
       - `ARTINFO("SYMBOL", "ASSET-NAME/CATEGORIES/SUB-CATEGORIES/etc.")` for specific asset info
</workflow>

<conversation-flow>
1. For Artemis formula requests:
   - For time-series data:
     - Use `generate-art-formula` with appropriate parameters
     - Explain how to use the ART formula in Artemis Sheets
   
   - For asset information and metadata:
     - Use `generate-artinfo-formula` with appropriate parameters
     - Explain how the formula works in Artemis Sheets
</conversation-flow>
"""


class ArtemisFormulaGenerator:
    @staticmethod
    def generate_art_formula(
        symbols: List[str],
        metrics: List[str],
        start_date: str = "",
        end_date: str = "",
        order: str = "ASC",
        show_dates: bool = False,
        hide_weekends: bool = False,
    ) -> str:
        """Generate an ART formula for Artemis Sheets based on user input.

        Args:
            symbols: List of crypto symbols (e.g., ["BTC", "ETH"]).
            metrics: List of metrics (e.g., ["PRICE", "MC"]).
            start_date: Optional start date for historical data (YYYY-MM-DD).
            end_date: Optional end date for historical data (YYYY-MM-DD).
            order: Sorting order, defaults to "ASC". The only other valid value is "DESC".
            show_dates: Whether to include dates in the result (True/False).
            hide_weekends: Whether to exclude weekends from the result (True/False).

        Returns:
            A properly formatted ART formula string.
        """
        if not symbols or not metrics:
            return "Error: ART formula requires at least one symbol and one metric."

        # Validate date format - must be YYYY-MM-DD
        date_error = ""
        if start_date and not (
            start_date == ""
            or (len(start_date) == 10 and start_date[4] == "-" and start_date[7] == "-")
        ):
            date_error += f" Start date '{start_date}' must be in YYYY-MM-DD format."

        if end_date and not (
            end_date == ""
            or (len(end_date) == 10 and end_date[4] == "-" and end_date[7] == "-")
        ):
            date_error += f" End date '{end_date}' must be in YYYY-MM-DD format."

        if date_error:
            return f"Error: Invalid date format.{date_error} ART formula requires dates in YYYY-MM-DD format."

        # Enforce "Market Cap" → "MC"
        metric_map = {
            "Market Cap": "MC",
            "market cap": "MC",
            "MARKET CAP": "MC",
            "Market capitalization": "MC",
        }
        metrics = [metric_map.get(m, m) for m in metrics]

        # Format symbols with double quotes
        if len(symbols) > 1:
            symbol_str = "{" + ",".join([f'"{s}"' for s in symbols]) + "}"
        else:
            symbol_str = f'"{symbols[0]}"'

        # Format metrics with double quotes
        if len(metrics) > 1:
            metric_str = "{" + ",".join([f'"{m}"' for m in metrics]) + "}"
        else:
            metric_str = f'"{metrics[0]}"'

        # Build the ART formula
        formula = f"=ART({symbol_str}, {metric_str}"

        # Handle optional parameters in correct order
        if start_date:
            formula += f', "{start_date}"'
        if end_date:
            formula += f', "{end_date}"'

        # Only include "order" if it's "DESC". Default "ASC" is omitted.
        if order == "DESC":
            formula += f', "{order}"'

        if show_dates:
            if order == "ASC":  # If order was omitted, keep correct placement
                formula += f", , TRUE"
            else:
                formula += f", TRUE"

        if hide_weekends:
            formula += ", TRUE"

        formula += ")"

        return f"Generated ART Formula: `{formula}`"

    @staticmethod
    def generate_artinfo_formula(
        parameter1: str = "ALL", parameter2: str = "", top_n: int = 0
    ) -> str:
        """Generate an ARTINFO formula for Artemis Sheets.

        Args:
            parameter1: The main category ("ALL" or a specific asset symbol like "BTC").
            parameter2: The subcategory ("SYMBOLS", "TOPn-SYMBOLS", "METRICS",
                        "ASSET-NAME", "CATEGORIES", "SUB-CATEGORIES",
                        "COINGECKO-ID", "MC-RANK", "SUPPORTED-METRICS").
            top_n: Optional parameter for retrieving top n assets (for "TOPn-SYMBOLS").

        Returns:
            A properly formatted ARTINFO formula string.
        """
        # Special case for market rankings - force correct usage pattern
        if (
            parameter1.upper()
            in ["RANK", "RANKING", "RANKINGS", "MARKET-RANK", "MARKET-RANKS", "MC-RANK"]
            or top_n > 0
        ):
            return f'Generated ARTINFO Formula: `=ARTINFO("ALL", "TOP{top_n or 10}-SYMBOLS")`'

        # Ensure parameter1 is uppercase and defaults to "ALL"
        parameter1_upper = parameter1.upper() if parameter1 else "ALL"

        # Handle empty formula case
        if not parameter1 and not parameter2 and top_n == 0:
            return "Generated ARTINFO Formula: `=ARTINFO()`"

        # Case 1: parameter1 is "ALL"
        if parameter1_upper == "ALL":
            # Case 1a: TOP-n SYMBOLS from parameter2
            if (
                parameter2.upper().startswith("TOP")
                and "-SYMBOLS" in parameter2.upper()
            ):
                try:
                    # Extract n from parameter2 if possible
                    n_value = parameter2.upper().split("TOP")[1].split("-")[0]
                    return f'Generated ARTINFO Formula: `=ARTINFO("ALL", "{parameter2.upper()}")`'
                except:
                    return (
                        f'Generated ARTINFO Formula: `=ARTINFO("ALL", "TOP10-SYMBOLS")`'
                    )

            # Case 1b: SYMBOLS or METRICS
            elif parameter2.upper() in ["SYMBOLS", "METRICS"]:
                return f'Generated ARTINFO Formula: `=ARTINFO("ALL", "{parameter2.upper()}")`'

            # Case 1c: parameter2 is "TOP-SYMBOLS" without a number
            elif parameter2.upper() == "TOP-SYMBOLS":
                return f'Generated ARTINFO Formula: `=ARTINFO("ALL", "TOP10-SYMBOLS")`'

            # Case 1d: No valid parameter2, default to ALL only
            elif not parameter2:
                return f'Generated ARTINFO Formula: `=ARTINFO("ALL")`'

            # Case 1e: Invalid parameter2 for ALL
            else:
                return f'Generated ARTINFO Formula: `=ARTINFO("ALL")` (Note: "{parameter2}" is not a valid second parameter when first parameter is "ALL")'

        # Case 2: parameter1 is a specific symbol
        else:
            valid_param2_for_symbol = [
                "ASSET-NAME",
                "CATEGORIES",
                "SUB-CATEGORIES",
                "COINGECKO-ID",
                "MC-RANK",
                "SUPPORTED-METRICS",
            ]

            # Case 2a: Valid parameter2 for a symbol
            if parameter2.upper() in valid_param2_for_symbol:
                return f'Generated ARTINFO Formula: `=ARTINFO("{parameter1_upper}", "{parameter2.upper()}")`'

            # Case 2b: No parameter2, return just the symbol
            elif not parameter2:
                return f'Generated ARTINFO Formula: `=ARTINFO("{parameter1_upper}")`'

            # Case 2c: Invalid parameter2 for a symbol
            else:
                valid_options = '", "'.join(valid_param2_for_symbol)
                return f'Generated ARTINFO Formula: `=ARTINFO("{parameter1_upper}")` (Note: Valid second parameters for a symbol are: "{valid_options}")'


# Create a formula generator instance
formula_generator = ArtemisFormulaGenerator()


@mcp.tool()
def generate_art_formula(
    symbols: list[str],
    metrics: list[str],
    start_date: str = "",
    end_date: str = "",
    order: str = "ASC",
    show_dates: bool = False,
    hide_weekends: bool = False,
) -> str:
    """Generate an ART formula for Artemis Sheets.

    This tool creates properly formatted ART formulas for time-series data retrieval
    such as prices, fees, revenue, and other historical data.

    Important notes:
    - Dates must be in YYYY-MM-DD format (e.g., "2025-02-28")
    - For relative dates, calculate the actual date before passing it to this tool
    - Order can be "ASC" (default) or "DESC"
    - Common metrics include: PRICE, VOLUME, MC (market cap), SUPPLY, TVL, etc.
    """
    # Validate and potentially transform inputs

    # Standardize metrics - map common terms to their API equivalents
    standardized_metrics = []
    metric_mapping = {
        "PRICE": "PRICE",
        "price": "PRICE",
        "prices": "PRICE",
        "PRICES": "PRICE",
        "CLOSE": "PRICE",
        "close": "PRICE",
        "closing": "PRICE",
        "closing price": "PRICE",
        "CLOSING PRICE": "PRICE",
        "Market Cap": "MC",
        "MARKET CAP": "MC",
        "market cap": "MC",
        "marketcap": "MC",
        "MARKETCAP": "MC",
        "MC": "MC",
        "mc": "MC",
        "volume": "DEX_VOLUMES",
        "VOLUME": "DEX_VOLUMES",
        "vol": "DEX_VOLUMES",
        "VOL": "DEX_VOLUMES",
        "24h volume": "24H_VOLUME",
        "24H VOLUME": "24H_VOLUME",
        "daily volume": "24H_VOLUME",
        "tvl": "TVL",
        "TVL": "TVL",
        "total value locked": "TVL",
        "TOTAL VALUE LOCKED": "TVL",
        "fees": "FEES",
        "FEES": "FEES",
        "fee": "FEES",
        "FEE": "FEES",
        "revenue": "REVENUE",
        "REVENUE": "REVENUE",
        "REVENUES": "REVENUE",
        "revenues": "REVENUE",
    }

    for metric in metrics:
        if metric in metric_mapping:
            standardized_metrics.append(metric_mapping[metric])
        else:
            standardized_metrics.append(metric)

    # Handle time period requests like "last week", "last month", etc.
    if (
        start_date
        and start_date not in ["", " "]
        and (
            not (
                len(start_date) == 10 and start_date[4] == "-" and start_date[7] == "-"
            )
        )
    ):
        from datetime import datetime, timedelta

        today = datetime.now().strftime("%Y-%m-%d")

        # Common relative date calculations
        if start_date.lower() in [
            "-7",
            "last week",
            "past week",
            "previous week",
            "7 days",
        ]:
            # Calculate date 7 days ago in YYYY-MM-DD format
            seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            start_date = seven_days_ago
            if not end_date:
                end_date = today

        elif start_date.lower() in [
            "-30",
            "last month",
            "past month",
            "previous month",
            "30 days",
        ]:
            # Calculate date 30 days ago in YYYY-MM-DD format
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            start_date = thirty_days_ago
            if not end_date:
                end_date = today

        elif start_date.lower() in [
            "-90",
            "last quarter",
            "past quarter",
            "previous quarter",
            "90 days",
        ]:
            # Calculate date 90 days ago in YYYY-MM-DD format
            ninety_days_ago = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
            start_date = ninety_days_ago
            if not end_date:
                end_date = today

        elif start_date.lower() in [
            "-365",
            "last year",
            "past year",
            "previous year",
            "365 days",
        ]:
            # Calculate date 365 days ago in YYYY-MM-DD format
            year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            start_date = year_ago
            if not end_date:
                end_date = today

    # Call the generator with transformed metrics and dates
    result = formula_generator.generate_art_formula(
        symbols,
        standardized_metrics,
        start_date,
        end_date,
        order,
        show_dates,
        hide_weekends,
    )

    # Add additional context about the formula
    if "Error" not in result:
        explanation = f"\nThis formula will retrieve {', '.join(standardized_metrics)} data for {', '.join(symbols)}."

        if start_date and end_date:
            explanation += f" Data range: {start_date} to {end_date}."
        elif start_date:
            explanation += f" Starting from {start_date}."

        if order == "DESC":
            explanation += " Results will be in descending order (newest first)."
        else:
            explanation += " Results will be in ascending order (oldest first)."

        if show_dates:
            explanation += " Dates will be included in the results."

        if hide_weekends:
            explanation += " Weekend data will be excluded."

        return result + explanation

    return result


@mcp.tool()
def generate_artinfo_formula(
    parameter1: str = "ALL", parameter2: str = "", top_n: int = 0
) -> str:
    """Generate an ARTINFO formula for Artemis Sheets.

    This tool creates properly formatted ARTINFO formulas for retrieving asset information,
    classifications, available metrics, market cap rankings, and other metadata.

    For market rankings:
    - To get top N assets by market cap, use top_n=N (e.g., top_n=25)
    - This will generate =ARTINFO("ALL", "TOPn-SYMBOLS")

    For asset information:
    - Use parameter1="SYMBOL" (e.g., "BTC") and parameter2="INFO_TYPE"
      (e.g., "ASSET-NAME", "MC-RANK", etc.)
    """
    # Special case for market rankings
    if (
        parameter1.upper()
        in ["RANK", "RANKING", "RANKINGS", "MARKET-RANK", "MARKET-CAPS"]
        or top_n > 0
    ):
        # Force correct usage for top assets
        if top_n <= 0:
            top_n = 10  # Default to top 10 if not specified
        formula = formula_generator.generate_artinfo_formula(
            "ALL", f"TOP{top_n}-SYMBOLS", 0
        )
        return f"{formula}\n\nThis formula will return the top {top_n} assets by market capitalization."

    # Normal case
    formula = formula_generator.generate_artinfo_formula(parameter1, parameter2, top_n)

    # Add context for formula usage
    if parameter1.upper() == "ALL":
        if parameter2.upper() == "SYMBOLS":
            return f"{formula}\n\nThis formula will return all available asset symbols."
        elif parameter2.upper() == "METRICS":
            return f"{formula}\n\nThis formula will return all available metrics."
    elif parameter1.upper() != "ALL" and parameter2:
        return f"{formula}\n\nThis formula will return {parameter2.upper()} information for {parameter1.upper()}."

    return formula


@mcp.prompt()
def prompt() -> str:
    """
    A prompt template focused on Artemis formula generation
    """
    return PROMPT_TEMPLATE


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
