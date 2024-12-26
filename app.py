import sys
import asyncio
from datetime import datetime, timedelta
import aiohttp


class HttpError(Exception):
    pass


class ExchangeRateFetcher:
    API_URL = "https://api.privatbank.ua/p24api/exchange_rates?date={date}"

    async def fetch_exchange_rates(self, date: str):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.API_URL.format(date=date)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    raise HttpError(f"Error fetching data: {resp.status}")
            except aiohttp.ClientError as e:
                raise HttpError(f"HTTP error: {e}")

    async def get_rates(self, days: int, currencies: list[str]):
        results = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%d.%m.%Y")
            try:
                data = await self.fetch_exchange_rates(date)
                rates = {}
                for rate in data.get("exchangeRate", []):
                    if rate.get("currency") and rate["currency"].upper() in currencies:
                        rates[rate["currency"].upper()] = {
                            "sale": rate.get("saleRate", "N/A"),
                            "purchase": rate.get("purchaseRate", "N/A"),
                        }
                results.append({date: rates})
            except HttpError as e:
                print(f"Error fetching rates for {date}: {e}")
        return results


async def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <days> [currencies...]")
        return

    days = int(sys.argv[1])
    if days > 10:
        print("Error: You can only fetch rates for up to 10 days.")
        return

    currencies = [currency.upper() for currency in sys.argv[2:]] or ["USD", "EUR"]
    fetcher = ExchangeRateFetcher()
    rates = await fetcher.get_rates(days, currencies)
    print(rates)


if __name__ == "__main__":
    asyncio.run(main())
