import datetime
import html
import logging
import os
import pandas as pd
import re
import requests
import time

logger = logging.getLogger(__name__)

from src.data.cache import get_cache
from src.data.models import (
    CompanyNews,
    CompanyNewsResponse,
    FinancialMetrics,
    FinancialMetricsResponse,
    Price,
    PriceResponse,
    LineItem,
    LineItemResponse,
    InsiderTrade,
    InsiderTradeResponse,
    CompanyFactsResponse,
)

# Global cache instance
_cache = get_cache()


def _make_api_request(url: str, headers: dict, method: str = "GET", json_data: dict = None, max_retries: int = 3) -> requests.Response:
    """
    Make an API request with rate limiting handling and moderate backoff.

    Args:
        url: The URL to request
        headers: Headers to include in the request
        method: HTTP method (GET or POST)
        json_data: JSON data for POST requests
        max_retries: Maximum number of retries (default: 3)

    Returns:
        requests.Response: The response object

    Raises:
        Exception: If the request fails with a non-429 error
    """
    for attempt in range(max_retries + 1):  # +1 for initial attempt
        if method.upper() == "POST":
            response = requests.post(url, headers=headers, json=json_data)
        else:
            response = requests.get(url, headers=headers)

        if response.status_code == 429 and attempt < max_retries:
            # Linear backoff: 60s, 90s, 120s, 150s...
            delay = 60 + (30 * attempt)
            print(f"Rate limited (429). Attempt {attempt + 1}/{max_retries + 1}. Waiting {delay}s before retrying...")
            time.sleep(delay)
            continue

        # Return the response (whether success, other errors, or final 429)
        return response


def get_prices(ticker: str, start_date: str, end_date: str, api_key: str = None) -> list[Price]:
    """Fetch price data from cache or API."""
    # Create a cache key that includes all parameters to ensure exact matches
    cache_key = f"{ticker}_{start_date}_{end_date}"

    # Check cache first - simple exact match
    if cached_data := _cache.get_prices(cache_key):
        return [Price(**price) for price in cached_data]

    # If not in cache, fetch from API
    headers = {}
    financial_api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
    if financial_api_key:
        headers["X-API-KEY"] = financial_api_key

    url = f"https://api.financialdatasets.ai/prices/?ticker={ticker}&interval=day&interval_multiplier=1&start_date={start_date}&end_date={end_date}"
    response = _make_api_request(url, headers)
    if response.status_code != 200:
        prices = _get_prices_from_yahoo(ticker, start_date, end_date)
        if prices:
            _cache.set_prices(cache_key, [p.model_dump() for p in prices])
        return prices

    # Parse response with Pydantic model
    try:
        price_response = PriceResponse(**response.json())
        prices = price_response.prices
    except Exception as e:
        logger.warning("Failed to parse price response for %s: %s", ticker, e)
        prices = _get_prices_from_yahoo(ticker, start_date, end_date)
        if prices:
            _cache.set_prices(cache_key, [p.model_dump() for p in prices])
        return prices

    if not prices:
        prices = _get_prices_from_yahoo(ticker, start_date, end_date)
        if prices:
            _cache.set_prices(cache_key, [p.model_dump() for p in prices])
        return prices

    # Cache the results using the comprehensive cache key
    _cache.set_prices(cache_key, [p.model_dump() for p in prices])
    return prices


