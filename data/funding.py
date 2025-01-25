import asyncio
import json
from datetime import datetime
from websockets import connect
from termcolor import cprint

# List of trading pairs
symbols = ['btcusdt', 'ethusdt', 'solusdt', 'bnbusdt', 'dogeusdt', 'wifusdt']
websocket_url_base = 'wss://fstream.binance.com/ws/'
shared_symbol_counter = {'count': 0}
print_lock = asyncio.Lock()  # Define print_lock correctly

async def binance_funding_stream(symbol, shared_counter):
    websocket_url = f'{websocket_url_base}{symbol}@markPrice'
    try:
        async with connect(websocket_url) as websocket:
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    event_time = datetime.fromtimestamp(data['E'] / 1000).strftime('%H:%M:%S')
                    symbol_display = data['s'].replace('USDT', '')
                    funding_rate = float(data['r'])
                    yearly_funding_rate = (funding_rate * 3 * 365) * 100

                    # Assign text and background colors based on yearly funding rate
                    if yearly_funding_rate > 50:
                        text_color, back_color = 'black', 'on_red'
                    elif yearly_funding_rate > 30:
                        text_color, back_color = 'black', 'on_yellow'
                    elif yearly_funding_rate > 5:
                        text_color, back_color = 'black', 'on_cyan'
                    elif yearly_funding_rate > -10:
                        text_color, back_color = 'black', 'on_green'
                    else:
                        text_color, back_color = 'black', 'on_light_green'

                    # Use lock to ensure clean output
                    async with print_lock:
                        cprint(f"{symbol_display} funding: {yearly_funding_rate:.2f}%", text_color, back_color)

                    # Increment the shared counter
                    shared_counter['count'] += 1

                    # Check if all symbols have been processed
                    if shared_counter['count'] >= len(symbols):
                        async with print_lock:
                            cprint(f'{event_time} Yearly Funding Summary', 'white', 'on_black')
                        shared_counter['count'] = 0
                except Exception as e:
                    print(f"Error processing data for {symbol}: {e}")
                    await asyncio.sleep(5)
    except Exception as e:
        print(f"Error connecting to WebSocket for {symbol}: {e}")
        await asyncio.sleep(5)

async def main():
    tasks = [binance_funding_stream(symbol, shared_symbol_counter) for symbol in symbols]
    await asyncio.gather(*tasks)

asyncio.run(main())