import asyncio
from pathlib import Path
from core.slide_generator import SlideGenerator
from core.psychological_engine import MonologueContent, SlideContent

slides = [
    SlideContent(page=1, role='Hook',    text='야근하고 집에 오면\n왜 더\n공허할까',        image_prompt='x'),
    SlideContent(page=2, role='Context', text='번아웃의 신호\n\n몸은 출근했지만 마음은 이미 퇴사했다. 그 감각, 당신만 느끼는 게 아니다.', image_prompt='x'),
    SlideContent(page=3, role='Insight', text='의미가 사라질 때\n\n프랭클은 말했다. 고통 자체가 문제가 아니라 고통의 이유를 모르는 것이 문제라고.', image_prompt='x'),
    SlideContent(page=4, role='Action',  text='오늘 하나만\n\n퇴근 후 5분, 핸드폰을 내려놓고 오늘 가장 힘들었던 순간을 종이에 써보자.', image_prompt='x'),
    SlideContent(page=5, role='Outro',   text='열심히 살았는데\n왜 아직도 이 자리야', image_prompt='x'),
]
content = MonologueContent(slides=slides, instagram_caption='', hashtags=[])
sg = SlideGenerator(image_generator=None, output_dir=Path('output_test'))
asyncio.run(sg.generate_slide_images(content))
print('DONE')
