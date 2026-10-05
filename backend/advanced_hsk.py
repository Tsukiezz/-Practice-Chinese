"""Original supplementary advanced material, not official HSK exam papers.

7/8/9 denote progressive HanziGo practice bands within the combined HSK 7-9.
Source for exam scope only: https://www.chinesetest.cn/HSK/7-9
All passages and questions below are original learning material.
"""
from copy import deepcopy
import json
import time
from urllib.parse import quote
from fastapi import HTTPException
from database import database
from premium_benefits import premium

NOTICE = 'Bài luyện bổ trợ do HanziGo biên soạn theo độ khó tăng dần; không phải đề HSK chính thức hay toàn bộ giáo trình HSK 7–9.'

# Each unit includes independent reading/listening comprehension and grammar.
UNITS = [
    (7, 'Thành phố và không gian công cộng',
     [('更新', 'gēngxīn', 'đổi mới'), ('兼顾', 'jiāngù', 'đồng thời quan tâm'), ('协商', 'xiéshāng', 'thương lượng')],
     '与其……不如……', 'So sánh hai cách làm, ưu tiên phương án sau.',
     ('与其一味扩大道路，不如改善公共交通。', 'Yǔqí yīwèi kuòdà dàolù, bùrú gǎishàn gōnggòng jiāotōng.', 'Thay vì chỉ mở rộng đường, nên cải thiện giao thông công cộng.'),
     '一座老城区计划把闲置仓库改造成公共阅览室。起初，设计团队主张拆除全部旧墙，以便安装统一的玻璃外立面。居民却认为，墙上的旧招牌承载着社区记忆，不能仅以美观为由抹去。经过协商，团队保留临街墙面，改造内部空间，并增设无障碍通道。项目负责人强调，城市更新不是让所有街道看起来一样，而是在安全、便利与历史之间寻找平衡。开放后，阅览室白天接待老人，晚上为年轻人提供自习座位。',
     'Khu phố chuyển kho cũ thành phòng đọc, giữ mặt tường lịch sử và cải tạo bên trong sau khi trao đổi với cư dân. Mục tiêu là cân bằng an toàn, tiện ích và ký ức cộng đồng.',
     [('居民反对拆墙的主要原因是什么？', ['墙面具有社区记忆价值', '玻璃无法安装', '仓库仍在使用'], 0, 'Cư dân muốn giữ biển hiệu cũ vì chúng lưu giữ ký ức của cộng đồng.'),
      ('哪项最符合负责人的观点？', ['所有街道应采用统一外观', '更新应兼顾多方面需求', '历史建筑不能改变用途'], 1, 'Người phụ trách nhấn mạnh sự cân bằng giữa an toàn, tiện lợi và lịch sử.')],
     '主持人：新阅览室为什么推迟开放？负责人：不是施工出了问题，而是居民建议增加轮椅坡道。我们重新调整了入口，虽然多花了两周，但使用起来更方便。主持人：旧墙保留了吗？负责人：保留了，还请老居民介绍墙上招牌的故事。',
     [('开放推迟的原因是？', ['施工材料损坏', '需要调整无障碍入口', '居民拒绝开放'], 1, 'Lối vào được điều chỉnh để có đường dốc cho xe lăn.'),
      ('谁将介绍旧招牌的故事？', ['老居民', '游客', '新来的学生'], 0, 'Người phụ trách mời cư dân lâu năm kể chuyện biển hiệu.')]),
    (7, 'Đọc hiểu khảo sát và giới hạn dữ liệu',
     [('样本', 'yàngběn', 'mẫu khảo sát'), ('偏差', 'piānchā', 'sai lệch'), ('推断', 'tuīduàn', 'suy luận')],
     '并非……而是……', 'Bác bỏ cách hiểu trước rồi đưa ra cách hiểu đúng.',
     ('差异并非来自年龄，而是来自使用习惯。', 'Chāyì bìngfēi láizì niánlíng, érshì láizì shǐyòng xíguàn.', 'Sự khác biệt không đến từ tuổi tác mà từ thói quen sử dụng.'),
     '一家书店通过手机问卷调查读者的阅读习惯。结果显示，多数受访者偏爱电子书，于是有人建议大幅减少纸质书库存。然而，店员发现问卷仅发布在电子阅读交流群，平时不使用手机的老顾客几乎没有参与。研究人员指出，样本数量即使很大，也未必具有代表性。书店随后在店内增加纸质问卷，并记录不同年龄段的反馈。新的结果并未否定电子阅读的增长，却表明纸质书仍有稳定需求。管理者最终决定小幅调整库存，而不是彻底改变经营方向。',
     'Khảo sát trực tuyến ban đầu thiên lệch vì chỉ tiếp cận nhóm đọc sách điện tử. Bổ sung khảo sát giấy giúp cửa hàng thấy nhu cầu sách giấy vẫn ổn định và chỉ điều chỉnh kho ở mức nhỏ.',
     [('最初调查的主要局限是什么？', ['问题数量太少', '参与者来源单一', '完全没有人回答'], 1, 'Bảng hỏi chỉ được đăng trong nhóm đọc sách điện tử.'),
      ('新的结果说明了什么？', ['电子阅读正在消失', '所有顾客都拒绝纸质书', '两种阅读需求可以同时存在'], 2, 'Sách điện tử tăng trưởng nhưng sách giấy vẫn có nhu cầu ổn định.')],
     '记者：两次问卷的结论为什么不同？店员：第一次只在网络群里发，第二次也邀请到店顾客填写纸质表格。记者：那么第一次数据没有价值吗？店员：不能这么说，它反映了部分读者的偏好，但不能代表全部顾客。',
     [('第二次调查增加了哪类参与者？', ['到店填写纸质表格的顾客', '只购买电子书的人', '只在国外生活的人'], 0, 'Lần hai bổ sung khách trực tiếp đến cửa hàng.'),
      ('店员如何评价第一次数据？', ['毫无意义', '可以代表所有人', '有价值但代表范围有限'], 2, 'Dữ liệu vẫn phản ánh một nhóm độc giả, không đại diện tất cả.')]),
    (8, 'Kinh tế tuần hoàn và đánh đổi',
     [('循环', 'xúnhuán', 'tuần hoàn'), ('回收', 'huíshōu', 'thu hồi, tái chế'), ('权衡', 'quánhéng', 'cân nhắc lợi hại')],
     '固然……但……', 'Thừa nhận một mặt rồi bổ sung giới hạn hoặc mặt đối lập.',
     ('回收固然重要，但减少浪费同样不可忽视。', 'Huíshōu gùrán zhòngyào, dàn jiǎnshǎo làngfèi tóngyàng bùkě hūshì.', 'Tái chế quả thực quan trọng, nhưng cũng không thể xem nhẹ giảm lãng phí.'),
     '某社区试行可重复使用的外卖餐盒。支持者认为，只要增加回收次数，就能减少一次性塑料的消耗。运营团队却提醒，清洗、消毒和运输同样需要水与能源，不能仅凭餐盒的材质判断整个方案是否环保。试点把回收点设在居民每日经过的出入口，以减少专程往返；同时公开餐盒周转次数与损耗率，接受居民监督。几个月后，项目仍未实现盈利，但丢失率逐渐下降。评估人员建议，既不要因短期亏损立即否定试点，也不要把回收量增长直接等同于环境效益，而应比较完整的使用周期。',
     'Thử nghiệm hộp đồ ăn tái sử dụng cần đánh giá cả rửa, vận chuyển và số vòng sử dụng. Điểm thu hồi thuận đường giảm chuyến đi riêng; lượng thu hồi tăng chưa tự động đồng nghĩa lợi ích môi trường tăng.',
     [('为什么不能只看餐盒材质？', ['材质无法辨认', '清洗和运输也消耗资源', '所有材质成本相同'], 1, 'Đánh giá vòng đời phải tính cả nước, năng lượng và vận chuyển.'),
      ('评估人员主张采用什么视角？', ['只看首月利润', '只看回收数量', '比较完整使用周期'], 2, 'Đoạn cuối yêu cầu so sánh toàn bộ chu kỳ sử dụng.')],
     '主持人：试点亏损是否意味着应该停止？评估员：还不能下结论。启动阶段的设备投入较高，我们需要区分一次性投入和日常运营成本。此外，如果为了回收一个餐盒专程开车，可能抵消原本的环境收益，因此回收点的位置也很关键。',
     [('评估员认为现在应该怎样做？', ['立即停止所有回收', '区分成本并继续评估', '只关注设备颜色'], 1, 'Cần phân biệt chi phí đầu tư ban đầu với chi phí vận hành.'),
      ('为什么回收点位置重要？', ['避免为回收专程开车', '方便提高餐盒售价', '可以省去消毒'], 0, 'Chuyến xe riêng có thể làm mất lợi ích môi trường.')]),
    (8, 'Số hóa di sản và bối cảnh',
     [('传承', 'chuánchéng', 'kế thừa và truyền lại'), ('语境', 'yǔjìng', 'ngữ cảnh'), ('阐释', 'chǎnshì', 'diễn giải')],
     '不仅……更……', 'Nhấn mạnh lớp ý sâu hơn ngoài lợi ích ban đầu.',
     ('数字化不仅保存图像，更需要保留语境。', 'Shùzìhuà bùjǐn bǎocún túxiàng, gèng xūyào bǎoliú yǔjìng.', 'Số hóa không chỉ lưu hình ảnh mà còn cần giữ bối cảnh.'),
     '博物馆把一批民间手工艺品制作成三维模型，观众可以在网上旋转、放大，观察细微纹理。这种展示降低了接触藏品的门槛，却不能自动传递制作技艺的全部意义。例如，同一图案在婚礼与祭祀中可能承担不同功能，若仅保留外形，观众容易把它当成普通装饰。策展团队因此邀请手艺人录制访谈，说明材料选择、使用场合以及学习过程。有人担心个人记忆不够准确，团队便把口述与地方文献相互参照，并标明尚存争议的部分。数字化由此不再只是复制物件，而成为持续讨论文化意义的入口。',
     'Mô hình 3D giúp tiếp cận hiện vật nhưng không tự truyền tải ý nghĩa văn hóa. Bảo tàng bổ sung phỏng vấn nghệ nhân, đối chiếu tư liệu và ghi rõ các điểm còn tranh luận.',
     [('只保留外形可能造成什么问题？', ['观众忽略物件的使用语境', '观众无法放大图像', '所有纹理都会消失'], 0, 'Cùng hoa văn có thể có chức năng khác nhau tùy nghi lễ.'),
      ('团队如何处理口述中的不确定性？', ['全部删除口述', '与文献对照并标注争议', '把记忆当作唯一事实'], 1, 'Nhóm đối chiếu ký ức với tư liệu địa phương và nêu phần còn tranh luận.')],
     '观众：三维模型这么清楚，为什么还要看访谈？策展人：模型告诉您物件长什么样，访谈帮助您理解人们为什么这样制作、在什么场合使用。观众：口述会不会有出入？策展人：会，所以我们把不同说法并列展示，而不是假装只有一种解释。',
     [('访谈主要补充什么？', ['模型的文件大小', '制作动机与使用场合', '门票优惠信息'], 1, 'Phỏng vấn giải thích lý do chế tác và hoàn cảnh sử dụng.'),
      ('策展人对不同说法采取什么态度？', ['并列呈现', '只留最受欢迎的一种', '一律隐藏'], 0, 'Những cách kể khác nhau được trình bày song song.')]),
    (9, 'Lập luận nhân quả và biến gây nhiễu',
     [('因果', 'yīnguǒ', 'nhân quả'), ('干预', 'gānyù', 'can thiệp'), ('混淆', 'hùnxiáo', 'làm lẫn lộn')],
     '即便……也未必……', 'Điều kiện được thừa nhận nhưng kết luận vẫn không tất yếu.',
     ('即便两者同步变化，也未必存在因果关系。', 'Jíbiàn liǎngzhě tóngbù biànhuà, yě wèibì cúnzài yīnguǒ guānxì.', 'Dù hai yếu tố cùng biến đổi, chưa chắc chúng có quan hệ nhân quả.'),
     '一项观察发现，经常参加社区活动的老年人平均健康状况较好。报道据此宣称，增加活动次数必然改善健康。然而，较好的身体条件本身就可能使人更愿意外出，家庭支持也可能同时影响参与程度与健康水平。若不区分这些路径，就容易把相关性误当作单向因果。研究团队随后跟踪新加入者，并与条件相近但尚未参与的人比较，同时记录原有疾病与生活方式。这样的设计有助于缩小解释范围，却仍无法排除所有未被测量的因素。审慎的结论并不是活动没有益处，而是现有证据支持的强度有限，公共建议应同时说明不确定性与适用条件。',
     'Người tham gia hoạt động cộng đồng khỏe hơn chưa chứng minh hoạt động là nguyên nhân duy nhất. Sức khỏe sẵn có và hỗ trợ gia đình có thể ảnh hưởng cả hai; nghiên cứu so sánh giúp thu hẹp nhưng không loại hết bất định.',
     [('哪种情况属于文中的反向解释？', ['健康较好的人更愿意外出', '所有活动都损害健康', '家庭支持与健康无关'], 0, 'Sức khỏe tốt có thể thúc đẩy tham gia, thay vì chỉ chiều ngược lại.'),
      ('作者认为应如何表达研究结论？', ['保证每个人都受益', '因存在不确定性而隐瞒结果', '说明证据强度与适用条件'], 2, 'Thận trọng là nói rõ giới hạn chứng cứ, không khẳng định tuyệt đối hoặc phủ nhận sạch.')],
     '记者：既然两组情况相近，为什么还不能确定因果？研究者：相近只针对我们记录的指标，例如年龄与既往疾病。未测量的因素仍可能影响结果。记者：那研究还有用吗？研究者：当然有，它能排除部分解释。科学结论往往逐步收敛，而不是一次观察就彻底确定。',
     [('研究者保留判断的原因是什么？', ['没有记录任何指标', '可能存在未测量因素', '两组人数必须完全相同'], 1, 'Các yếu tố chưa đo vẫn có thể ảnh hưởng kết quả.'),
      ('“逐步收敛”在这里强调什么？', ['结论在积累证据中逐渐明确', '研究只能重复原有观点', '所有解释同样可信'], 0, 'Chứng cứ tích lũy làm kết luận dần rõ hơn.')]),
    (9, 'Dịch thuật và sắc thái diễn ngôn',
     [('措辞', 'cuòcí', 'cách lựa chọn lời'), ('隐含', 'yǐnhán', 'hàm chứa'), ('立场', 'lìchǎng', 'lập trường')],
     '看似……实则……', 'Đối chiếu biểu hiện bề ngoài với bản chất.',
     ('这处改动看似细微，实则改变了作者的立场。', 'Zhè chù gǎidòng kànsì xìwēi, shízé gǎibiàn le zuòzhě de lìchǎng.', 'Chỉnh sửa này có vẻ nhỏ nhưng thực chất thay đổi lập trường của tác giả.'),
     '翻译一篇评论时，译者把“这一方案或许能够缓解压力”改成了“这一方案必将解决问题”。后一句读起来更有力量，却把原文的试探性判断变成了确定承诺，也扩大了政策效果的范围。编辑指出，忠实并不意味着机械对应每一个词，而是需要保留论证关系、语气强弱和适用边界。为了让目标读者理解背景，译者可以补充必要说明，但应明确区分作者观点与译者注释。尤其面对有争议的议题，流畅的表达不能成为替作者作出更强判断的理由。真正负责任的转述，是既让读者读懂，又让他们看见原文保留的余地。',
     'Đổi “có lẽ giảm áp lực” thành “chắc chắn giải quyết vấn đề” làm tăng cả độ chắc chắn và phạm vi. Bản dịch cần giữ quan hệ lập luận, sắc thái và ranh giới; chú thích phải phân biệt với ý tác giả.',
     [('译文的问题主要体现在哪里？', ['增加了不必要的标点', '提高确定性并扩大效果范围', '完整保留了原文语气'], 1, '或许 thành 必将, 缓解 thành 解决: cả mức chắc chắn và kết quả đều bị nâng lên.'),
      ('作者如何看待译者补充背景？', ['可以补充但须区分注释与原意', '必须完全禁止', '可以不加说明地改变立场'], 0, 'Có thể chú giải nhưng phải phân biệt rõ ai là người đưa ra nhận định.')],
     '编辑：你为什么把“可能”删掉了？译者：我怕读者觉得作者没有信心。编辑：这里的保留并非犹豫，而是对证据范围的准确表达。译者：那我能加一条背景注释吗？编辑：可以，但请标明是译者注，不能把解释直接写成作者的结论。',
     [('编辑认为“可能”体现了什么？', ['作者完全不懂问题', '对证据范围的准确把握', '译者没有时间修改'], 1, 'Từ này giữ đúng giới hạn chứng cứ, không đơn giản là thiếu tự tin.'),
      ('背景解释应怎样加入？', ['标明译者注', '冒充作者结论', '替换原文所有判断'], 0, 'Biên tập viên yêu cầu ghi rõ chú thích của người dịch.')]),
]


