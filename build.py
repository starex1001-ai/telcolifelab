"""Dependency-free static blog generator. Python 3.10+."""
import argparse, json, re, shutil
from pathlib import Path
from datetime import date
from content_support import render_body, validate_posts, today
from html import escape
from xml.etree import ElementTree as ET

def build(root):
    root=Path(root).resolve()
    config=json.loads((root/'site.json').read_text(encoding='utf-8'))
    posts=json.loads((root/'content/posts.json').read_text(encoding='utf-8'))
    validate_posts(posts, config)
    base=config['url'].rstrip('/')
    if not re.fullmatch(r'https://[a-z0-9.-]+',base): raise ValueError('Invalid site URL')
    categories={c['slug']:c for c in config['categories']}
    seen=set()
    for p in posts:
        if not re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*',p['slug']): raise ValueError('Invalid slug')
        if p['slug'] in seen: raise ValueError('Duplicate slug: '+p['slug'])
        seen.add(p['slug'])
        if p['category'] not in categories: raise ValueError('Unknown category')
        if p['status'] not in ['draft','published']: raise ValueError('Invalid status')
        for field in ['date','updated']: date.fromisoformat(p[field])
        if p['updated']<p['date']: raise ValueError('Update date precedes publication')
    posts=sorted([p for p in posts if p['status']=='published' and p['date']<=today().isoformat()],key=lambda p:(p['date'],p['id']),reverse=True)
    out=root/'dist'
    # Only this generator-owned output directory is replaced; uploaded verification files belong in public/.
    if out.is_symlink(): raise ValueError("dist must not be a symlink")
    if out.exists(): shutil.rmtree(out)
    out.mkdir()
    shutil.copytree(root/'public',out,dirs_exist_ok=True)
    urls=[]
    e=escape
    def write(file,text):
        f=out/file; f.parent.mkdir(parents=True,exist_ok=True); f.write_text(text,encoding='utf-8')
    def listing(p):
        return f'<article class="entry" data-post-id="{e(p["id"])}"><div class="entry-meta"><span>{e(categories[p["category"]]["name"])}</span><span>{p["minutes"]}분 읽기</span></div><h3><a href="/posts/{p["slug"]}/">{e(p["title"])}</a></h3><p>{e(p["description"])}</p><div class="entry-bottom"><span>{e(p["label"])}</span><a href="/posts/{p["slug"]}/" aria-label="{e(p["title"])} 읽기">읽기 ↗</a></div></article>'
    nav=''.join(f'<a href="/category/{c["slug"]}/">{e(c["name"])}</a>' for c in categories.values())
    def page(route,title,description,body,post=None):
        url=base+route
        if route!='/404.html': urls.append((url,post['updated'] if post else None))
        schema={'@context':'https://schema.org','@type':'WebPage','name':title,'url':url,'inLanguage':'ko-KR'}
        if post:
            schema={'@context':'https://schema.org','@type':'BlogPosting','headline':title,'description':description,'mainEntityOfPage':url,'datePublished':post['date'],'dateModified':post['updated'],'inLanguage':'ko-KR','author':{'@type':'Organization','name':config['name'],'url':base+'/about/'},'publisher':{'@type':'Organization','name':config['name'],'url':base}}
        schemas=[schema]
        if post:
            schemas.append({'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'홈','item':base+'/'},{'@type':'ListItem','position':2,'name':categories[post['category']]['name'],'item':base+'/category/'+post['category']+'/'},{'@type':'ListItem','position':3,'name':title,'item':url}]})
        data=json.dumps(schemas,ensure_ascii=False).replace('<','\\u003c')
        head=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} | {e(config['name'])}</title><meta name="description" content="{e(description)}"><meta name="robots" content="index,follow,max-image-preview:large"><link rel="canonical" href="{url}"><meta property="og:type" content="{'article' if post else 'website'}"><meta property="og:locale" content="ko_KR"><meta property="og:site_name" content="{e(config['name'])}"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(description)}"><meta property="og:url" content="{url}"><meta property="og:image" content="{base}/assets/social.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="TELCO LIFE LAB — Telecom, subscriptions and internet guides"><meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#087c86"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/style.css"><script type="application/ld+json">{data}</script></head>'''
        html=head+f'''<body><a class="skip" href="#main">본문으로 건너뛰기</a><header><div class="header-inner"><a class="brand" href="/"><span class="brand-symbol" aria-hidden="true">TL</span><span>{e(config['brand'])}<small>{e(config['name'])}</small></span></a><nav aria-label="주 메뉴">{nav}<a href="/about/">생활랩 소개</a></nav></div></header><main id="main">{body}</main><footer><div class="footer-inner"><div><strong>{e(config['brand'])}</strong><p>매일의 연결을 더 잘 이해하는 곳.</p></div><nav aria-label="하단 메뉴"><a href="/about/">소개</a><a href="/contact/">문의</a><a href="/privacy/">개인정보처리방침</a></nav><small>© {date.today().year} {e(config['name'])}</small></div></footer><script src="/assets/site.js" defer></script></body></html>'''
        file='index.html' if route=='/' else route.lstrip('/')+('index.html' if route.endswith('/') else '')
        write(file,html)
    counts={slug:sum(p['category']==slug for p in posts) for slug in categories}
    tabs=''.join(f'<a class="topic" href="/category/{c["slug"]}/"><span class="topic-no">0{i+1}</span><div><h2>{e(c["name"])}</h2><p>{e(c["description"])}</p></div><span class="topic-count">{counts[c["slug"]]}편 ↗</span></a>' for i,c in enumerate(categories.values()))
    feature=next((p for p in posts if p['slug']=='mobile-bill-checklist'),posts[0] if posts else None)
    featured=f'<a class="feature" href="/posts/{feature["slug"]}/"><span class="kicker">처음 시작한다면</span><h2>{e(feature["title"])}</h2><span class="feature-link">청구 항목 살펴보기 ↗</span></a>' if feature else ''
    page('/','통신 생활, 조건부터 차근차근',config['description'],f'''<section class="intro"><div class="intro-label">THE CONNECTED LIFE JOURNAL <span>MOBILE / SUBSCRIPTION / INTERNET</span></div><h1>연결은 편하게.<br><span>선택은 꼼꼼하게.</span></h1><p>휴대폰 청구서부터 구독 갱신일, 집 안 와이파이까지.<br>복잡한 조건을 하나씩 확인하는 통신 생활 가이드.</p></section><section class="topics" aria-label="주제별 가이드">{tabs}</section><section class="reading"><div class="feed"><div class="section-title"><h2>최근 발행한 가이드</h2><span>THE LATEST</span></div><div data-feed="latest">{''.join(listing(p) for p in posts[:12]) or '<p>발행된 글이 없습니다.</p>'}</div></div><aside>{featured}<div class="principles"><span class="kicker">OUR APPROACH</span><h2>요금보다 먼저 조건을,<br>변경 전에는 내역을.</h2><p>계약과 청구 내역을 직접 확인할 수 있도록, 필요한 질문과 정리 순서를 안내합니다.</p><a href="/about/">작성 원칙 읽기 ↗</a></div></aside></section>''')
    for slug,c in categories.items():
        page('/category/'+slug+'/',c['name'],c['description'],f'<section class="page-heading"><span class="kicker">TOPIC / {counts[slug]} ARTICLES</span><h1>{e(c["name"])}</h1><p>{e(c["description"])}</p></section><div class="category-feed" data-feed="category">'+''.join(listing(p) for p in posts if p['category']==slug)+'</div>')
    for p in posts:
        toc=''.join(f'<li><a href="#section-{i}">{e(s["heading"])}</a></li>' for i,s in enumerate(p['sections']))
        sections=''
        for i,s in enumerate(p['sections']):
            sections+=f'<section id="section-{i}"><h2>{e(s["heading"])}</h2>'+''.join(f'<p>{e(t)}</p>' for t in s['paragraphs'])
            if s.get('example'): sections+=f'<div class="example"><div><strong>확인 메모</strong><button type="button" class="copy" aria-label="확인 메모 복사">복사</button></div><pre>{e(s["example"])}</pre><span class="copy-status" role="status"></span></div>'
            sections+='</section>'
        if 'body_html' in p:
            toc, sections = render_body(p)
        related=''.join(f'<a href="/posts/{q["slug"]}/">{e(q["title"])} ↗</a>' for q in posts if q['id']!=p['id'])
        body=f'''<div class="article-layout"><article class="prose"><div class="breadcrumbs"><a href="/">홈</a> / <a href="/category/{p['category']}/">{e(categories[p['category']]['name'])}</a></div><span class="kicker">{e(p['label'])}</span><h1>{e(p['title'])}</h1><p class="lead">{e(p['description'])}</p><div class="byline">{e(config['name'])} · <time datetime="{p['date']}">{p['date']}</time> · {p['minutes']}분 읽기</div><p>{e(p['intro'])}</p>{sections}<div class="article-note">이 글은 일반적인 확인 절차를 정리한 가이드입니다. 실제 요금, 계약, 취소 조건은 이용 중인 서비스의 공식 안내와 본인 계약을 확인하세요.</div><section class="related"><h2>이어 읽기</h2>{related}</section></article><aside class="toc"><strong>이 글의 순서</strong><ol>{toc}</ol><a class="backtop" href="#main">맨 위로 ↑</a></aside></div>'''
        page('/posts/'+p['slug']+'/',p['title'],p['description'],body,p)
    page('/about/','생활랩 소개','통신생활랩의 주제와 콘텐츠 작성 원칙을 소개합니다.',f'<article class="prose standalone"><span class="kicker">ABOUT TELCO LIFE</span><h1>매일 쓰는 통신,<br>조건부터 이해합니다.</h1><p class="lead">{e(config["name"])}은 통신·구독·인터넷을 다루는 한국어 생활 정보 블로그입니다.</p><h2>우리가 다루는 질문</h2><p>청구서를 어떻게 읽을지, 구독을 어디서 관리할지, 연결 문제를 어떤 순서로 확인할지 살펴봅니다. 통신사 고객센터나 판매 대리점이 아닌 독립적인 정보 사이트이며, 계약 조건은 이용 중인 서비스의 공식 안내로 확인해야 합니다.</p><h2>작성과 수정 원칙</h2><p>직접 사용한 후기와 일반 가이드를 구분합니다. 확인하지 않은 경험이나 성능 수치를 만들지 않습니다. 가격과 기능 등 변할 수 있는 정보는 공식 자료와 확인 시점을 함께 검토합니다. 할인이나 절감액을 보장하지 않으며, 계약과 사용 환경에 따라 달라지는 조건은 구분해서 설명합니다.</p><h2>광고와 제휴</h2><p>협찬 또는 제휴 관계가 있는 글에는 해당 내용을 표시합니다. 현재 사이트에는 광고나 제휴 링크가 연결되어 있지 않습니다.</p><h2>오류 제보</h2><p>수정이 필요한 글은 <a href="/contact/">문의 페이지</a>로 알려주세요.</p></article>')
    page('/contact/','문의','통신생활랩 문의와 콘텐츠 오류 제보 연락처입니다.',f'<article class="prose standalone"><span class="kicker">CONTACT</span><h1>함께 더 정확하게.</h1><p class="lead">오류 제보, 다뤄주길 바라는 주제, 협업 문의를 보내주세요.</p><a class="email" href="mailto:{e(config["email"])}">{e(config["email"])}</a><h2>문의에 포함할 내용</h2><p>관련 글 주소와 확인이 필요한 부분을 함께 적어주세요. 비밀번호, API 키, 회사 기밀 등 민감한 정보는 보내지 마세요.</p><p>이메일 링크는 기기에 설정된 메일 앱을 엽니다. 메일 앱이 없다면 주소를 복사해 이용 중인 이메일 서비스에서 보내주세요.</p></article>')
    page('/privacy/','개인정보처리방침','사이트 이용과 문의 이메일에 관한 데이터 처리 안내입니다.',f'<article class="prose standalone"><span class="kicker">PRIVACY</span><h1>개인정보처리방침</h1><p>적용일: 2026-09-14</p><h2>사이트 기능</h2><p>현재 회원가입, 댓글, 문의 입력 양식은 없습니다. 방문 분석 및 광고 스크립트, 쿠키나 로컬 저장소에 방문자 정보를 기록하는 기능은 포함하지 않았습니다. 확인 메모 복사는 사용자가 버튼을 누를 때 해당 문장을 기기의 클립보드에 복사하며, 서버로 보내지 않습니다.</p><h2>호스팅과 접속 정보</h2><p>Cloudflare를 통한 페이지 전달과 보안 과정에서 IP 주소와 요청 정보 등이 처리될 수 있습니다. 제공자의 처리 내용은 <a href="https://www.cloudflare.com/privacypolicy/">Cloudflare 개인정보 안내</a>를 참고하세요.</p><h2>이메일 문의</h2><p>운영자는 회신 주소와 문의 내용을 문의 응대에 필요한 범위에서 사용합니다. 목적이 끝나면 불필요한 정보를 삭제합니다. 이메일 서비스의 처리 조건도 함께 적용될 수 있습니다.</p><h2>변경과 연락처</h2><p>광고나 분석 도구 도입 등 실제 처리 방식이 바뀌면 이 안내와 적용일을 갱신합니다. 문의 정보 삭제 및 처리 관련 요청은 <a href="mailto:{e(config["email"])}">{e(config["email"])}</a>로 보내주세요.</p></article>')
    page('/404.html','페이지를 찾을 수 없습니다','주소를 확인하거나 통신생활랩 홈에서 가이드를 찾아보세요.','<section class="page-heading error"><span class="kicker">404 / NOT FOUND</span><h1>잠깐, 경로를<br>다시 확인해주세요.</h1><p>페이지가 이동했거나 주소가 잘못되었을 수 있습니다.</p><a class="button" href="/">가이드 홈으로</a></section>')
    write('robots.txt',f'User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n')
    ET.register_namespace('','http://www.sitemaps.org/schemas/sitemap/0.9')
    tree=ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')
    for url,updated in urls:
        item=ET.SubElement(tree,'url'); ET.SubElement(item,'loc').text=url
        if updated: ET.SubElement(item,'lastmod').text=updated
    write('sitemap.xml','<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(tree,encoding='unicode'))
    for f in out.rglob('*.html'):
        if f.name.startswith('google'): continue
        html=f.read_text(encoding='utf-8')
        assert 'noindex' not in html
        for target in re.findall(r'(?:href|src)="(/[^"#]*)',html):
            dest=out/target.lstrip('/')
            if target.endswith('/'): dest=dest/'index.html'
            assert dest.is_file(),f'{f}: missing {target}'
    print(f'Built {len(urls)} pages + 404, {len(posts)} published posts: {out}')

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--site',default=str(Path(__file__).parent)); args=parser.parse_args(); build(args.site)

