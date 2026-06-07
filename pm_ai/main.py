#!/usr/bin/env python3
"""
AI 상품페이지 기획자 (PM AI Employee)
화장품 전성분 → 상품 페이지 기획안 자동 생성

사용법:
    python main.py

환경 변수:
    ANTHROPIC_API_KEY - Anthropic API 키 (필수)
"""

import os
import json
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

# .env 파일 자동 로드
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

import anthropic

MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """당신은 15년 경력의 전문 화장품 상품 기획자 AI입니다.

핵심 역할:
- 화장품 전성분을 분석하여 실제 효능 도출
- 소비자 언어(고객 언어)로 상품 설명 작성
- 소비자 페인포인트와 연결한 판매 포인트 3개 도출
- 경쟁사 대비 차별화 포인트 분석

분석 철학:
- 성분명을 고객이 느끼는 피부 변화로 번역
- 기술적 정보를 감성적 스토리로 전환
- 트렌드와 소비자 니즈를 반영한 포지셔닝
- 구체적 성분 근거 기반의 신뢰 있는 카피 작성"""


def get_analysis_prompt(ingredients: str, product_info: str, competitor_info: str) -> str:
    return f"""다음 화장품 정보를 분석하여 완성된 상품 페이지 기획안을 JSON 형식으로 작성해주세요.

## 입력 정보

**전성분:**
{ingredients}

**상품 정보 (유형/가격대/브랜드 등):**
{product_info if product_info else "입력 없음 - 전성분으로 추정하세요"}

**경쟁사/경쟁 상품 정보:**
{competitor_info if competitor_info else "경쟁사 정보 없음 - 일반적인 시장 기준으로 분석"}

## 출력 요구사항

반드시 아래 JSON 형식으로만 출력하세요 (추가 텍스트 없이 JSON만):

{{
  "product_analysis": {{
    "product_type": "추정 상품 유형 (예: 수분 세럼, 선크림 등)",
    "skin_type_target": "타겟 피부 타입",
    "key_ingredients": [
      {{"name": "성분명", "benefit": "고객 언어로 효능 설명", "star_rating": "★★★☆☆"}}
    ],
    "efficacy_summary": "주요 효능 요약 (고객 관점, 2-3문장)"
  }},
  "customer_copy": {{
    "headline": "메인 카피 (20자 이내, 임팩트 있게)",
    "sub_headline": "서브 카피 (30-40자)",
    "description": "상품 설명글 (150-200자, 고객 언어로 자연스럽게)",
    "usage_tip": "사용 팁 또는 효과 체감 시점 (1-2문장)"
  }},
  "selling_points": [
    {{
      "number": 1,
      "pain_point": "소비자가 겪는 구체적인 문제/불편",
      "solution": "이 상품이 해결하는 방식 (성분 연결)",
      "message": "판매 포인트 메시지 (감성적, 30자 이내)",
      "evidence": "핵심 성분명 + 효능 근거"
    }},
    {{
      "number": 2,
      "pain_point": "두 번째 페인포인트",
      "solution": "해결 방식",
      "message": "두 번째 판매 포인트 메시지",
      "evidence": "성분 근거"
    }},
    {{
      "number": 3,
      "pain_point": "세 번째 페인포인트",
      "solution": "해결 방식",
      "message": "세 번째 판매 포인트 메시지",
      "evidence": "성분 근거"
    }}
  ],
  "competitor_analysis": {{
    "market_positioning": "시장 내 포지셔닝 설명 (1-2문장)",
    "our_advantages": [
      {{"point": "차별화 포인트 제목", "description": "경쟁사와 비교 설명"}}
    ],
    "comparison_table": [
      {{"feature": "비교 항목", "our_product": "우리 상품 특징", "competitor": "일반 경쟁사 수준"}}
    ],
    "usp": "핵심 USP - 경쟁사 대비 유일한 강점 (한 문장)"
  }},
  "visual_concept": {{
    "banner_concept": "배너 이미지 콘셉트 설명 (무드, 스타일)",
    "color_palette": {{
      "primary": "#HEX",
      "secondary": "#HEX",
      "accent": "#HEX",
      "background": "#HEX",
      "text": "#HEX"
    }},
    "mood_keywords": ["분위기 키워드1", "키워드2", "키워드3"],
    "image_direction": "이미지 방향성 (배경, 소재, 스타일 등)",
    "midjourney_prompt": "영어로 작성된 Midjourney/DALL-E 프롬프트 (구체적으로)"
  }},
  "trend_analysis": {{
    "why_trending": "이 성분/상품이 지금 트렌디한 이유 (2-3문장)",
    "target_consumer": "핵심 타겟 소비자 프로필 (연령, 라이프스타일, 피부 고민)",
    "purchase_trigger": "구매 결정 시점/트리거 (어떤 상황에서 구매하는가)",
    "market_timing": "시장 타이밍 분석 (1-2문장)"
  }}
}}"""


