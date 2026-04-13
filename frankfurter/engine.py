from .logger import Logger
from .utils import BASE_URL, BASE_HEADERS
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from .exceptions import FrankfurterCallFailedException, UnknownCurrencyException
from datetime import date as _date
import json
import socket


def _normalise_symbols(symbols: str) -> str:
    return ",".join(s.strip() for s in symbols.split(","))


def _parse_date(value: str, param_name: str) -> str:
    try:
        _date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"'{param_name}' must be in YYYY-MM-DD format, got: {value!r}")
    return value


class FrankfurterEngine:
    def __init__(self, quiet_mode: bool = True, timeout: float = 10.0) -> None:
        self.quiet_mode = quiet_mode
        self._timeout = timeout
        self._currencies_cache: dict | None = None
        if not quiet_mode:
            Logger.info("Currency Engine Initialized")
        self.__base_url = BASE_URL
        self.__base_headers = BASE_HEADERS

    def __api_call(
        self,
        query_params: dict | None = None,
        path_params: list[str] | None = None,
        extra_headers: dict | None = None,
    ) -> dict:
        """Handles the API request core logic."""
        query_params = query_params or {}
        path_params = path_params or []
        extra_headers = extra_headers or {}
        params_str = urlencode({k: v for k, v in query_params.items() if v})
        path_str = "/".join(path_params)
        request = Request(
            url=f"https://{self.__base_url}/{path_str}?{params_str}",
            method="GET",
            headers={**self.__base_headers, **extra_headers},
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                if not self.quiet_mode:
                    Logger.info("Found the Forex data successfully")
                return json.loads(response.read().decode())
        except HTTPError as e:
            raise FrankfurterCallFailedException(e.code, e.msg)
        except (URLError, socket.timeout) as e:
            raise FrankfurterCallFailedException(0, str(e))

    def _check_valid_currency(self, currency: str) -> None:
        """Validates if the currency code exists."""
        if currency not in self.fetch_currencies().keys():
            raise UnknownCurrencyException(f"Unknown Currency : {currency}")

    def fetch_latest_data(self, base: str | None = None, symbols: str | None = None) -> dict:
        """
        Fetches the latest forex data provided by the European Central Bank.

        Parameters:
            base (str): The base currency to convert from (optional, default: EUR).
            symbols (str): Comma-separated list of target currencies (optional).

        Returns:
            dict: Latest forex data for the provided base and target currencies.
        """
        if symbols:
            symbols = _normalise_symbols(symbols)
        if base:
            self._check_valid_currency(base)
        if symbols:
            for symbol in symbols.split(","):
                self._check_valid_currency(symbol)
        return self.__api_call({"base": base, "symbols": symbols}, path_params=["latest"])

    def fetch_time_series_data(
        self,
        start_date: str,
        base: str | None = None,
        symbols: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """
        Fetches forex data for a specified time range.

        Parameters:
            start_date (str): The start date in YYYY-MM-DD format (required).
            base (str): The base currency to convert from (optional, default: EUR).
            symbols (str): Comma-separated list of target currencies (optional).
            end_date (str): The end date in YYYY-MM-DD format (optional).

        Returns:
            dict: Forex data for the given time range.
        """
        _parse_date(start_date, "start_date")
        if end_date:
            _parse_date(end_date, "end_date")
        if symbols:
            symbols = _normalise_symbols(symbols)
        if base:
            self._check_valid_currency(base)
        if symbols:
            for symbol in symbols.split(","):
                self._check_valid_currency(symbol)
        path_params = [f'{start_date}..{end_date or ""}']
        return self.__api_call(query_params={"base": base, "symbols": symbols}, path_params=path_params)

    def fetch_data_for_date(self, date: str, base: str | None = None, symbols: str | None = None) -> dict:
        """
        Fetches forex data for a specific date.

        Parameters:
            date (str): The specific date in YYYY-MM-DD format.
            base (str): The base currency to convert from (optional, default: EUR).
            symbols (str): Comma-separated list of target currencies (optional).

        Returns:
            dict: Forex data for the specified date.
        """
        _parse_date(date, "date")
        if symbols:
            symbols = _normalise_symbols(symbols)
        if base:
            self._check_valid_currency(base)
        if symbols:
            for symbol in symbols.split(","):
                self._check_valid_currency(symbol)
        return self.__api_call(query_params={"base": base, "symbols": symbols}, path_params=[date])

    def fetch_currencies(self) -> dict:
        """
        Fetches the list of supported currencies.

        Returns:
            dict: A dictionary of supported currencies where the keys are currency codes.
        """
        if self._currencies_cache is None:
            self._currencies_cache = self.__api_call(path_params=["currencies"])
        return self._currencies_cache

    def convert_currency(self, amount: float, base: str, to: str) -> float:
        """
        Converts a specified amount from one currency to another using the latest exchange rate.

        Parameters:
            amount (float): The amount to convert.
            base (str): The source currency.
            to (str): The target currency.

        Returns:
            float: The converted amount based on the latest exchange rate.
        """
        self._check_valid_currency(base)
        self._check_valid_currency(to)
        rates = self.fetch_latest_data(base=base, symbols=to)
        exchange_rate = rates["rates"].get(to)
        if exchange_rate:
            return amount * exchange_rate
        raise FrankfurterCallFailedException(404, f"No exchange rate found for {base} to {to}.")
