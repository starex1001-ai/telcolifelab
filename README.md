# 통신생활랩 · GitHub 업로드용 사이트

통신·구독·인터넷 분야의 정적 블로그입니다. 공개 주소는 `https://telcolifelab.webnote-lab.workers.dev`로 설정되어 있습니다. 실제 Worker 생성과 이 주소의 배포 여부는 별도로 확인해야 합니다. 테크픽랩 저장소를 덮어쓰지 말고 통신생활랩용 저장소에 올리세요.

## 가장 먼저 할 일

1. ZIP을 풀고 모든 내용을 GitHub의 통신생활랩 저장소 최상위에 업로드합니다. `dist`, `content`, `public`, `build.py`, `site.json`, `wrangler.jsonc`가 최상위에 있어야 합니다.
2. Cloudflare에서 해당 저장소를 `telcolifelab` Worker에 연결합니다.
3. 빌드 명령은 `python3 build.py`, 배포 명령은 `npx wrangler deploy`로 지정합니다. 루트 디렉터리는 저장소 최상위입니다. Cloudflare 빌드 환경에서 Python 3.10 이상이 필요합니다.
4. 빌드 환경에서 Python을 제공하지 않을 경우 로컬/중앙 Python 실행 환경에서 먼저 `python build.py`를 실행하고 생성된 `dist`까지 커밋하세요. Cloudflare 빌드 명령을 비우고 배포 명령 `npx wrangler deploy`를 사용합니다. 이 저장소에는 최초 생성된 dist가 이미 포함되어 있습니다.
5. 배포 후 홈, 카테고리, 글, 복사 버튼, sitemap.xml, robots.txt, 존재하지 않는 URL의 404 응답을 확인합니다.

이 패키지는 GitHub용 전체 저장소입니다. Cloudflare 정적 파일 드래그 업로드에는 저장소 전체가 아니라 `dist` 폴더만 사용하세요.

## 구조와 자동화 규약

```
site.json                 사이트별 이름·주소·메일·카테고리
content/posts.json        게시글 원본 데이터
build.py                  Python 표준 라이브러리만 사용하는 생성기
public/                   복사되는 공통 자산·인증 파일
  assets/style.css        사이트별 디자인
  assets/site.js          확인 메모 복사 기능
  assets/social.png       공유 미리보기 이미지
  favicon.svg
  _headers
dist/                     배포 결과: 자동 생성 후 Git에 커밋
  index.html
  posts/<slug>/index.html
  category/<slug>/index.html
  about/index.html
  contact/index.html
  privacy/index.html
  assets/
  sitemap.xml
  robots.txt
  _headers
  404.html
  favicon.svg
wrangler.jsonc            Worker 이름·정적 자산 경로·404 설정
```

HTML을 찾아 바꾸는 방식 대신 JSON 원본을 수정하고 전체를 재생성합니다. 글 추가 시 홈 최신 12편, 카테고리 목록, 관련 글, 사이트맵이 함께 갱신됩니다. 홈 목록은 날짜와 ID 역순으로 정렬됩니다. 전체 글은 카테고리 페이지에서 접근할 수 있습니다.

`python build.py --site <사이트폴더>`로 다른 사이트 폴더를 지정할 수 있습니다. 동일 데이터 규약과 public 구조를 사용하는 사이트에는 이 생성기 하나를 순차 적용할 수 있습니다. 향후 서로 다른 레이아웃을 추가할 때는 렌더링 부분을 템플릿으로 분리하고 데이터 규약을 유지하세요. 기존 테크픽랩은 아직 이 JSON 규약으로 변환되지 않았습니다.

게시글 필드: `id`, `slug`, `category`, `status`, `title`, `description`, `date`, `updated`, `minutes`, `label`, `intro`, `sections`. 각 section은 `heading`, `paragraphs`, 선택적인 `example`을 가집니다. 모든 콘텐츠 문자열은 HTML 이스케이프됩니다. `status`는 `draft` 또는 `published`입니다. draft와 미래 날짜 글은 생성하지 않습니다. 날짜가 도래한 예약 글은 다시 빌드해야 공개됩니다. 생성기에 예약 실행 기능 자체는 없습니다.

slug는 영문 소문자·숫자·하이픈이며 사이트 안에서 고유해야 합니다. 같은 글의 slug는 유지하세요. 날짜는 YYYY-MM-DD입니다. 중복 slug·잘못된 카테고리·날짜는 빌드를 실패시킵니다. 파일 생성 전 원본 데이터의 유효성을 검사합니다.

## 향후 Google Sheets → Python → GitHub → Cloudflare

1. 시트에서 사이트 ID, 주제, 자료, 상태, 예약일을 관리합니다.
2. 중앙 Python 작업이 승인된 행만 가져와 사이트별 posts.json에 반영합니다. 중복 방지는 안정적인 id를 기준으로 구현합니다.
3. 이 생성기를 실행하고 링크·내용 검수를 수행합니다.
4. 성공한 사이트의 원본과 dist를 GitHub에 커밋합니다.
5. 연결된 Cloudflare가 배포합니다.

Sheets 연결, AI API, 예약 실행, 비용 제한, GitHub 자동 커밋은 이번 사이트 템플릿에 구현되어 있지 않습니다. 인증키를 사이트나 저장소에 넣지 말고 후속 자동화 실행 환경의 비밀 저장소를 사용하세요. 하루 100편 운영 전에 실패 재시도·중복 방지·발행 보류·사이트별 비용 제한을 추가해야 합니다.

## SEO와 운영

canonical, meta description, OG, 공유 이미지, JSON-LD WebPage/BlogPosting/BreadcrumbList, 내부 링크, sitemap, robots, 반응형 레이아웃을 포함합니다. 정적 HTML이므로 JavaScript 없이 글과 메뉴를 읽을 수 있습니다. 복사 버튼만 JavaScript를 사용합니다.

404는 사이트맵에서 제외하고 Cloudflare에서 실제 404 상태로 처리하도록 설정했습니다. 색인 차단 문구는 넣지 않았습니다. 정책 페이지는 현재 기능을 설명한 초기 안내이며 광고·분석·정보 수집을 추가하면 실제 운영에 맞게 바꾸세요. 애드센스 승인, Search Console 인증과 광고 코드는 포함하지 않았습니다. 임의의 게시자 ID나 ads.txt는 넣지 않았습니다.

Google 인증 HTML을 받으면 `public/` 최상위에 넣고 다시 빌드하세요. `dist`에만 넣으면 다음 빌드에서 사라집니다. 테크픽랩 인증 파일은 통신생활랩에 재사용하지 않았습니다.

## 디자인 및 변경 사항

테크픽랩의 3열 최신글 카드와 짙은 네이비 히어로를 복제하지 않았습니다. 청록색 안내 패널, 세로 주제 탐색, 3열 가이드 카드, 하단 시작 가이드, 데스크톱 본문 옆 고정 목차로 구성했습니다. 모바일에서는 단일 열로 전환합니다.

샘플 글 3편은 통신 청구서·구독 갱신 관리·와이파이 상황 점검을 다루는 일반 가이드입니다. 특정 제품의 가상 사용 후기나 검증되지 않은 성능 수치는 포함하지 않았습니다. 글 안의 확인 메모를 복사할 수 있고 실패 시 수동 복사 안내가 나옵니다.

현재 결과물은 로컬에서 제작·검수한 템플릿이며 GitHub 업로드나 실제 Cloudflare 배포는 수행하지 않았습니다.
