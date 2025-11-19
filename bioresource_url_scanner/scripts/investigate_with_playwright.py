#!/usr/bin/env python3
"""
investigate_with_playwright.py - Investigate low-scoring sites with browser rendering
"""

import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import json

# Sites to investigate (low scorers that are live)
SITES_TO_INVESTIGATE = [
    {
        'name': 'BloodSpot',
        'url': 'http://www.bloodspot.eu',
        'v2_score': 0
    },
    {
        'name': 'RiPPMiner',
        'url': 'http://www.nii.ac.in/rippminer.html',
        'v2_score': 0
    },
    {
        'name': 'NPIDB',
        'url': 'http://npidb.belozersky.msu.ru/',
        'v2_score': 2
    },
    {
        'name': 'CSDB',
        'url': 'http://csdb.glycoscience.ru',
        'v2_score': 8
    }
]

async def investigate_site(site_info):
    """Investigate a single site with Playwright"""
    print(f"\n{'=' * 80}")
    print(f"Investigating: {site_info['name']}")
    print(f"URL: {site_info['url']}")
    print(f"V2 Score: {site_info['v2_score']}")
    print(f"{'=' * 80}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # Navigate to the page
            print(f"\n1. Loading page...")
            response = await page.goto(site_info['url'], timeout=30000, wait_until='networkidle')

            # Get final URL after redirects
            final_url = page.url
            print(f"   Initial URL: {site_info['url']}")
            print(f"   Final URL: {final_url}")
            print(f"   Status: {response.status}")

            # Wait for page to render
            await page.wait_for_timeout(2000)

            # Get page title
            title = await page.title()
            print(f"\n2. Page Title: {title}")

            # Get visible text content
            body_text = await page.inner_text('body')
            text_preview = ' '.join(body_text.split()[:100])
            print(f"\n3. Visible Text (first 100 words):")
            print(f"   {text_preview}...")

            # Check for key indicators in visible text
            text_lower = body_text.lower()
            print(f"\n4. Indicator Detection in Rendered Content:")

            key_indicators = {
                'database': text_lower.count('database'),
                'search': text_lower.count('search'),
                'data': text_lower.count('data'),
                'gene': text_lower.count('gene'),
                'protein': text_lower.count('protein'),
                'genome': text_lower.count('genome'),
                'query': text_lower.count('query'),
                'browse': text_lower.count('browse'),
                'download': text_lower.count('download')
            }

            for indicator, count in sorted(key_indicators.items(), key=lambda x: -x[1])[:10]:
                if count > 0:
                    print(f"   - '{indicator}': {count} occurrences")

            # Check for iframes
            iframes = await page.query_selector_all('iframe')
            print(f"\n5. Page Structure:")
            print(f"   - iframes found: {len(iframes)}")

            # Check for JavaScript rendering
            html = await page.content()
            print(f"   - HTML size: {len(html)} bytes")
            print(f"   - Visible text size: {len(body_text)} bytes")

            # Get meta tags
            meta_description = await page.get_attribute('meta[name="description"]', 'content') or 'None'
            meta_keywords = await page.get_attribute('meta[name="keywords"]', 'content') or 'None'
            print(f"\n6. Meta Tags:")
            print(f"   - Description: {meta_description[:100]}")
            print(f"   - Keywords: {meta_keywords[:100]}")

            # Screenshot
            screenshot_path = f"data/screenshot_{site_info['name'].lower().replace(' ', '_')}.png"
            await page.screenshot(path=screenshot_path)
            print(f"\n7. Screenshot saved to: {screenshot_path}")

            # Return analysis
            return {
                'name': site_info['name'],
                'url': site_info['url'],
                'v2_score': site_info['v2_score'],
                'final_url': final_url,
                'redirected': final_url != site_info['url'],
                'status_code': response.status,
                'title': title,
                'html_size': len(html),
                'visible_text_size': len(body_text),
                'has_iframes': len(iframes) > 0,
                'iframe_count': len(iframes),
                'indicators_found': {k: v for k, v in key_indicators.items() if v > 0},
                'total_indicator_matches': sum(key_indicators.values()),
                'meta_description': meta_description,
                'meta_keywords': meta_keywords
            }

        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            return {
                'name': site_info['name'],
                'url': site_info['url'],
                'error': str(e)
            }
        finally:
            await browser.close()

async def main():
    print("=" * 80)
    print("PLAYWRIGHT INVESTIGATION OF LOW-SCORING SITES")
    print("=" * 80)

    results = []
    for site in SITES_TO_INVESTIGATE:
        result = await investigate_site(site)
        results.append(result)
        await asyncio.sleep(2)  # Be polite

    # Save results
    with open('data/playwright_investigation.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary
    print(f"\n\n{'=' * 80}")
    print("SUMMARY OF FINDINGS")
    print(f"{'=' * 80}")

    for result in results:
        if 'error' in result:
            print(f"\n{result['name']} - ERROR: {result['error']}")
            continue

        print(f"\n{result['name']}:")
        print(f"   V2 Score: {result['v2_score']}")
        print(f"   Redirected: {result['redirected']}")
        print(f"   Has iframes: {result['has_iframes']}")
        print(f"   Rendered text size: {result['visible_text_size']} bytes")
        print(f"   Total indicator matches: {result['total_indicator_matches']}")
        print(f"   Top indicators: {', '.join(list(result['indicators_found'].keys())[:5])}")

        # Calculate what score SHOULD be based on rendered content
        estimated_score = result['total_indicator_matches'] * 2  # Rough estimate
        print(f"   Estimated score from rendered content: ~{estimated_score}")

    print(f"\n{'=' * 80}")
    print("✅ Investigation complete. Results saved to data/playwright_investigation.json")
    print(f"{'=' * 80}")

if __name__ == '__main__':
    asyncio.run(main())
