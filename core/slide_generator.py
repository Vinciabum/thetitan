"""
Slide Generator - 5페이지 슬라이드 이미지 생성 및 조립
"""
import asyncio
from pathlib import Path
from typing import List, Optional

from core.image_generator import ImageGenerator
from core.psychological_engine import MonologueContent, SlideContent


class SlideGenerator:
    """MonologueContent의 각 슬라이드에 대한 이미지를 생성"""

    def __init__(self, image_generator: ImageGenerator, output_dir: Path):
        self.image_generator = image_generator
        self.output_dir = output_dir

    async def generate_slide_images(self, content: MonologueContent) -> List[Path]:
        """5개 슬라이드 이미지를 병렬 생성, 성공한 것(None 아닌 Path)만 반환"""
        tasks = [
            self._generate_one(slide)
            for slide in content.slides
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, Path)]

    async def _generate_one(self, slide: SlideContent) -> Optional[Path]:
        """슬라이드 1개 이미지 생성"""
        filename = f"slide_{slide.page:02d}_{slide.role.lower()}.jpg"
        output_path = self.output_dir / filename
        full_prompt = (
            f"{slide.image_prompt}\n\n"
            f"Overlay text (Korean, minimal, centered): \"{slide.text}\"\n"
            f"Typography: clean sans-serif, white text, subtle dark gradient overlay"
        )
        return await self.image_generator.generate(full_prompt, output_path)