def lessons():
    output = []
    for index, unit in enumerate(UNITS):
        level, title, words, pattern, note, example, passage, translation, reading, listening, heard = unit
        questions = [{'id': f'q{i+1}', 'kind': 'reading', 'prompt': q[0], 'options': q[1], 'answer': q[2], 'explanation': q[3]}
                     for i, q in enumerate(reading)]
        for i, word in enumerate(words[:2]):
            options = [w[2] for w in words]
            questions.append({'id': f'q{i+3}', 'kind': 'vocabulary', 'prompt': f'{word[0]} ({word[1]}) nghĩa là gì?',
                              'options': options, 'answer': i, 'explanation': f'{word[0]}: {word[2]}.'})
        output.append({'id': f'hsk{level}-{index % 2 + 1:02}', 'hsk': level, 'order': index % 2 + 1,
                       'title': title, 'minutes': 20, 'review': index % 2 == 1, 'premium_only': True,
                       'objective': f'Luyện phân tích nội dung nâng cao: {title.lower()}. {NOTICE}',
                       'vocabulary': [dict(zip(('hanzi', 'pinyin', 'meaning'), w), hsk=level) for w in words],
                       'grammar': {'pattern': pattern, 'note': note, 'example': dict(zip(('hanzi', 'pinyin', 'meaning'), example))},
                       'reading': {'hanzi': passage, 'meaning': translation},
                       'task': 'Tóm tắt lập luận bằng 3–5 câu tiếng Trung, nêu một giới hạn và dùng mẫu câu vừa học.',
                       'questions': questions})
    output.append({
        'id': 'communication-01', 'hsk': 0, 'order': 1, 'title': 'Giao tiếp: Thương lượng lịch giao hàng',
        'minutes': 15, 'review': False, 'premium_only': True,
        'objective': 'Xác nhận yêu cầu, đề xuất phương án thay thế và chốt thỏa thuận lịch sự.',
        'vocabulary': [{'hanzi': '交货', 'pinyin': 'jiāohuò', 'meaning': 'giao hàng'},
                       {'hanzi': '延期', 'pinyin': 'yánqī', 'meaning': 'hoãn thời hạn'},
                       {'hanzi': '确认', 'pinyin': 'quèrèn', 'meaning': 'xác nhận'}],
        'grammar': {'pattern': '能否……？如果……，我们可以……',
                    'note': '能否 hỏi lịch sự về khả năng; câu điều kiện đề xuất giải pháp thay thế.',
                    'example': {'hanzi': '如果周五来不及，我们可以分批交货。',
                                'pinyin': 'Rúguǒ zhōuwǔ láibují, wǒmen kěyǐ fēnpī jiāohuò.',
                                'meaning': 'Nếu không kịp thứ Sáu, chúng tôi có thể giao theo từng đợt.'}},
        'reading': {'hanzi': '客户：能否在周五之前交货？供应商：全部交货恐怕来不及，不过可以先发一半。客户：我们周六有活动，能先发急需的型号吗？供应商：可以，请您今天确认型号和数量，剩余部分下周二发出。客户：好的，请把安排写进邮件。',
                    'meaning': 'Khách muốn giao trước thứ Sáu. Nhà cung cấp đề nghị giao một nửa trước, ưu tiên mẫu cần gấp sau khi khách xác nhận hôm nay; phần còn lại gửi thứ Ba tuần sau và xác nhận bằng email.'},
        'task': 'Đóng vai khách hàng: nêu hạn giao, giải thích lý do và xác nhận phương án bằng 3 câu tiếng Trung.',
        'questions': [
            {'id': 'q1', 'kind': 'reading', 'prompt': '供应商提出什么方案？', 'options': ['全部取消', '分批交货', '提高价格'], 'answer': 1, 'explanation': 'Nhà cung cấp đề nghị giao trước một nửa.'},
            {'id': 'q2', 'kind': 'reading', 'prompt': '客户今天需要确认什么？', 'options': ['型号和数量', '活动地点', '付款银行'], 'answer': 0, 'explanation': 'Cần xác nhận mẫu hàng và số lượng hôm nay.'},
            {'id': 'q3', 'kind': 'reading', 'prompt': '剩余部分什么时候发出？', 'options': ['本周五', '本周六', '下周二'], 'answer': 2, 'explanation': 'Phần còn lại được gửi vào thứ Ba tuần sau.'},
            {'id': 'q4', 'kind': 'grammar', 'prompt': '哪种说法适合礼貌协商？', 'options': ['你必须马上送来！', '能否先发急需的型号？', '我什么都不确认。'], 'answer': 1, 'explanation': '能否 đưa ra yêu cầu dưới dạng hỏi lịch sự.'},
        ],
    })
    return output


