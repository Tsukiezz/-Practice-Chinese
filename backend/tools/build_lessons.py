"""Build the original HanziGo short-course content. No network or AI API calls.

Each authored record: title, target words, structure, explanation, example
(Chinese / pinyin / Vietnamese), reading (Chinese / Vietnamese), reading question
(prompt / correct / distractor / distractor), grammar question, personal task.
The course is supplementary HSK 2.0 practice, not an official exam syllabus.
"""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data'
# Each nonempty line is a field; slash surrounded by spaces separates subfields.
UNITS = {}
UNITS[1] = '''
Chào hỏi và giới thiệu
你,我,是,学生,老师
A + 是 + B
是 nối chủ ngữ với danh từ chỉ người hoặc nghề nghiệp. Dùng 不是 để phủ định; không đặt 是 trước mọi tính từ.
我是学生。 / Wǒ shì xuésheng. / Tôi là học sinh.
你好！我叫小明。我是学生。她是我的老师。 / Xin chào! Tôi tên Tiểu Minh. Tôi là học sinh. Cô ấy là giáo viên của tôi.
小明是谁？ / 学生 / 医生 / 老师
我___学生。 / 是 / 很 / 在
Tự giới thiệu tên và vai trò của bạn bằng hai câu.

Hỏi thăm và câu hỏi có–không
好,吗,不,很,高兴
Câu trần thuật + 吗？
Thêm 吗 ở cuối câu để hỏi có–không. Khi trả lời, lặp lại động từ hoặc tính từ; phủ định thường dùng 不.
你好吗？我很好。 / Nǐ hǎo ma? Wǒ hěn hǎo. / Bạn khỏe không? Tôi khỏe.
小王：你好吗？小李：我很好。你呢？小王：我也很好。 / Tiểu Vương: Bạn khỏe không? Tiểu Lý: Tôi khỏe. Còn bạn? Tiểu Vương: Tôi cũng khỏe.
小李怎么样？ / 很好 / 不好 / 很冷
你是老师___？ / 吗 / 的 / 在
Viết một câu hỏi có–không và một câu trả lời phủ định.

Gia đình và sở hữu
爸爸,妈妈,儿子,女儿,家
Người sở hữu + 的 + danh từ
的 thể hiện quan hệ sở hữu. Với quan hệ gia đình gần gũi có thể lược 的: 我妈妈. Đừng nhầm 的 với động từ 是.
这是我的妈妈。 / Zhè shì wǒ de māma. / Đây là mẹ của tôi.
我家有三个人：爸爸、妈妈和我。我爸爸是医生。我妈妈是老师。 / Nhà tôi có ba người: bố, mẹ và tôi. Bố tôi là bác sĩ. Mẹ tôi là giáo viên.
谁是医生？ / 爸爸 / 妈妈 / 我
这是我___家。 / 的 / 吗 / 不
Giới thiệu hai người thân và nghề nghiệp của họ.

Số lượng và tuổi
一,二,三,个,岁
Số + lượng từ + danh từ
个 là lượng từ thông dụng nhưng không dùng cho mọi danh từ. Hỏi tuổi trẻ em bằng 几岁; hỏi người lớn dùng 多大. Nói tuổi không cần 是.
我有三个朋友。 / Wǒ yǒu sān ge péngyou. / Tôi có ba người bạn.
我有一个儿子和一个女儿。儿子五岁，女儿三岁。他们都很高兴。 / Tôi có một con trai và một con gái. Con trai năm tuổi, con gái ba tuổi. Cả hai đều rất vui.
女儿几岁？ / 三岁 / 五岁 / 一岁
我有三___朋友。 / 个 / 岁 / 点
Viết tuổi và số người trong gia đình bạn.

Ngày tháng và giờ giấc
今天,明天,点,分钟,时候
Chủ ngữ + thời gian + hành động
Cụm thời gian thường đứng trước động từ, sau chủ ngữ hoặc đầu câu. 点 chỉ giờ; 分钟 chỉ khoảng thời gian tính bằng phút.
我明天八点去学校。 / Wǒ míngtiān bā diǎn qù xuéxiào. / Ngày mai tôi đến trường lúc tám giờ.
今天是星期一。我八点去学校，十二点吃饭。明天我也去学校。 / Hôm nay là thứ Hai. Tôi đến trường lúc tám giờ, ăn cơm lúc mười hai giờ. Ngày mai tôi cũng đến trường.
我几点吃饭？ / 十二点 / 八点 / 三点
我明天八___去学校。 / 点 / 个 / 岁
Viết lịch một ngày với ba mốc giờ.

Ăn uống và sở thích
吃,喝,茶,米饭,喜欢
喜欢 + danh từ / động từ
喜欢 diễn tả sở thích; 想 diễn tả ý muốn trong tình huống hiện tại. Ăn dùng 吃, uống dùng 喝.
我喜欢喝茶。 / Wǒ xǐhuan hē chá. / Tôi thích uống trà.
我喜欢吃米饭，也喜欢喝茶。今天中午我在家吃饭。妈妈喝水，我喝茶。 / Tôi thích ăn cơm, cũng thích uống trà. Trưa nay tôi ăn ở nhà. Mẹ uống nước, tôi uống trà.
妈妈喝什么？ / 水 / 茶 / 米饭
我喜欢___茶。 / 喝 / 吃 / 看
Nói hai món hoặc đồ uống bạn thích và một món không thích.

Vị trí và nơi chốn
在,学校,商店,前面,后面
Người / vật + 在 + nơi chốn
在 có thể chỉ vị trí. Khi diễn tả làm gì ở đâu, dùng 在 + địa điểm trước động từ: 我在家学习.
学校在商店后面。 / Xuéxiào zài shāngdiàn hòumian. / Trường học ở phía sau cửa hàng.
我家前面有一个商店。学校在商店后面。我今天在学校学习汉语。 / Trước nhà tôi có một cửa hàng. Trường học ở sau cửa hàng. Hôm nay tôi học tiếng Trung ở trường.
学校在哪里？ / 商店后面 / 商店前面 / 我家里面
我___学校学习汉语。 / 在 / 是 / 的
Mô tả vị trí nhà, trường hoặc cửa hàng quen thuộc.

Ôn tập: Một ngày của tôi
学习,汉语,朋友,看,书
Chủ ngữ + thời gian + 在 + nơi chốn + động từ
Kết hợp thời gian, địa điểm và hành động. 也 đứng trước vị ngữ để bổ sung một ý tương tự. Giữ câu ngắn và rõ trước khi nối nhiều ý.
我今天在家看书。 / Wǒ jīntiān zài jiā kàn shū. / Hôm nay tôi đọc sách ở nhà.
我叫小林，是学生。我今天在家看书。下午三点，我和朋友去学校学习汉语。 / Tôi tên Tiểu Lâm, là học sinh. Hôm nay tôi đọc sách ở nhà. Ba giờ chiều, tôi cùng bạn đến trường học tiếng Trung.
下午三点，小林做什么？ / 去学校学习汉语 / 在家喝茶 / 去商店买东西
我在家___书。 / 看 / 喝 / 是
Viết 4–5 câu giới thiệu bản thân và lịch sinh hoạt.
'''
UNITS[2] = '''
Việc đã làm và trải nghiệm gần đây
已经,昨天,买,东西,了
Động từ + 了 + tân ngữ
了 sau động từ đánh dấu hành động đã hoàn thành trong ngữ cảnh; không phải cứ quá khứ là thêm 了. Phủ định việc chưa làm thường dùng 没 + động từ và bỏ 了.
我昨天买了一本书。 / Wǒ zuótiān mǎi le yì běn shū. / Hôm qua tôi đã mua một cuốn sách.
昨天我和姐姐去商店。我买了一本书，姐姐买了一件衣服。今天我们没有去商店。 / Hôm qua tôi cùng chị đến cửa hàng. Tôi mua một cuốn sách, chị mua một bộ quần áo. Hôm nay chúng tôi không đến cửa hàng.
谁买了衣服？ / 姐姐 / 我 / 弟弟
我昨天没___书。 / 买 / 买了 / 了买
Kể hai việc đã làm hôm qua và một việc chưa làm.

Đang làm gì?
正在,说话,做,看,电视
正在 + động từ + tân ngữ
正在 nhấn mạnh hành động đang diễn ra. Có thể dùng 呢 cuối câu. Không dùng 正在 cho trạng thái sở hữu như 有 khi không có ý nghĩa hành động.
他正在看电视呢。 / Tā zhèngzài kàn diànshì ne. / Anh ấy đang xem ti vi.
晚上八点，爸爸正在看电视，妈妈正在做饭。我没有看电视，我正在学习。 / Tám giờ tối, bố đang xem ti vi, mẹ đang nấu cơm. Tôi không xem ti vi, tôi đang học.
我正在做什么？ / 学习 / 看电视 / 做饭
妈妈___做饭呢。 / 正在 / 每 / 比
Mô tả ba hành động đang xảy ra quanh bạn.

So sánh khi mua sắm
比,贵,便宜,颜色,件
A + 比 + B + tính từ
比 đặt đối tượng so sánh trước tính từ. Không thêm 很 ngay trước tính từ trong mẫu cơ bản này. Có thể thêm 一点儿 để nói chênh lệch nhỏ.
这件衣服比那件便宜。 / Zhè jiàn yīfu bǐ nà jiàn piányi. / Bộ quần áo này rẻ hơn bộ kia.
这件红衣服一百块，那件白衣服八十块。红衣服比白衣服贵。小王喜欢白色，所以买了白衣服。 / Bộ quần áo đỏ giá một trăm tệ, bộ trắng tám mươi tệ. Bộ đỏ đắt hơn bộ trắng. Tiểu Vương thích màu trắng nên đã mua bộ trắng.
小王买了什么颜色的衣服？ / 白色 / 红色 / 黑色
红衣服___白衣服贵。 / 比 / 在 / 给
So sánh hai món đồ theo giá hoặc kích thước.

Lý do và kết quả
因为,所以,生病,休息,药
因为……所以……
因为 nêu nguyên nhân, 所以 nêu kết quả. Có thể chỉ dùng một vế liên từ khi quan hệ đã rõ; hãy kiểm tra thứ tự nguyên nhân–kết quả.
因为我生病了，所以今天休息。 / Yīnwèi wǒ shēngbìng le, suǒyǐ jīntiān xiūxi. / Vì tôi bị ốm nên hôm nay nghỉ ngơi.
今天小李没有去上班。因为他生病了，所以在家休息。医生说要多喝水，按时吃药。 / Hôm nay Tiểu Lý không đi làm. Vì bị ốm nên anh ấy nghỉ ở nhà. Bác sĩ dặn uống nhiều nước và uống thuốc đúng giờ.
小李为什么没去上班？ / 生病了 / 去旅游了 / 买衣服了
因为下雨了，___我没出去。 / 所以 / 虽然 / 比
Giải thích lý do cho một thay đổi trong kế hoạch của bạn.

Khả năng và xin phép
会,能,可以,游泳,帮助
会 / 能 / 可以 + động từ
会 thường nói kỹ năng đã học; 能 nhấn mạnh khả năng hoặc điều kiện; 可以 thường xin phép hoặc nói điều được phép. Nghĩa có thể giao nhau tùy ngữ cảnh.
我会游泳，今天可以去吗？ / Wǒ huì yóuyǒng, jīntiān kěyǐ qù ma? / Tôi biết bơi, hôm nay đi được không?
小张会游泳，也会打篮球。但是今天他生病了，不能去游泳。他想明天再去。 / Tiểu Trương biết bơi, cũng biết chơi bóng rổ. Nhưng hôm nay bị ốm nên không thể đi bơi. Anh ấy muốn ngày mai đi.
小张今天为什么不能游泳？ / 生病了 / 不会游泳 / 没有朋友
我学过游泳，所以我___游泳。 / 会 / 是 / 的
Viết một kỹ năng bạn có và một câu xin phép.

Dự định cuối tuần
想,要,旅游,准备,一起
想 / 要 + động từ
想 thể hiện mong muốn; 要 thường thể hiện ý định rõ hơn hoặc sự cần thiết. Dùng 想 để đề xuất nhẹ nhàng; ngữ cảnh quyết định sắc thái.
我们想一起去旅游。 / Wǒmen xiǎng yìqǐ qù lǚyóu. / Chúng tôi muốn cùng đi du lịch.
这个星期六，我想和朋友一起去北京。我们准备坐火车去，星期天晚上回来。如果下雨，就不去公园。 / Thứ Bảy này tôi muốn cùng bạn đi Bắc Kinh. Chúng tôi định đi tàu hỏa và về tối Chủ nhật. Nếu trời mưa thì không đi công viên.
他们准备怎么去北京？ / 坐火车 / 坐飞机 / 走路
我们___一起去旅游。 / 想 / 的 / 过
Lập kế hoạch cuối tuần: đi đâu, với ai, bằng phương tiện gì.

Nhận xét cách thực hiện
得,快,慢,跑步,唱歌
Động từ + 得 + nhận xét
得 sau động từ nối với phần nhận xét: 跑得快. Với tân ngữ, có thể nhắc lại động từ: 他唱歌唱得很好. Phân biệt 得 với 的 chỉ sở hữu.
她唱歌唱得很好。 / Tā chàng gē chàng de hěn hǎo. / Cô ấy hát rất hay.
小王每天早上跑步。他跑得很快。小李喜欢唱歌，她唱得很好，但是跑得不快。 / Tiểu Vương chạy bộ mỗi sáng. Anh ấy chạy rất nhanh. Tiểu Lý thích hát, cô ấy hát hay nhưng chạy không nhanh.
谁唱得好？ / 小李 / 小王 / 老师
他跑___很快。 / 得 / 的 / 地方
Nhận xét cách bạn hoặc bạn bè làm hai hoạt động.

Ôn tập: Một chuyến đi
火车,机场,到,从,离
从 + nơi xuất phát + 到 + điểm đến
从 chỉ điểm bắt đầu, 到 chỉ điểm đến. 离 dùng nói khoảng cách giữa hai nơi; không dùng thay cho động từ di chuyển.
从我家到车站要十分钟。 / Cóng wǒ jiā dào chēzhàn yào shí fēnzhōng. / Từ nhà tôi đến ga cần mười phút.
昨天我从家坐车到火车站。因为车站离家不远，所以十分钟就到了。我坐九点的火车去北京。 / Hôm qua tôi đi xe từ nhà đến ga tàu. Vì ga không xa nhà nên chỉ mười phút đã đến. Tôi đi chuyến tàu chín giờ đến Bắc Kinh.
到火车站用了多长时间？ / 十分钟 / 九分钟 / 一小时
___我家到车站要十分钟。 / 从 / 比 / 的
Kể chuyến đi bằng 5–6 câu, có thời gian, phương tiện và một lý do.
'''
UNITS[3] = '''
Kinh nghiệm và trải nghiệm
以前,旅游,过,地方,城市
Động từ + 过
过 nhấn mạnh đã từng có trải nghiệm, không tập trung thời điểm hoàn thành. Phủ định dùng 没 + động từ + 过; thường đi với 以前.
我以前去过这个城市。 / Wǒ yǐqián qù guo zhège chéngshì. / Trước đây tôi từng đến thành phố này.
我以前去过北京两次，但是没去过上海。朋友说上海有很多有意思的地方。今年暑假，我们打算一起去看看。 / Trước đây tôi đến Bắc Kinh hai lần nhưng chưa đến Thượng Hải. Bạn nói Thượng Hải có nhiều nơi thú vị. Hè năm nay chúng tôi định cùng đi xem.
作者没去过哪里？ / 上海 / 北京 / 两个城市都去过
我以前去___北京。 / 过 / 的 / 比
Viết ba trải nghiệm đã có hoặc chưa có và một dự định.

Sắp xếp đồ vật với 把
把,放,房间,干净,桌子
Chủ ngữ + 把 + vật xác định + động từ + kết quả / vị trí
把 nhấn mạnh xử lý một đối tượng đã biết. Vị ngữ thường cần phần kết quả hoặc vị trí; không chỉ đặt một động từ đơn lẻ sau 把.
请把书放在桌子上。 / Qǐng bǎ shū fàng zài zhuōzi shang. / Hãy đặt sách lên bàn.
周末，小林打扫房间。他把书放在桌子上，把衣服放进柜子里。房间干净了，他才开始做作业。 / Cuối tuần, Tiểu Lâm dọn phòng. Anh đặt sách lên bàn, cho quần áo vào tủ. Phòng sạch rồi anh mới bắt đầu làm bài tập.
小林把书放在哪里？ / 桌子上 / 柜子里 / 地上
请___书放在桌子上。 / 把 / 比 / 从
Dùng 把 viết hai lời nhờ sắp xếp đồ đạc.

Kết quả và sự cố với 被
被,自行车,发现,解决,问题
Đối tượng chịu tác động + 被 + tác nhân + hành động
被 chuyển trọng tâm sang đối tượng chịu tác động. Tác nhân có thể lược khi không biết hoặc không cần nêu. Không phải câu 被 nào cũng nói điều xấu.
我的自行车被弟弟骑走了。 / Wǒ de zìxíngchē bèi dìdi qí zǒu le. / Xe đạp của tôi bị em trai đi mất rồi.
早上，我发现自行车不见了。后来才知道，自行车被弟弟骑走了。他下午就会把车送回来，所以我先坐公共汽车上班。 / Sáng nay tôi thấy xe đạp biến mất. Sau đó mới biết em trai đã đi xe mất. Chiều em sẽ mang về nên tôi đi xe buýt đến chỗ làm trước.
谁骑走了自行车？ / 弟弟 / 同事 / 司机
自行车___弟弟骑走了。 / 被 / 比 / 从
Kể một sự việc từ góc nhìn của vật hoặc người chịu tác động.

Điều kiện và kế hoạch dự phòng
如果,就,天气,决定,运动
如果……就……
如果 nêu điều kiện giả định; 就 thường đứng sau chủ ngữ của vế kết quả. Phân biệt giả định với 因为 nêu nguyên nhân đã biết.
如果明天下雨，我们就在家学习。 / Rúguǒ míngtiān xià yǔ, wǒmen jiù zài jiā xuéxí. / Nếu mai mưa thì chúng tôi học ở nhà.
我们决定星期天去爬山。如果天气好，就早上八点出发；如果下雨，就去图书馆。大家都觉得这个计划不错。 / Chúng tôi quyết định Chủ nhật đi leo núi. Nếu trời đẹp thì xuất phát lúc tám giờ sáng; nếu mưa thì đi thư viện. Mọi người đều thấy kế hoạch này tốt.
如果下雨，他们去哪里？ / 图书馆 / 山上 / 机场
___明天下雨，我们就不爬山。 / 如果 / 已经 / 一边
Đưa ra kế hoạch A và kế hoạch B theo một điều kiện.

Tương phản và nhượng bộ
虽然,但是,容易,难,努力
虽然……但是……
虽然 thừa nhận một thực tế; 但是 đưa ý trái với dự đoán thông thường. Hai vế phải có quan hệ tương phản hợp lý.
虽然汉字很难，但是我想继续学。 / Suīrán Hànzì hěn nán, dànshì wǒ xiǎng jìxù xué. / Tuy chữ Hán khó nhưng tôi muốn học tiếp.
小安觉得写汉字不容易。虽然每天只有二十分钟，但是他一直坚持练习。三个月后，他已经能写很多常用字了。 / Tiểu An thấy viết chữ Hán không dễ. Dù mỗi ngày chỉ có hai mươi phút, bạn ấy vẫn kiên trì luyện tập. Ba tháng sau, bạn đã viết được nhiều chữ thông dụng.
小安怎样提高写字能力？ / 每天坚持练习 / 完全不练习 / 只买书不学习
___很难，但是我会努力。 / 虽然 / 所以 / 为了
Viết hai câu nhượng bộ về việc học hoặc công việc.

Thay đổi theo thời gian
越来越,健康,习惯,锻炼,身体
越来越 + tính từ / động từ tâm lý
越来越 diễn tả mức độ tăng dần theo thời gian. Không thêm 很 ngay sau 越来越. So với 比, mẫu này nhấn mạnh xu hướng chứ không so hai đối tượng.
我的身体越来越好了。 / Wǒ de shēntǐ yuèláiyuè hǎo le. / Sức khỏe của tôi ngày càng tốt.
以前我很少运动，总觉得累。现在我每天走路半小时，也早一点儿睡觉。坚持两个月以后，身体越来越好了。 / Trước đây tôi ít vận động, luôn thấy mệt. Nay tôi đi bộ nửa giờ mỗi ngày và ngủ sớm hơn. Sau hai tháng kiên trì, sức khỏe ngày càng tốt.
作者现在每天做什么？ / 走路半小时 / 睡到中午 / 完全不运动
天气___热了。 / 越来越 / 一边 / 把
Mô tả hai điều đang thay đổi trong cuộc sống.

Hai hoạt động song song
一边,音乐,做饭,练习,习惯
一边……一边……
Hai vế 一边 diễn tả hành động cùng xảy ra, thường cùng một chủ thể. Không dùng cho hai việc nối tiếp đã hoàn thành.
她一边听音乐，一边做饭。 / Tā yìbiān tīng yīnyuè, yìbiān zuò fàn. / Cô ấy vừa nghe nhạc vừa nấu ăn.
姐姐喜欢一边听音乐一边做饭。我做作业时却不听音乐，因为我容易分心。我们有不同的学习和生活习惯。 / Chị thích vừa nghe nhạc vừa nấu ăn. Còn tôi không nghe nhạc khi làm bài vì dễ mất tập trung. Chúng tôi có thói quen học và sinh hoạt khác nhau.
作者做作业时为什么不听音乐？ / 容易分心 / 没有音乐 / 姐姐不喜欢音乐
她一边听音乐，___做饭。 / 一边 / 以前 / 已经
Mô tả một tình huống làm hai việc cùng lúc và nhận xét hiệu quả.

Ôn tập: Học tập có kế hoạch
计划,复习,考试,提高,完成
先……再……最后……
先、再、最后 sắp xếp trình tự. Kết hợp điều kiện, lý do hoặc kết quả để viết một đoạn rõ ràng; tránh dùng 一边 cho các bước nối tiếp.
我先复习生词，再做练习。 / Wǒ xiān fùxí shēngcí, zài zuò liànxí. / Tôi ôn từ mới trước rồi làm bài tập.
下个月有考试。我计划每天先复习生词，再读课文，最后做练习。如果遇到不懂的问题，就问老师。我希望通过这个方法提高成绩。 / Tháng sau có kỳ thi. Tôi định mỗi ngày ôn từ mới trước, rồi đọc bài, cuối cùng làm bài tập. Nếu gặp vấn đề chưa hiểu thì hỏi giáo viên. Tôi mong cách này giúp cải thiện điểm số.
计划中的第一步是什么？ / 复习生词 / 做练习 / 问老师
我先复习，___做练习。 / 再 / 比 / 被
Viết kế hoạch học một tuần với trình tự và cách xử lý khó khăn.
'''
UNITS[4] = '''
Mục đích và hành động
为了,提高,能力,交流,机会
为了 + mục tiêu，chủ ngữ + hành động
为了 nêu mục đích chưa nhất thiết đạt được; 因为 nêu nguyên nhân. Sau 为了 thường là cụm động từ thể hiện mục tiêu có chủ đích.
为了提高口语，我每天和同学交流。 / Wèile tígāo kǒuyǔ, wǒ měitiān hé tóngxué jiāoliú. / Để nâng cao khẩu ngữ, tôi trao đổi với bạn học mỗi ngày.
小陈以前不敢开口说汉语。为了提高交流能力，他报名参加了学校的中文活动。开始时，他只能说简单的句子，但每次都认真听别人怎么表达。几个月后，他已经能主动介绍自己的家乡了。 / Trước đây Tiểu Trần không dám nói tiếng Trung. Để nâng cao khả năng giao tiếp, anh đăng ký hoạt động tiếng Trung của trường. Ban đầu anh chỉ nói được câu đơn giản nhưng luôn chú ý cách người khác diễn đạt. Vài tháng sau, anh đã có thể chủ động giới thiệu quê mình.
小陈参加活动的主要目的是什么？ / 提高交流能力 / 获得旅游机会 / 减少学习时间
___提高口语，我每天练习。 / 为了 / 因为 / 虽然
Viết mục tiêu học tập, hai hành động cụ thể và cách tự đánh giá.

Bổ sung thông tin và tăng tiến
不仅,而且,经验,丰富,负责
不仅……而且……
Mẫu này thêm ý thứ hai mạnh hơn hoặc bổ sung ý thứ nhất. Khi hai vế khác chủ ngữ, 不仅 thường đứng trước chủ ngữ thứ nhất.
她不仅经验丰富，而且很负责。 / Tā bùjǐn jīngyàn fēngfù, érqiě hěn fùzé. / Cô ấy không chỉ giàu kinh nghiệm mà còn rất có trách nhiệm.
公司需要一位新的项目负责人。大家推荐李老师，因为她不仅经验丰富，而且愿意听不同的意见。遇到困难时，她总是先了解情况，再和同事一起讨论办法。因此，年轻同事也很信任她。 / Công ty cần người phụ trách dự án mới. Mọi người đề cử cô Lý vì cô không chỉ giàu kinh nghiệm mà còn lắng nghe ý kiến khác. Khi khó khăn, cô tìm hiểu tình hình rồi bàn cách giải quyết với đồng nghiệp. Vì vậy các đồng nghiệp trẻ cũng tin tưởng cô.
大家推荐李老师的原因是什么？ / 有经验并愿意听取意见 / 从不与同事讨论 / 只重视自己的想法
她不仅认真，___很负责。 / 而且 / 所以 / 虽然
Giới thiệu một người hoặc một sản phẩm bằng hai ưu điểm có dẫn chứng.

Điều kiện đủ và điều kiện cần
只要,只有,坚持,成功,方法
只要……就…… / 只有……才……
只要 nêu điều kiện đủ để có kết quả trong ngữ cảnh; 只有 nêu điều kiện cần. Không đảo 就 và 才 một cách máy móc vì sẽ thay đổi quan hệ logic.
只有认真准备，才能做好这次报告。 / Zhǐyǒu rènzhēn zhǔnbèi, cái néng zuò hǎo zhè cì bàogào. / Chỉ khi chuẩn bị nghiêm túc mới có thể làm tốt báo cáo này.
学校的实验室规定，只有完成安全培训，学生才能独立使用设备。小周想参加实验，所以先报名培训。老师提醒他，学会操作还不够，做实验时也必须遵守规定。这些要求是为了保护每一个人。 / Phòng thí nghiệm quy định sinh viên chỉ được dùng thiết bị độc lập sau khi hoàn thành tập huấn an toàn. Tiểu Châu muốn làm thí nghiệm nên đăng ký tập huấn trước. Giáo viên nhắc biết thao tác chưa đủ, còn phải tuân thủ quy định khi thực hành. Các yêu cầu này nhằm bảo vệ mọi người.
独立使用设备的必要条件是什么？ / 完成安全培训 / 只看设备价格 / 提前买好午饭
只有认真准备，___能做好报告。 / 才 / 就 / 也
Viết một điều kiện cần và một điều kiện đủ trong việc học hoặc làm việc.

Kết quả ngoài dự đoán
却,竟然,原来,以为,结果
以为……，却……
以为 nêu nhận định trước đó, thường được sửa lại sau; 却 làm nổi bật kết quả trái dự đoán. 竟然 nhấn mạnh sự ngạc nhiên, không đơn thuần nối hai sự việc.
我以为他会拒绝，他却答应了。 / Wǒ yǐwéi tā huì jùjué, tā què dāying le. / Tôi tưởng anh ấy sẽ từ chối, vậy mà anh ấy đồng ý.
我以为周末的博物馆一定很安静，所以没有提前预约。到了门口才发现，参观的人竟然排起了长队。原来当天有一个特别的展览。我只好改变计划，下次先查好信息再来。 / Tôi tưởng bảo tàng cuối tuần sẽ yên tĩnh nên không đặt trước. Đến cửa mới thấy người tham quan xếp hàng dài. Hóa ra hôm đó có triển lãm đặc biệt. Tôi đành đổi kế hoạch; lần sau sẽ tìm hiểu thông tin trước khi đến.
作者为什么没有预约？ / 以为博物馆会很安静 / 已经买到了门票 / 不知道博物馆在哪里
我以为他不同意，他___答应了。 / 却 / 所以 / 为了
Kể một lần dự đoán sai, nêu điều bạn đã rút kinh nghiệm.

Lựa chọn và cân nhắc
选择,考虑,适合,或者,还是
Câu hỏi lựa chọn dùng 还是；câu trần thuật thường dùng 或者
还是 yêu cầu chọn giữa các phương án trong câu hỏi. 或者 nêu các khả năng trong câu trần thuật. 还是 còn có nghĩa khác tùy ngữ cảnh nên cần đọc cả câu.
你想坐火车还是坐飞机？ / Nǐ xiǎng zuò huǒchē háishi zuò fēijī? / Bạn muốn đi tàu hỏa hay máy bay?
小林要去外地参加会议。他考虑坐飞机或者坐高铁。飞机虽然快，但机场离家很远。高铁站就在附近，而且车上也能工作。比较时间和费用以后，他决定选择高铁。 / Tiểu Lâm đi tỉnh khác dự hội nghị. Anh cân nhắc máy bay hoặc tàu cao tốc. Máy bay nhanh nhưng sân bay xa nhà. Ga cao tốc ở gần, trên tàu cũng có thể làm việc. So sánh thời gian và chi phí xong, anh chọn tàu cao tốc.
小林最终选择了什么？ / 高铁 / 飞机 / 出租车
你想喝茶___喝咖啡？ / 还是 / 或者 / 因为
So sánh hai lựa chọn và giải thích quyết định bằng ba tiêu chí.

Ước lượng và mức độ
大概,左右,至少,超过,数量
Số lượng + 左右 / 至少 + số lượng
左右 chỉ xấp xỉ; 至少 chỉ giới hạn thấp nhất. Không dùng 左右 khi thông tin cần chính xác tuyệt đối. 大概 còn có thể thể hiện suy đoán.
参加活动的大概有三十人。 / Cānjiā huódòng de dàgài yǒu sānshí rén. / Có khoảng ba mươi người tham gia hoạt động.
社区计划举办读书活动，预计有三十人左右参加。工作人员准备了四十把椅子，并要求每位发言者至少提前十分钟到场。活动开始前，报名人数已经超过三十五人，大家于是又增加了几把椅子。 / Khu dân cư dự kiến tổ chức buổi đọc sách với khoảng ba mươi người. Nhân viên chuẩn bị bốn mươi ghế và yêu cầu người phát biểu đến sớm ít nhất mười phút. Trước giờ bắt đầu, số đăng ký đã vượt ba mươi lăm nên họ kê thêm ghế.
发言者至少要提前多久到场？ / 十分钟 / 三十分钟 / 四十分钟
大约有三十人___参加。 / 左右 / 至少 / 不到
Tóm tắt một sự kiện, phân biệt số ước lượng và yêu cầu tối thiểu.

Đề xuất và thương lượng
建议,意见,商量,安排,接受
要不……吧 / 最好 + động từ
要不……吧 đưa phương án thay thế thân thiện. 最好 đưa lời khuyên, không phải mệnh lệnh tuyệt đối. Giải thích lý do giúp lời đề xuất thuyết phục hơn.
要不我们把会议改到下午吧。 / Yàobù wǒmen bǎ huìyì gǎi dào xiàwǔ ba. / Hay là chúng ta chuyển cuộc họp sang chiều nhé.
原来的会议安排在周一上午，但两位同事那时要接待客户。小王建议改到下午，并提前发邮件询问大家是否方便。经过商量，大家接受了这个安排。这样既照顾了客户，也保证所有成员都能参加讨论。 / Cuộc họp vốn xếp sáng thứ Hai nhưng hai đồng nghiệp phải tiếp khách lúc đó. Tiểu Vương đề nghị chuyển sang chiều và gửi thư hỏi mọi người có tiện không. Sau trao đổi, cả nhóm chấp nhận. Cách này vừa lo được khách hàng vừa giúp đủ thành viên dự thảo luận.
会议为什么改到下午？ / 两位同事上午要接待客户 / 下午没有人参加 / 会议已经取消了
___我们改到下午吧。 / 要不 / 尽管 / 由于
Viết lời đề nghị đổi lịch, nêu lý do và hỏi ý kiến người nhận.

Ôn tập: Giải quyết một vấn đề
原因,办法,解决,效果,总结
问题 → 原因 → 办法 → 结果
Khi trình bày giải pháp, tách việc quan sát được khỏi suy đoán về nguyên nhân. Dùng 首先、其次、因此 để nối ý; kết luận phải dựa vào dữ kiện đã nêu.
我们先找出原因，再讨论解决办法。 / Wǒmen xiān zhǎo chū yuányīn, zài tǎolùn jiějué bànfǎ. / Chúng ta tìm nguyên nhân trước rồi bàn cách giải quyết.
图书馆最近总有人抱怨找不到书。工作人员调查后发现，并不是书太少，而是分类标志不清楚。他们重新设计了指示牌，还增加了查询说明。一个月后，类似的抱怨明显减少。这说明，先找对原因比急着增加资源更重要。 / Gần đây nhiều người phàn nàn không tìm được sách ở thư viện. Khảo sát cho thấy không phải ít sách mà biển phân loại thiếu rõ ràng. Nhân viên làm lại biển chỉ dẫn và thêm hướng dẫn tra cứu. Một tháng sau, phàn nàn giảm rõ rệt. Điều này cho thấy xác định đúng nguyên nhân quan trọng hơn vội tăng nguồn lực.
找不到书的主要原因是什么？ / 分类标志不清楚 / 图书馆完全没有书 / 工作人员不允许查询
我们先找原因，___讨论办法。 / 再 / 却 / 除非
Viết 8–10 câu theo bốn phần: vấn đề, nguyên nhân, giải pháp, kết quả dự kiến.
'''
UNITS[5] = '''
Nêu quan điểm và dẫn chứng
观点,事实,证明,结论,分析
在我看来……；以……为例
在我看来 đánh dấu nhận định cá nhân. 以……为例 đưa dẫn chứng, nhưng một ví dụ chưa đủ chứng minh kết luận áp dụng cho mọi trường hợp.
在我看来，评价方法比单纯比较分数更重要。 / Zài wǒ kàn lái, píngjià fāngfǎ bǐ dānchún bǐjiào fēnshù gèng zhòngyào. / Theo tôi, đánh giá phương pháp quan trọng hơn chỉ so sánh điểm số.
有些人认为，学习时间越长，成绩就一定越好。在我看来，这种说法忽略了方法的作用。以背单词为例，只是反复看词表，未必能在交流中正确使用；如果把词放进句子，再隔几天复习，往往更容易记住。当然，不同学习者的情况并不完全相同。因此，评价学习效果时，既要看投入的时间，也要看实际运用的能力。 / Có người cho rằng học càng lâu thì điểm chắc chắn càng tốt. Theo tôi, nhận định này bỏ qua phương pháp. Chẳng hạn, chỉ nhìn đi nhìn lại danh sách từ chưa chắc giúp dùng đúng khi giao tiếp; đặt từ vào câu rồi ôn cách vài ngày thường dễ nhớ hơn. Tình hình từng người dĩ nhiên không hoàn toàn giống nhau. Vì vậy, đánh giá hiệu quả cần xem cả thời gian đầu tư lẫn khả năng vận dụng.
作者主要反对哪种观点？ / 学习时间能单独决定效果 / 学习方法值得关注 / 运用能力应该被评价
___背单词为例，我们可以比较不同方法。 / 以 / 被 / 把
Viết một quan điểm, một ví dụ và một giới hạn của kết luận.

Nguyên nhân trong văn viết
由于,导致,因素,产生,影响
由于 + nguyên nhân，……；……导致 + kết quả
由于 thường xuất hiện trong văn viết. 导致 nối nguyên nhân với hệ quả, thường là hệ quả không mong muốn. Phân biệt quan hệ nhân quả với việc hai hiện tượng cùng xuất hiện.
由于缺少沟通，项目进度受到了影响。 / Yóuyú quēshǎo gōutōng, xiàngmù jìndù shòudào le yǐngxiǎng. / Do thiếu trao đổi, tiến độ dự án bị ảnh hưởng.
一家公司发现，项目总是比计划完成得晚。最初，管理者认为员工不够努力。但进一步调查显示，各部门对任务的理解并不一致，信息又传递得很慢。由于缺少及时沟通，同样的工作常常被重复完成。公司随后建立了统一的任务记录，并安排定期交流。问题有所改善，不过管理者仍需要继续观察，不能仅凭短期变化就判断所有问题已经解决。 / Một công ty thấy dự án luôn trễ kế hoạch. Ban đầu quản lý cho rằng nhân viên thiếu cố gắng. Khảo sát sâu hơn cho thấy các bộ phận hiểu nhiệm vụ khác nhau và thông tin truyền chậm. Thiếu trao đổi kịp thời khiến công việc bị làm trùng. Công ty dùng bản ghi nhiệm vụ chung và trao đổi định kỳ. Tình hình cải thiện nhưng vẫn cần quan sát, không thể dựa vào thay đổi ngắn hạn để kết luận mọi vấn đề đã hết.
调查发现的主要问题是什么？ / 任务理解不一致且信息传递慢 / 员工全部缺少技能 / 公司完全没有项目
___缺少沟通，进度受到了影响。 / 由于 / 尽管 / 以便
Phân tích một vấn đề, nêu hai nguyên nhân khả dĩ và bằng chứng cần kiểm tra.

Nhượng bộ trong lập luận
尽管,仍然,困难,坚持,价值
尽管……，仍然 / 还是……
尽管 thừa nhận một thực tế bất lợi nhưng kết quả vẫn diễn ra. 即使 thường đưa tình huống giả định. Khi viết, làm rõ điều nào đã biết và điều nào chỉ giả sử.
尽管条件有限，团队仍然坚持完成调查。 / Jǐnguǎn tiáojiàn yǒuxiàn, tuánduì réngrán jiānchí wánchéng diàochá. / Dù điều kiện hạn chế, nhóm vẫn kiên trì hoàn thành khảo sát.
一个学生团队想了解社区老人的出行困难。尽管经费有限，他们仍然利用周末进行访问。为了避免只听到熟人的意见，他们还主动联系了不同小区的居民。调查结果不能代表所有老人，却让团队看到了几个过去忽略的问题。他们据此提出改进建议，并在报告中明确说明了调查范围和限制。 / Một nhóm sinh viên muốn tìm hiểu khó khăn đi lại của người cao tuổi. Dù kinh phí ít, nhóm vẫn phỏng vấn cuối tuần. Để tránh chỉ nghe người quen, họ liên hệ cư dân ở nhiều khu. Kết quả không đại diện mọi người cao tuổi nhưng chỉ ra những vấn đề từng bị bỏ qua. Nhóm đưa đề xuất và ghi rõ phạm vi, giới hạn khảo sát.
团队为什么联系不同小区的居民？ / 避免只听到熟人的意见 / 保证结果代表所有人 / 取消周末访问
尽管经费有限，他们___继续调查。 / 仍然 / 才能 / 以免
Trình bày một nỗ lực trong điều kiện bất lợi, kèm giới hạn của thành quả.

Lựa chọn có đánh đổi
与其,不如,宁可,选择,后果
与其……，不如……
与其 nêu lựa chọn kém mong muốn hơn; 不如 đưa lựa chọn được ưu tiên. Hai vế cần có thể so sánh trong cùng tình huống, không phải hai sự việc ngẫu nhiên.
与其反复抱怨，不如先尝试改变方法。 / Yǔqí fǎnfù bàoyuàn, bùrú xiān chángshì gǎibiàn fāngfǎ. / Thay vì than phiền mãi, chi bằng thử đổi phương pháp trước.
小林毕业后拿到了两份工作邀请。一份工资较高，但工作内容比较单一；另一份收入稍低，却有机会参与不同项目。他没有马上决定，而是向前辈了解长期发展情况。考虑自己的目标后，他选择了第二份工作。他认为，与其只关注眼前收入，不如选择更适合自己成长的环境。不过，这并不意味着相同选择适合每个人。 / Sau tốt nghiệp, Tiểu Lâm nhận hai lời mời. Một việc lương cao nhưng nội dung đơn điệu; việc kia thu nhập thấp hơn một chút nhưng được làm nhiều dự án. Anh hỏi người đi trước về phát triển lâu dài rồi chọn việc thứ hai. Theo anh, thay vì chỉ nhìn thu nhập trước mắt, nên chọn môi trường hợp với sự trưởng thành của mình. Điều đó không có nghĩa lựa chọn này phù hợp mọi người.
小林最重视什么？ / 与个人目标相符的成长机会 / 最高的眼前收入 / 最单一的工作内容
与其抱怨，___改变方法。 / 不如 / 尽管 / 由于
So sánh hai lựa chọn, nêu lợi ích, chi phí và lý do ưu tiên một bên.

Dữ liệu, xu hướng và giới hạn
比例,增长,减少,平均,数据
与……相比……；从……上升到……
与……相比 xác định mốc so sánh. Từ 从 đến 到 chỉ điểm đầu và cuối, còn 增长了 chỉ mức tăng. Luôn nêu đơn vị, thời gian và đối tượng thống kê.
与去年相比，今年的报名人数增加了。 / Yǔ qùnián xiāngbǐ, jīnnián de bàomíng rénshù zēngjiā le. / So với năm ngoái, số người đăng ký năm nay tăng lên.
某阅读活动去年的报名人数是一百人，今年增加到一百二十人，增长了百分之二十。组织者同时发现，实际到场的人数只增加了十人。因此，报名人数的增长并不完全等于参与程度的提高。要评价活动效果，还需要观察参加者是否持续阅读、是否愿意再次参加，而不能只选一个看起来最漂亮的数字。 / Hoạt động đọc sách có một trăm người đăng ký năm ngoái, năm nay tăng lên một trăm hai mươi, tức tăng 20%. Tuy nhiên số thực sự đến chỉ tăng mười người. Vì vậy tăng đăng ký không hoàn toàn đồng nghĩa mức tham gia tăng. Đánh giá hiệu quả còn cần xem họ có đọc đều và muốn tham gia lại không, thay vì chỉ chọn con số đẹp nhất.
报名人数增长了多少？ / 百分之二十 / 百分之一百二十 / 十人
人数从一百人增加___一百二十人。 / 到 / 从 / 与
Viết đoạn mô tả số liệu giả định, phân biệt mức tăng và giá trị cuối.

Điều kiện ngoại lệ
除非,否则,条件,允许,规定
除非……，否则……
除非 nêu ngoại lệ hoặc điều kiện cần để tránh kết quả ở vế 否则. Diễn đạt lại bằng 如果不 giúp kiểm tra logic và tránh hiểu ngược.
除非提前申请，否则不能延长借书时间。 / Chúfēi tíqián shēnqǐng, fǒuzé bù néng yáncháng jiè shū shíjiān. / Trừ khi xin trước, nếu không sẽ không được gia hạn mượn sách.
图书馆规定，读者需要按时归还资料。除非在到期前申请并获得批准，否则不能延长借阅时间。有些读者以为发送申请就自动获得延期，但工作人员提醒，热门资料可能已经被别人预约。制定这一规定，是为了在个人需要和其他读者的使用机会之间取得平衡。 / Thư viện quy định trả tài liệu đúng hạn. Nếu không xin trước hạn và được chấp thuận thì không được gia hạn. Có người tưởng gửi yêu cầu là tự được kéo dài, nhưng nhân viên nhắc tài liệu phổ biến có thể đã được người khác đặt. Quy định nhằm cân bằng nhu cầu cá nhân và cơ hội sử dụng của người khác.
申请延期是否一定会被批准？ / 不一定，还要看预约情况 / 一定会自动批准 / 从来不允许申请
除非提前申请，___不能延期。 / 否则 / 而且 / 甚至
Viết một quy định có ngoại lệ rồi diễn đạt lại bằng câu 如果不.

Tóm tắt không thêm ý
概括,内容,重点,保持,完整
原文指出……；主要原因是……
Tóm tắt giữ chủ thể, sự kiện và quan hệ logic chính. Không thêm đánh giá cá nhân, không đổi 可能 thành 一定 và không biến ý kiến một người thành kết luận chung.
原文指出，方便并不等于适合所有人。 / Yuánwén zhǐchū, fāngbiàn bìng bù děngyú shìhé suǒyǒu rén. / Bài gốc chỉ ra rằng tiện lợi không đồng nghĩa phù hợp với tất cả mọi người.
一家社区中心推出网上预约，年轻居民觉得很方便，但部分老人不会使用。工作人员没有取消网上服务，而是保留了电话和现场预约。几个月后，不同年龄的居民都能找到适合自己的方式。文章以此说明，改进服务不一定要用一种新方式完全替代旧方式，也可以让多种渠道互相补充。 / Trung tâm cộng đồng mở đặt hẹn trực tuyến, người trẻ thấy tiện nhưng một số người cao tuổi không biết dùng. Nhân viên giữ thêm đặt qua điện thoại và tại chỗ thay vì hủy dịch vụ mạng. Vài tháng sau, các nhóm tuổi đều tìm được cách phù hợp. Bài viết minh họa rằng cải thiện dịch vụ không nhất thiết thay hoàn toàn cách cũ; nhiều kênh có thể bổ sung nhau.
哪项最准确地概括文章？ / 多种预约方式可以互相补充 / 网上预约必须全部取消 / 所有居民都只喜欢电话预约
哪种概括符合原文且没有扩大范围？ / 多种预约方式可以互相补充 / 所有老人都拒绝网上预约 / 新技术总会降低服务质量
Tóm tắt đoạn đọc bằng 2–3 câu, sau đó đối chiếu xem có thêm ý ngoài bài không.

Ôn tập: Đề xuất có căn cứ
方案,实施,资源,评价,调整
现状 → 目标 → 方案 → 评价
Một đề xuất cần mục tiêu đo được, hành động khả thi và cách theo dõi. Nêu cả rủi ro hoặc điều kiện để tránh hứa hẹn kết quả tuyệt đối.
我们先小范围实施，再根据反馈调整方案。 / Wǒmen xiān xiǎo fànwéi shíshī, zài gēnjù fǎnkuì tiáozhěng fāng'àn. / Chúng ta triển khai phạm vi nhỏ trước, rồi điều chỉnh theo phản hồi.
学校想减少食物浪费，却不能只要求学生少吃。调查发现，有些学生并不知道每份饭菜的分量。学生会建议先在一个窗口试行小份菜，并清楚标明分量和价格。两周后，再比较剩菜数量、用餐满意度和工作人员的负担。如果效果不错，就逐步扩大范围；如果出现新问题，则先调整，而不是急着宣布成功。 / Trường muốn giảm lãng phí thức ăn nhưng không thể chỉ yêu cầu học sinh ăn ít. Khảo sát thấy một số em không biết khẩu phần. Hội sinh viên đề nghị thử suất nhỏ ở một quầy, ghi rõ lượng và giá. Sau hai tuần, so sánh thức ăn thừa, mức hài lòng và khối lượng việc của nhân viên. Hiệu quả tốt thì mở rộng dần; có vấn đề thì điều chỉnh thay vì vội tuyên bố thành công.
方案首先采取什么行动？ / 在一个窗口试行小份菜 / 立即取消所有大份菜 / 要求所有学生减少饭量
先试行，___根据反馈调整。 / 再 / 尽管 / 除非
Viết đề xuất 120–150 chữ Hán: vấn đề, hành động thử nghiệm, tiêu chí đánh giá.
'''
UNITS[6] = '''
Luận điểm, tiền đề và suy luận
前提,推理,论证,结论,依据
只有在……的前提下，才能……
Phân biệt điều kiện cần, dữ kiện và kết luận. Một lập luận có thể hợp hình thức nhưng kết luận vẫn thiếu chắc chắn nếu tiền đề chưa được chứng minh.
只有在样本具有代表性的前提下，才能作出可靠判断。 / Zhǐyǒu zài yàngběn jùyǒu dàibiǎoxìng de qiántí xià, cái néng zuò chū kěkào pànduàn. / Chỉ khi mẫu có tính đại diện mới có thể đưa ra nhận định đáng tin.
一份调查显示，接受访问的居民大多支持延长图书馆开放时间。有人据此断言，全市居民都有同样的需求。然而，调查只在图书馆门口进行，受访者本来就更可能使用这项服务。结果能够说明常来图书馆的人有这种愿望，却不足以直接代表所有市民。若要扩大结论的适用范围，就应补充不同地区、年龄和使用习惯的样本，并公开调查方式。这并不是否定调查的价值，而是让结论与证据保持相称。 / Khảo sát cho thấy đa số người được hỏi ủng hộ kéo dài giờ thư viện. Có người kết luận toàn thành phố có cùng nhu cầu. Nhưng khảo sát chỉ diễn ra ở cửa thư viện, nơi người được hỏi vốn dễ dùng dịch vụ hơn. Kết quả cho biết mong muốn của người hay đến, chưa đại diện mọi cư dân. Muốn mở rộng kết luận cần thêm mẫu theo khu vực, tuổi và thói quen, đồng thời công khai cách khảo sát. Đây không phải phủ nhận giá trị mà là giữ kết luận tương xứng bằng chứng.
作者质疑的主要是什么？ / 从有限样本推及全体居民 / 图书馆存在使用需求 / 调查完全没有任何价值
“只有在样本具有代表性的前提下，才能推广结论”强调什么？ / 代表性是推广结论的必要条件 / 样本数量多就一定能推广结论 / 任何样本都能代表所有人
Chỉ ra tiền đề còn thiếu trong một kết luận phổ biến và cách kiểm tra nó.

Tương quan không đồng nghĩa nhân quả
相关,因果,干扰,验证,机制
与……相关，不等于由……引起
Hai biến thay đổi cùng nhau có thể do yếu tố thứ ba hoặc nhân quả đảo chiều. Dùng 可能、尚不能 xác định mức chắc chắn thay vì kết luận vượt dữ liệu.
两种现象同时出现，并不意味着存在直接因果关系。 / Liǎng zhǒng xiànxiàng tóngshí chūxiàn, bìng bù yìwèizhe cúnzài zhíjiē yīnguǒ guānxi. / Hai hiện tượng cùng xuất hiện không có nghĩa có quan hệ nhân quả trực tiếp.
某学校发现，经常参加社团的学生平均成绩较高，于是有人建议把参加社团作为提高成绩的唯一办法。这个建议忽略了多种可能：这些学生也许原本就更善于安排时间，家庭支持程度也可能不同。社团活动或许确有帮助，但仅凭这组数据，还无法排除其他因素。更谨慎的做法是追踪同一批学生的变化，比较相近条件下的情况，并说明研究的限制。发现相关关系可以提出问题，却不能替代对原因的验证。 / Một trường thấy học sinh thường tham gia câu lạc bộ có điểm trung bình cao hơn, nên có người đề nghị coi đó là cách duy nhất nâng điểm. Nhưng các em có thể vốn biết quản lý thời gian hơn hoặc nhận hỗ trợ gia đình khác nhau. Câu lạc bộ có thể hữu ích, song dữ liệu này chưa loại trừ yếu tố khác. Cách thận trọng hơn là theo dõi cùng nhóm theo thời gian, so điều kiện gần nhau và nêu giới hạn nghiên cứu. Tương quan giúp đặt câu hỏi chứ không thay việc xác minh nguyên nhân.
作者认为目前的数据能说明什么？ / 两者相关，但原因尚需验证 / 社团是提高成绩的唯一原因 / 家庭支持完全没有影响
“并不意味着存在因果关系”表达什么？ / 现有信息不足以确认因果关系 / 已经证明两者绝不相关 / 已经证明前者一定导致后者
Viết đoạn phản biện một kết luận nhân quả, đưa ra hai giải thích thay thế.

Sắc thái và mức độ khẳng định
未必,难免,显然,倾向,判断
未必 / 不见得 + vị ngữ
未必 nghĩa là không nhất thiết, không phải chắc chắn phủ định. 难免 nói điều khó tránh; 显然 đánh dấu người viết cho là rõ ràng nhưng vẫn cần căn cứ.
表达得越复杂，未必就越有说服力。 / Biǎodá de yuè fùzá, wèibì jiù yuè yǒu shuōfúlì. / Diễn đạt càng phức tạp chưa chắc càng thuyết phục.
在专业讨论中，术语能够提高表达效率，但术语越多，文章未必越严谨。如果作者没有解释概念之间的关系，读者即使认识每个词，也可能无法理解论证。相反，一篇语言朴素、证据清楚的文章，往往更容易让人检验其观点。这里强调的不是排斥专业语言，而是根据读者和目的作出选择。真正的准确，不在于刻意制造理解障碍，而在于让复杂内容得到恰当说明。 / Trong thảo luận chuyên môn, thuật ngữ giúp diễn đạt hiệu quả nhưng nhiều thuật ngữ chưa chắc làm bài chặt chẽ. Không giải thích quan hệ khái niệm thì người đọc biết từng từ vẫn có thể không hiểu lập luận. Bài dùng lời giản dị, bằng chứng rõ thường dễ kiểm tra quan điểm hơn. Ý này không bài xích ngôn ngữ chuyên môn mà đòi chọn theo độc giả và mục đích. Chính xác là giải thích hợp lý nội dung phức tạp, không phải cố tạo rào cản.
文中“未必越严谨”是什么意思？ / 不一定更严谨 / 一定不严谨 / 一定更严谨
哪句与“术语越多，文章未必越严谨”意思最接近？ / 术语多不一定能提高严谨程度 / 只要使用术语，文章就不严谨 / 术语多少完全决定文章质量
Sửa ba câu khẳng định quá mạnh bằng từ chỉ mức độ phù hợp, giữ nguyên ý chính.

Hàm ý và giọng điệu
含义,暗示,语气,场合,意图
言外之意：kết hợp lời nói + ngữ cảnh
Hàm ý cần được suy ra từ bối cảnh và quan hệ người nói. Không gán mỉa mai chỉ vì thấy một từ tích cực; nên phân biệt điều văn bản nói thẳng và điều người đọc suy luận.
这句话表面上是询问，实际上是在提醒。 / Zhè jù huà biǎomiàn shang shì xúnwèn, shíjì shang shì zài tíxǐng. / Câu này bề ngoài là hỏi, thực chất là nhắc nhở.
会议已经超过预定时间，主持人看了一眼时钟，对正在补充细节的同事说：“这些信息很有价值，我们是不是可以先确定今天的结论？”这句话并没有否定同事的工作，却把讨论重点从继续补充转向作出决定。如果只看“信息很有价值”，可能会误以为主持人在鼓励对方无限延长发言。理解这类表达，需要同时注意场合、时间压力和后半句的行动建议，也应避免把礼貌提醒轻率地解释为讽刺。 / Cuộc họp quá giờ, chủ trì nhìn đồng hồ rồi nói với đồng nghiệp đang thêm chi tiết: “Thông tin này rất có giá trị, chúng ta có thể xác định kết luận hôm nay trước không?” Câu nói không phủ nhận công việc mà chuyển trọng tâm sang quyết định. Chỉ nhìn lời khen có thể tưởng chủ trì muốn kéo dài phát biểu. Hiểu đúng cần chú ý bối cảnh, áp lực thời gian và đề nghị hành động, đồng thời không vội coi lời nhắc lịch sự là mỉa mai.
主持人的主要意图是什么？ / 推动讨论形成结论 / 要求无限补充细节 / 否定所有信息的价值
“表面上是询问，实际上是在提醒”区分了什么？ / 话语的形式与交际意图 / 事情发生的先后顺序 / 两位说话者的年龄差异
Phân tích một lời nhắc lịch sự: nghĩa trực tiếp, hàm ý và chứng cứ ngữ cảnh.

Mạch liên kết và phép quy chiếu
衔接,结构,逻辑,指代,层次
这 / 此 / 其 cần có đối tượng quy chiếu rõ
Đại từ và từ nối giúp mạch văn liền lạc khi người đọc xác định được chúng chỉ gì. Một từ nối đúng ngữ pháp vẫn có thể sai quan hệ logic của hai vế.
这一变化既带来了便利，也提出了新的要求。 / Zhè yī biànhuà jì dàilái le biànlì, yě tíchū le xīn de yāoqiú. / Thay đổi này vừa đem lại tiện lợi vừa đặt ra yêu cầu mới.
城市越来越多地使用线上平台处理公共事务，居民不必为每一项手续都到现场排队。这一变化提高了效率，也使数字能力成为获得便利的重要条件。对于不熟悉智能设备的人，单纯增加线上功能未必能改善体验。因此，服务设计还需要保留必要的人工协助。这里的“协助”并非否定技术，而是补足技术无法独立解决的环节。只有把效率与可及性放在一起考虑，改进才不至于让部分人落在后面。 / Thành phố ngày càng dùng nền tảng trực tuyến xử lý việc công, người dân không phải đến xếp hàng cho mọi thủ tục. Thay đổi này tăng hiệu suất nhưng cũng khiến kỹ năng số thành điều kiện hưởng tiện ích. Với người không quen thiết bị, chỉ thêm chức năng mạng chưa chắc cải thiện trải nghiệm. Vì thế cần giữ hỗ trợ con người. Hỗ trợ không phủ nhận công nghệ mà bổ sung phần công nghệ chưa tự giải quyết được. Cân nhắc cả hiệu suất lẫn khả năng tiếp cận mới tránh bỏ lại một số người.
“这一变化”主要指什么？ / 更多公共事务转到线上处理 / 所有人都不使用智能设备 / 完全取消人工协助
要让“这一变化”指代清楚，前文需要什么？ / 一个可以明确识别的变化 / 尽可能多的无关例子 / 完全相反且未解释的结论
Rút gọn một đoạn lặp từ bằng phép quy chiếu nhưng không làm mơ hồ chủ thể.

Phản biện công bằng
反驳,立场,让步,争议,客观
不可否认……，但这并不意味着……
Trước khi phản biện, trình bày đúng ý đối phương và thừa nhận phần có căn cứ. Bác bỏ một kết luận quá rộng không đồng nghĩa phủ nhận toàn bộ hiện tượng.
不可否认，技术提高了效率，但这并不意味着判断可以完全交给机器。 / Bù kě fǒurèn, jìshù tígāo le xiàolǜ, dàn zhè bìng bù yìwèizhe pànduàn kěyǐ wánquán jiāo gěi jīqì. / Không thể phủ nhận công nghệ tăng hiệu suất, nhưng điều đó không có nghĩa giao toàn bộ phán đoán cho máy.
有人主张用自动系统完成所有服务评价，理由是机器不会疲劳，能够保持一致。这个观点指出了自动化的优势，值得认真对待。然而，一致地执行规则不等于规则本身合理。当评价涉及特殊处境或规则尚未覆盖的情况时，仍需要解释和申诉的空间。因此，更有建设性的讨论不是简单地支持或反对自动化，而是明确哪些环节适合自动处理、哪些决定必须允许人工复核，以及出现错误时由谁负责。 / Có người muốn dùng hệ thống tự động cho mọi đánh giá dịch vụ vì máy không mệt và nhất quán. Quan điểm này nêu ưu thế thực của tự động hóa. Tuy nhiên thi hành quy tắc nhất quán không bảo đảm quy tắc hợp lý. Trường hợp đặc biệt hoặc ngoài quy tắc vẫn cần giải thích và khiếu nại. Thảo luận hữu ích hơn là xác định khâu tự động, quyết định cần con người xem lại và trách nhiệm khi có lỗi, thay vì chỉ ủng hộ hay phản đối chung chung.
作者对自动化持什么态度？ / 承认优势，同时要求明确边界和责任 / 完全否定所有自动化 / 认为一致性足以保证合理性
“不可否认……，但这并不意味着……”采用哪种论证方式？ / 先承认合理部分，再限制结论范围 / 先完全否定事实，再重复对方结论 / 不分析证据，直接扩大适用范围
Viết phản biện 150 chữ Hán: trình bày ý đối phương, thừa nhận ưu điểm, nêu giới hạn.

Văn phong và biên tập câu
简洁,准确,冗长,修改,表达
删繁就简：giữ nghĩa, bỏ trùng lặp
Biên tập không chỉ rút ngắn: phải giữ điều kiện, phạm vi và mức chắc chắn. Cụm 可能、部分、在……情况下 có thể cần thiết, không nên xóa để câu trông mạnh hơn.
修改的目标是表达准确，而不只是字数更少。 / Xiūgǎi de mùbiāo shì biǎodá zhǔnquè, ér bù zhǐ shì zìshù gèng shǎo. / Mục tiêu chỉnh sửa là diễn đạt chính xác, không chỉ giảm số chữ.
一位编辑把“在本次调查的受访者中，部分人表示可能愿意再次参加”改成“大家都愿意再次参加”。句子虽然短了，意思却发生了明显变化：调查范围被扩大，“部分”变成“全部”，“可能”也变成了确定态度。这样的修改不能算成功。更合适的表达是“部分受访者表示可能再次参加”。它删去了可以省略的词语，却保留了范围和不确定性。由此可见，简洁必须以忠实于原意为前提，而不是用过度肯定换取表面上的有力。 / Biên tập viên đổi “Trong người tham gia khảo sát này, một số cho biết có thể muốn tham gia lại” thành “Mọi người đều muốn tham gia lại”. Câu ngắn hơn nhưng phạm vi bị mở rộng, một số thành toàn bộ, có thể thành chắc chắn. Cách sửa tốt hơn là “Một số người được hỏi cho biết có thể tham gia lại”, bỏ từ thừa mà giữ phạm vi và độ bất định. Súc tích phải trung thành ý gốc, không đổi sự thận trọng lấy vẻ mạnh mẽ.
原修改最主要的问题是什么？ / 扩大范围并强化了确定性 / 保留了原文全部限制 / 只是减少了重复词语
哪项修改保留了“部分人可能再次参加”的含义？ / 一些人或许会再次参加 / 所有人一定会再次参加 / 没有人愿意再次参加
Biên tập một đoạn 120 chữ xuống 80 chữ và liệt kê những giới hạn nghĩa đã giữ.

Ôn tập: Tổng hợp nhiều góc nhìn
综合,权衡,长期,可行,反思
共识 → 分歧 → 权衡 → 有条件的结论
Tổng hợp không phải ghép các ý rời. Xác định điểm đồng thuận, khác biệt về tiêu chí, đánh đổi và điều kiện áp dụng. Kết luận cần nêu điều còn chưa biết.
在权衡成本与收益之后，我们仍需检验方案的可行性。 / Zài quánhéng chéngběn yǔ shōuyì zhīhòu, wǒmen réng xū jiǎnyàn fāng'àn de kěxíngxìng. / Sau khi cân nhắc chi phí và lợi ích, chúng ta vẫn cần kiểm chứng tính khả thi của phương án.
一座城市讨论是否延长公交运营时间。支持者强调夜间工作者的出行需要，反对者则担心成本增加和部分线路乘客过少。双方其实都希望公共资源得到有效使用，分歧在于如何衡量需求与投入。与其立即全面延长或彻底否决，不如先在需求较明确的线路试行，记录乘客数量、实际成本和其他交通方式的变化。评估还应关注服务是否帮助了原本出行困难的人，而不仅是平均客流。试行不能保证最终成功，却能让下一步决定建立在更充分的证据上。 / Một thành phố bàn kéo dài giờ xe buýt. Bên ủng hộ nhấn mạnh nhu cầu người làm đêm; bên phản đối lo chi phí và tuyến ít khách. Hai bên đều muốn dùng hiệu quả nguồn lực, khác nhau ở cách cân nhu cầu với đầu tư. Thay vì mở rộng ngay hoặc bác bỏ toàn bộ, có thể thử tuyến có nhu cầu rõ, ghi số khách, chi phí và thay đổi phương tiện khác. Đánh giá cần xem người vốn khó đi lại có được giúp không, ngoài lượng khách trung bình. Thử nghiệm không bảo đảm thành công nhưng cung cấp bằng chứng tốt hơn cho quyết định tiếp theo.
双方的共同目标是什么？ / 有效使用公共资源 / 立即取消所有夜班公交 / 不考虑任何成本
“与其立即全面推行，不如先小范围试行”倾向哪种选择？ / 先试行，再根据证据决定下一步 / 不经过评估就全面推行 / 不考虑任何条件而永久否决
Viết 200–250 chữ Hán tổng hợp hai lập trường, một phương án thử và điều kiện đánh giá.
'''

