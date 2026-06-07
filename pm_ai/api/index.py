"""
AI 상품페이지 기획자 — Vercel Web App
화장품 전성분 → 고객 언어 설명 + 판매 포인트 + 경쟁사 분석 + 비주얼 기획
"""
from flask import Flask, request
import anthropic
import os
import json
from datetime import datetime

app = Flask(__name__)
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


def get_analysis_prompt(ingredients, product_info, competitor_info):
    return """다음 화장품 정보를 분석하여 완성된 상품 페이지 기획안을 JSON 형식으로 작성해주세요.

## 입력 정보

**전성분:**
{ingredients}

**상품 정보 (유형/가격대/브랜드 등):**
{product_info}

**경쟁사/경쟁 상품 정보:**
{competitor_info}

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
}}""".format(
        ingredients=ingredients,
        product_info=product_info if product_info else "입력 없음 - 전성분으로 추정하세요",
        competitor_info=competitor_info if competitor_info else "경쟁사 정보 없음 - 일반 시장 기준으로 분석",
    )


def analyze_product(ingredients, product_info, competitor_info):
    client = anthropic.Anthropic()
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

    json_str = full_response.strip()
    if "```json" in json_str:
        start = json_str.find("```json") + 7
        end = json_str.find("```", start)
        json_str = json_str[start:end].strip()
    elif "```" in json_str:
        start = json_str.find("```") + 3
        end = json_str.find("```", start)
        json_str = json_str[start:end].strip()

    return json.loads(json_str)


