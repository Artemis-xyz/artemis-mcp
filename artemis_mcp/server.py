import os
from typing import Any, List
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("artemis")

# Constants
ARTEMIS_API_BASE = "https://api.artemisxyz.com"
PROMPT_TEMPLATE = """The assistant's goal is to help users interact with the Artemis API efficiently and generate Artemis formulas for Artemis Sheets.

<mcp>
Tools:
- "validate-artemis-api-key": Creates and validates connection to Artemis API
- "get-artemis-data": Retrieves data from artemis API for given crypto token symbols and metrics
- "get-artemis-supported-metrics-for-symbol": Retrieves supported metrics for a given crypto token symbol
- "generate-art-formula": Generates an ART formula for retrieving crypto prices, fees, revenue, and other time-series data.
- "generate-artinfo-formula": Generates an ARTINFO formula for asset classifications, available metrics, market cap rankings, and metadata.
</mcp>

<workflow>
1. Connection Setup:
   - Use validate-artemis-api-key to establish connection and validate API key

2. Artemis API Exploration:
   - When user mentions a specific token symbol or symbols (e.g., BTC, ETH), list relevant metrics (FEES, REVENUE, PRICE)
   - You can help prompt the user to explore the data by suggesting supported metrics for a given symbol

3. Artemis API Execution:
   - Parse user's crypto data related questions making sure to highlight the token symbols and metrics
   - If the user gives a date range, ensure the date range is in the format YYYY-MM-DD
   - Make sure that the start date is before the end date
   - If no date range is provided, default to the last 30 days
   - Generate appropriate artemis api url
   - Call the Artemis API for the specific token and metrics with a specific timeframe and then display results
   - Provide clear explanations of findings and insights

4. Formula Generation:
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

5. Best Practices:
   - Cache schema information to avoid redundant calls
   - Use clear error handling and user feedback
   - Maintain context across multiple queries
   - Explain query logic when helpful

6. Visualization Support:
   - Create artifacts for data visualization when appropriate
   - Support common chart types and dashboards
   - Ensure visualizations enhance understanding of results
</workflow>

<conversation-flow>
1. Start with: "Hi! I'm here to help you interact with the Artemis API and generate Artemis formulas. How can I assist you today?"

2. After validation of API key:
   - Acknowledge success/failure
   - List some crypto tokens that are relevant such as HYPE, RAY, BTC, ETH
   - Guide user toward data exploration or formula generation

3. For each analytical question:
   - Confirm the API URL by highlighting the symbols and metrics and also showing the url used
   - Generate the appropriate url for the API
   - Present results clearly
   - Visualize data when helpful. Don't make a complicated dashboard. Just make a chart or table.
   - Only make 1 to 2 visualizations per query

4. For formula requests:
   - For time-series data:
     - Use `generate-art-formula` with appropriate parameters
     - Explain how to use the ART formula in Artemis Sheets

   - For asset information and metadata:
     - Use `generate-artinfo-formula` with appropriate parameters
     - Explain how the formula works in Artemis Sheets

5. Maintain awareness of:
   - Previously fetched api data
   - Current API context
   - API call history and insights
</conversation-flow>

<error-handling>
- Connection failures: Suggest alternative connection type
- API errors: Verify the url by highlighting the metrics and symbols that were used
- API errors: Return the API Error message
</error-handling>

Start interaction with connection type question, maintain context throughout conversation, and adapt api structure based on user needs.

Remember:
- Use artifacts for visualizations
- Provide clear explanations
- Handle errors gracefully

Don't:
- Make assumptions about the metric or symbol definitions
- Ignore previous conversation context
- Leave errors unexplained
"""