def require_advanced(user):
    if not premium(user):
        raise HTTPException(403, 'HSK 7–9 và bài giao tiếp mở rộng dành cho HanziGo Premium còn hạn.')


def exams(level):
    output = []
    mixed = []
    for index, unit in enumerate(u for u in UNITS if u[0] == level):
        for skill, text, checks in [('reading', unit[6], unit[8]), ('listening', unit[9], unit[10])]:
            questions = []
            for i, (prompt, options, answer, explanation) in enumerate(checks):
                questions.append({'id': f'adv{level}-{index}-{skill}-{i}', 'section': skill,
                                  'question_type': 'multiple_choice', 'weight': 1,
                                  'prompt': f'{text}\n\n{prompt}' if skill == 'reading' else prompt,
                                  'options': options, 'answer': options[answer], 'explanation': explanation,
                                  'transcript': text if skill == 'listening' else '',
                                  'audio_url': '/api/tts?text=' + quote(text) if skill == 'listening' else ''})
            # Negative IDs are a separate immutable catalog namespace, never DB exam IDs.
            output.append({'id': -(level * 100 + index * 2 + (1 if skill == 'reading' else 2)),
                           'title': f'HSK {level} · {"Đọc" if skill == "reading" else "Nghe"}: {unit[1]}',
                           'hsk': level, 'duration_minutes': 10, 'version': 1, 'questions': questions})
            mixed.extend(deepcopy(questions))
    output.append({'id': -(level * 100 + 99), 'title': f'HSK {level} · Kiểm tra nâng cao ({len(mixed)} câu)',
                   'hsk': level, 'duration_minutes': 20, 'version': 1, 'questions': mixed})
    return output