LEVELS = [
    ('Nền tảng đầu tiên', 'Bắt đầu từ câu ngắn: giới thiệu, hỏi đáp và sinh hoạt hằng ngày.', 'Chưa cần kiến thức tiếng Trung. Đọc pinyin chậm, nhận diện thanh điệu trước khi tăng tốc.'),
    ('Giao tiếp quen thuộc', 'Kể việc đã làm, so sánh và trao đổi những kế hoạch đơn giản.', 'Nên hiểu câu 是, 有, 在 và câu hỏi 吗 của HSK 1.'),
    ('Kết nối ý và kể chuyện', 'Nối câu, diễn tả trải nghiệm và giải thích kế hoạch của mình.', 'Ôn cách dùng 了, câu so sánh 比 và các động từ năng nguyện.'),
    ('Diễn đạt có tổ chức', 'Trình bày mục đích, đề xuất, điều kiện và cách giải quyết vấn đề.', 'Nên nắm các liên từ cơ bản, câu 把 và cách kể trải nghiệm.'),
    ('Lập luận và văn viết', 'Phân tích dữ kiện, tóm tắt và đưa đề xuất có căn cứ.', 'Có thể đọc đoạn văn nhiều câu, phân biệt nguyên nhân với điều kiện.'),
    ('Đọc sâu và diễn đạt chính xác', 'Nhận diện hàm ý, kiểm tra lập luận và tổng hợp nhiều góc nhìn.', 'Nên đọc được đoạn nghị luận, tóm tắt trung thành và giải thích quan điểm.')]

