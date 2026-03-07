import asyncio
from app.main import cafe_stream_generator

async def test():
    class DummyRequest:
        async def is_disconnected(self):
            return False
            
    print("Starting generator...")
    try:
        async for chunk in cafe_stream_generator(DummyRequest(), 43.6532, -79.3832, 10, 5):
            print("GOT CHUNK:", chunk[:100])
    except Exception as e:
        print("GENERATOR CRASH:", e)

if __name__ == "__main__":
    asyncio.run(test())