def public_exams(level, user):
    require_advanced(user)
    rows = exams(level)
    for row in rows:
        row['questions'] = [{k: v for k, v in q.items() if k not in ('answer', 'explanation', 'transcript')} for q in row['questions']]
    return rows


def submit(exam_id, body, user):
    require_advanced(user)
    exam = next((e for level in (7, 8, 9) for e in exams(level) if e['id'] == exam_id), None)
    if not exam:
        raise HTTPException(404, 'Không tìm thấy đề nâng cao.')
    if body.version != exam['version']:
        raise HTTPException(409, 'Đề đã cập nhật. Vui lòng tải lại.')
    questions = exam['questions']
    if set(body.answers) != {q['id'] for q in questions}:
        raise HTTPException(422, 'Hãy trả lời đủ các câu hỏi.')
    answers = body.answers
    if any(not isinstance(answers[q['id']], str) or answers[q['id']] not in q['options'] for q in questions):
        raise HTTPException(422, 'Lựa chọn không hợp lệ.')
    scores = {q['id']: 100 if answers[q['id']] == q['answer'] else 0 for q in questions}
    score = round(sum(scores.values()) / len(scores), 2)
    sections = {q['section'] for q in questions}
    snapshot = {**exam, 'exam_title': exam['title'], 'answers': answers,
                'section_scores': {s: round(sum(scores[q['id']] for q in questions if q['section'] == s) /
                                          sum(q['section'] == s for q in questions), 2) for s in sections}}
    feedback = f'Kết quả luyện tập: {score}/100. {NOTICE}'
    with database() as conn:
        rid = conn.execute('''INSERT INTO results(user_id,exam_id,kind,content,score,original_score,feedback,graded_by,created_at)
                              VALUES(?,NULL,'exam',?,?,?,?,?,?)''',
                           (user['id'], json.dumps(snapshot, ensure_ascii=False), score, score, feedback, 'automatic', int(time.time()))).lastrowid
        return dict(conn.execute('SELECT * FROM results WHERE id=?', (rid,)).fetchone())
