# tests/test_slide_generator.py
import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from core.psychological_engine import SlideContent, MonologueContent

# Mock replicate before importing slide_generator to avoid Python 3.14 compatibility issues
sys.modules['replicate'] = MagicMock()

from core.slide_generator import SlideGenerator


@pytest.fixture
def sample_monologue_content():
    slides = [
        SlideContent(page=1, role="Hook", text="오늘 당신은 누구였나요?",
                     image_prompt="empty chair window morning light"),
        SlideContent(page=2, role="Context", text="뉴스가 말하는 오늘",
                     image_prompt="rainy city street morning"),
        SlideContent(page=3, role="Insight", text="프랭클의 통찰",
                     image_prompt="open book desk sunlight"),
        SlideContent(page=4, role="Action", text="오늘의 작은 행동",
                     image_prompt="path through misty forest"),
        SlideContent(page=5, role="Outro", text="당신의 의미는?",
                     image_prompt="window dawn golden hour"),
    ]
    return MonologueContent(
        slides=slides,
        instagram_caption="오늘도 수고했습니다.",
        hashtags=["#모노로그"]
    )


@pytest.mark.asyncio
async def test_generate_images_returns_five_paths(sample_monologue_content, tmp_path):
    mock_generator = MagicMock()
    mock_generator.generate = AsyncMock(return_value=tmp_path / "test.jpg")

    generator = SlideGenerator(image_generator=mock_generator, output_dir=tmp_path)
    paths = await generator.generate_slide_images(sample_monologue_content)

    assert len(paths) == 5
    assert mock_generator.generate.call_count == 5


@pytest.mark.asyncio
async def test_generate_images_skips_failed_slides(sample_monologue_content, tmp_path):
    mock_generator = MagicMock()
    mock_generator.generate = AsyncMock(side_effect=[
        tmp_path / "s1.jpg",
        tmp_path / "s2.jpg",
        None,
        tmp_path / "s4.jpg",
        tmp_path / "s5.jpg",
    ])

    generator = SlideGenerator(image_generator=mock_generator, output_dir=tmp_path)
    paths = await generator.generate_slide_images(sample_monologue_content)

    assert len(paths) == 4


@pytest.mark.asyncio
async def test_slide_filenames_include_page_and_role(sample_monologue_content, tmp_path):
    """이미지 파일명에 페이지 번호와 역할이 포함되는지 확인"""
    captured_paths = []

    async def capture_generate(prompt, output_path):
        captured_paths.append(output_path)
        return output_path

    mock_generator = MagicMock()
    mock_generator.generate = capture_generate

    generator = SlideGenerator(image_generator=mock_generator, output_dir=tmp_path)
    await generator.generate_slide_images(sample_monologue_content)

    assert len(captured_paths) == 5
    # 첫 번째 슬라이드 파일명 확인
    assert "01" in str(captured_paths[0].name)
    assert "hook" in str(captured_paths[0].name).lower()