def build():
    source = json.loads((DATA / 'hsk20_source.json').read_text(encoding='utf-8'))
    vi = {r['source_id']: r['meaning'] for r in json.loads((DATA / 'hsk20_vi.json').read_text(encoding='utf-8'))}
    words = {}
    for r in source:
        words.setdefault(r['hanzi'], {'hanzi': r['hanzi'], 'pinyin': r['pinyin'], 'meaning': vi[r['source_id']], 'hsk': r['hsk']})
    # Useful combinations and technical terms introduced explicitly in these lessons.
    supplements = {
        '火车': ('huǒchē', 'tàu hỏa'), '越来越': ('yuèláiyuè', 'ngày càng'),
        '只有': ('zhǐyǒu', 'chỉ khi; chỉ có'), '机制': ('jīzhì', 'cơ chế'),
        '简洁': ('jiǎnjié', 'ngắn gọn; súc tích'), '长期': ('chángqī', 'dài hạn'),
        '做饭': ('zuò fàn', 'nấu ăn'), '前提': ('qiántí', 'tiền đề; điều kiện tiên quyết'),
        '因果': ('yīnguǒ', 'nhân quả'), '相关': ('xiāngguān', 'có liên quan'),
        '验证': ('yànzhèng', 'kiểm chứng'), '衔接': ('xiánjiē', 'liên kết; nối tiếp'),
        '指代': ('zhǐdài', 'quy chiếu; chỉ thay'), '冗长': ('rǒngcháng', 'dài dòng'),
        '权衡': ('quánhéng', 'cân nhắc các mặt'), '反思': ('fǎnsī', 'suy ngẫm lại'),
    }
    words.update({h: {'hanzi': h, 'pinyin': p, 'meaning': m, 'hsk': None} for h, (p, m) in supplements.items() if h not in words})
    result = []
    for level, text in UNITS.items():
        blocks = text.strip().split('\n\n')
        assert len(blocks) == 8
        for order, block in enumerate(blocks, 1):
            title, vocab, pattern, note, example, reading, rq, gq, task = block.splitlines()
            vocab = list(dict.fromkeys(vocab.split(',')))
            missing = [w for w in vocab if w not in words]
            if missing:
                raise ValueError(f'{title}: missing {missing}')
            vocabs = [words[w] for w in vocab]
            zh, py, translation = example.split(' / ')
            passage, passage_vi = reading.split(' / ')
            questions = []
            for qi, field in enumerate([gq, rq]):
                prompt, correct, *wrong = field.split(' / ')
                options = [correct, *wrong]
                shift = (level + order + qi) % 3
                options = options[shift:] + options[:shift]
                questions.append({'id': f'q{qi+1}', 'kind': ['grammar', 'reading'][qi], 'prompt': prompt,
                    'options': options, 'answer': options.index(correct),
                    'explanation': (note + ' Ví dụ: ' + zh) if qi == 0 else ('Đối chiếu đoạn đọc: ' + passage_vi)})
            for wi in range(2):
                word = vocabs[wi]
                distractors = [w['meaning'] for w in vocabs if w['meaning'] != word['meaning']][:2]
                options = [word['meaning'], *distractors]
                shift = (level + order + wi) % 3
                options = options[shift:] + options[:shift]
                questions.append({'id': f'q{wi+3}', 'kind': 'vocabulary', 'prompt': f"Trong bài này, {word['hanzi']} ({word['pinyin']}) nghĩa là gì?",
                    'options': options, 'answer': options.index(word['meaning']),
                    'explanation': f"{word['hanzi']} · {word['pinyin']}: {word['meaning']}."})
            result.append({'id': f'hsk{level}-{order:02}', 'hsk': level, 'order': order, 'title': title,
                'minutes': 8 + level * 2 + (2 if order == 8 else 0), 'review': order == 8,
                'objective': 'Vận dụng ' + pattern + ' trong chủ đề ' + title.lower() + '.',
                'vocabulary': vocabs, 'grammar': {'pattern': pattern, 'note': note, 'example': {'hanzi': zh, 'pinyin': py, 'meaning': translation}},
                'reading': {'hanzi': passage, 'meaning': passage_vi}, 'task': task, 'questions': questions})
    payload = {'edition': 'HSK 2.0', 'version': 1,
        'description': '48 bài học bổ trợ do HanziGo biên soạn theo hướng từ cơ bản đến nâng cao; không thay thế toàn bộ giáo trình hoặc đề thi HSK chính thức.',
        'levels': [{'hsk': i, 'title': a, 'description': b, 'prerequisite': c} for i, (a, b, c) in enumerate(LEVELS, 1)],
        'lessons': result}
    (DATA / 'lessons.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'Built {len(result)} lessons, {sum(len(r["questions"]) for r in result)} questions')

if __name__ == '__main__':
    build()