class ArtemisConnectManager:
    def __init__(self, api_key: str):
        self._api_key = api_key


    def initialize_and_validate_connection(self) -> str:
        """
        Initializes connection to Artemis and validates API Key
        """
        if not self.validate_api_key():
            return "Invalid API Key. Please check the API Key and try again."
        return "Connection successfully created!"

    def validate_api_key(self) -> bool:
        """Check if the Artemis API key is valid."""
        url = f"{ARTEMIS_API_BASE}/data/price/?symbols=btc&APIKey={self._api_key}"
        data = self.make_artemis_request(url)
        return data is not None

    async def make_artemis_request(self, url: str) -> dict[str, Any] | None:
        """Make a request to the Artemis API with proper error handling."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                return response.json()
            except Exception:
                return None

    def format_artemis_supported_metrics_url(self, symbol) -> str:
        """Format the Artemis API URL with the given symbols and metrics and date range."""
        return f"{ARTEMIS_API_BASE}/supported-metrics/?symbol={symbol}&APIKey={self._api_key}"

    def format_artemis_api_url(self, symbols: list[str], metrics: list[str], start_date: str, end_date: str) -> str:
        """Format the Artemis API URL with the given symbols and metrics and date range."""
        symbol_str = ",".join(symbols)
        metric_str = ",".join(metrics)
        return f"{ARTEMIS_API_BASE}/data/{metric_str}/?symbols={symbol_str}&APIKey={self._api_key}&startDate={start_date}&endDate={end_date}"

    def validate_artemis_data(self, data: dict) -> bool:
        """Check if the returned data is valid."""
        return "data" in data and "symbols" in data["data"]

    def format_artemis_response(self, data: dict, api:str = 'data') -> str:
        """Format an Artemis Data Response into a readable string so claude can read it and display it nicely to the user."""
        if api == "data":
            response_string = ""
            artemis_data = data["data"]["symbols"]
            for symbol in artemis_data:
                symbol_data = artemis_data[symbol]
                for metric in symbol_data:
                    metric_data = symbol_data[metric]
                    if isinstance(metric_data, list):
                        metric_data_string = "column title: date, value\n"
                        metric_data_string += ",".join([f"{data['date']},{data['val']}\n" for data in metric_data])
                    else:
                        metric_data_string = f"no data because of error message: {metric_data}"
                    # Format the data here
                    response_string += f"Data for Symbol: {symbol}, Metric: {metric}\n"
                    response_string += metric_data_string
            return response_string
        if api == "supported-metrics":
            response_str = ""
            artemis_metrics = data["metrics"]
            for metric in artemis_metrics:
                key = list(metric.keys())[0]
                response_str += f"Metric Friendly Name: {metric[key]['label']}\n"
                response_str += f"Metric Artemis Name for API: {key}\n"
                response_str += f"Description: {metric[key]['description']}\n"
                response_str += f"Source: {metric[key]['source']}\n"
            return response_str


artemis_api_key = os.getenv("ARTEMIS_API_KEY")
if not artemis_api_key:
    raise ValueError("ARTEMIS_API_KEY environment variable not set.")

artemis_manager = ArtemisConnectManager(artemis_api_key)


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
async def get_artemis_data(symbols: list[str], metrics: list[str], start_date: str, end_date: str) -> str:
    """ Get Crypto data from the Artemis API for the given symbols and metrics.

    Args:
        symbols: List of symbols to call the API for
        metrics: List of metrics to call the API for
        start_date: start date for the API make sure to use the format YYYY-MM-DD no other format will work
        end_date: end date for the API make sure to use the format YYYY-MM-DD no other format will work
    """
    artemis_url = artemis_manager.format_artemis_api_url(symbols, metrics, start_date, end_date)
    data = await artemis_manager.make_artemis_request(artemis_url)
    if not data:
        return f"Unable to fetch data from Artemis API with the following url: {artemis_url} \n"
    if not artemis_manager.validate_artemis_data(data):
        return f"Invalid data returned from Artemis API with the following url: {artemis_url} \n The Response was: {data} \n"
    return artemis_manager.format_artemis_response(data)


@mcp.tool()
async def get_artemis_supported_metrics_for_symbol(symbol: str) -> str:
    """ Get Metrics that Artemis Supports for a given symbol and their descriptions + sources.

    Args:
        symbol: can only take one symbol at a time to get the list of supported metrics for that symbol
    """
    artemis_url = artemis_manager.format_artemis_supported_metrics_url(symbol)
    data = await artemis_manager.make_artemis_request(artemis_url)
    if not data:
        return f"Unable to fetch data from Artemis API with the following url: {artemis_url} \n"

    return artemis_manager.format_artemis_response(data, api="supported-metrics")


@mcp.tool()
async def validate_artemis_api_key() -> str:
    """ Validate the Artemis API Key.

    """
    validated_key = artemis_manager.initialize_and_validate_connection()
    if not validated_key:
        return "Invalid API Key. Please check the API Key and restart Claude to try again."
    return "API Key validated successfully."


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
    A prompt template for the unified Artemis MCP server
    """
    return PROMPT_TEMPLATE

def main():
    """
    Main entry point for running the server
    """
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