def analyze_product(ingredients: str, product_info: str, competitor_info: str) -> dict:
    """Claude API로 상품 분석 실행"""
    client = anthropic.Anthropic()

    print("\n분석 중 (시간이 걸릴 수 있습니다)...\n")

    full_response = ""

    with client.messages.stream(
        model=MODEL,
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": get_analysis_prompt(ingredients, product_info, competitor_info),
            }
        ],
    ) as stream:
        for text in stream.text_stream:
            full_response += text
            print(".", end="", flush=True)

    print("\n\n분석 완료!\n")

    # JSON 추출
    json_str = full_response.strip()
    if "```json" in json_str:
        start = json_str.find("```json") + 7
        end = json_str.find("```", start)
        json_str = json_str[start:end].strip()
    elif "```" in json_str:
        start = json_str.find("```") + 3
        end = json_str.find("```", start)
        json_str = json_str[start:end].strip()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류: {e}")
        print("원본 응답:\n", full_response[:500])
        return {"raw_output": full_response}


def generate_html_report(analysis: dict, ingredients: str, product_info: str) -> str:
    """분석 결과를 HTML 보고서로 변환"""

    pa = analysis.get("product_analysis", {})
    cc = analysis.get("customer_copy", {})
    sp = analysis.get("selling_points", [])
    ca = analysis.get("competitor_analysis", {})
    vc = analysis.get("visual_concept", {})
    ta = analysis.get("trend_analysis", {})

    palette = vc.get("color_palette", {})
    primary = palette.get("primary", "#2d6a4f")
    secondary = palette.get("secondary", "#40916c")
    accent = palette.get("accent", "#b7e4c7")
    bg_color = palette.get("background", "#f8fffe")
    text_color = palette.get("text", "#1b4332")

    # 판매 포인트 카드 HTML
    sp_cards = ""
    for point in sp:
        n = point.get("number", "")
        sp_cards += f"""
        <div class="sp-card">
            <div class="sp-number">{n}</div>
            <div class="sp-content">
                <div class="sp-pain">
                    <span class="label">페인포인트</span>
                    <p>{point.get('pain_point', '')}</p>
                </div>
                <div class="sp-arrow">→</div>
                <div class="sp-solution">
                    <span class="label">솔루션</span>
                    <p>{point.get('solution', '')}</p>
                </div>
            </div>
            <div class="sp-message">"{point.get('message', '')}"</div>
            <div class="sp-evidence">근거: {point.get('evidence', '')}</div>
        </div>"""

    # 주요 성분 카드
    ki_cards = ""
    for ing in pa.get("key_ingredients", []):
        ki_cards += f"""
        <div class="ingredient-card">
            <div class="ing-name">{ing.get('name', '')}</div>
            <div class="ing-rating">{ing.get('star_rating', '')}</div>
            <div class="ing-benefit">{ing.get('benefit', '')}</div>
        </div>"""

    # 경쟁사 비교 테이블
    comp_rows = ""
    for row in ca.get("comparison_table", []):
        comp_rows += f"""
        <tr>
            <td class="feature-cell">{row.get('feature', '')}</td>
            <td class="our-cell">{row.get('our_product', '')}</td>
            <td class="comp-cell">{row.get('competitor', '')}</td>
        </tr>"""

    # 우리 강점 리스트
    adv_items = ""
    for adv in ca.get("our_advantages", []):
        adv_items += f"""
        <div class="advantage-item">
            <div class="adv-title">{adv.get('point', '')}</div>
            <div class="adv-desc">{adv.get('description', '')}</div>
        </div>"""

    # 색상 팔레트 스와치
    color_swatches = ""
    color_labels = {"primary": "메인", "secondary": "서브", "accent": "포인트", "background": "배경", "text": "텍스트"}
    for key, label in color_labels.items():
        hex_val = palette.get(key, "#cccccc")
        color_swatches += f"""
        <div class="swatch">
            <div class="swatch-color" style="background:{hex_val}"></div>
            <div class="swatch-label">{label}</div>
            <div class="swatch-hex">{hex_val}</div>
        </div>"""

    # 무드 키워드 태그
    mood_tags = ""
    for kw in vc.get("mood_keywords", []):
        mood_tags += f'<span class="mood-tag">{kw}</span>'

    now = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 상품페이지 기획안 - {pa.get('product_type', '상품')}</title>