def _get_prices_from_yahoo(ticker: str, start_date: str, end_date: str) -> list[Price]:
    """Fallback daily OHLCV prices from Yahoo chart API."""
    try:
        start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
        end_dt = (datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)).replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        logger.warning("Invalid price date range for %s: %s to %s", ticker, start_date, end_date)
        return []

    period1 = int(start_dt.timestamp())
    period2 = int(end_dt.timestamp())
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}" f"?period1={period1}&period2={period2}&interval=1d&events=history"
    response = _make_api_request(url, {"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        return []

    try:
        result = response.json()["chart"]["result"][0]
        timestamps = result.get("timestamp") or []
        quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    except Exception as e:
        logger.warning("Failed to parse Yahoo price response for %s: %s", ticker, e)
        return []

    prices: list[Price] = []
    for idx, timestamp in enumerate(timestamps):
        try:
            open_price = quote.get("open", [])[idx]
            close_price = quote.get("close", [])[idx]
            high_price = quote.get("high", [])[idx]
            low_price = quote.get("low", [])[idx]
            volume = quote.get("volume", [])[idx]
            if None in (open_price, close_price, high_price, low_price, volume):
                continue

            prices.append(
                Price(
                    open=float(open_price),
                    close=float(close_price),
                    high=float(high_price),
                    low=float(low_price),
                    volume=int(volume),
                    time=datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc).strftime("%Y-%m-%d"),
                )
            )
        except (IndexError, TypeError, ValueError):
            continue

    return prices


_STOCKANALYSIS_CACHE: dict[str, dict[str, dict[str, dict[str, float | str | None]]]] = {}


def _stockanalysis_slug(ticker: str) -> str:
    return ticker.lower().replace(".", "-")


def _parse_stockanalysis_table(url: str) -> dict[str, list[str]]:
    response = _make_api_request(url, {"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        return {}

    rows: dict[str, list[str]] = {}
    for row_html in re.findall(r"<tr[^>]*>(.*?)</tr>", response.text, flags=re.DOTALL):
        cells = []
        for cell_html in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, flags=re.DOTALL):
            text = re.sub(r"<script.*?</script>", "", cell_html, flags=re.DOTALL)
            text = re.sub(r"<style.*?</style>", "", text, flags=re.DOTALL)
            text = re.sub(r"<[^>]*>", " ", text)
            text = html.unescape(text)
            text = re.sub(r"\s+", " ", text).strip()
            cells.append(text)
        if cells:
            rows[cells[0]] = cells[1:]
    return rows


def _parse_stockanalysis_number(value: str | None, *, percent: bool = False, millions: bool = False) -> float | None:
    if value is None:
        return None
    value = value.strip()
    if not value or value in {"-", "--", "n/a"}:
        return None

    multiplier = 1.0
    if value[-1:] in {"B", "M", "K"}:
        multiplier = {"B": 1_000_000_000.0, "M": 1_000_000.0, "K": 1_000.0}[value[-1]]
        value = value[:-1]
    elif millions:
        multiplier = 1_000_000.0

    value = value.replace(",", "").replace("$", "").replace("%", "")
    try:
        number = float(value) * multiplier
    except ValueError:
        return None
    return number / 100.0 if percent else number


def _parse_stockanalysis_period(value: str | None) -> str:
    if not value:
        return ""
    match = re.search(r"[A-Z][a-z]{2} \d{1,2}, \d{4}", value)
    if not match:
        return value
    try:
        return datetime.datetime.strptime(match.group(0), "%b %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        return value


def _stockanalysis_financial_data(ticker: str) -> dict[str, dict[str, dict[str, float | str | None]]]:
    slug = _stockanalysis_slug(ticker)
    if slug in _STOCKANALYSIS_CACHE:
        return _STOCKANALYSIS_CACHE[slug]

    base = f"https://stockanalysis.com/stocks/{slug}"
    tables = {
        "income": _parse_stockanalysis_table(f"{base}/financials/"),
        "balance": _parse_stockanalysis_table(f"{base}/financials/balance-sheet/"),
        "cashflow": _parse_stockanalysis_table(f"{base}/financials/cash-flow-statement/"),
        "ratios": _parse_stockanalysis_table(f"{base}/financials/ratios/"),
    }

    if not tables["income"]:
        return {}

    fiscal_years = tables["income"].get("Fiscal Year", [])
    periods = tables["income"].get("Period Ending", [])
    data: dict[str, dict[str, dict[str, float | str | None]]] = {}

    def value(table: str, label: str, idx: int, *, percent: bool = False, millions: bool = True) -> float | None:
        row = tables.get(table, {}).get(label, [])
        if idx >= len(row):
            return None
        return _parse_stockanalysis_number(row[idx], percent=percent, millions=millions)

    for idx, fiscal_year in enumerate(fiscal_years):
        if fiscal_year != "TTM" and not fiscal_year.startswith("FY "):
            continue
        report_period = _parse_stockanalysis_period(periods[idx] if idx < len(periods) else None)
        record: dict[str, float | str | None] = {
            "ticker": ticker.upper(),
            "report_period": report_period,
            "period": "ttm" if fiscal_year == "TTM" else "annual",
            "currency": "USD",
            "revenue": value("income", "Revenue", idx),
            "cost_of_revenue": value("income", "Cost of Revenue", idx),
            "gross_profit": value("income", "Gross Profit", idx),
            "research_and_development": value("income", "Research & Development", idx),
            "selling_general_and_administrative_expenses": value("income", "Selling, General & Admin", idx),
            "operating_income": value("income", "Operating Income", idx),
            "interest_expense": value("income", "Interest Expense", idx),
            "pretax_income": value("income", "Pretax Income", idx),
            "net_income": value("income", "Net Income", idx),
            "earnings_per_share": value("income", "EPS (Diluted)", idx, millions=False),
            "outstanding_shares": value("income", "Shares Outstanding", idx),
            "free_cash_flow": value("income", "Free Cash Flow", idx),
            "free_cash_flow_per_share": value("income", "Free Cash Flow Per Share", idx, millions=False),
            "gross_margin": value("income", "Gross Margin", idx, percent=True, millions=False),
            "operating_margin": value("income", "Operating Margin", idx, percent=True, millions=False),
            "net_margin": value("income", "Profit Margin", idx, percent=True, millions=False),
            "ebitda": value("income", "EBITDA", idx),
            "ebit": value("income", "EBIT", idx),
            "cash_and_equivalents": value("balance", "Cash & Equivalents", idx),
            "current_assets": value("balance", "Total Current Assets", idx),
            "current_liabilities": value("balance", "Total Current Liabilities", idx),
            "total_assets": value("balance", "Total Assets", idx),
            "total_liabilities": value("balance", "Total Liabilities", idx),
            "total_debt": value("balance", "Total Debt", idx),
            "shareholders_equity": value("balance", "Shareholders' Equity", idx),
            "book_value_per_share": value("balance", "Book Value Per Share", idx, millions=False),
            "goodwill_and_intangible_assets": ((value("balance", "Goodwill", idx) or 0.0) + (value("balance", "Other Intangible Assets", idx) or 0.0)),
            "operating_cash_flow": value("cashflow", "Operating Cash Flow", idx),
            "capital_expenditure": value("cashflow", "Capital Expenditures", idx),
            "market_cap": value("ratios", "Market Cap", idx),
            "enterprise_value": value("ratios", "Enterprise Value", idx),
            "price_to_earnings_ratio": value("ratios", "PE Ratio", idx, millions=False),
            "price_to_book_ratio": value("ratios", "PB Ratio", idx, millions=False),
            "price_to_sales_ratio": value("ratios", "PS Ratio", idx, millions=False),
            "enterprise_value_to_ebitda_ratio": value("ratios", "EV/EBITDA Ratio", idx, millions=False),
            "enterprise_value_to_revenue_ratio": value("ratios", "EV/Sales Ratio", idx, millions=False),
            "peg_ratio": value("ratios", "PEG Ratio", idx, millions=False),
            "debt_to_equity": value("ratios", "Debt / Equity Ratio", idx, millions=False),
            "current_ratio": value("ratios", "Current Ratio", idx, millions=False),
            "quick_ratio": value("ratios", "Quick Ratio", idx, millions=False),
            "return_on_equity": value("ratios", "Return on Equity (ROE)", idx, percent=True, millions=False),
            "return_on_assets": value("ratios", "Return on Assets (ROA)", idx, percent=True, millions=False),
            "return_on_invested_capital": value("ratios", "Return on Invested Capital (ROIC)", idx, percent=True, millions=False),
            "asset_turnover": value("ratios", "Asset Turnover", idx, millions=False),
            "inventory_turnover": value("ratios", "Inventory Turnover", idx, millions=False),
            "free_cash_flow_yield": value("ratios", "FCF Yield", idx, percent=True, millions=False),
        }

        fcf = record.get("free_cash_flow")
        total_debt = record.get("total_debt")
        total_assets = record.get("total_assets")
        if fcf and record.get("market_cap"):
            record["free_cash_flow_yield"] = float(fcf) / float(record["market_cap"])
        if total_debt and total_assets:
            record["debt_to_assets"] = float(total_debt) / float(total_assets)

        key = "ttm" if fiscal_year == "TTM" else "annual"
        data.setdefault(key, {})[report_period or fiscal_year] = record

    _STOCKANALYSIS_CACHE[slug] = data
    return data


def _records_for_period(ticker: str, period: str, limit: int) -> list[dict[str, float | str | None]]:
    data = _stockanalysis_financial_data(ticker)
    key = "ttm" if period == "ttm" else "annual"
    records = list(data.get(key, {}).values())
    return records[:limit]


def _get_financial_metrics_from_stockanalysis(ticker: str, period: str, limit: int) -> list[FinancialMetrics]:
    metrics = []
    for record in _records_for_period(ticker, period, limit):
        payload = {field: record.get(field) for field in FinancialMetrics.model_fields}
        payload.update(record)
        metrics.append(FinancialMetrics(**payload))
    return metrics


def _search_line_items_from_stockanalysis(
    ticker: str,
    line_items: list[str],
    period: str,
    limit: int,
) -> list[LineItem]:
    results = []
    requested = set(line_items)
    base_fields = {"ticker", "report_period", "period", "currency"}
    for record in _records_for_period(ticker, period, limit):
        payload = {key: record.get(key) for key in base_fields}
        for item in requested:
            payload[item] = record.get(item)
        for extra in (
            "revenue",
            "net_income",
            "free_cash_flow",
            "operating_cash_flow",
            "capital_expenditure",
            "outstanding_shares",
            "earnings_per_share",
            "book_value_per_share",
            "gross_margin",
            "operating_margin",
            "return_on_invested_capital",
            "goodwill_and_intangible_assets",
            "total_assets",
            "total_liabilities",
            "current_assets",
            "current_liabilities",
            "total_debt",
            "shareholders_equity",
            "research_and_development",
            "interest_expense",
        ):
            if extra not in payload:
                payload[extra] = record.get(extra)
        results.append(LineItem(**payload))
    return results


def _get_market_cap_from_stockanalysis(ticker: str) -> float | None:
    records = _records_for_period(ticker, "ttm", 1)
    if not records:
        return None
    market_cap = records[0].get("market_cap")
    return float(market_cap) if market_cap else None


def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
    api_key: str = None,
) -> list[FinancialMetrics]:
    """Fetch financial metrics from cache or API."""
    # Create a cache key that includes all parameters to ensure exact matches
    cache_key = f"{ticker}_{period}_{end_date}_{limit}"

    # Check cache first - simple exact match
    if cached_data := _cache.get_financial_metrics(cache_key):
        return [FinancialMetrics(**metric) for metric in cached_data]

    # If not in cache, fetch from API
    headers = {}
    financial_api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
    if financial_api_key:
        headers["X-API-KEY"] = financial_api_key

    url = f"https://api.financialdatasets.ai/financial-metrics/?ticker={ticker}&report_period_lte={end_date}&limit={limit}&period={period}"
    response = _make_api_request(url, headers)
    if response.status_code != 200:
        financial_metrics = _get_financial_metrics_from_stockanalysis(ticker, period, limit)
        if financial_metrics:
            _cache.set_financial_metrics(cache_key, [m.model_dump() for m in financial_metrics])
        return financial_metrics

    # Parse response with Pydantic model
    try:
        metrics_response = FinancialMetricsResponse(**response.json())
        financial_metrics = metrics_response.financial_metrics
    except Exception as e:
        logger.warning("Failed to parse financial metrics response for %s: %s", ticker, e)
        financial_metrics = _get_financial_metrics_from_stockanalysis(ticker, period, limit)
        if financial_metrics:
            _cache.set_financial_metrics(cache_key, [m.model_dump() for m in financial_metrics])
        return financial_metrics

    if not financial_metrics:
        financial_metrics = _get_financial_metrics_from_stockanalysis(ticker, period, limit)
        if financial_metrics:
            _cache.set_financial_metrics(cache_key, [m.model_dump() for m in financial_metrics])
        return financial_metrics

    # Cache the results as dicts using the comprehensive cache key
    _cache.set_financial_metrics(cache_key, [m.model_dump() for m in financial_metrics])
    return financial_metrics


def search_line_items(
    ticker: str,
    line_items: list[str],
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
    api_key: str = None,
) -> list[LineItem]:
    """Fetch line items from API."""
    # If not in cache or insufficient data, fetch from API
    headers = {}
    financial_api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
    if financial_api_key:
        headers["X-API-KEY"] = financial_api_key

    url = "https://api.financialdatasets.ai/financials/search/line-items"

    body = {
        "tickers": [ticker],
        "line_items": line_items,
        "end_date": end_date,
        "period": period,
        "limit": limit,
    }
    response = _make_api_request(url, headers, method="POST", json_data=body)
    if response.status_code != 200:
        return _search_line_items_from_stockanalysis(ticker, line_items, period, limit)

    try:
        data = response.json()
        response_model = LineItemResponse(**data)
        search_results = response_model.search_results
    except Exception as e:
        logger.warning("Failed to parse line items response for %s: %s", ticker, e)
        return _search_line_items_from_stockanalysis(ticker, line_items, period, limit)
    if not search_results:
        return _search_line_items_from_stockanalysis(ticker, line_items, period, limit)

    # Cache the results
    return search_results[:limit]


def get_insider_trades(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
    api_key: str = None,
) -> list[InsiderTrade]:
    """Fetch insider trades from cache or API."""
    # Create a cache key that includes all parameters to ensure exact matches
    cache_key = f"{ticker}_{start_date or 'none'}_{end_date}_{limit}"

    # Check cache first - simple exact match
    if cached_data := _cache.get_insider_trades(cache_key):
        return [InsiderTrade(**trade) for trade in cached_data]

    # If not in cache, fetch from API
    headers = {}
    financial_api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
    if financial_api_key:
        headers["X-API-KEY"] = financial_api_key

    all_trades = []
    current_end_date = end_date

    while True:
        url = f"https://api.financialdatasets.ai/insider-trades/?ticker={ticker}&filing_date_lte={current_end_date}"
        if start_date:
            url += f"&filing_date_gte={start_date}"
        url += f"&limit={limit}"

        response = _make_api_request(url, headers)
        if response.status_code != 200:
            break

        try:
            data = response.json()
            response_model = InsiderTradeResponse(**data)
            insider_trades = response_model.insider_trades
        except Exception as e:
            logger.warning("Failed to parse insider trades response for %s: %s", ticker, e)
            break

        if not insider_trades:
            break

        all_trades.extend(insider_trades)

        # Only continue pagination if we have a start_date and got a full page
        if not start_date or len(insider_trades) < limit:
            break

        # Update end_date to the oldest filing date from current batch for next iteration
        current_end_date = min(trade.filing_date for trade in insider_trades).split("T")[0]

        # If we've reached or passed the start_date, we can stop
        if current_end_date <= start_date:
            break

    if not all_trades:
        return []

    # Cache the results using the comprehensive cache key
    _cache.set_insider_trades(cache_key, [trade.model_dump() for trade in all_trades])
    return all_trades


def get_company_news(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
    api_key: str = None,
) -> list[CompanyNews]:
    """Fetch company news from cache or API."""
    # Create a cache key that includes all parameters to ensure exact matches
    cache_key = f"{ticker}_{start_date or 'none'}_{end_date}_{limit}"

    # Check cache first - simple exact match
    if cached_data := _cache.get_company_news(cache_key):
        return [CompanyNews(**news) for news in cached_data]

    # If not in cache, fetch from API
    headers = {}
    financial_api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
    if financial_api_key:
        headers["X-API-KEY"] = financial_api_key

    all_news = []
    current_end_date = end_date

    while True:
        url = f"https://api.financialdatasets.ai/news/?ticker={ticker}&end_date={current_end_date}"
        if start_date:
            url += f"&start_date={start_date}"
        url += f"&limit={limit}"

        response = _make_api_request(url, headers)
        if response.status_code != 200:
            break

        try:
            data = response.json()
            response_model = CompanyNewsResponse(**data)
            company_news = response_model.news
        except Exception as e:
            logger.warning("Failed to parse company news response for %s: %s", ticker, e)
            break

        if not company_news:
            break

        all_news.extend(company_news)

        # Only continue pagination if we have a start_date and got a full page
        if not start_date or len(company_news) < limit:
            break

        # Update end_date to the oldest date from current batch for next iteration
        current_end_date = min(news.date for news in company_news).split("T")[0]

        # If we've reached or passed the start_date, we can stop
        if current_end_date <= start_date:
            break

    if not all_news:
        return []

    # Cache the results using the comprehensive cache key
    _cache.set_company_news(cache_key, [news.model_dump() for news in all_news])
    return all_news


def get_market_cap(
    ticker: str,
    end_date: str,
    api_key: str = None,
) -> float | None:
    """Fetch market cap from the API."""
    # Check if end_date is today
    if end_date == datetime.datetime.now().strftime("%Y-%m-%d"):
        # Get the market cap from company facts API
        headers = {}
        financial_api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
        if financial_api_key:
            headers["X-API-KEY"] = financial_api_key

        url = f"https://api.financialdatasets.ai/company/facts/?ticker={ticker}"
        response = _make_api_request(url, headers)
        if response.status_code != 200:
            print(f"Error fetching company facts: {ticker} - {response.status_code}")
            return _get_market_cap_from_stockanalysis(ticker)

        data = response.json()
        response_model = CompanyFactsResponse(**data)
        return response_model.company_facts.market_cap or _get_market_cap_from_stockanalysis(ticker)

    financial_metrics = get_financial_metrics(ticker, end_date, api_key=api_key)
    if not financial_metrics:
        return _get_market_cap_from_stockanalysis(ticker)

    market_cap = financial_metrics[0].market_cap

    if not market_cap:
        return _get_market_cap_from_stockanalysis(ticker)

    return market_cap


def prices_to_df(prices: list[Price]) -> pd.DataFrame:
    """Convert prices to a DataFrame."""
    df = pd.DataFrame([p.model_dump() for p in prices])
    df["Date"] = pd.to_datetime(df["time"])
    df.set_index("Date", inplace=True)
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_index(inplace=True)
    return df


# Update the get_price_data function to use the new functions
def get_price_data(ticker: str, start_date: str, end_date: str, api_key: str = None) -> pd.DataFrame:
    prices = get_prices(ticker, start_date, end_date, api_key=api_key)
    return prices_to_df(prices)
