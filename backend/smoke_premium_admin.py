"""Offline browser regression: cancelled orders must never look pending."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect


def main():
    source = (Path(__file__).resolve().parents[1] / 'admin/premium.js').read_text(encoding='utf-8')
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.route('http://premium.test/**', lambda route: route.fulfill(
            content_type='text/javascript' if route.request.url.endswith('.js') else 'text/html',
            body=source if route.request.url.endswith('.js') else '<main id="content"></main>'))
        page.goto('http://premium.test/')
        page.evaluate('''async () => {
          const {renderPremiumManagement} = await import('/premium.js');
          const items = ['pending','completed','cancelled'].map((status, i) => ({
            id:i, order_code:'TEST'+i, status, plan_type:'1_month', amount:49000,
            created_at:1700000000, user_name:'Test user'
          }));
          const stats={total_revenue:49000,active_subscribers:1,pending_orders:1,total_vouchers:0,ai_vouchers:0};
          window.calls=[];
          const api=async (url) => {
            window.calls.push(url);
            if(url.includes('transactions')){
              const status=new URL(url,location.origin).searchParams.get('status');
              return {items:items.filter(x=>!status||x.status===status)};
            }
            return stats;
          };
          renderPremiumManagement(document.querySelector('main'),stats,api,()=>{},()=>{});
        }''')
        expect(page.locator('[data-prem-tab]')).to_have_count(2)
        expect(page.locator('#sepay-config-form')).to_have_count(0)
        cancelled = page.locator('tr').filter(has_text='TEST2')
        expect(cancelled).to_contain_text('Đã hủy / Hết hạn 10 phút')
        assert 'Chờ chuyển tiền' not in cancelled.inner_text()
        expect(page.locator('tr').filter(has_text='TEST0')).to_contain_text('Chờ chuyển tiền')
        expect(page.locator('tr').filter(has_text='TEST1')).to_contain_text('Đã thanh toán')
        page.select_option('#filter-tx-status', 'cancelled')
        expect(page.locator('tbody tr')).to_have_count(1)
        expect(page.locator('tbody')).to_contain_text('TEST2')
        assert not any('sepay-config' in url for url in page.evaluate('window.calls'))
        assert not errors, errors
        browser.close()
    print('PASS: removed configuration tab; correct paid/pending/cancelled labels and filter')


if __name__ == '__main__':
    main()