<style>
  :root {{
    --primary: {primary};
    --secondary: {secondary};
    --accent: {accent};
    --bg: {bg_color};
    --text: {text_color};
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;
    background: #f0f0f0;
    color: #333;
    font-size: 14px;
    line-height: 1.6;
  }}
  .page {{ max-width: 960px; margin: 0 auto; background: white; }}

  /* ── 배너 ── */
  .banner {{
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 60%, var(--accent) 100%);
    padding: 60px 48px;
    color: white;
    position: relative;
    overflow: hidden;
  }}
  .banner::before {{
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 200px; height: 200px;
    border-radius: 50%;
    background: rgba(255,255,255,0.08);
  }}
  .banner::after {{
    content: '';
    position: absolute;
    bottom: -60px; left: -20px;
    width: 280px; height: 280px;
    border-radius: 50%;
    background: rgba(255,255,255,0.06);
  }}
  .banner-badge {{
    display: inline-block;
    background: rgba(255,255,255,0.2);
    border: 1px solid rgba(255,255,255,0.4);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 12px;
    margin-bottom: 20px;
    letter-spacing: 0.5px;
  }}
  .banner h1 {{
    font-size: 40px;
    font-weight: 800;
    margin-bottom: 12px;
    letter-spacing: -0.5px;
  }}
  .banner .sub {{ font-size: 18px; opacity: 0.9; margin-bottom: 28px; }}
  .banner-meta {{
    font-size: 12px;
    opacity: 0.7;
    border-top: 1px solid rgba(255,255,255,0.3);
    padding-top: 16px;
    margin-top: 20px;
  }}

  /* ── 섹션 공통 ── */
  .section {{ padding: 40px 48px; border-bottom: 1px solid #eee; }}
  .section-title {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--primary);
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .section-title::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(to right, var(--accent), transparent);
  }}

  /* ── 요약 카드 ── */
  .summary-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }}
  .summary-card {{
    background: var(--bg);
    border-radius: 12px;
    padding: 20px 24px;
    border-left: 3px solid var(--primary);
  }}
  .summary-card .card-label {{
    font-size: 11px;
    color: #888;
    margin-bottom: 6px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
  }}
  .summary-card .card-value {{ font-size: 15px; color: #222; font-weight: 500; }}

  /* ── 카피 블록 ── */
  .copy-headline {{
    font-size: 32px;
    font-weight: 800;
    color: var(--primary);
    margin-bottom: 8px;
    letter-spacing: -0.5px;
  }}
  .copy-sub {{
    font-size: 16px;
    color: #555;
    margin-bottom: 20px;
    font-weight: 500;
  }}
  .copy-description {{
    font-size: 15px;
    line-height: 1.8;
    color: #444;
    background: var(--bg);
    padding: 20px 24px;
    border-radius: 8px;
    margin-bottom: 16px;
  }}
  .copy-tip {{
    font-size: 13px;
    color: var(--secondary);
    padding: 10px 16px;
    border-left: 3px solid var(--accent);
    background: #fafffe;
  }}

  /* ── 성분 카드 ── */
  .ingredients-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 20px;
  }}
  .ingredient-card {{
    background: white;
    border: 1px solid #e8f4ed;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    transition: box-shadow 0.2s;
  }}
  .ingredient-card:hover {{ box-shadow: 0 4px 12px rgba(45,106,79,0.1); }}
  .ing-name {{ font-size: 13px; font-weight: 700; color: var(--primary); margin-bottom: 4px; }}
  .ing-rating {{ font-size: 14px; color: #f4a261; margin-bottom: 6px; }}
  .ing-benefit {{ font-size: 12px; color: #666; line-height: 1.5; }}
  .efficacy-summary {{
    background: linear-gradient(to right, var(--bg), white);
    border-radius: 10px;
    padding: 18px 22px;
    font-size: 14px;
    color: #444;
    line-height: 1.7;
    border: 1px solid #e8f4ed;
  }}

  /* ── 판매 포인트 ── */
  .sp-card {{
    background: white;
    border-radius: 12px;
    border: 1px solid #e8f4ed;
    padding: 24px;
    margin-bottom: 16px;
    position: relative;
    overflow: hidden;
  }}
  .sp-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    background: var(--primary);
  }}
  .sp-number {{
    font-size: 11px;
    font-weight: 700;
    color: var(--primary);
    background: var(--accent);
    width: 24px; height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;
  }}
  .sp-content {{
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 16px;
    align-items: center;
    margin-bottom: 16px;
  }}
  .sp-pain, .sp-solution {{
    background: #f8f9fa;
    border-radius: 8px;
    padding: 12px 14px;
  }}
  .sp-solution {{ background: #f0faf5; }}
  .sp-arrow {{ color: var(--primary); font-size: 20px; font-weight: 300; text-align: center; }}
  .label {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    color: #888;
    text-transform: uppercase;
    display: block;
    margin-bottom: 4px;
  }}
  .sp-message {{
    font-size: 17px;
    font-weight: 700;
    color: var(--primary);
    text-align: center;
    padding: 12px;
    background: var(--bg);
    border-radius: 8px;
    margin-bottom: 10px;
  }}
  .sp-evidence {{
    font-size: 12px;
    color: #888;
    text-align: right;
  }}

  /* ── 경쟁사 분석 ── */
  .usp-box {{
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    color: white;
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 24px;
    font-size: 16px;
    font-weight: 600;
    text-align: center;
  }}
  .usp-label {{
    font-size: 11px;
    opacity: 0.8;
    letter-spacing: 1px;
    margin-bottom: 6px;
    text-transform: uppercase;
  }}
  .advantages-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 24px;
  }}
  .advantage-item {{
    background: var(--bg);
    border-radius: 10px;
    padding: 16px 20px;
  }}
  .adv-title {{ font-size: 13px; font-weight: 700; color: var(--primary); margin-bottom: 6px; }}
  .adv-desc {{ font-size: 12px; color: #555; line-height: 1.5; }}
  .comp-table {{ width: 100%; border-collapse: collapse; }}
  .comp-table th {{
    background: var(--primary);
    color: white;
    padding: 10px 16px;
    text-align: left;
    font-size: 12px;
    font-weight: 600;
  }}
  .comp-table th:first-child {{ border-radius: 8px 0 0 0; }}
  .comp-table th:last-child {{ border-radius: 0 8px 0 0; }}
  .comp-table td {{ padding: 10px 16px; font-size: 13px; border-bottom: 1px solid #eee; }}
  .feature-cell {{ font-weight: 600; color: #555; }}
  .our-cell {{ color: var(--primary); font-weight: 500; }}
  .comp-cell {{ color: #888; }}
  .comp-table tr:hover td {{ background: #f8fffe; }}

  /* ── 비주얼 콘셉트 ── */
  .palette-row {{ display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }}
  .swatch {{
    text-align: center;
    width: 80px;
  }}
  .swatch-color {{
    width: 80px; height: 60px;
    border-radius: 8px;
    margin-bottom: 6px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }}
  .swatch-label {{ font-size: 11px; color: #555; font-weight: 600; }}
  .swatch-hex {{ font-size: 10px; color: #999; }}
  .mood-tags {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }}
  .mood-tag {{
    background: var(--accent);
    color: var(--primary);
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
  }}
  .prompt-box {{
    background: #1e1e1e;
    color: #a8d8a8;
    font-family: 'Monaco', 'Consolas', monospace;
    font-size: 12px;
    padding: 16px 20px;
    border-radius: 8px;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-all;
  }}
  .prompt-label {{
    font-size: 11px;
    color: #888;
    margin-bottom: 6px;
    font-weight: 600;
  }}

  /* ── 트렌드 분석 ── */
  .trend-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  .trend-card {{
    background: var(--bg);
    border-radius: 10px;
    padding: 18px 22px;
  }}
  .trend-card .tc-label {{
    font-size: 11px;
    font-weight: 700;
    color: var(--primary);
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 8px;
  }}
  .trend-card p {{ font-size: 13px; color: #444; line-height: 1.6; }}
  .why-trending {{
    background: linear-gradient(to right, var(--bg), white);
    border-radius: 10px;
    padding: 18px 22px;
    font-size: 14px;
    color: #444;
    line-height: 1.7;
    border: 1px solid #e8f4ed;
    margin-bottom: 20px;
  }}

  /* ── 전성분 ── */
  .ingredients-raw {{
    background: #f8f9fa;
    border-radius: 8px;
    padding: 16px 20px;
    font-size: 12px;
    color: #666;
    line-height: 1.7;
    font-family: 'Monaco', 'Consolas', monospace;
    border: 1px solid #eee;
  }}

  /* ── 푸터 ── */
  .footer {{
    background: var(--primary);
    color: rgba(255,255,255,0.7);
    text-align: center;
    padding: 20px;
    font-size: 12px;
  }}

  @media print {{
    body {{ background: white; }}
    .page {{ max-width: 100%; }}
  }}
</style>
</head>
<body>
<div class="page">

  <!-- 배너 -->
  <div class="banner">
    <div class="banner-badge">AI 상품페이지 기획안</div>
    <h1>{cc.get('headline', pa.get('product_type', '상품'))}</h1>
    <div class="sub">{cc.get('sub_headline', '')}</div>
    <div style="display:flex;gap:20px;flex-wrap:wrap;">
      <span style="background:rgba(255,255,255,0.2);padding:6px 16px;border-radius:20px;font-size:13px;">
        {pa.get('product_type', '화장품')}
      </span>
      <span style="background:rgba(255,255,255,0.2);padding:6px 16px;border-radius:20px;font-size:13px;">
        타겟: {pa.get('skin_type_target', '')}
      </span>
    </div>
    <div class="banner-meta">생성일: {now} &nbsp;|&nbsp; 모델: {MODEL} &nbsp;|&nbsp; Powered by AI 상품기획자</div>
  </div>

  <!-- 고객 카피 -->
  <div class="section">
    <div class="section-title">고객 언어 카피</div>
    <div class="copy-headline">{cc.get('headline', '')}</div>
    <div class="copy-sub">{cc.get('sub_headline', '')}</div>
    <div class="copy-description">{cc.get('description', '')}</div>
    <div class="copy-tip">💡 {cc.get('usage_tip', '')}</div>
  </div>

  <!-- 성분 분석 -->
  <div class="section">
    <div class="section-title">성분 분석</div>
    <div class="ingredients-grid">{ki_cards}</div>
    <div class="efficacy-summary">{pa.get('efficacy_summary', '')}</div>
  </div>

  <!-- 판매 포인트 3개 -->
  <div class="section">
    <div class="section-title">판매 포인트 3</div>
    {sp_cards}
  </div>

  <!-- 경쟁사 차이점 -->
  <div class="section">
    <div class="section-title">경쟁사 차이점</div>
    <div class="usp-box">
      <div class="usp-label">핵심 USP</div>
      {ca.get('usp', '')}
    </div>
    <div style="font-size:13px;color:#555;margin-bottom:16px;line-height:1.6;">
      {ca.get('market_positioning', '')}
    </div>
    <div class="advantages-grid">{adv_items}</div>
    <table class="comp-table">
      <thead>
        <tr>
          <th>비교 항목</th>
          <th>우리 상품</th>
          <th>일반 경쟁사</th>
        </tr>
      </thead>
      <tbody>{comp_rows}</tbody>
    </table>
  </div>

  <!-- 비주얼 콘셉트 -->
  <div class="section">
    <div class="section-title">비주얼 콘셉트</div>
    <div style="font-size:14px;color:#444;margin-bottom:20px;line-height:1.6;">
      {vc.get('banner_concept', '')}
    </div>
    <div style="font-size:12px;color:#888;font-weight:600;margin-bottom:10px;">색상 팔레트</div>
    <div class="palette-row">{color_swatches}</div>
    <div class="mood-tags">{mood_tags}</div>
    <div style="font-size:13px;color:#444;margin-bottom:16px;line-height:1.6;">
      <strong>이미지 방향:</strong> {vc.get('image_direction', '')}
    </div>
    <div class="prompt-label">Midjourney / DALL-E 프롬프트</div>
    <div class="prompt-box">{vc.get('midjourney_prompt', '')}</div>
  </div>

  <!-- 트렌드 분석 -->
  <div class="section">
    <div class="section-title">트렌드 분석</div>
    <div class="why-trending">{ta.get('why_trending', '')}</div>
    <div class="trend-grid">
      <div class="trend-card">
        <div class="tc-label">타겟 소비자</div>
        <p>{ta.get('target_consumer', '')}</p>
      </div>
      <div class="trend-card">
        <div class="tc-label">구매 트리거</div>
        <p>{ta.get('purchase_trigger', '')}</p>
      </div>
      <div class="trend-card" style="grid-column:span 2;">
        <div class="tc-label">시장 타이밍</div>
        <p>{ta.get('market_timing', '')}</p>
      </div>
    </div>
  </div>

  <!-- 원본 전성분 -->
  <div class="section">
    <div class="section-title">입력 전성분</div>
    <div class="ingredients-raw">{ingredients}</div>
    {"<div style='margin-top:12px;font-size:12px;color:#999;'>상품 정보: " + product_info + "</div>" if product_info else ""}
  </div>

  <div class="footer">
    AI 상품페이지 기획자 &nbsp;|&nbsp; Generated {now}
  </div>

</div>
</body>
</html>"""

    return html


def main():
    print("=" * 60)
    print("  AI 상품페이지 기획자")
    print("  화장품 전성분 -> 상품페이지 기획안 자동 생성")
    print("=" * 60)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n오류: ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
        print("  .env.example 파일을 참고하여 API 키를 설정하세요.\n")
        sys.exit(1)

    print("\n[1/3] 전성분을 입력하세요.")
    print("      입력 완료 후 빈 줄 + Enter 를 누르세요:")
    ingredients_lines = []
    while True:
        line = input()
        if line == "":
            break
        ingredients_lines.append(line)
    ingredients = "\n".join(ingredients_lines)

    if not ingredients.strip():
        print("오류: 전성분을 입력해야 합니다.")
        sys.exit(1)

    print("\n[2/3] 상품 정보 입력 (선택, Enter 건너뛰기)")
    print("      예: 수분 세럼, 3만원대, 민감성 피부용")
    product_info = input().strip()

    print("\n[3/3] 경쟁사 정보 입력 (선택, Enter 건너뛰기)")
    print("      예: A브랜드 히알루론산 세럼, B브랜드 EGF 앰플")
    competitor_info = input().strip()

    # 분석 실행
    analysis = analyze_product(ingredients, product_info, competitor_info)

    if "raw_output" in analysis:
        print("분석 결과 (원본):\n")
        print(analysis["raw_output"])
        return

    # HTML 보고서 생성
    html = generate_html_report(analysis, ingredients, product_info)

    # 저장
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"product_plan_{timestamp}.html"
    output_file.write_text(html, encoding="utf-8")

    print(f"보고서 저장됨: {output_file}")

    # 브라우저에서 열기
    webbrowser.open(output_file.as_uri())
    print("브라우저에서 보고서가 열렸습니다!")


if __name__ == "__main__":
    main()
