"""Public, script-free privacy and manual data deletion instructions."""
from fastapi.responses import HTMLResponse

CONTACT = 'nguyenvovinhnguyen@gmail.com'


def page(title, body):
    return HTMLResponse(f'''<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · HanziGo</title>
<style>body{{margin:0;background:#f4f7f3;color:#183e34;font:17px/1.7 system-ui,sans-serif}}
main{{max-width:820px;margin:32px auto;padding:28px;background:white;border-radius:18px}}
a{{color:#16634e;overflow-wrap:anywhere}}h1{{line-height:1.3;font-size:30px}}
h2{{font-size:22px;margin-top:28px}}nav{{display:flex;gap:18px;flex-wrap:wrap}}
@media(max-width:600px){{main{{margin:12px;padding:20px}}}}</style></head>
<body><main><nav aria-label="Điều hướng"><a href="/">HanziGo</a>
<a href="/privacy-policy">Quyền riêng tư</a><a href="/data-deletion">Xóa dữ liệu</a></nav>
<h1>{title}</h1><p>Cập nhật: 16/10/2026</p>{body}
<hr><p>Liên hệ HanziGo: <a href="mailto:{CONTACT}">{CONTACT}</a></p>
</main></body></html>''', headers={'Cache-Control': 'public, max-age=300',
        'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
        'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"})


def register_privacy_pages(app):
    @app.get('/privacy-policy', response_class=HTMLResponse, include_in_schema=False)
    def privacy_policy():
        return page('Chính sách quyền riêng tư HanziGo', '''
<p>Trang này mô tả việc xử lý dữ liệu khi bạn sử dụng website và ứng dụng học tiếng Trung HanziGo.
Đầu mối phụ trách yêu cầu về dữ liệu là địa chỉ liên hệ ở cuối trang.</p>
<h2>Dữ liệu được xử lý</h2>
<ul><li>Tài khoản: tên hiển thị, email, thông tin hồ sơ bạn cung cấp và phiên đăng nhập.
Đăng ký bằng mật khẩu sử dụng giá trị băm mật khẩu để xác thực.</li>
<li>Đăng nhập Google/Facebook: thông tin định danh và email được nhà cung cấp cho phép chia sẻ;
Google có thể cung cấp ảnh đại diện. Facebook được dùng để xác thực tài khoản, không để đăng bài
hay đọc danh sách bạn bè. Tích hợp Facebook cần được cấu hình và được Meta cho phép trước khi sử dụng.</li>
<li>Học tập: bài làm, kết quả, tiến độ, chuỗi ngày học, từ đã lưu, nội dung viết tay và tùy chọn cá nhân.</li>
<li>Tính năng AI: câu hỏi, bài làm, nội dung trò chuyện hoặc tệp bạn chủ động gửi;
âm thanh khi bạn sử dụng tính năng thu âm/phát âm và cấp quyền micro.</li>
<li>Premium: mã đơn, gói đăng ký, số tiền và thông tin xác nhận giao dịch do hệ thống thanh toán cung cấp.</li>
<li>Dữ liệu kỹ thuật phục vụ vận hành: thông tin yêu cầu mạng, nhật ký lỗi và hoạt động bảo mật.
Trình duyệt có thể lưu phiên đăng nhập, tùy chọn và bộ nhớ đệm ứng dụng.</li></ul>
<h2>Mục đích sử dụng</h2>
<p>Xác thực đăng nhập; cung cấp và cá nhân hóa việc học; lưu kết quả; chấm bài và hỗ trợ bằng AI;
xác nhận thanh toán và quyền Premium; xử lý hỗ trợ, lỗi và hành vi lạm dụng.</p>
<h2>Dịch vụ bên thứ ba</h2>
<p>HanziGo sử dụng hạ tầng lưu trữ/triển khai (Vercel và cơ sở dữ liệu), Google/Meta cho đăng nhập,
dịch vụ gửi email cho mã xác thực, SePay cho đối soát thanh toán, và nhà cung cấp AI được cấu hình
(như Google Gemini) cho các chức năng AI. Dữ liệu cần thiết cho chức năng tương ứng có thể được
gửi đến nhà cung cấp và được xử lý trên hạ tầng ngoài Việt Nam. Việc sử dụng tài khoản Google,
Facebook và dịch vụ thanh toán cũng chịu chính sách riêng của các nhà cung cấp đó.</p>
<p>Không đưa mật khẩu, mã OTP, thông tin tài chính nhạy cảm hoặc dữ liệu riêng tư không cần thiết vào trò chuyện AI.</p>
<h2>Lưu giữ và bảo vệ</h2>
<p>Dữ liệu được lưu để duy trì tài khoản, lịch sử học tập và giao dịch. Khi nhận yêu cầu xóa,
HanziGo xác minh chủ tài khoản và xem xét phạm vi dữ liệu cần xóa hoặc ẩn danh. Một số hồ sơ
giao dịch, bảo mật hoặc bản sao lưu có thể cần được giữ lại theo nghĩa vụ áp dụng và cơ chế lưu trữ;
bộ phận hỗ trợ sẽ thông báo phạm vi, lý do và thời gian xử lý cho trường hợp cụ thể.
Không có hệ thống truyền hoặc lưu trữ dữ liệu nào được bảo đảm an toàn tuyệt đối.</p>
<h2>Lựa chọn và yêu cầu của bạn</h2>
<p>Bạn có thể sửa thông tin trong mục Cá nhân, từ chối quyền micro khi không sử dụng thu âm,
hoặc liên hệ để yêu cầu truy cập, sửa hay xóa dữ liệu. Xem
<a href="/data-deletion">hướng dẫn yêu cầu xóa dữ liệu</a>. Gỡ kết nối Facebook hoặc gỡ cài đặt
ứng dụng không đồng nghĩa dữ liệu HanziGo đã được xóa.</p>
<h2>Thay đổi chính sách</h2>
<p>Nội dung có thể được cập nhật khi chức năng hoặc cách xử lý dữ liệu thay đổi.
Ngày cập nhật được ghi ở đầu trang. Nếu có thắc mắc, vui lòng liên hệ HanziGo.</p>''')

    @app.get('/data-deletion', response_class=HTMLResponse, include_in_schema=False)
    def data_deletion():
        return page('Hướng dẫn yêu cầu xóa dữ liệu HanziGo', f'''
<p>Bạn có thể gửi yêu cầu xóa tài khoản hoặc dữ liệu liên quan đến việc sử dụng HanziGo,
bao gồm dữ liệu nhận qua Đăng nhập bằng Facebook.</p>
<h2>Cách gửi yêu cầu</h2>
<ol><li>Gửi email đến <a href="mailto:{CONTACT}">{CONTACT}</a>,
ưu tiên từ email đang liên kết với tài khoản HanziGo.</li>
<li>Đặt tiêu đề: <strong>Yêu cầu xóa dữ liệu HanziGo</strong>.</li>
<li>Ghi tên hiển thị, email tài khoản, cách đăng nhập (Facebook/Google/email),
và yêu cầu xóa toàn bộ tài khoản hay loại dữ liệu cụ thể.</li></ol>
<p><strong>Không gửi mật khẩu, App Secret, mã OTP hoặc access token.</strong>
Nếu không còn truy cập email liên kết, hãy nêu rõ để bộ phận hỗ trợ hướng dẫn xác minh phù hợp.</p>
<h2>Sau khi gửi</h2>
<p>Yêu cầu được xử lý thủ công. Bộ phận hỗ trợ xác minh quyền sở hữu trước khi thực hiện,
trao đổi phạm vi và thời gian dự kiến qua email, rồi thông báo kết quả.
Trang này không tự xóa tài khoản và không phải endpoint callback xóa dữ liệu của Meta.</p>
<p>Phạm vi yêu cầu có thể bao gồm hồ sơ, liên kết Facebook, phiên đăng nhập, lịch sử học,
bài làm, nội dung trò chuyện và tệp liên quan. Dữ liệu giao dịch hoặc nhật ký cần giữ lại
theo nghĩa vụ áp dụng sẽ được giải thích khi xử lý; việc xóa không phải yêu cầu hoàn tiền.
Xóa toàn bộ tài khoản có thể làm mất khả năng truy cập tiến độ và quyền lợi gắn với tài khoản đó.</p>
<h2>Ngắt kết nối Facebook</h2>
<p>Bạn cũng có thể tìm HanziGo trong phần Ứng dụng và trang web của cài đặt Facebook để gỡ kết nối.
Thao tác này không thay thế yêu cầu xóa dữ liệu đã lưu tại HanziGo; hãy gửi email theo hướng dẫn trên.</p>''')
