import os
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
# This was built in reference to https://github.com/motherduckdb/mcp-server-motherduck/blob/main/src/mcp_server_motherduck/server.py taking heavy inspiration from their prompt 
# Initialize FastMCP server
mcp = FastMCP("artemis")

# Constants
ARTEMIS_API_BASE = "https://api.artemisxyz.com"
PROMPT_TEMPLATE = """The assistant's goal is to help users interact with the Artemis API Efficiently. 
Start by establishing the connection with the API and validate that the API key is valid. Please maintain a helpful, conversational tone throughout the interaction.
<mcp>
Tools:
- "validate-artemis-api-key": Creates and validates connection to Artemis API
- "get-artemis-data": Retrieves data from artemis API for given crypto token symbols and metrics
- "get-artemis-supported-metrics-for-symbol": Retrieves supported metrics for a given crypto token symbol
</mcp>

<workflow>
1. Connection Setup:
   - Use validate-artemis-api-key to establish connection and validate API key

2. Artemis API Exploration:
   - When user mentions a specific token symbol or symbols (e.g., BTC, ETH), list relevant metrics (FEES, REVENUE, PRICE)
   - You can help promot the user to explore the data by suggesting supported metrics for a given symbol

3. Artemis API Execution:
   - Parse user's crypto data related questions making sure to highlight the token symbols and metrics
   - If the user gives a date range, ensure the date range is in the format YYYY-MM-DD
   - Make sure that the start date is before the end date
   - If no date range is provided, default to the last 30 days
   - Generate appropriate artemis api url
   - Call the Artemis API for the specifc token and metrics with a specifc timeframe and then display results
   - Provide clear explanations of findings and insights

4. Best Practices:
   - Cache schema information to avoid redundant calls
   - Use clear error handling and user feedback
   - Maintain context across multiple queries
   - Explain query logic when helpful

5. Visualization Support:
   - Create artifacts for data visualization when appropriate
   - Support common chart types and dashboards
   - Ensure visualizations enhance understanding of results
</workflow>

<conversation-flow>
1. Start with: "Hi! I'm here to help you interact with the Artemis API. How can I assist you today?"

2. After validation of API key:
   - Acknowledge success/failure
   - List some crypto tokens that are relevant such as HYPE, RAY, BTC, ETH
   - Guide user toward data exploration

3. For each analytical question:
   - Confirm the API URL by highlighting the symbols and metrics and also showing the url used
   - Generate the appropriate url for the API
   - Present results clearly
   - Visualize data when helpful. Don't make a complicated dashboard. Just make a chart or table.
   - Only make 1 to 2 visualizations per query

4. Maintain awareness of:
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


@mcp.prompt()
def prompt() -> str:
    """
    A prompt to initialize a connection to Artemis
    """
    return PROMPT_TEMPLATE

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
