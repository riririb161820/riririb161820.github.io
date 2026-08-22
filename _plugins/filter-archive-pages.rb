#!/usr/bin/env ruby
# frozen_string_literal: true
#
# 태그·카테고리 목록 페이지를 검색엔진 색인 대상에서 제외한다.
#
# 배경: jekyll-archives가 태그마다 페이지를 하나씩 만들어서, 사이트맵의
# 대부분이 "글 1개만 걸린 목록 페이지"로 채워진다(실측: 135개 중 92개).
# 신생 사이트는 크롤 예산이 적어서, 이 저가치 URL이 실제 글보다 먼저
# 예산을 잡아먹는다.
#
# 조치: 생성된 개별 태그·카테고리 페이지에
#   1) sitemap: false  → sitemap.xml에서 제외
#   2) <meta name="robots" content="noindex, follow"> → 색인 제외.
#      단 follow라서 크롤러는 링크를 계속 따라가므로 글 발견 경로는 유지된다.
#
# 탭 페이지(/tags/, /categories/)와 글·페이지네이션은 건드리지 않는다.
# 사용자가 보는 태그 탐색 동작에는 아무 변화가 없다.

NOINDEX_META = '<meta name="robots" content="noindex, follow">'

def archive_listing?(page)
  url = page.url.to_s
  return false if url == "/tags/" || url == "/categories/"

  url.start_with?("/tags/", "/categories/")
end

# 생성기(jekyll-archives)가 돈 뒤, 렌더 전에 사이트맵 제외 표시를 붙인다.
Jekyll::Hooks.register :site, :pre_render do |site|
  site.pages.each do |page|
    page.data["sitemap"] = false if archive_listing?(page)
  end
end

# 렌더된 HTML의 </head> 앞에 noindex 메타를 삽입한다.
# 테마가 젬(gem)이라 레이아웃을 오버라이드하지 않고 출력만 손댄다.
Jekyll::Hooks.register :site, :post_render do |site|
  site.pages.each do |page|
    next unless archive_listing?(page)
    next if page.output.nil? || page.output.include?(NOINDEX_META)

    page.output = page.output.sub("</head>", "#{NOINDEX_META}\n</head>")
  end
end
