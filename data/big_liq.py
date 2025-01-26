import asyncio
import json
import os
from datetime import datetime
import pytz
from websockets import connect
from termcolor import cprint

# Corrected WebSocket URL
websocket_url = 'wss://fstream.binance.com/ws/!forceOrder@arr'
filename = 'big_liquidations_binance.csv'

# Ensure the CSV file exists with a header
if not os.path.isfile(filename):
    with open(filename, 'w') as f:
        f.write(','.join([
            'symbol', 'side', 'order_type', 'time_in_force', 'original_quantity', 'price',
            'average_price', 'order_status', 'order_last_filled_quantity',
            'order_filled_accumulated_quantity', 'order_trade_time', 'usd_size'
        ]) + '\n')
async def binance_liquidation(uri, filename):
    while True:
        try:
            # Use asyncio.wait_for to apply timeout to the connection
            websocket = await asyncio.wait_for(connect(uri), timeout=10)
            async with websocket:  # Use async with for the websocket connection
                while True:
                    try:
                        # Receive a message
                        msg = await websocket.recv()
                        order_data = json.loads(msg)['o']
                    
                            
                        symbol = order_data['s'].replace('USDT', '')
                        side = order_data['S']
                        timestamp = int(order_data['T'])
                        filled_quantity = float(order_data['q'])
                        price = float(order_data['p'])
                        usd_size = filled_quantity * price

                        # Format time
                        est = pytz.timezone('US/Eastern')
                        time_est = datetime.fromtimestamp(timestamp / 1000, est).strftime('%H:%M:%S')

                        if usd_size > 100000:
                            liquidation_type = 'L LIQ' if side == 'SELL' else 'S LIQ'
                            symbol =symbol[:4]
                            output = f"{liquidation_type} {symbol[:4]} {time_est} {usd_size:,.2f}"
                            color = 'blue' if side == 'SELL' else 'magenta'
                            attrs = ['bold'] if usd_size > 10000 else []

                            usd_size = usd_size / 1000000

                            cprint({output}, 'white', f'on_{color}', attrs=attrs )

                            print('')

                        # Write data to the CSV file
                        msg_values = [str(order_data.get(key)) for key in ['s', 'S', 'o', 'f', 'q', 'p', 'ap', 'X', 'l', 'z', 'T']]
                        msg_values.append(str(usd_size))
                        with open(filename, 'a') as f:
                            trade_info = ','.join(msg_values).replace('USDT', '') + '\n'
                            f.write(trade_info)

                    except Exception as e:
                        cprint(f"Error while processing message: {e}", 'red')
                        await asyncio.sleep(5)

        except asyncio.exceptions.TimeoutError:
            cprint("Connection timed out. Retrying in 5 seconds...", 'red')
            await asyncio.sleep(5)
        except Exception as e:
            cprint(f"Unexpected error: {e}", 'red')
            await asyncio.sleep(5)


# Run the WebSocket connection
asyncio.run(binance_liquidation(websocket_url, filename))
        