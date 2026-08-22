#!/usr/bin/env ruby
# frozen_string_literal: true
#
# sitemap.xml의 <urlset> 헤더를 구글 문서가 예시로 드는 최소 형태로 바꾼다.
#
# 배경: jekyll-sitemap은 XSD 스키마 선언까지 붙인 긴 헤더를 낸다.
#
#   <urlset xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
#           xsi:schemaLocation="... sitemap.xsd"
#           xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
#
# Chirpy 이슈 #2658에서 "GSC가 이 복잡한 헤더를 파싱하지 못해
# couldn't fetch가 난다"는 가설이 제기됐다(미검증). 구글 공식 문서의 예시는
# 아래 최소 형태다.
#
#   <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
#
# 스키마 선언은 사이트맵 규격상 선택 사항이라 빼도 유효하다. 비용이 없으니
# 가설 검증 삼아 최소 형태로 낸다. 효과가 없으면 이 파일만 지우면 된다.
#
# 참고: https://github.com/cotes2020/jekyll-theme-chirpy/issues/2658

SIMPLE_URLSET = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'

Jekyll::Hooks.register :site, :post_render do |site|
  site.pages.each do |page|
    next unless page.url == "/sitemap.xml"
    next if page.output.nil?

    # 여는 <urlset ...> 태그 하나만 최소 형태로 교체한다.
    page.output = page.output.sub(/<urlset\b[^>]*>/, SIMPLE_URLSET)
  end
end