def generate_html_report(analysis, ingredients, product_info):
    pa = analysis.get("product_analysis", {})
    cc = analysis.get("customer_copy", {})
    sp = analysis.get("selling_points", [])
    ca = analysis.get("competitor_analysis", {})
    vc = analysis.get("visual_concept", {})
    ta = analysis.get("trend_analysis", {})

    palette = vc.get("color_palette", {})
    primary    = palette.get("primary",    "#2d6a4f")
    secondary  = palette.get("secondary",  "#40916c")
    accent     = palette.get("accent",     "#b7e4c7")
    bg_color   = palette.get("background", "#f8fffe")
    text_color = palette.get("text",       "#1b4332")

    sp_cards = ""
    for point in sp:
        sp_cards += """
        <div class="sp-card">
          <div class="sp-number">{n}</div>
          <div class="sp-content">
            <div class="sp-pain"><span class="label label-pain">페인포인트</span><p>{pain}</p></div>
            <div class="sp-arrow">→</div>
            <div class="sp-solution"><span class="label label-sol">솔루션</span><p>{sol}</p></div>
          </div>
          <div class="sp-message">"{msg}"</div>
          <div class="sp-evidence">근거: {ev}</div>
        </div>""".format(
            n=point.get("number", ""),
            pain=point.get("pain_point", ""),
            sol=point.get("solution", ""),
            msg=point.get("message", ""),
            ev=point.get("evidence", ""),
        )

    ki_cards = ""
    for ing in pa.get("key_ingredients", []):
        ki_cards += """
        <div class="ingredient-card">
          <div class="ing-name">{name}</div>
          <div class="ing-rating">{rating}</div>
          <div class="ing-benefit">{benefit}</div>
        </div>""".format(
            name=ing.get("name", ""),
            rating=ing.get("star_rating", ""),
            benefit=ing.get("benefit", ""),
        )

    comp_rows = ""
    for row in ca.get("comparison_table", []):
        comp_rows += """
        <tr>
          <td class="feature-cell">{f}</td>
          <td class="our-cell">{o}</td>
          <td class="comp-cell">{c}</td>
        </tr>""".format(
            f=row.get("feature", ""),
            o=row.get("our_product", ""),
            c=row.get("competitor", ""),
        )

    adv_items = ""
    for adv in ca.get("our_advantages", []):
        adv_items += """
        <div class="advantage-item">
          <div class="adv-title">{t}</div>
          <div class="adv-desc">{d}</div>
        </div>""".format(t=adv.get("point", ""), d=adv.get("description", ""))

    color_labels = [("primary","메인"), ("secondary","서브"), ("accent","포인트"), ("background","배경"), ("text","텍스트")]
    color_swatches = ""
    for key, label in color_labels:
        hex_val = palette.get(key, "#cccccc")
        color_swatches += """
        <div class="swatch">
          <div class="swatch-color" style="background:{hex}"></div>
          <div class="swatch-label">{label}</div>
          <div class="swatch-hex">{hex}</div>
        </div>""".format(hex=hex_val, label=label)

    mood_tags = "".join(
        '<span class="mood-tag">{}</span>'.format(kw)
        for kw in vc.get("mood_keywords", [])
    )

    now = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")

    return """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>기획안 — {product_type}</title>
<style>
  :root {{
    --primary: {primary};
    --secondary: {secondary};
    --accent: {accent};
    --bg: {bg};
    --text: {text};
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Apple SD Gothic Neo','Noto Sans KR',sans-serif; background:#f0f0f0; color:#333; font-size:14px; line-height:1.6; }}
  .page {{ max-width:960px; margin:0 auto; background:white; }}

  .back-btn {{
    display: block;
    padding: 12px 48px;
    background: rgba(255,255,255,0.15);
    color: white;
    text-decoration: none;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.5px;
    transition: background 0.2s;
  }}
  .back-btn:hover {{ background: rgba(255,255,255,0.25); }}

  .banner {{
    background: linear-gradient(135deg, {primary} 0%, {secondary} 60%, {accent} 100%);
    padding: 48px 48px 40px;
    color: white;
    position: relative;
    overflow: hidden;
  }}
  .banner::before {{ content:''; position:absolute; top:-40px; right:-40px; width:200px; height:200px; border-radius:50%; background:rgba(255,255,255,0.08); }}
  .banner h1 {{ font-size:38px; font-weight:900; margin-bottom:10px; letter-spacing:-0.5px; }}
  .banner .sub {{ font-size:16px; opacity:.88; margin-bottom:20px; }}
  .banner-tags {{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:20px; }}
  .banner-tag {{ background:rgba(255,255,255,0.2); padding:5px 14px; border-radius:20px; font-size:12px; }}
  .banner-meta {{ font-size:11px; opacity:.6; border-top:1px solid rgba(255,255,255,0.25); padding-top:14px; }}

  .section {{ padding:36px 48px; border-bottom:1px solid #eef2f5; }}
  .section-title {{
    font-size:10px; font-weight:800; letter-spacing:2.5px; text-transform:uppercase;
    color:var(--primary); margin-bottom:24px; display:flex; align-items:center; gap:12px;
  }}
  .section-title::after {{ content:''; flex:1; height:1px; background:linear-gradient(to right, var(--accent), transparent); }}

  .copy-headline {{ font-size:32px; font-weight:900; color:var(--primary); margin-bottom:8px; letter-spacing:-0.5px; }}
  .copy-sub {{ font-size:16px; color:#555; margin-bottom:20px; font-weight:500; }}
  .copy-description {{ font-size:14px; line-height:1.9; color:#3a4a54; background:var(--bg); padding:20px 24px; border-radius:10px; margin-bottom:14px; border:1px solid #ddd; }}
  .copy-tip {{ font-size:13px; color:var(--secondary); padding:10px 16px; border-left:3px solid var(--accent); background:#fafffe; border-radius:0 6px 6px 0; }}

  .ingredients-grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(185px,1fr)); gap:14px; margin-bottom:20px; }}
  .ingredient-card {{ background:white; border:1px solid #ddd; border-radius:10px; padding:16px; text-align:center; }}
  .ing-name {{ font-size:12px; font-weight:700; color:var(--primary); margin-bottom:4px; }}
  .ing-rating {{ font-size:13px; color:#f4a261; margin-bottom:6px; }}
  .ing-benefit {{ font-size:12px; color:#555; line-height:1.5; }}
  .efficacy-summary {{ background:var(--bg); border-radius:10px; padding:18px 22px; font-size:14px; color:#3a4a54; line-height:1.8; border:1px solid #ddd; }}

  .sp-card {{ background:white; border-radius:12px; border:1px solid #ddd; padding:24px; margin-bottom:16px; position:relative; overflow:hidden; }}
  .sp-card::before {{ content:''; position:absolute; top:0; left:0; width:4px; height:100%; background:linear-gradient(to bottom, var(--primary), var(--secondary)); }}
  .sp-number {{ font-size:10px; font-weight:800; color:white; background:var(--primary); width:22px; height:22px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; margin-bottom:16px; }}
  .sp-content {{ display:grid; grid-template-columns:1fr 36px 1fr; gap:12px; align-items:center; margin-bottom:16px; }}
  .sp-pain {{ background:#fdf5f0; border-radius:8px; padding:12px 14px; border:1px solid #fde8d8; }}
  .sp-solution {{ background:#f0fafd; border-radius:8px; padding:12px 14px; border:1px solid #ddd; }}
  .sp-arrow {{ color:var(--primary); font-size:20px; text-align:center; opacity:.6; }}
  .label {{ font-size:9px; font-weight:800; letter-spacing:1.5px; text-transform:uppercase; display:block; margin-bottom:4px; }}
  .label-pain {{ color:#c97a3a; }}
  .label-sol {{ color:var(--secondary); }}
  .sp-pain p, .sp-solution p {{ font-size:13px; color:#444; line-height:1.6; }}
  .sp-message {{ font-size:17px; font-weight:800; color:var(--primary); text-align:center; padding:12px; background:var(--bg); border-radius:8px; margin-bottom:10px; }}
  .sp-evidence {{ font-size:11px; color:#888; text-align:right; font-style:italic; }}

  .usp-box {{ background:linear-gradient(135deg, var(--primary), var(--secondary)); color:white; border-radius:12px; padding:20px 28px; margin-bottom:22px; text-align:center; }}
  .usp-label {{ font-size:10px; opacity:.75; letter-spacing:2px; margin-bottom:6px; text-transform:uppercase; }}
  .usp-text {{ font-size:15px; font-weight:700; line-height:1.5; }}
  .market-pos {{ font-size:13px; color:#3a4a54; line-height:1.7; margin-bottom:20px; padding:14px 18px; background:var(--bg); border-radius:8px; }}
  .advantages-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:22px; }}
  .advantage-item {{ background:var(--bg); border-radius:10px; padding:16px 18px; border:1px solid #ddd; }}
  .adv-title {{ font-size:13px; font-weight:700; color:var(--primary); margin-bottom:5px; }}
  .adv-desc {{ font-size:12px; color:#555; line-height:1.5; }}
  .comp-table {{ width:100%; border-collapse:collapse; border-radius:10px; overflow:hidden; }}
  .comp-table th {{ background:var(--primary); color:white; padding:11px 16px; text-align:left; font-size:12px; font-weight:600; }}
  .comp-table td {{ padding:10px 16px; font-size:13px; border-bottom:1px solid #eee; }}
  .comp-table tr:last-child td {{ border-bottom:none; }}
  .feature-cell {{ font-weight:600; color:#555; }}
  .our-cell {{ color:var(--primary); font-weight:500; }}
  .comp-cell {{ color:#888; }}

  .palette-row {{ display:flex; gap:12px; margin-bottom:20px; flex-wrap:wrap; }}
  .swatch {{ text-align:center; width:78px; }}
  .swatch-color {{ width:78px; height:58px; border-radius:8px; margin-bottom:6px; box-shadow:0 2px 8px rgba(0,0,0,0.1); }}
  .swatch-label {{ font-size:11px; color:#555; font-weight:600; }}
  .swatch-hex {{ font-size:10px; color:#999; }}
  .mood-tags {{ display:flex; gap:8px; flex-wrap:wrap; margin-bottom:18px; }}
  .mood-tag {{ background:var(--accent); color:var(--primary); padding:5px 14px; border-radius:20px; font-size:12px; font-weight:700; }}
  .concept-text {{ font-size:13px; color:#3a4a54; line-height:1.7; margin-bottom:16px; padding:16px 20px; background:var(--bg); border-radius:8px; border:1px solid #ddd; }}
  .prompt-label {{ font-size:10px; color:#888; margin-bottom:7px; font-weight:700; letter-spacing:1px; text-transform:uppercase; }}
  .prompt-box {{ background:#0d1117; color:#79c0ff; font-family:'Monaco','Consolas',monospace; font-size:12px; padding:16px 20px; border-radius:10px; line-height:1.7; white-space:pre-wrap; word-break:break-word; }}

  .why-box {{ background:var(--bg); border-radius:10px; padding:18px 22px; font-size:14px; color:#3a4a54; line-height:1.8; border:1px solid #ddd; margin-bottom:18px; }}
  .trend-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
  .trend-card {{ background:var(--bg); border-radius:10px; padding:16px 20px; border:1px solid #ddd; }}
  .trend-card.full {{ grid-column:span 2; }}
  .tc-label {{ font-size:10px; font-weight:800; color:var(--primary); letter-spacing:1.5px; text-transform:uppercase; margin-bottom:8px; display:block; }}
  .trend-card p {{ font-size:13px; color:#444; line-height:1.65; }}

  .ing-raw {{ background:#f8f9fa; border-radius:8px; padding:16px 20px; font-size:12px; color:#666; line-height:2.0; font-family:'Monaco','Consolas',monospace; border:1px solid #e4e8ec; word-break:keep-all; }}
  .footer {{ background:var(--primary); color:rgba(255,255,255,0.65); text-align:center; padding:20px; font-size:11px; }}
</style>
</head>
<body>
<div class="page">

  <a href="/" class="back-btn">← 새 상품 분석하기</a>

  <div class="banner">
    <h1>{headline}</h1>
    <div class="sub">{sub_headline}</div>
    <div class="banner-tags">
      <span class="banner-tag">{product_type}</span>
      <span class="banner-tag">타겟: {skin_type}</span>
    </div>
    <div class="banner-meta">생성: {now} &nbsp;|&nbsp; {model}</div>
  </div>

  <div class="section">
    <div class="section-title">고객 언어 카피</div>
    <div class="copy-headline">{headline}</div>
    <div class="copy-sub">{sub_headline}</div>
    <div class="copy-description">{description}</div>
    <div class="copy-tip">💡 {usage_tip}</div>
  </div>

  <div class="section">
    <div class="section-title">성분 분석</div>
    <div class="ingredients-grid">{ki_cards}</div>
    <div class="efficacy-summary">{efficacy_summary}</div>
  </div>

  <div class="section">
    <div class="section-title">판매 포인트 3</div>
    {sp_cards}
  </div>

  <div class="section">
    <div class="section-title">경쟁사 차이점</div>
    <div class="usp-box">
      <div class="usp-label">핵심 USP</div>
      <div class="usp-text">{usp}</div>
    </div>
    <div class="market-pos">{market_pos}</div>
    <div class="advantages-grid">{adv_items}</div>
    <table class="comp-table">
      <thead><tr><th>비교 항목</th><th>우리 상품</th><th>일반 경쟁사</th></tr></thead>
      <tbody>{comp_rows}</tbody>
    </table>
  </div>

  <div class="section">
    <div class="section-title">비주얼 콘셉트</div>
    <div class="concept-text">{banner_concept}</div>
    <div style="font-size:11px;color:#888;font-weight:700;margin-bottom:10px;letter-spacing:1px;text-transform:uppercase;">색상 팔레트</div>
    <div class="palette-row">{color_swatches}</div>
    <div class="mood-tags">{mood_tags}</div>
    <div class="concept-text"><strong>이미지 방향:</strong> {image_direction}</div>
    <div class="prompt-label">Midjourney / DALL-E 프롬프트</div>
    <div class="prompt-box">{midjourney_prompt}</div>
  </div>

  <div class="section">
    <div class="section-title">트렌드 분석</div>
    <div class="why-box">{why_trending}</div>
    <div class="trend-grid">
      <div class="trend-card"><span class="tc-label">타겟 소비자</span><p>{target_consumer}</p></div>
      <div class="trend-card"><span class="tc-label">구매 트리거</span><p>{purchase_trigger}</p></div>
      <div class="trend-card full"><span class="tc-label">시장 타이밍</span><p>{market_timing}</p></div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">입력 전성분</div>
    <div class="ing-raw">{ingredients}</div>
    {product_info_line}
  </div>

  <div class="footer">AI 상품페이지 기획자 &nbsp;|&nbsp; Generated {now}</div>
</div>
</body>
</html>""".format(
        primary=primary, secondary=secondary, accent=accent, bg=bg_color, text=text_color,
        product_type=pa.get("product_type", "화장품"),
        skin_type=pa.get("skin_type_target", ""),
        headline=cc.get("headline", ""),
        sub_headline=cc.get("sub_headline", ""),
        description=cc.get("description", ""),
        usage_tip=cc.get("usage_tip", ""),
        ki_cards=ki_cards,
        efficacy_summary=pa.get("efficacy_summary", ""),
        sp_cards=sp_cards,
        usp=ca.get("usp", ""),
        market_pos=ca.get("market_positioning", ""),
        adv_items=adv_items,
        comp_rows=comp_rows,
        banner_concept=vc.get("banner_concept", ""),
        color_swatches=color_swatches,
        mood_tags=mood_tags,
        image_direction=vc.get("image_direction", ""),
        midjourney_prompt=vc.get("midjourney_prompt", ""),
        why_trending=ta.get("why_trending", ""),
        target_consumer=ta.get("target_consumer", ""),
        purchase_trigger=ta.get("purchase_trigger", ""),
        market_timing=ta.get("market_timing", ""),
        ingredients=ingredients,
        product_info_line='<div style="margin-top:10px;font-size:12px;color:#999;">상품 정보: {}</div>'.format(product_info) if product_info else "",
        now=now,
        model=MODEL,
    )


