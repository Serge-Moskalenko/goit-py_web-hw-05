import asyncio
import websockets
import aiohttp
from aiohttp import web
from datetime import datetime, timedelta
import json


class WebSocketExchangeServer:
    def __init__(self):
        self.websocket_port = 4000
        self.http_port = 4001

    async def fetch_exchange_rate(self, days, currencies):
        results = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%d.%m.%Y")
            url = f"https://api.privatbank.ua/p24api/exchange_rates?date={date}"

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            exchange_rates = {
                                rate["currency"]: {
                                    "sale": rate.get("saleRate", "N/A"),
                                    "purchase": rate.get("purchaseRate", "N/A"),
                                }
                                for rate in data.get("exchangeRate", [])
                                if rate["currency"]
                                in [cur.upper() for cur in currencies]
                            }
                            results.append({date: exchange_rates})
                        else:
                            results.append(
                                {
                                    date: {
                                        "error": f"Failed to fetch data: {response.status}"
                                    }
                                }
                            )
                except Exception as e:
                    results.append({date: {"error": str(e)}})
        return results

    async def websocket_handler(self, websocket):
        async for message in websocket:
            print(f"Received message: {message}")
            if message.lower().startswith("exchange"):
                try:
                    parts = message.split()
                    days = int(parts[1]) if len(parts) > 1 else 1
                    currencies = parts[2:] if len(parts) > 2 else ["USD", "EUR"]

                    if days > 10:
                        await websocket.send(
                            json.dumps(
                                {"error": "Cannot fetch data for more than 10 days."}
                            )
                        )
                    else:
                        rates = await self.fetch_exchange_rate(days, currencies)
                        await websocket.send(json.dumps(rates))
                except Exception as e:
                    await websocket.send(json.dumps({"error": str(e)}))
            else:
                await websocket.send(json.dumps({"error": "Invalid command"}))

    async def start_websocket_server(self):
        print(f"WebSocket server started on ws://localhost:{self.websocket_port}")
        async with websockets.serve(
            self.websocket_handler, "localhost", self.websocket_port
        ):
            await asyncio.Future()

    async def start_http_server(self):
        async def handle(request):
            with open("index.html", "r", encoding="utf-8") as f:
                html = f.read()
            return web.Response(text=html, content_type="text/html")

        app = web.Application()
        app.router.add_get("/", handle)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", self.http_port)
        await site.start()
        print(f"HTTP server started on http://localhost:{self.http_port}")

    async def start(self):
        await asyncio.gather(self.start_websocket_server(), self.start_http_server())


if __name__ == "__main__":
    server = WebSocketExchangeServer()
    asyncio.run(server.start())
