import asyncio
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler


CAPTURE = "C 10"
SET = "S C 0.999"
GET = "G SOP"

async def tcp_pol_client(msg):
    reader, writer = await asyncio.open_connection(
        '127.0.0.1', 6000)

    print(f'Sending: {msg}')
    writer.write(msg.encode())
    await writer.drain()
    data = await reader.read(1024)
    print(f'Received: {data.decode()!r}')
    writer.close()
    await writer.wait_closed()


async def calibrate_job():
    await tcp_pol_client(SET)

async def get_sop_job():
    await tcp_pol_client(GET)

scheduler = AsyncIOScheduler()
scheduler.add_job(get_sop_job, 'interval', seconds=10)
scheduler.add_job(calibrate_job, 'interval', minutes=1)

try:

    loop = asyncio.get_event_loop()
    loop.run_until_complete(tcp_pol_client(CAPTURE))
    #time.sleep(240)
    #loop.run_until_complete(tcp_pol_client(SET))
    scheduler.start()
    loop.run_forever()
except (KeyboardInterrupt, SystemExit):
    pass
