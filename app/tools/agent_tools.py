from typing import Literal

def get_real_time_stock_price(ticker_symbol: str) -> str:
    """
    REQUIRED: Call this function whenever the user asks for the price, 
    value, or quote of a specific stock ticker (e.g., GOOG, AAPL).
    """
    # For now, we return a mock value.

    print(f"DEBUG: stock price tool triggered!")
    if ticker_symbol.upper() == "GOOG":
        return "The current price for GOOG is $142.50. (Source: Mock API)"
    elif ticker_symbol.upper() == "MSFT":
        return "The current price for MSFT is $405.10. (Source: Mock API)"
    else:
        return f"Stock price for {ticker_symbol} not found."


def schedule_meeting(
    participant_names: list[str], 
    date: str, 
    time: str, 
    duration: Literal["30m", "1h", "2h"]
) -> str:
    """
    Args:
        participant_names: A list of people to invite (e.g., ['Alice', 'Bob']).
        date: The date for the meeting (e.g., '2025-12-20').
        time: The start time for the meeting (e.g., '14:30').
        duration: The length of the meeting (must be '30m', '1h', or '2h').
    """
    # NOTE: this would call your Calendar/Gmail tool integration.
    return (
        f"Successfully scheduled a {duration} meeting on {date} at {time} "
        f"for participants: {', '.join(participant_names)}. "
        f"Confirmation sent."
    )