# ── 홈 화면 HTML ────────────────────────────────────────────────────────────
HOME_HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 상품페이지 기획자</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    min-height: 100vh;
    background: linear-gradient(135deg, #0d2137 0%, #1a4a62 40%, #2A6B8A 75%, #3D9CB5 100%);
    font-family: 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    padding: 48px 16px 80px;
  }
  .header {
    text-align: center;
    color: white;
    margin-bottom: 40px;
  }
  .header-badge {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 20px;
    padding: 5px 16px;
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 18px;
  }
  .header h1 { font-size: 36px; font-weight: 900; letter-spacing: -0.5px; margin-bottom: 10px; }
  .header p { font-size: 16px; opacity: 0.8; line-height: 1.6; }

  .card {
    background: white;
    border-radius: 20px;
    padding: 40px 44px;
    width: 100%;
    max-width: 680px;
    box-shadow: 0 24px 64px rgba(0,0,0,0.2);
  }

  .field { margin-bottom: 24px; }
  .field label {
    display: block;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #2A6B8A;
    margin-bottom: 8px;
  }
  .field .optional {
    font-size: 10px;
    color: #aaa;
    font-weight: 400;
    letter-spacing: 0;
    text-transform: none;
    margin-left: 6px;
  }
  textarea, input[type="text"] {
    width: 100%;
    border: 1.5px solid #e4e8ec;
    border-radius: 10px;
    padding: 14px 16px;
    font-size: 13px;
    font-family: inherit;
    color: #333;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
    resize: vertical;
    background: #fafcff;
  }
  textarea:focus, input[type="text"]:focus {
    border-color: #2A6B8A;
    box-shadow: 0 0 0 3px rgba(42,107,138,0.1);
    background: white;
  }
  textarea.mono { font-family: 'Monaco', 'Consolas', monospace; font-size: 12px; line-height: 1.7; }
  .hint { font-size: 11px; color: #aaa; margin-top: 5px; }

  .submit-btn {
    width: 100%;
    padding: 16px;
    background: linear-gradient(135deg, #2A6B8A, #3D9CB5);
    color: white;
    border: none;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 700;
    cursor: pointer;
    letter-spacing: 0.3px;
    transition: opacity 0.2s, transform 0.1s;
    margin-top: 8px;
  }
  .submit-btn:hover { opacity: 0.92; transform: translateY(-1px); }
  .submit-btn:active { transform: translateY(0); }
  .submit-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

  /* 로딩 오버레이 */
  #loading {
    display: none;
    position: fixed;
    inset: 0;
    background: linear-gradient(135deg, #0d2137 0%, #1a4a62 40%, #2A6B8A 75%, #3D9CB5 100%);
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    color: white;
  }
  .spinner {
    width: 52px; height: 52px;
    border: 4px solid rgba(255,255,255,0.2);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.9s linear infinite;
    margin-bottom: 28px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  #loading h2 { font-size: 22px; font-weight: 700; margin-bottom: 10px; }
  #loading p { font-size: 14px; opacity: 0.7; }
  .dots::after {
    content: '';
    animation: dots 1.5s steps(4, end) infinite;
  }
  @keyframes dots {
    0%   { content: ''; }
    25%  { content: '.'; }
    50%  { content: '..'; }
    75%  { content: '...'; }
  }

  .error-box {
    display: none;
    background: #fff5f5;
    border: 1px solid #ffcdd2;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 20px;
    font-size: 13px;
    color: #c62828;
  }

  .footer-note {
    color: rgba(255,255,255,0.5);
    font-size: 12px;
    margin-top: 28px;
    text-align: center;
  }
</style>
</head>
<body>

<div class="header">
  <div class="header-badge">AI Product Planner</div>
  <h1>AI 상품페이지 기획자</h1>
  <p>전성분을 입력하면 고객 언어 설명, 판매 포인트 3개,<br>경쟁사 차이점, 비주얼 콘셉트까지 자동으로 생성합니다.</p>
</div>

<div class="card">
  <div class="error-box" id="error-box">전성분을 입력해주세요.</div>

  <form id="analyze-form">
    <div class="field">
      <label>전성분 <span style="color:#e53935;margin-left:2px;">*</span></label>
      <textarea name="ingredients" class="mono" rows="8"
        placeholder="예) 정제수, 글리세린, 나이아신아마이드, 히알루론산, 세라마이드엔피, 판테놀, 알란토인..."></textarea>
      <div class="hint">화장품 용기 뒷면 또는 제조사 제공 전성분표를 붙여넣으세요</div>
    </div>

    <div class="field">
      <label>상품 정보 <span class="optional">선택</span></label>
      <input type="text" name="product_info"
        placeholder="예: 수분 세럼, 4만원대, 민감성 피부용">
    </div>

    <div class="field">
      <label>경쟁사 정보 <span class="optional">선택</span></label>
      <textarea name="competitor_info" rows="3"
        placeholder="예: A브랜드 히알루론산 세럼 (2만원대), B브랜드 EGF 앰플 (5만원대)"></textarea>
    </div>

    <button type="submit" class="submit-btn" id="submit-btn">
      AI 기획안 생성하기
    </button>
  </form>
</div>

<div class="footer-note">Powered by Claude claude-opus-4-8 &nbsp;·&nbsp; 분석에 30~60초 소요됩니다</div>

<!-- 로딩 오버레이 -->
<div id="loading">
  <div class="spinner"></div>
  <h2>AI 분석 중<span class="dots"></span></h2>
  <p>전성분을 분석하고 기획안을 작성하고 있습니다</p>
</div>

<script>
document.getElementById('analyze-form').addEventListener('submit', async function(e) {
  e.preventDefault();

  const ingredients = this.ingredients.value.trim();
  const errorBox = document.getElementById('error-box');

  if (!ingredients) {
    errorBox.style.display = 'block';
    this.ingredients.focus();
    return;
  }
  errorBox.style.display = 'none';

  // 로딩 표시
  document.getElementById('loading').style.display = 'flex';
  document.getElementById('submit-btn').disabled = true;

  try {
    const res = await fetch('/analyze', {
      method: 'POST',
      body: new FormData(this)
    });

    const html = await res.text();

    if (!res.ok) {
      throw new Error(html);
    }

    // 보고서로 페이지 교체
    document.open();
    document.write(html);
    document.close();

  } catch (err) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('submit-btn').disabled = false;
    errorBox.textContent = '오류가 발생했습니다: ' + err.message;
    errorBox.style.display = 'block';
  }
});
</script>

</body>
</html>"""


# ── Flask 라우트 ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return HOME_HTML


@app.route("/analyze", methods=["POST"])
def analyze():
    ingredients    = request.form.get("ingredients", "").strip()
    product_info   = request.form.get("product_info", "").strip()
    competitor_info = request.form.get("competitor_info", "").strip()

    if not ingredients:
        return "전성분을 입력해주세요.", 400

    try:
        analysis = analyze_product(ingredients, product_info, competitor_info)
        if "raw_output" in analysis:
            return "<pre style='padding:2rem;white-space:pre-wrap;'>" + analysis["raw_output"] + "</pre>"
        return generate_html_report(analysis, ingredients, product_info)
    except Exception as e:
        return "분석 중 오류가 발생했습니다: " + str(e), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
