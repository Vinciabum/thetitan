import asyncio, os, sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from core.context_engine import ContextEngine
from core.psychological_engine import PsychologicalEngine
from core.slide_generator import SlideGenerator
from core.image_generator import ImageGeneratorFactory
from google import genai

class Adapter:
    def generate_content(self, p):
        client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
        return client.models.generate_content(model='gemini-2.5-flash', contents=p)

async def run():
    print("1. 컨텍스트 수집 중...", flush=True)
    context = await ContextEngine().collect()
    print(f"   {context.weather.season} / {context.weather.description} / {context.weather.temperature}C", flush=True)

    print("2. AI 콘텐츠 생성 중...", flush=True)
    monologue = await PsychologicalEngine(Adapter()).generate(context)
    for s in monologue.slides:
        print(f"   [{s.role}] {s.text[:50]}", flush=True)

    print("3. 슬라이드 이미지 생성 중...", flush=True)
    creds = {'GEMINI_API_KEY': os.environ.get('GEMINI_API_KEY','')}
    cfg = {
        'default_provider': 'gemini',
        'providers': {'gemini': {'model': 'gemini-2.5-flash-image', 'aspect_ratio': '1:1'}}
    }
    gen = ImageGeneratorFactory.create('gemini', creds, cfg)
    out = Path('output_test')
    sg = SlideGenerator(image_generator=gen, output_dir=out)
    paths = await sg.generate_slide_images(monologue)
    print(f"완료: {len(paths)}장 생성", flush=True)

asyncio.run(run())
