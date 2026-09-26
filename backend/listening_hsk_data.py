"""Dữ liệu đề thi luyện nghe chuẩn hoá cho HSK 1 đến HSK 6 (18 đề thi phong phú)."""

LISTENING_EXAMS_HSK1_6 = [
    {
        "title": "HSK 1 · Nghe hiểu: Chào hỏi & Làm quen",
        "hsk": 1,
        "duration_minutes": 10,
        "questions": [
            {
                "id": "hsk1_l1_q1",
                "section": "listening",
                "prompt": "Người nói tên là gì?",
                "options": [
                    "Lý Hoa (李华)",
                    "Tiểu Minh (小明)",
                    "Vương Phương (王芳)"
                ],
                "answer": "Lý Hoa (李华)",
                "transcript": "你好！我叫李华，很高兴认识你。(Nǐ hǎo! Wǒ jiào Lǐ Huá, hěn gāoxìng rènshí nǐ.)",
                "explanation": "我叫李华 nghĩa là Tôi tên Lý Hoa. 很高兴认识你 là rất vui được làm quen với bạn.",
                "audio_url": "/api/tts?text=%E4%BD%A0%E5%A5%BD%EF%BC%81%E6%88%91%E5%8F%AB%E6%9D%8E%E5%8D%8E%EF%BC%8C%E5%BE%88%E9%AB%98%E5%85%B4%E8%AE%A4%E8%AF%86%E4%BD%A0%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk1_l1_q2",
                "section": "listening",
                "prompt": "Hôm nay là thứ mấy?",
                "options": [
                    "Thứ sáu (星期五)",
                    "Thứ bảy (星期六)",
                    "Chủ nhật (星期天)"
                ],
                "answer": "Thứ sáu (星期五)",
                "transcript": "今天星期几？今天星期五。(Jīntiān xīngqī jǐ? Jīntiān xīngqīwǔ.)",
                "explanation": "星期五 nghĩa là thứ sáu trong tuần.",
                "audio_url": "/api/tts?text=%E4%BB%8A%E5%A4%A9%E6%98%9F%E6%9C%9F%E5%87%A0%EF%BC%9F%E4%BB%8A%E5%A4%A9%E6%98%9F%E6%9C%9F%E4%BA%94%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk1_l1_q3",
                "section": "listening",
                "prompt": "Người nói muốn uống gì?",
                "options": [
                    "Trà (茶)",
                    "Cà phê (咖啡)",
                    "Nước lọc (水)"
                ],
                "answer": "Trà (茶)",
                "transcript": "你想喝什么？我想喝一杯茶。(Nǐ xiǎng hē shénme? Wǒ xiǎng hē yì bēi chá.)",
                "explanation": "想喝一杯茶 nghĩa là muốn uống một tách trà.",
                "audio_url": "/api/tts?text=%E4%BD%A0%E6%83%B3%E5%96%9D%E4%BB%80%E4%B9%88%EF%BC%9F%E6%88%91%E6%83%B3%E5%96%9D%E4%B8%80%E6%9D%AF%E8%8C%B6%E3%80%82",
                "word_id": None
            }
        ]
    },
    {
        "title": "HSK 1 · Nghe hiểu: Mua sắm & Giá cả",
        "hsk": 1,
        "duration_minutes": 10,
        "questions": [
            {
                "id": "hsk1_l2_q1",
                "section": "listening",
                "prompt": "Táo bao nhiêu tiền một cân?",
                "options": [
                    "Năm tệ (五块)",
                    "Mười tệ (十块)",
                    "Ba tệ (三块)"
                ],
                "answer": "Năm tệ (五块)",
                "transcript": "这个苹果多少钱一斤？五块钱一斤。(Zhè ge píngguǒ duōshao qián yì jīn? Wǔ kuài qián yì jīn.)",
                "explanation": "多少钱 nghĩa là bao nhiêu tiền, 五块钱 là 5 tệ.",
                "audio_url": "/api/tts?text=%E8%BF%99%E4%B8%AA%E8%8B%B9%E6%9E%9C%E5%A4%9A%E5%B0%91%E9%92%B1%E4%B8%80%E6%96%A4%EF%BC%9F%E4%BA%94%E5%9D%97%E9%92%B1%E4%B8%80%E6%96%A4%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk1_l2_q2",
                "section": "listening",
                "prompt": "Người nói mua mấy cốc trà sữa?",
                "options": [
                    "Hai cốc (两杯)",
                    "Một cốc (一杯)",
                    "Ba cốc (三杯)"
                ],
                "answer": "Hai cốc (两杯)",
                "transcript": "服务员，我要两杯奶茶，谢谢。(Fúwùyuán, wǒ yào liǎng bēi nǎichá, xièxie.)",
                "explanation": "两杯 là 2 cốc, 奶茶 là trà sữa.",
                "audio_url": "/api/tts?text=%E6%9C%8D%E5%8A%A1%E5%91%98%EF%BC%8C%E6%88%91%E8%A6%81%E4%B8%A4%E6%9D%AF%E5%A5%B6%E8%8C%B6%EF%BC%8C%E8%B0%A2%E8%B0%A2%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk1_l2_q3",
                "section": "listening",
                "prompt": "Người nói thanh toán bằng cách nào?",
                "options": [
                    "Quét mã điện thoại (扫码)",
                    "Tiền mặt (现金)",
                    "Thẻ tín dụng (刷卡)"
                ],
                "answer": "Quét mã điện thoại (扫码)",
                "transcript": "你可以扫微信二维码付款。(Nǐ kěyǐ sǎo Wēixìn èrwéimǎ fùkuǎn.)",
                "explanation": "扫二维码 nghĩa là quét mã QR để thanh toán.",
                "audio_url": "/api/tts?text=%E4%BD%A0%E5%8F%AF%E4%BB%A5%E6%89%AB%E5%BE%AE%E4%BF%A1%E4%BA%8C%E7%BB%B4%E7%A0%81%E4%BB%98%E6%AC%BE%E3%80%82",
                "word_id": None
            }
        ]
    },
    {
        "title": "HSK 1 · Nghe hiểu: Gia đình & Trường học",
        "hsk": 1,
        "duration_minutes": 10,
        "questions": [
            {
                "id": "hsk1_l3_q1",
                "section": "listening",
                "prompt": "Gia đình người nói có mấy người?",
                "options": [
                    "Bốn người (四口人)",
                    "Ba người (三口人)",
                    "Năm người (五口人)"
                ],
                "answer": "Bốn người (四口人)",
                "transcript": "你家有几口人？我家有四口人：爸爸、妈妈、哥哥和我。(Nǐ jiā yǒu jǐ kǒu rén? Wǒ jiā yǒu sì kǒu rén: bàba, māma, gēge hé wǒ.)",
                "explanation": "四口人 nghĩa là 4 người trong gia đình.",
                "audio_url": "/api/tts?text=%E4%BD%A0%E5%AE%B6%E6%9C%89%E5%87%A0%E5%8F%A3%E4%BA%BA%EF%BC%9F%E6%88%91%E5%AE%B6%E6%9C%89%E5%9B%9B%E5%8F%A3%E4%BA%BA%EF%BC%9A%E7%88%B8%E7%88%B8%E3%80%81%E5%A6%88%E5%A6%88%E3%80%81%E5%93%A5%E5%93%A5%E5%92%8C%E6%88%91%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk1_l3_q2",
                "section": "listening",
                "prompt": "Người nói đi đâu vào ngày mai?",
                "options": [
                    "Đi trường học (去学校)",
                    "Đi bệnh viện (去医院)",
                    "Đi cửa hàng (去商店)"
                ],
                "answer": "Đi trường học (去学校)",
                "transcript": "明天上午我要去学校学习汉语。(Míngtiān shàngwǔ wǒ yào qù xuéxiào xuéxí Hànyǔ.)",
                "explanation": "去学校 nghĩa là đi đến trường học.",
                "audio_url": "/api/tts?text=%E6%98%8E%E5%A4%A9%E4%B8%8A%E5%8D%88%E6%88%91%E8%A6%81%E5%8E%BB%E5%AD%A6%E6%A0%A1%E5%AD%A6%E4%B9%A0%E6%B1%89%E8%AF%AD%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk1_l3_q3",
                "section": "listening",
                "prompt": "Thầy giáo Vương là người nước nào?",
                "options": [
                    "Người Trung Quốc (中国人)",
                    "Người Mỹ (美国人)",
                    "Người Việt Nam (越南人)"
                ],
                "answer": "Người Trung Quốc (中国人)",
                "transcript": "王老师是中国人，他是我们的汉语老师。(Wáng lǎoshī shì Zhōngguó rén, tā shì wǒmen de Hànyǔ lǎoshī.)",
                "explanation": "中国人 nghĩa là người Trung Quốc.",
                "audio_url": "/api/tts?text=%E7%8E%8B%E8%80%81%E5%B8%88%E6%98%AF%E4%B8%AD%E5%9B%BD%E4%BA%BA%EF%BC%8C%E4%BB%96%E6%98%AF%E6%88%91%E4%BB%AC%E7%9A%84%E6%B1%89%E8%AF%AD%E8%80%81%E5%B8%88%E3%80%82",
                "word_id": None
            }
        ]
    },
    {
        "title": "HSK 2 · Nghe hiểu: Đời sống & Di chuyển",
        "hsk": 2,
        "duration_minutes": 12,
        "questions": [
            {
                "id": "hsk2_l1_q1",
                "section": "listening",
                "prompt": "Thời tiết bên ngoài như thế nào?",
                "options": [
                    "Trời đang mưa (下雨)",
                    "Trời nhiều mây (阴天)",
                    "Trời có tuyết (下雪)"
                ],
                "answer": "Trời đang mưa (下雨)",
                "transcript": "外面下雨了，你出门别忘了带雨伞。(Wàimiàn xiàyǔ le, nǐ chūmén bié wàng le dài yǔsǎn.)",
                "explanation": "下雨 nghĩa là trời mưa, 雨伞 là cây ô/dù che mưa.",
                "audio_url": "/api/tts?text=%E5%A4%96%E9%9D%A2%E4%B8%8B%E9%9B%A8%E4%BA%86%EF%BC%8C%E4%BD%A0%E5%87%BA%E9%97%A8%E5%88%AB%E5%BF%98%E4%BA%86%E5%B8%A6%E9%9B%A8%E4%BC%9E%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk2_l1_q2",
                "section": "listening",
                "prompt": "Đi xe buýt đến ga xe lửa mất bao lâu?",
                "options": [
                    "Nửa tiếng (半个小时)",
                    "Một tiếng (一个小时)",
                    "Mười lăm phút (十五分钟)"
                ],
                "answer": "Nửa tiếng (半个小时)",
                "transcript": "从这里坐公共汽车去火车站需要半个小时。(Cóng zhèlǐ zuò gōnggòng qìchē qù huǒchēzhàn xūyào bàn gè xiǎoshí.)",
                "explanation": "公共汽车 là xe buýt, 半个小时 là nửa giờ (30 phút).",
                "audio_url": "/api/tts?text=%E4%BB%8E%E8%BF%99%E9%87%8C%E5%9D%90%E5%85%AC%E5%85%B1%E6%B1%BD%E8%BD%A6%E5%8E%BB%E7%81%AB%E8%BD%A6%E7%AB%99%E9%9C%80%E8%A6%81%E5%8D%8A%E4%B8%AA%E5%B0%8F%E6%97%B6%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk2_l1_q3",
                "section": "listening",
                "prompt": "Người nói đang tìm đồ vật gì?",
                "options": [
                    "Điện thoại di động (手机)",
                    "Ví tiền (钱包)",
                    "Chìa khóa (钥匙)"
                ],
                "answer": "Điện thoại di động (手机)",
                "transcript": "你看见我的手机了吗？我记得放在桌子上了。(Nǐ kànjiàn wǒ de shǒujī le ma? Wǒ jìdé fàng zài zhuōzi shàng le.)",
                "explanation": "手机 là điện thoại di động, 桌子上 là trên bàn.",
                "audio_url": "/api/tts?text=%E4%BD%A0%E7%9C%8B%E8%A7%81%E6%88%91%E7%9A%84%E6%89%8B%E6%9C%BA%E4%BA%86%E5%90%97%EF%BC%9F%E6%88%91%E8%AE%B0%E5%BE%97%E6%94%BE%E5%9C%A8%E6%A1%8C%E5%AD%90%E4%B8%8A%E4%BA%86%E3%80%82",
                "word_id": None
            }
        ]
    },
    {
        "title": "HSK 2 · Nghe hiểu: Ẩm thực & Nhà hàng",
        "hsk": 2,
        "duration_minutes": 12,
        "questions": [
            {
                "id": "hsk2_l2_q1",
                "section": "listening",
                "prompt": "Món cá hôm nay có vị như thế nào?",
                "options": [
                    "Hơi cay một chút (有点儿辣)",
                    "Rất ngọt (很甜)",
                    "Không mặn không nhạt (不咸)"
                ],
                "answer": "Hơi cay một chút (有点儿辣)",
                "transcript": "今天的这条鱼做得很新鲜，但是有点儿辣。(Jīntiān de zhè tiáo yú zuò de hěn xīnxiān, dànshì yǒudiǎnr là.)",
                "explanation": "有点儿辣 nghĩa là hơi cay một chút.",
                "audio_url": "/api/tts?text=%E4%BB%8A%E5%A4%A9%E7%9A%84%E8%BF%99%E6%9D%A1%E9%B1%BC%E5%81%9A%E5%BE%97%E5%BE%88%E6%96%B0%E9%B2%9C%EF%BC%8C%E4%BD%86%E6%98%AF%E6%9C%89%E7%82%B9%E5%84%BF%E8%BE%A3%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk2_l2_q2",
                "section": "listening",
                "prompt": "Buổi trưa họ quyết định ăn món gì?",
                "options": [
                    "Sủi cảo (饺子)",
                    "Mì sợi (面条)",
                    "Cơm chiên (炒饭)"
                ],
                "answer": "Sủi cảo (饺子)",
                "transcript": "今天中午天气太热了，我们一起去吃饺子吧。(Jīntiān zhōngwǔ tiānqì tài rè le, wǒmen yìqǐ qù chī jiǎozi ba.)",
                "explanation": "吃饺子 nghĩa là ăn sủi cảo.",
                "audio_url": "/api/tts?text=%E4%BB%8A%E5%A4%A9%E4%B8%AD%E5%8D%88%E5%A4%A9%E6%B0%94%E5%A4%AA%E7%83%AD%E4%BA%86%EF%BC%8C%E6%88%91%E4%BB%AC%E4%B8%80%E8%B5%B7%E5%8E%BB%E5%90%83%E9%A5%BA%E5%AD%90%E5%90%A7%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk2_l2_q3",
                "section": "listening",
                "prompt": "Người phụ nữ muốn uống loại đồ uống nào?",
                "options": [
                    "Nước ép dưa hấu (西瓜汁)",
                    "Cà phê đá (冰咖啡)",
                    "Trà xanh (绿茶)"
                ],
                "answer": "Nước ép dưa hấu (西瓜汁)",
                "transcript": "我不喝茶，请给我来一杯西瓜汁，谢谢。(Wǒ bù hē chá, qǐng gěi wǒ lái yì bēi xīguāzhī, xièxie.)",
                "explanation": "西瓜汁 nghĩa là nước ép dưa hấu.",
                "audio_url": "/api/tts?text=%E6%88%91%E4%B8%8D%E5%96%9D%E8%8C%B6%EF%BC%8C%E8%AF%B7%E7%BB%99%E6%88%91%E6%9D%A5%E4%B8%80%E6%9D%AF%E8%A5%BF%E7%93%9C%E6%B1%81%EF%BC%8C%E8%B0%A2%E8%B0%A2%E3%80%82",
                "word_id": None
            }
        ]
    },
    {
        "title": "HSK 2 · Nghe hiểu: Sức khỏe & Thể thao",
        "hsk": 2,
        "duration_minutes": 12,
        "questions": [
            {
                "id": "hsk2_l3_q1",
                "section": "listening",
                "prompt": "Bác sĩ khuyên bệnh nhân làm gì?",
                "options": [
                    "Uống nhiều nước và nghỉ ngơi (多喝水多休息)",
                    "Đi chạy bộ mỗi ngày (每天跑步)",
                    "Uống thuốc ba lần (吃三次药)"
                ],
                "answer": "Uống nhiều nước và nghỉ ngơi (多喝水多休息)",
                "transcript": "你感冒了，这几天一定要多喝温水，多休息。(Nǐ gǎnmào le, zhè jǐ tiān yídìng yào duō hē wēnshuǐ, duō xiūxi.)",
                "explanation": "多喝水多休息 nghĩa là uống nhiều nước và nghỉ ngơi nhiều.",
                "audio_url": "/api/tts?text=%E4%BD%A0%E6%84%9F%E5%86%92%E4%BA%86%EF%BC%8C%E8%BF%99%E5%87%A0%E5%A4%A9%E4%B8%80%E5%AE%9A%E8%A6%81%E5%A4%9A%E5%96%9D%E6%B8%A9%E6%B0%B4%EF%BC%8C%E5%A4%9A%E4%BC%91%E6%81%AF%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk2_l3_q2",
                "section": "listening",
                "prompt": "Họ thường bơi lội vào thời gian nào?",
                "options": [
                    "Chiều thứ bảy (星期六下午)",
                    "Sáng chủ nhật (星期天上午)",
                    "Tối thứ sáu (星期五晚上)"
                ],
                "answer": "Chiều thứ bảy (星期六下午)",
                "transcript": "我和朋友经常在星期六下午去体育馆游泳。(Wǒ hé péngyou jīngcháng zài xīngqīliù xiàwǔ qù tǐyùguǎn yóuyǒng.)",
                "explanation": "星期六下午 là chiều thứ bảy, 游泳 là bơi lội.",
                "audio_url": "/api/tts?text=%E6%88%91%E5%92%8C%E6%9C%8B%E5%8F%8B%E7%BB%8F%E5%B8%B8%E5%9C%A8%E6%98%9F%E6%9C%9F%E5%85%AD%E4%B8%8B%E5%8D%88%E5%8E%BB%E4%BD%93%E8%82%B2%E9%A6%86%E6%B8%B8%E6%B3%B3%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk2_l3_q3",
                "section": "listening",
                "prompt": "Tại sao hôm nay anh ấy không đi đá bóng?",
                "options": [
                    "Chân bị đau (脚疼)",
                    "Bận làm việc (工作忙)",
                    "Trời mưa to (下大雨)"
                ],
                "answer": "Chân bị đau (脚疼)",
                "transcript": "昨天跑步跑太久了，今天我的脚很疼，不能去踢足球了。(Zuótiān pǎobù pǎo tài jiǔ le, jīntiān wǒ de jiǎo hěn téng, bù néng qù tī zúqiú le.)",
                "explanation": "脚很疼 nghĩa là chân rất đau, không thể đi đá bóng.",
                "audio_url": "/api/tts?text=%E6%98%A8%E5%A4%A9%E8%B7%91%E6%AD%A5%E8%B7%91%E5%A4%AA%E4%B9%85%E4%BA%86%EF%BC%8C%E4%BB%8A%E5%A4%A9%E6%88%91%E7%9A%84%E8%84%9A%E5%BE%88%E7%96%BC%EF%BC%8C%E4%B8%8D%E8%83%BD%E5%8E%BB%E8%B8%A2%E8%B6%B3%E7%90%83%E4%BA%86%E3%80%82",
                "word_id": None
            }
        ]
    },
    {
        "title": "HSK 3 · Nghe hiểu: Kế hoạch & Du lịch",
        "hsk": 3,
        "duration_minutes": 15,
        "questions": [
            {
                "id": "hsk3_l1_q1",
                "section": "listening",
                "prompt": "Họ dự định đi đâu vào mùa nào?",
                "options": [
                    "Bắc Kinh vào mùa thu",
                    "Thượng Hải vào mùa xuân",
                    "Tây An vào mùa đông"
                ],
                "answer": "Bắc Kinh vào mùa thu",
                "transcript": "我们打算下个月去北京旅游，听说秋天的北京最美丽。(Wǒmen dǎsuàn xià gè yuè qù Běijīng lǚyóu, tīngshuō qiūtiān de Běijīng zuì měilì.)",
                "explanation": "打算 là dự định, 北京 là Bắc Kinh, 秋天 là mùa thu.",
                "audio_url": "/api/tts?text=%E6%88%91%E4%BB%AC%E6%89%93%E7%AE%97%E4%B8%8B%E4%B8%AA%E6%9C%88%E5%8E%BB%E5%8C%97%E4%BA%AC%E6%97%85%E6%B8%B8%EF%BC%8C%E5%90%AC%E8%AF%B4%E7%A7%8B%E5%A4%A9%E7%9A%84%E5%8C%97%E4%BA%AC%E6%9C%80%E7%BE%8E%E4%B8%BD%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk3_l1_q2",
                "section": "listening",
                "prompt": "Tài liệu này đã được xử lý như thế nào?",
                "options": [
                    "Đã kiểm tra kỹ, có thể in (仔细检查过了)",
                    "Chưa hoàn thành cần sửa (还没写完)",
                    "Đã gửi qua email (发邮件了)"
                ],
                "answer": "Đã kiểm tra kỹ, có thể in (仔细检查过了)",
                "transcript": "这份材料我已经仔细检查过了，没有任何问题，可以直接打印。(Zhè fèn cáiliào wǒ yǐjīng zǐxì jiǎnchá guò le, méiyǒu rènhé wèntí, kěyǐ zhíjiē dǎyìn.)",
                "explanation": "仔细检查 nghĩa là kiểm tra cẩn thận, 打印 là in ấn.",
                "audio_url": "/api/tts?text=%E8%BF%99%E4%BB%BD%E6%9D%90%E6%96%99%E6%88%91%E5%B7%B2%E7%BB%8F%E4%BB%94%E7%BB%86%E6%A3%80%E6%9F%A5%E8%BF%87%E4%BA%86%EF%BC%8C%E6%B2%A1%E6%9C%89%E4%BB%BB%E4%BD%95%E9%97%AE%E9%A2%98%EF%BC%8C%E5%8F%AF%E4%BB%A5%E7%9B%B4%E6%8E%A5%E6%89%93%E5%8D%B0%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk3_l1_q3",
                "section": "listening",
                "prompt": "Người nói muốn gọi đồ uống gì?",
                "options": [
                    "Một tách trà xanh nóng (一杯热绿茶)",
                    "Một ly nước cam lạnh (一杯冰橙汁)",
                    "Một cốc cà phê đen (一杯黑咖啡)"
                ],
                "answer": "Một tách trà xanh nóng (一杯热绿茶)",
                "transcript": "外面的风很大，我想喝一杯热绿茶暖和一下身体。(Wàimiàn de fēng hěn dà, wǒ xiǎng hē yì bēi rè lǜchá nuǎnhuo yíxià shēntǐ.)",
                "explanation": "热绿茶 là trà xanh nóng, 暖和 là ấm áp.",
                "audio_url": "/api/tts?text=%E5%A4%96%E9%9D%A2%E7%9A%84%E9%A3%8E%E5%BE%88%E5%A4%A7%EF%BC%8C%E6%88%91%E6%83%B3%E5%96%9D%E4%B8%80%E6%9D%AF%E7%83%AD%E7%BB%BF%E8%8C%B6%E6%9A%96%E5%92%8C%E4%B8%80%E4%B8%8B%E8%BA%AB%E4%BD%93%E3%80%82",
                "word_id": None
            }
        ]
    },
    {
        "title": "HSK 3 · Nghe hiểu: Công việc & Văn phòng",
        "hsk": 3,
        "duration_minutes": 15,
        "questions": [
            {
                "id": "hsk3_l2_q1",
                "section": "listening",
                "prompt": "Cuộc họp chiều nay bắt đầu lúc mấy giờ?",
                "options": [
                    "Hai giờ rưỡi (两点半)",
                    "Ba giờ (三点)",
                    "Hai giờ (两点)"
                ],
                "answer": "Hai giờ rưỡi (两点半)",
                "transcript": "王经理通知，下午的会议推迟到两点半在二楼会议室举行。(Wáng jīnglǐ tōngzhī, xiàwǔ de huìyì tuīchí dào liǎng diǎn bàn zài èr lóu huìyìshì jǔxíng.)",
                "explanation": "推迟到两点半 nghĩa là hoãn đến 2 giờ 30 phút.",
                "audio_url": "/api/tts?text=%E7%8E%8B%E7%BB%8F%E7%90%86%E9%80%9A%E7%9F%A5%EF%BC%8C%E4%B8%8B%E5%8D%88%E7%9A%84%E4%BC%9A%E8%AE%AE%E6%8E%A8%E8%BF%9F%E5%88%B0%E4%B8%A4%E7%82%B9%E5%8D%8A%E5%9C%A8%E4%BA%8C%E6%A5%BC%E4%BC%9A%E8%AE%AE%E5%AE%A4%E4%B8%BE%E8%A1%8C%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk3_l2_q2",
                "section": "listening",
                "prompt": "Người nói yêu cầu gửi tài liệu bằng cách nào?",
                "options": [
                    "Gửi qua thư điện tử (发电子邮箱)",
                    "In ra giấy mang đến (打印送来)",
                    "Gửi tin nhắn điện thoại (发短信)"
                ],
                "answer": "Gửi qua thư điện tử (发电子邮箱)",
                "transcript": "请在下班之前把修改好的报告发到我的电子邮箱里。(Qǐng zài xiàbān zhīqián bǎ xiūgǎi hǎo de bàogào fā dào wǒ de diànzǐ yóuxiāng lǐ.)",
                "explanation": "发到我的电子邮箱 nghĩa là gửi vào hộp thư điện tử của tôi.",
                "audio_url": "/api/tts?text=%E8%AF%B7%E5%9C%A8%E4%B8%8B%E7%8F%AD%E4%B9%8B%E5%89%8D%E6%8A%8A%E4%BF%AE%E6%94%B9%E5%A5%BD%E7%9A%84%E6%8A%A5%E5%91%8A%E5%8F%91%E5%88%B0%E6%88%91%E7%9A%84%E7%94%B5%E5%AD%90%E9%82%AE%E7%AE%B1%E9%87%8C%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk3_l2_q3",
                "section": "listening",
                "prompt": "Đồng nghiệp mới đến từ thành phố nào?",
                "options": [
                    "Thượng Hải (上海)",
                    "Quảng Châu (广州)",
                    "Thành Đô (成都)"
                ],
                "answer": "Thượng Hải (上海)",
                "transcript": "新来的李同事以前在上海工作，业务能力非常出色。(Xīn lái de Lǐ tóngshì yǐqián zài Shànghǎi gōngzuò, yèwù nénglì fēicháng chūsè.)",
                "explanation": "在上海工作 nghĩa là từng làm việc tại Thượng Hải.",
                "audio_url": "/api/tts?text=%E6%96%B0%E6%9D%A5%E7%9A%84%E6%9D%8E%E5%90%8C%E4%BA%8B%E4%BB%A5%E5%89%8D%E5%9C%A8%E4%B8%8A%E6%B5%B7%E5%B7%A5%E4%BD%9C%EF%BC%8C%E4%B8%9A%E5%8A%A1%E8%83%BD%E5%8A%9B%E9%9D%9E%E5%B8%B8%E5%87%BA%E8%89%B2%E3%80%82",
                "word_id": None
            }
        ]
    },
    {
        "title": "HSK 3 · Nghe hiểu: Mua sắm & Đời sống",
        "hsk": 3,
        "duration_minutes": 15,
        "questions": [
            {
                "id": "hsk3_l3_q1",
                "section": "listening",
                "prompt": "Chiếc áo len màu gì được người nói chọn mua?",
                "options": [
                    "Màu xanh lam (蓝色的)",
                    "Màu đỏ (红色的)",
                    "Màu vàng (黄色的)"
                ],
                "answer": "Màu xanh lam (蓝色的)",
                "transcript": "我觉得这件红色的有点大，那件蓝色的更适合你，就买蓝色的吧。(Wǒ juéde zhè jiàn hóngsè de yǒudiǎn dà, nà jiàn lánsè de gèng shìhé nǐ, jiù mǎi lánsè de ba.)",
                "explanation": "更适合你 là hợp với bạn hơn, 蓝色的 nghĩa là màu xanh lam.",
                "audio_url": "/api/tts?text=%E6%88%91%E8%A7%89%E5%BE%97%E8%BF%99%E4%BB%B6%E7%BA%A2%E8%89%B2%E7%9A%84%E6%9C%89%E7%82%B9%E5%A4%A7%EF%BC%8C%E9%82%A3%E4%BB%B6%E8%93%9D%E8%89%B2%E7%9A%84%E6%9B%B4%E9%80%82%E5%90%88%E4%BD%A0%EF%BC%8C%E5%B0%B1%E4%B9%B0%E8%93%9D%E8%89%B2%E7%9A%84%E5%90%A7%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk3_l3_q2",
                "section": "listening",
                "prompt": "Họ quyết định đi xem phim vào khi nào?",
                "options": [
                    "Tối chủ nhật (星期天晚上)",
                    "Chiều thứ bảy (星期六下午)",
                    "Tối thứ sáu (星期五晚上)"
                ],
                "answer": "Tối chủ nhật (星期天晚上)",
                "transcript": "周末我们一起去看那部新电影吧，星期天晚上的票已经买好了。(Zhōumò wǒmen yìqǐ qù kàn nà bù xīn diànyǐng ba, xīngqītiān wǎnshang de piào yǐjīng mǎi hǎo le.)",
                "explanation": "星期天晚上 nghĩa là tối chủ nhật.",
                "audio_url": "/api/tts?text=%E5%91%A8%E6%9C%AB%E6%88%91%E4%BB%AC%E4%B8%80%E8%B5%B7%E5%8E%BB%E7%9C%8B%E9%82%A3%E9%83%A8%E6%96%B0%E7%94%B5%E5%BD%B1%E5%90%A7%EF%BC%8C%E6%98%9F%E6%9C%9F%E5%A4%A9%E6%99%9A%E4%B8%8A%E7%9A%84%E7%A5%A8%E5%B7%B2%E7%BB%8F%E4%B9%B0%E5%A5%BD%E4%BA%86%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk3_l3_q3",
                "section": "listening",
                "prompt": "Món quà sinh nhật tặng mẹ là gì?",
                "options": [
                    "Một chiếc khăn quàng cổ (一条围巾)",
                    "Một đôi giày (一双鞋)",
                    "Một chiếc đồng hồ (一块手表)"
                ],
                "answer": "Một chiếc khăn quàng cổ (一条围巾)",
                "transcript": "下周是妈妈的生日，我给她买了一条羊毛围巾作为礼物。(Xià zhōu shì māma de shēngrì, wǒ gěi tā mǎi le yì tiáo yángmáo wéijīn zuòwéi lǐwù.)",
                "explanation": "围巾 nghĩa là chiếc khăn quàng cổ.",
                "audio_url": "/api/tts?text=%E4%B8%8B%E5%91%A8%E6%98%AF%E5%A6%88%E5%A6%88%E7%9A%84%E7%94%9F%E6%97%A5%EF%BC%8C%E6%88%91%E7%BB%99%E5%A5%B9%E4%B9%B0%E4%BA%86%E4%B8%80%E6%9D%A1%E7%BE%8A%E6%AF%9B%E5%9B%B4%E5%B7%BE%E4%BD%9C%E4%B8%BA%E7%A4%BC%E7%89%A9%E3%80%82",
                "word_id": None
            }
        ]
    },
    {
        "title": "HSK 4 · Nghe hiểu: Phỏng vấn & Đời sống văn phòng",
        "hsk": 4,
        "duration_minutes": 20,
        "questions": [
            {
                "id": "hsk4_l1_q1",
                "section": "listening",
                "prompt": "Buổi phỏng vấn được sắp xếp vào lúc nào và ở đâu?",
                "options": [
                    "9h30 sáng mai tại phòng họp số 3",
                    "10h00 sáng mai tại phòng giám đốc",
                    "2h30 chiều mai tại hội trường tầng 1"
                ],
                "answer": "9h30 sáng mai tại phòng họp số 3",
                "transcript": "王经理，明天的面试安排在上午九点半的三号会议室，应聘者的简历我已经打印好了。(Wáng jīnglǐ, míngtiān de miànshì ānpái zài shàngwǔ jiǔ diǎn bàn de sān hào huìyìshì, yìngpìnzhě de jiǎnlì wǒ yǐjīng dǎyìn hǎo le.)",
                "explanation": "九点半 là 9h30, 三号会议室 là phòng họp số 3.",
                "audio_url": "/api/tts?text=%E7%8E%8B%E7%BB%8F%E7%90%86%EF%BC%8C%E6%98%8E%E5%A4%A9%E7%9A%84%E9%9D%A2%E8%AF%95%E5%AE%89%E6%8E%92%E5%9C%A8%E4%B8%8A%E5%8D%88%E4%B9%9D%E7%82%B9%E5%8D%8A%E7%9A%84%E4%B8%89%E5%8F%B7%E4%BC%9A%E8%AE%AE%E5%AE%A4%EF%BC%8C%E5%BA%94%E8%81%98%E8%80%85%E7%9A%84%E7%AE%80%E5%8E%86%E6%88%91%E5%B7%B2%E7%BB%8F%E6%89%93%E5%8D%B0%E5%A5%BD%E4%BA%86%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk4_l1_q2",
                "section": "listening",
                "prompt": "Theo đoạn văn, thói quen đọc sách mang lại lợi ích gì?",
                "options": [
                    "Làm phong phú tri thức và giảm căng thẳng công việc",
                    "Giúp ngủ nhanh và không bị mệt mỏi",
                    "Nâng cao thu nhập và mở rộng quan hệ"
                ],
                "answer": "Làm phong phú tri thức và giảm căng thẳng công việc",
                "transcript": "养成良好的阅读习惯不仅能丰富知识，还能缓解日常工作环境中的压力，让心态更加平和。(Yǎngchéng liánghǎo de yuèdú xíguàn bùjǐn néng fēngfù zhīshi, hái néng huǎnjiě rìcháng gōngzuò huánjìng zhōng de yālì, ràng xīntài gèngjiā pínghé.)",
                "explanation": "丰富知识 (làm phong phú kiến thức) và 缓解压力 (giảm bớt căng thẳng).",
                "audio_url": "/api/tts?text=%E5%85%BB%E6%88%90%E8%89%AF%E5%A5%BD%E7%9A%84%E9%98%85%E8%AF%BB%E4%B9%A0%E6%83%AF%E4%B8%8D%E4%BB%85%E8%83%BD%E4%B8%B0%E5%AF%8C%E7%9F%A5%E8%AF%86%EF%BC%8C%E8%BF%98%E8%83%BD%E7%BC%93%E8%A7%A3%E6%97%A5%E5%B8%B8%E5%B7%A5%E4%BD%9C%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84%E5%8E%8B%E5%8A%9B%EF%BC%8C%E8%AE%A9%E5%BF%83%E6%80%81%E6%9B%B4%E5%8A%A0%E5%B9%B3%E5%92%8C%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk4_l1_q3",
                "section": "listening",
                "prompt": "Tại sao người nói muốn đổi vé máy bay?",
                "options": [
                    "Vì công ty đột xuất sắp xếp cuộc họp quan trọng vào sáng thứ hai",
                    "Vì thời tiết xấu chuyến bay bị hoãn",
                    "Vì sức khỏe không tốt cần đi khám bệnh"
                ],
                "answer": "Vì công ty đột xuất sắp xếp cuộc họp quan trọng vào sáng thứ hai",
                "transcript": "因为周一早上公司临时安排了一个重要会议，我想把原定周日晚上的航班改签到周一下午。(Yīnwèi zhōuyī zǎoshang gōngsī línshí ānpái le yí gè zhòngyào huìyì, wǒ xiǎng bǎ yuándìng zhōurì wǎnshang de hángbān gǎiqiān dào zhōuyī xiàwǔ.)",
                "explanation": "临时安排了重要会议 nghĩa là đột xuất có cuộc họp quan trọng, 改签航班 là đổi chuyến bay.",
                "audio_url": "/api/tts?text=%E5%9B%A0%E4%B8%BA%E5%91%A8%E4%B8%80%E6%97%A9%E4%B8%8A%E5%85%AC%E5%8F%B8%E4%B8%B4%E6%97%B6%E5%AE%89%E6%8E%92%E4%BA%86%E4%B8%80%E4%B8%AA%E9%87%8D%E8%A6%81%E4%BC%9A%E8%AE%AE%EF%BC%8C%E6%88%91%E6%83%B3%E6%8A%8A%E5%8E%9F%E5%AE%9A%E5%91%A8%E6%97%A5%E6%99%9A%E4%B8%8A%E7%9A%84%E8%88%AA%E7%8F%AD%E6%94%B9%E7%AD%BE%E5%88%B0%E5%91%A8%E4%B8%80%E4%B8%8B%E5%8D%88%E3%80%82",
                "word_id": None
            }
        ]
    },
    {
        "title": "HSK 4 · Nghe hiểu: Giao tiếp & Mối quan hệ",
        "hsk": 4,
        "duration_minutes": 20,
        "questions": [
            {
                "id": "hsk4_l2_q1",
                "section": "listening",
                "prompt": "Yếu tố quan trọng nhất để duy trì tình bạn chân thành là gì?",
                "options": [
                    "Sự thấu hiểu và tôn trọng lẫn nhau (互相理解与尊重)",
                    "Thường xuyên tặng quà cáp (经常送礼物)",
                    "Có cùng sở thích du lịch (爱好相同)"
                ],
                "answer": "Sự thấu hiểu và tôn trọng lẫn nhau (互相理解与尊重)",
                "transcript": "真正的友谊不在于平时的甜言蜜语，而在于遇到困难时能够互相信任、互相理解与尊重。(Zhēnzhèng de yǒuyì bú zàiyú píngshí de tiányán mìyǔ, ér zàiyú yù dào kùnnan shí nénggòu hùxiāng xìnrèn, hùxiāng lǐjiě yǔ zūnzhòng.)",
                "explanation": "互相信任、互相理解与尊重 là tin cậy, thấu hiểu và tôn trọng lẫn nhau.",
                "audio_url": "/api/tts?text=%E7%9C%9F%E6%AD%A3%E7%9A%84%E5%8F%8B%E8%B0%8A%E4%B8%8D%E5%9C%A8%E4%BA%8E%E5%B9%B3%E6%97%B6%E7%9A%84%E7%94%9C%E8%A8%80%E8%9C%9C%E8%AF%AD%EF%BC%8C%E8%80%8C%E5%9C%A8%E4%BA%8E%E9%81%87%E5%88%B0%E5%9B%B0%E9%9A%BE%E6%97%B6%E8%83%BD%E5%A4%9F%E4%BA%92%E7%9B%B8%E4%BF%A1%E4%BB%BB%E3%80%81%E4%BA%92%E7%9B%B8%E7%90%86%E8%A7%A3%E4%B8%8E%E5%B0%8A%E9%87%8D%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk4_l2_q2",
                "section": "listening",
                "prompt": "Khi gặp thất bại trong công việc, thái độ đúng đắn là gì?",
                "options": [
                    "Tổng kết bài học kinh nghiệm và kiên trì nỗ lực (总结经验，坚持努力)",
                    "Trách móc đồng nghiệp (推卸责任)",
                    "Từ bỏ và chuyển việc khác ngay (立刻放弃)"
                ],
                "answer": "Tổng kết bài học kinh nghiệm và kiên trì nỗ lực (总结经验，坚持努力)",
                "transcript": "面对工作中的暂时失利，我们不应该灰心丧气，而要及时总结经验教训，坚持继续努力。(Miànduì gōngzuò zhōng de zànshí shīlì, wǒmen bù yīnggāi huīxīn sàngqì, ér yào jíshí zǒngjié jīngyàn jiàoxùn, jiānchí jìxù nǔlì.)",
                "explanation": "总结经验教训 nghĩa là đúc kết kinh nghiệm bài học, 坚持 là kiên trì.",
                "audio_url": "/api/tts?text=%E9%9D%A2%E5%AF%B9%E5%B7%A5%E4%BD%9C%E4%B8%AD%E7%9A%84%E6%9A%82%E6%97%B6%E5%A4%B1%E5%88%A9%EF%BC%8C%E6%88%91%E4%BB%AC%E4%B8%8D%E5%BA%94%E8%AF%A5%E7%81%B0%E5%BF%83%E4%B8%A7%E6%B0%94%EF%BC%8C%E8%80%8C%E8%A6%81%E5%8F%8A%E6%97%B6%E6%80%BB%E7%BB%93%E7%BB%8F%E9%AA%8C%E6%95%99%E8%AE%AD%EF%BC%8C%E5%9D%9A%E6%8C%81%E7%BB%A7%E7%BB%AD%E5%8A%AA%E5%8A%9B%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk4_l2_q3",
                "section": "listening",
                "prompt": "Tại sao trong hợp tác kinh doanh lại cần giữ chữ tín?",
                "options": [
                    "Vì chữ tín là nền tảng để hợp tác lâu dài (诚信是长期合作的基础)",
                    "Để kiếm lợi nhuận trước mắt (为了短期利益)",
                    "Để cạnh tranh bằng giá rẻ (降低价格)"
                ],
                "answer": "Vì chữ tín là nền tảng để hợp tác lâu dài (诚信是长期合作的基础)",
                "transcript": "在商业合作中，诚信是立足之本。只有言出必行，才能赢得客户长期的信任与支持。(Zài shāngyè hézuò zhōng, chéngxìn shì lìzú zhī běn. Zhǐyǒu yán chū bì xíng, cái néng yíngdé kèhù chángqī de xìnrèn yǔ zhīchí.)",
                "explanation": "诚信 (sự uy tín, chân thành) là nền móng để có được sự tin tưởng lâu dài.",
                "audio_url": "/api/tts?text=%E5%9C%A8%E5%95%86%E4%B8%9A%E5%90%88%E4%BD%9C%E4%B8%AD%EF%BC%8C%E8%AF%9A%E4%BF%A1%E6%98%AF%E7%AB%8B%E8%B6%B3%E4%B9%8B%E6%9C%AC%E3%80%82%E5%8F%AA%E6%9C%89%E8%A8%80%E5%87%BA%E5%BF%85%E8%A1%8C%EF%BC%8C%E6%89%8D%E8%83%BD%E8%B5%A2%E5%BE%97%E5%AE%A2%E6%88%B7%E9%95%BF%E6%9C%9F%E7%9A%84%E4%BF%A1%E4%BB%BB%E4%B8%8E%E6%94%AF%E6%8C%81%E3%80%82",
                "word_id": None
            }
        ]
    },
    {
        "title": "HSK 4 · Nghe hiểu: Công nghệ & Môi trường",
        "hsk": 4,
        "duration_minutes": 20,
        "questions": [
            {
                "id": "hsk4_l3_q1",
                "section": "listening",
                "prompt": "Hành động nào giúp giảm thiểu ô nhiễm rác thải nhựa?",
                "options": [
                    "Tự mang túi vải đi siêu thị (自带布袋购物)",
                    "Dùng nhiều túi nilon một lần (多用塑料袋)",
                    "Vứt rác bừa bãi nơi công cộng (乱扔垃圾)"
                ],
                "answer": "Tự mang túi vải đi siêu thị (自带布袋购物)",
                "transcript": "为了保护我们生活的环境，大家在去超市购物时应当尽量自带环保布袋，减少塑料袋的使用。(Wèile bǎohù wǒmen shēnghuó de huánjìng, dàjiā zài qù chāoshì gòuwù shí yīngdāng jǐnliàng zìdài huánbǎo bùdài, jiǎnshǎo sùliàodài de shǐyòng.)",
                "explanation": "自带环保布袋 nghĩa là tự mang túi vải bảo vệ môi trường.",
                "audio_url": "/api/tts?text=%E4%B8%BA%E4%BA%86%E4%BF%9D%E6%8A%A4%E6%88%91%E4%BB%AC%E7%94%9F%E6%B4%BB%E7%9A%84%E7%8E%AF%E5%A2%83%EF%BC%8C%E5%A4%A7%E5%AE%B6%E5%9C%A8%E5%8E%BB%E8%B6%85%E5%B8%82%E8%B4%AD%E7%89%A9%E6%97%B6%E5%BA%94%E5%BD%93%E5%B0%BD%E9%87%8F%E8%87%AA%E5%B8%A6%E7%8E%AF%E4%BF%9D%E5%B8%83%E8%A2%8B%EF%BC%8C%E5%87%8F%E5%B0%91%E5%A1%91%E6%96%99%E8%A2%8B%E7%9A%84%E4%BD%BF%E7%94%A8%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk4_l3_q2",
                "section": "listening",
                "prompt": "Ưu điểm lớn nhất của sách điện tử được nhắc tới là gì?",
                "options": [
                    "Tiện lợi mang theo và tiết kiệm giấy (携带方便，节约纸张)",
                    "Giá thành đắt đỏ (价格昂贵)",
                    "Khó đọc trên màn hình (屏幕刺眼)"
                ],
                "answer": "Tiện lợi mang theo và tiết kiệm giấy (携带方便，节约纸张)",
                "transcript": "电子书不仅携带方便、存储量巨大，而且减少了纸张印刷，对森林资源的保护起到了积极作用。(Diànzǐshū bùjǐn xiédài fāngbiàn, cúnchúliàng jùdà, érqiě jiǎnshǎo le zhǐzhāng yìnshuā, duì sēnlín zīyuán de bǎohù qǐ dào le jījí zuòyòng.)",
                "explanation": "携带方便 (tiện mang theo) và 节约纸张 (tiết kiệm giấy in).",
                "audio_url": "/api/tts?text=%E7%94%B5%E5%AD%90%E4%B9%A6%E4%B8%8D%E4%BB%85%E6%90%BA%E5%B8%A6%E6%96%B9%E4%BE%BF%E3%80%81%E5%AD%98%E5%82%A8%E9%87%8F%E5%B7%A8%E5%A4%A7%EF%BC%8C%E8%80%8C%E4%B8%94%E5%87%8F%E5%B0%91%E4%BA%86%E7%BA%B8%E5%BC%A0%E5%8D%B0%E5%88%B7%EF%BC%8C%E5%AF%B9%E6%A3%AE%E6%9E%97%E8%B5%84%E6%BA%90%E7%9A%84%E4%BF%9D%E6%8A%A4%E8%B5%B7%E5%88%B0%E4%BA%86%E7%A7%AF%E6%9E%81%E4%BD%9C%E7%94%A8%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk4_l3_q3",
                "section": "listening",
                "prompt": "Thông điệp tiết kiệm điện trong gia đình là gì?",
                "options": [
                    "Tắt các thiết bị điện khi ra khỏi phòng (随手关灯关电器)",
                    "Mở điều hòa cả ngày nhiệt độ thấp (整天开低温空调)",
                    "Bật đèn sáng khắp nhà (全开灯光)"
                ],
                "answer": "Tắt các thiết bị điện khi ra khỏi phòng (随手关灯关电器)",
                "transcript": "节约用电要从日常生活中的点滴做起，离开房间时随手关灯关掉电源，既安全又环保。(Jiéyuē yòng diàn yào cóng rìcháng shēnghuó zhōng de diǎndī zuò qǐ, líkāi fángjiān shí suíshǒu guāndēng guāndiào diànyuán, jì ānquán yòu huánbǎo.)",
                "explanation": "随手关灯 nghĩa là tiện tay tắt đèn khi ra khỏi phòng.",
                "audio_url": "/api/tts?text=%E8%8A%82%E7%BA%A6%E7%94%A8%E7%94%B5%E8%A6%81%E4%BB%8E%E6%97%A5%E5%B8%B8%E7%94%9F%E6%B4%BB%E4%B8%AD%E7%9A%84%E7%82%B9%E6%BB%B4%E5%81%9A%E8%B5%B7%EF%BC%8C%E7%A6%BB%E5%BC%80%E6%88%BF%E9%97%B4%E6%97%B6%E9%9A%8F%E6%89%8B%E5%85%B3%E7%81%AF%E5%85%B3%E6%8E%89%E7%94%B5%E6%BA%90%EF%BC%8C%E6%97%A2%E5%AE%89%E5%85%A8%E5%8F%88%E7%8E%AF%E4%BF%9D%E3%80%82",
                "word_id": None
            }
        ]
    },
    {
        "title": "HSK 5 · Nghe hiểu: Kinh tế xã hội & Quản lý thời gian",
        "hsk": 5,
        "duration_minutes": 25,
        "questions": [
            {
                "id": "hsk5_l1_q1",
                "section": "listening",
                "prompt": "Theo đoạn văn, sự phát triển của thanh toán di động đem lại kết quả gì?",
                "options": [
                    "Ra ngoài không cần mang tiền mặt vẫn đáp ứng mọi nhu cầu sinh hoạt",
                    "Làm giảm chi tiêu của người tiêu dùng",
                    "Gây khó khăn cho các trung tâm thương mại truyền thống"
                ],
                "answer": "Ra ngoài không cần mang tiền mặt vẫn đáp ứng mọi nhu cầu sinh hoạt",
                "transcript": "随着移动支付的普及，人们出门即使不带现金，也能轻松满足所有需求。从乘坐公交、便利店购物到缴纳水电费，手机几乎涵盖了日常生活的所有场景。(Suízhe yídòng zhīfù de pǔjí, rénmen chūmén jíshǐ bú dài xiànjīn, yě néng qīngsōng mǎnzú suǒyǒu xūqiú. Cóng chéngzuò gōngjiāo, biànlìdiàn gòuwù dào jiǎonà shuǐdiànfèi, shǒujī jīhū hángài le rìcháng shēnghuó de suǒyǒu chǎngjǐng.)",
                "explanation": "不带现金也能轻松满足所有需求 là không mang tiền mặt vẫn thỏa mãn được mọi nhu cầu.",
                "audio_url": "/api/tts?text=%E9%9A%8F%E7%9D%80%E7%A7%BB%E5%8A%A8%E6%94%AF%E4%BB%98%E7%9A%84%E6%99%AE%E5%8F%8A%EF%BC%8C%E4%BA%BA%E4%BB%AC%E5%87%BA%E9%97%A8%E5%8D%B3%E4%BD%BF%E4%B8%8D%E5%B8%A6%E7%8E%B0%E9%87%91%EF%BC%8C%E4%B9%9F%E8%83%BD%E8%BD%BB%E6%9D%BE%E6%BB%A1%E8%B6%B3%E6%89%80%E6%9C%89%E9%9C%80%E6%B1%82%E3%80%82%E4%BB%8E%E4%B9%98%E5%9D%90%E5%85%AC%E4%BA%A4%E3%80%81%E4%BE%BF%E5%88%A9%E5%BA%97%E8%B4%AD%E7%89%A9%E5%88%B0%E7%BC%B4%E7%BA%B3%E6%B0%B4%E7%94%B5%E8%B4%B9%EF%BC%8C%E6%89%8B%E6%9C%BA%E5%87%A0%E4%B9%8E%E6%B6%B5%E7%9B%96%E4%BA%86%E6%97%A5%E5%B8%B8%E7%94%9F%E6%B4%BB%E7%9A%84%E6%89%80%E6%9C%89%E5%9C%BA%E6%99%AF%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk5_l1_q2",
                "section": "listening",
                "prompt": "Để nổi bật trong cạnh tranh thị trường, doanh nghiệp cần ưu tiên điều gì?",
                "options": [
                    "Không ngừng thúc đẩy đổi mới công nghệ và nâng cao chất lượng dịch vụ",
                    "Cắt giảm tối đa chi phí nhân sự và đào tạo",
                    "Chỉ tập trung vào quảng cáo trên truyền thông"
                ],
                "answer": "Không ngừng thúc đẩy đổi mới công nghệ và nâng cao chất lượng dịch vụ",
                "transcript": "面对激烈的市场竞争，企业只有不断推动技术创新、提升服务品质，才能在行业变革中占据优势地位，实现可持续的长远发展。(Miànduì jīliè de shìchǎng jìngzhēng, qǐyè zhǐyǒu bùduàn tuīdòng jìshù chuàngxīn, tíshēng fúwù pǐnzhì, cái néng zài hángyè biàngé zhōng zhànjù yōushì dìwèi, shíxiàn kěchíxù de chángyuǎn fāzhǎn.)",
                "explanation": "技术创新 (đổi mới công nghệ) và 服务品质 (chất lượng dịch vụ) là chìa khóa chiếm lĩnh ưu thế.",
                "audio_url": "/api/tts?text=%E9%9D%A2%E5%AF%B9%E6%BF%80%E7%83%88%E7%9A%84%E5%B8%82%E5%9C%BA%E7%AB%9E%E4%BA%89%EF%BC%8C%E4%BC%81%E4%B8%9A%E5%8F%AA%E6%9C%89%E4%B8%8D%E6%96%AD%E6%8E%A8%E5%8A%A8%E6%8A%80%E6%9C%AF%E5%88%9B%E6%96%B0%E3%80%81%E6%8F%90%E5%8D%87%E6%9C%8D%E5%8A%A1%E5%93%81%E8%B4%A8%EF%BC%8C%E6%89%8D%E8%83%BD%E5%9C%A8%E8%A1%8C%E4%B8%9A%E5%8F%98%E9%9D%A9%E4%B8%AD%E5%8D%A0%E6%8D%AE%E4%BC%98%E5%8A%BF%E5%9C%B0%E4%BD%8D%EF%BC%8C%E5%AE%9E%E7%8E%B0%E5%8F%AF%E6%8C%81%E7%BB%AD%E7%9A%84%E9%95%BF%E8%BF%9C%E5%8F%91%E5%B1%95%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk5_l1_q3",
                "section": "listening",
                "prompt": "Bí quyết để cân bằng công việc và cuộc sống theo diễn giả là gì?",
                "options": [
                    "Lập kế hoạch khoa học và phân định mức độ ưu tiên công việc",
                    "Làm thêm giờ vào cuối tuần để bù đắp công việc",
                    "Nghỉ phép thường xuyên không thông báo"
                ],
                "answer": "Lập kế hoạch khoa học và phân định mức độ ưu tiên công việc",
                "transcript": "在快节奏的工作环境中，要想保持工作与生活的平衡，关键在于科学合理地规划时间，明确轻重缓急，避免被琐事分散宝贵的注意力。(Zài kuài jiézòu de gōngzuò huánjìng zhōng, yào xiǎng bǎochí gōngzuò yǔ shēnghuó de pínghéng, guānjiàn zàiyú kēxué hélǐ de guīhuà shíjiān, míngquè qīngzhòng huǎnjí, bìmiǎn bèi suǒshì fēnsàn bǎoguì de zhùyìlì.)",
                "explanation": "科学规划时间 (quy hoạch thời gian khoa học) và 明确轻重缓急 (rõ ràng việc gấp/việc quan trọng).",
                "audio_url": "/api/tts?text=%E5%9C%A8%E5%BF%AB%E8%8A%82%E5%A5%8F%E7%9A%84%E5%B7%A5%E4%BD%9C%E7%8E%AF%E5%A2%83%E4%B8%AD%EF%BC%8C%E8%A6%81%E6%83%B3%E4%BF%9D%E6%8C%81%E5%B7%A5%E4%BD%9C%E4%B8%8E%E7%94%9F%E6%B4%BB%E7%9A%84%E5%B9%B3%E8%A1%A1%EF%BC%8C%E5%85%B3%E9%94%AE%E5%9C%A8%E4%BA%8E%E7%A7%91%E5%AD%A6%E5%90%88%E7%90%86%E5%9C%B0%E8%A7%84%E5%88%92%E6%97%B6%E9%97%B4%EF%BC%8C%E6%98%8E%E7%A1%AE%E8%BD%BB%E9%87%8D%E7%BC%93%E6%80%A5%EF%BC%8C%E9%81%BF%E5%85%8D%E8%A2%AB%E7%90%90%E4%BA%8B%E5%88%86%E6%95%A3%E5%AE%9D%E8%B4%B5%E7%9A%84%E6%B3%A8%E6%84%8F%E5%8A%9B%E3%80%82",
                "word_id": None
            }
        ]
    },
    {
        "title": "HSK 5 · Nghe hiểu: Khoa học công nghệ & Đổi mới",
        "hsk": 5,
        "duration_minutes": 25,
        "questions": [
            {
                "id": "hsk5_l2_q1",
                "section": "listening",
                "prompt": "Ứng dụng trí tuệ nhân tạo trong y học mang lại hiệu quả nổi bật nào?",
                "options": [
                    "Hỗ trợ phân tích chẩn đoán hình ảnh chính xác và nhanh chóng",
                    "Thay thế hoàn toàn bác sĩ trong mọi ca phẫu thuật",
                    "Làm giảm chi phí sản xuất tất cả các loại dược phẩm"
                ],
                "answer": "Hỗ trợ phân tích chẩn đoán hình ảnh chính xác và nhanh chóng",
                "transcript": "人工智能在医疗健康领域的深入应用，不仅协助医生快速准确地分析海量医学影像，还大幅缩短了重大疾病的早期筛查周期。(Rén'gōng zhìnéng zài yīliáo jiànkāng lǐngyù de shēnrù yīngyòng, bùjǐn xiézhù yīshēng kuàisù zhǔnquè de fēnxī hǎiliàng yīxué yǐngxiàng, hái dàfú suōduǎn le zhòngdà jíbìng de zǎoqī shāichá zhōuqī.)",
                "explanation": "快速准确地分析海量医学影像 là phân tích hình ảnh y học nhanh và chuẩn xác.",
                "audio_url": "/api/tts?text=%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%9C%A8%E5%8C%BB%E7%96%97%E5%81%A5%E5%BA%B7%E9%A2%86%E5%9F%9F%E7%9A%84%E6%B7%B1%E5%85%A5%E5%BA%94%E7%94%A8%EF%BC%8C%E4%B8%8D%E4%BB%85%E5%8D%8F%E5%8A%A9%E5%8C%BB%E7%94%9F%E5%BF%AB%E9%80%9F%E5%87%86%E7%A1%AE%E5%9C%B0%E5%88%86%E6%9E%90%E6%B5%B7%E9%87%8F%E5%8C%BB%E5%AD%A6%E5%BD%B1%E5%83%8F%EF%BC%8C%E8%BF%98%E5%A4%A7%E5%B9%85%E7%BC%A9%E7%9F%AD%E4%BA%86%E9%87%8D%E5%A4%A7%E7%96%BE%E7%97%85%E7%9A%84%E6%97%A9%E6%9C%9F%E7%AD%9B%E6%9F%A5%E5%91%A8%E6%9C%9F%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk5_l2_q2",
                "section": "listening",
                "prompt": "Vì sao xe năng lượng mới (xe điện) được khuyến khích phát triển mạnh?",
                "options": [
                    "Giảm phát thải khí nhà kính và thúc đẩy chuyển đổi năng lượng xanh",
                    "Vì giá thành xe điện rẻ hơn tất cả xe xăng",
                    "Vì không cần trạm sạc điện công cộng"
                ],
                "answer": "Giảm phát thải khí nhà kính và thúc đẩy chuyển đổi năng lượng xanh",
                "transcript": "推广新能源汽车是降低城市碳排放、推动绿色能源转型的核心举措，有助于从根本上改善大气环境质量。(Tuīguǎng xīn néngyuán qìchē shì jiàngdī chéngshì tàn páifàng, tuīdòng lǜsè néngyuán zhuǎnxíng de héxīn jǔcuò, yǒuzhùyú cóng gēnběn shàng gǎishàn dàqì huánjìng zhìliàng.)",
                "explanation": "降低城市碳排放 (giảm phát thải carbon) và 推动绿色能源转型 (chuyển đổi năng lượng xanh).",
                "audio_url": "/api/tts?text=%E6%8E%A8%E5%B9%BF%E6%96%B0%E8%83%BD%E6%BA%90%E6%B1%BD%E8%BD%A6%E6%98%AF%E9%99%8D%E4%BD%8E%E5%9F%8E%E5%B8%82%E7%A2%B3%E6%8E%92%E6%94%BE%E3%80%81%E6%8E%A8%E5%8A%A8%E7%BB%BF%E8%89%B2%E8%83%BD%E6%BA%90%E8%BD%AC%E5%9E%8B%E7%9A%84%E6%A0%B8%E5%BF%83%E4%B8%BE%E6%8E%AA%EF%BC%8C%E6%9C%89%E5%8A%A9%E4%BA%8E%E4%BB%8E%E6%A0%B9%E6%9C%AC%E4%B8%8A%E6%94%B9%E5%96%84%E5%A4%A7%E6%B0%94%E7%8E%AF%E5%A2%83%E8%B4%A8%E9%87%8F%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk5_l2_q3",
                "section": "listening",
                "prompt": "Biện pháp then chốt để bảo vệ thông tin dữ liệu cá nhân là gì?",
                "options": [
                    "Tăng cường ý thức cảnh giác bảo mật và sử dụng mật khẩu phức tạp",
                    "Chia sẻ tài khoản cho bạn bè cùng quản lý",
                    "Lưu mật khẩu vào các trang web công cộng"
                ],
                "answer": "Tăng cường ý thức cảnh giác bảo mật và sử dụng mật khẩu phức tạp",
                "transcript": "防范网络诈骗与保护个人隐私，需要我们时刻保持安全防范意识，设置高强度密码并不在未知平台透露敏感数据。(Fángfàn wǎngluò zhàpiàn yǔ bǎohù gèrén yǐnsī, xūyào wǒmen shíkè bǎochí ānquán fángfàn yìshí, shèzhì gāo qiángdù mìmǎ bìng bú zài wèizhī píngtái tòulù mǐngǎn shùjù.)",
                "explanation": "保持安全防范意识 và 设置高强度密码 (nâng cao cảnh giác và cài mật khẩu mạnh).",
                "audio_url": "/api/tts?text=%E9%98%B2%E8%8C%83%E7%BD%91%E7%BB%9C%E8%AF%88%E9%AA%97%E4%B8%8E%E4%BF%9D%E6%8A%A4%E4%B8%AA%E4%BA%BA%E9%9A%90%E7%A7%81%EF%BC%8C%E9%9C%80%E8%A6%81%E6%88%91%E4%BB%AC%E6%97%B6%E5%88%BB%E4%BF%9D%E6%8C%81%E5%AE%89%E5%85%A8%E9%98%B2%E8%8C%83%E6%84%8F%E8%AF%86%EF%BC%8C%E8%AE%BE%E7%BD%AE%E9%AB%98%E5%BC%BA%E5%BA%A6%E5%AF%86%E7%A0%81%E5%B9%B6%E4%B8%8D%E5%9C%A8%E6%9C%AA%E7%9F%A5%E5%B9%B3%E5%8F%B0%E9%80%8F%E9%9C%B2%E6%95%8F%E6%84%9F%E6%95%B0%E6%8D%AE%E3%80%82",
                "word_id": None
            }
        ]
    },
    {
        "title": "HSK 5 · Nghe hiểu: Nghệ thuật & Đời sống tinh thần",
        "hsk": 5,
        "duration_minutes": 25,
        "questions": [
            {
                "id": "hsk5_l3_q1",
                "section": "listening",
                "prompt": "Tinh thần cốt lõi của nghệ thuật thưởng trà truyền thống là gì?",
                "options": [
                    "Sự tĩnh lặng nội tâm và thanh lọc tâm hồn (追求内心的宁静与澄澈)",
                    "Uống trà để giữ tỉnh táo làm đêm (单纯为了提神熬夜)",
                    "Sưu tầm bộ ấm trà đắt tiền nhất (追求昂贵的茶具)"
                ],
                "answer": "Sự tĩnh lặng nội tâm và thanh lọc tâm hồn (追求内心的宁静与澄澈)",
                "transcript": "中国茶文化所讲究的茶道精神，不仅在于品尝茶汤的醇厚甘冽，更在于借泡茶品茗的过程，追求内心的平和与纯净。(Zhōngguó chá wénhuà suǒ jiǎngjiu de chádào jīngshén, bùjǐn zàiyú pǐncháng chátāng de chúnhòu gānliè, gèng zàiyú jiè pào chá pǐn míng de guòchéng, zhuīqiú nèixīn de pínghé yǔ chúnjìng.)",
                "explanation": "追求内心的平和与纯净 nghĩa là tìm cầu sự bình hòa và thanh sạch trong tâm trí.",
                "audio_url": "/api/tts?text=%E4%B8%AD%E5%9B%BD%E8%8C%B6%E6%96%87%E5%8C%96%E6%89%80%E8%AE%B2%E7%A9%B6%E7%9A%84%E8%8C%B6%E9%81%93%E7%B2%BE%E7%A5%9E%EF%BC%8C%E4%B8%8D%E4%BB%85%E5%9C%A8%E4%BA%8E%E5%93%81%E5%B0%9D%E8%8C%B6%E6%B1%A4%E7%9A%84%E9%86%87%E5%8E%9A%E7%94%98%E5%86%BD%EF%BC%8C%E6%9B%B4%E5%9C%A8%E4%BA%8E%E5%80%9F%E6%B3%A1%E8%8C%B6%E5%93%81%E8%8C%97%E7%9A%84%E8%BF%87%E7%A8%8B%EF%BC%8C%E8%BF%BD%E6%B1%82%E5%86%85%E5%BF%83%E7%9A%84%E5%B9%B3%E5%92%8C%E4%B8%8E%E7%BA%AF%E5%87%80%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk5_l3_q2",
                "section": "listening",
                "prompt": "Yếu tố quyết định sự bứt phá của cá nhân trong sự nghiệp là gì?",
                "options": [
                    "Sự tập trung bền bỉ và không ngừng học hỏi mở rộng nhận thức",
                    "Chỉ dựa vào may mắn và thời cơ ngẫu nhiên",
                    "Thay đổi định hướng liên tục theo xu hướng ngắn hạn"
                ],
                "answer": "Sự tập trung bền bỉ và không ngừng học hỏi mở rộng nhận thức",
                "transcript": "一个人在专业领域的持续深耕与终身学习，往往决定了他能够达到的职业高度。耐得住寂寞才能守得住繁华。(Yí gè rén zài zhuānyè lǐngyù de chíxù shēngēng yǔ zhōngshēn xuéxí, wǎngwǎng juédìng le tā nénggòu dádào de zhíyè gāodù. Nài de zhù jìmò cái néng shǒu de zhù fánhuá.)",
                "explanation": "持续深耕与终身学习 là kiên trì đào sâu chuyên môn và học tập suốt đời.",
                "audio_url": "/api/tts?text=%E4%B8%80%E4%B8%AA%E4%BA%BA%E5%9C%A8%E4%B8%93%E4%B8%9A%E9%A2%86%E5%9F%9F%E7%9A%84%E6%8C%81%E7%BB%AD%E6%B7%B1%E8%80%95%E4%B8%8E%E7%BB%88%E8%BA%AB%E5%AD%A6%E4%B9%A0%EF%BC%8C%E5%BE%80%E5%BE%80%E5%86%B3%E5%AE%9A%E4%BA%86%E4%BB%96%E8%83%BD%E5%A4%9F%E8%BE%BE%E5%88%B0%E7%9A%84%E8%81%8C%E4%B8%9A%E9%AB%98%E5%BA%A6%E3%80%82%E8%80%90%E5%BE%97%E4%BD%8F%E5%AF%82%E5%AF%9E%E6%89%8D%E8%83%BD%E5%AE%88%E5%BE%97%E4%BD%8F%E7%B9%81%E5%8D%8E%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk5_l3_q3",
                "section": "listening",
                "prompt": "Lời khuyên khi đối mặt với lo âu trong môi trường hiện đại là gì?",
                "options": [
                    "Chấp nhận cảm xúc tự nhiên, vận động thể chất và điều chỉnh kỳ vọng",
                    "Kìm nén hoàn toàn cảm xúc không chia sẻ với ai",
                    "Ngừng làm việc và từ bỏ mọi dự án"
                ],
                "answer": "Chấp nhận cảm xúc tự nhiên, vận động thể chất và điều chỉnh kỳ vọng",
                "transcript": "缓解现代生活带来的焦虑情绪，首先要学会接纳自己的不完美，通过适当的体育锻炼与亲近自然来释放心理压力。(Huǎnjiě xiàndài shēnghuó dài lái de jiāolǜ qíngxù, shǒuxiān yào xuéhuì jiēnà zìjǐ de bù wánměi, tōngguò shìdàng de tǐyù duànliàn yǔ qīnjìn zìrán lái shìfàng xīnlǐ yālì.)",
                "explanation": "接纳不完美 (chấp nhận chưa hoàn hảo) và 体育锻炼 (tập luyện thể thao) để giải tỏa áp lực.",
                "audio_url": "/api/tts?text=%E7%BC%93%E8%A7%A3%E7%8E%B0%E4%BB%A3%E7%94%9F%E6%B4%BB%E5%B8%A6%E6%9D%A5%E7%9A%84%E7%84%A6%E8%99%91%E6%83%85%E7%BB%AA%EF%BC%8C%E9%A6%96%E5%85%88%E8%A6%81%E5%AD%A6%E4%BC%9A%E6%8E%A5%E7%BA%B3%E8%87%AA%E5%B7%B1%E7%9A%84%E4%B8%8D%E5%AE%8C%E7%BE%8E%EF%BC%8C%E9%80%9A%E8%BF%87%E9%80%82%E5%BD%93%E7%9A%84%E4%BD%93%E8%82%B2%E9%94%BB%E7%82%BC%E4%B8%8E%E4%BA%B2%E8%BF%91%E8%87%AA%E7%84%B6%E6%9D%A5%E9%87%8A%E6%94%BE%E5%BF%83%E7%90%86%E5%8E%8B%E5%8A%9B%E3%80%82",
                "word_id": None
            }
        ]
    },
    {
        "title": "HSK 6 · Nghe hiểu: Triết học nhân sinh & Văn hóa nghệ thuật",
        "hsk": 6,
        "duration_minutes": 35,
        "questions": [
            {
                "id": "hsk6_l1_q1",
                "section": "listening",
                "prompt": "Nghệ thuật 'chừa khoảng trắng' (留白) trong tranh thủy mặc mang ngụ ý gì?",
                "options": [
                    "Để lại không gian liên tưởng sâu sắc cho người thưởng thức",
                    "Tiết kiệm mực vẽ và thời gian hoàn thành",
                    "Biểu thị bức tranh chưa được vẽ xong"
                ],
                "answer": "Để lại không gian liên tưởng sâu sắc cho người thưởng thức",
                "transcript": "中国传统水墨画讲究留白艺术，在空白处营造出深邃意境，给观赏者留下了无限的遐想空间，达到‘无声胜有声’的美学境界。(Zhōngguó chuántǒng shuǐmòhuà jiǎngjiu liúbái yìshù, zài kòngbáichù yíngzào chū shēnsuì yìjìng, gěi guānshǎngzhě liú xià le wúxiàn de xiáxiǎng kōngjiān, dádào ‘wúshēng shèng yǒushēng’ de měixué jìngjiè.)",
                "explanation": "留白艺术 tạo ra ý cảnh sâu thẳm, để lại không gian tưởng tượng vô hạn.",
                "audio_url": "/api/tts?text=%E4%B8%AD%E5%9B%BD%E4%BC%A0%E7%BB%9F%E6%B0%B4%E5%A2%A8%E7%94%BB%E8%AE%B2%E7%A9%B6%E7%95%99%E7%99%BD%E8%89%BA%E6%9C%AF%EF%BC%8C%E5%9C%A8%E7%A9%BA%E7%99%BD%E5%A4%84%E8%90%A5%E9%80%A0%E5%87%BA%E6%B7%B1%E9%82%83%E6%84%8F%E5%A2%83%EF%BC%8C%E7%BB%99%E8%A7%82%E8%B5%8F%E8%80%85%E7%95%99%E4%B8%8B%E4%BA%86%E6%97%A0%E9%99%90%E7%9A%84%E9%81%90%E6%83%B3%E7%A9%BA%E9%97%B4%EF%BC%8C%E8%BE%BE%E5%88%B0%E2%80%98%E6%97%A0%E5%A3%B0%E8%83%9C%E6%9C%89%E5%A3%B0%E2%80%99%E7%9A%84%E7%BE%8E%E5%AD%A6%E5%A2%83%E7%95%8C%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk6_l1_q2",
                "section": "listening",
                "prompt": "Câu nói 'Đại trí nhược ngu' (大智若愚) hàm chứa triết lý gì?",
                "options": [
                    "Người thực sự thông tuệ thường khiêm nhường kín đáo, không phô trương",
                    "Người thông minh cần giả vờ ngốc nghếch để trốn tránh trách nhiệm",
                    "Trí tuệ cao chỉ đạt được khi không tiếp thu thêm kiến thức"
                ],
                "answer": "Người thực sự thông tuệ thường khiêm nhường kín đáo, không phô trương",
                "transcript": "真正的智者往往大智若愚，他们不急于彰显自身的才华与锋芒，而是在静水流深中积蓄力量，以从容谦逊的胸怀包容世间万物。(Zhēnzhèng de zhìzhě wǎngwǎng dàzhì ruò yú, tāmen bù jíyú zhāngxiǎn zìshēn de cáihuá yǔ fēngmáng, ér shì zài jìngshuǐ liúshēn zhōng jīxù lìliàng, yǐ cóngróng qiānxùn de xiōnghuái bāoróng shìjiān wànwù.)",
                "explanation": "大智若愚 (bậc đại trí trông như ngờ nghệch) chỉ sự khiêm tốn, không khoe khoang lộ liễu.",
                "audio_url": "/api/tts?text=%E7%9C%9F%E6%AD%A3%E7%9A%84%E6%99%BA%E8%80%85%E5%BE%80%E5%BE%80%E5%A4%A7%E6%99%BA%E8%8B%A5%E6%84%9A%EF%BC%8C%E4%BB%96%E4%BB%AC%E4%B8%8D%E6%80%A5%E4%BA%8E%E5%BD%B0%E6%98%BE%E8%87%AA%E8%BA%AB%E7%9A%84%E6%89%8D%E5%8D%8E%E4%B8%8E%E9%94%8B%E8%8A%92%EF%BC%8C%E8%80%8C%E6%98%AF%E5%9C%A8%E9%9D%99%E6%B0%B4%E6%B5%81%E6%B7%B1%E4%B8%AD%E7%A7%AF%E8%93%84%E5%8A%9B%E9%87%8F%EF%BC%8C%E4%BB%A5%E4%BB%8E%E5%AE%B9%E8%B0%A6%E9%80%8A%E7%9A%84%E8%83%B8%E6%80%80%E5%8C%85%E5%AE%B9%E4%B8%96%E9%97%B4%E4%B8%87%E7%89%A9%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk6_l1_q3",
                "section": "listening",
                "prompt": "Theo diễn giả, nghịch cảnh trong cuộc đời đóng vai trò như thế nào?",
                "options": [
                    "Là cơ hội quý báu để rèn giũa ý chí và nâng cao bản lĩnh",
                    "Là dấu hiệu thất bại hoàn toàn không thể cứu vãn",
                    "Là rào cản khiến con người vĩnh viễn mất đi niềm tin"
                ],
                "answer": "Là cơ hội quý báu để rèn giũa ý chí và nâng cao bản lĩnh",
                "transcript": "面对人生的逆境与坎坷，唯有将其视作磨砺意志的良机，方能在重重困境中砥砺前行，铸就非凡的坚韧与宽广格局。(Miànduì rénshēng de nìjìng yǔ kǎnkě, wéi yǒu jiāng qí shì zuò mólì yìzhì de liángjī, fāng néng zài chóngchóng kùnjìng zhōng dǐlì qiánxíng, zhùjiù fēifán de jiānrèn yǔ kuānguǎng géjú.)",
                "explanation": "磨砺意志的良机 nghĩa là cơ hội tốt để tôi luyện ý chí kiên định.",
                "audio_url": "/api/tts?text=%E9%9D%A2%E5%AF%B9%E4%BA%BA%E7%94%9F%E7%9A%84%E9%80%86%E5%A2%83%E4%B8%8E%E5%9D%8E%E5%9D%B7%EF%BC%8C%E5%94%AF%E6%9C%89%E5%B0%86%E5%85%B6%E8%A7%86%E4%BD%9C%E7%A3%A8%E7%A0%BA%E6%84%8F%E5%BF%97%E7%9A%84%E8%89%AF%E6%9C%BA%EF%BC%8C%E6%96%B9%E8%83%BD%E5%9C%A8%E9%87%8D%E9%87%8D%E5%9B%B0%E5%A2%83%E4%B8%AD%E7%A0%A5%E7%A0%BA%E5%89%8D%E8%A1%8C%EF%BC%8C%E9%93%B8%E5%B0%B1%E9%9D%9E%E5%87%A1%E7%9A%84%E5%9D%9A%E9%9F%A7%E4%B8%8E%E5%AE%BD%E5%B9%BF%E6%A0%BC%E5%B1%80%E3%80%82",
                "word_id": None
            }
        ]
    },
    {
        "title": "HSK 6 · Nghe hiểu: Tư tưởng cổ đại & Văn học truyền thống",
        "hsk": 6,
        "duration_minutes": 35,
        "questions": [
            {
                "id": "hsk6_l2_q1",
                "section": "listening",
                "prompt": "Tư tưởng 'Thượng thiện nhược thủy' (上善若水) của Lão Tử đề cao phẩm chất gì?",
                "options": [
                    "Sự nhu hòa, bao dung và cống hiến thầm lặng không tranh giành",
                    "Sức mạnh hủy diệt ghê gớm của lũ lụt",
                    "Khả năng thích ứng để thủ lợi cho cá nhân"
                ],
                "answer": "Sự nhu hòa, bao dung và cống hiến thầm lặng không tranh giành",
                "transcript": "老子曰：‘上善若水。水善利万物而不争，处众人之所恶，故几于道。’它阐明了谦下包容、滋养万物却不争功利的至高品德。(Lǎozǐ yuē: ‘Shàngshàn ruò shuǐ. Shuǐ shàn lì wànwù ér bù zhēng, chù zhòngrén zhī suǒ è, gù jī yú dào.’ Tā chǎnmíng le qiānxià bāoróng, zīyǎng wànwù què bù zhēng gōnglì de zhìgāo pǐndé.)",
                "explanation": "上善若水 ca ngợi đức tính khiêm nhường, đem lại lợi ích cho vạn vật mà không tranh chấp.",
                "audio_url": "/api/tts?text=%E8%80%81%E5%AD%90%E6%9B%B0%EF%BC%9A%E4%B8%8A%E5%96%84%E8%8B%A5%E6%B0%B4%E3%80%82%E6%B0%B4%E5%96%84%E5%88%A9%E4%B8%87%E7%89%A9%E8%80%8C%E4%B8%8D%E4%BA%89%EF%BC%8C%E5%A4%84%E4%BC%97%E4%BA%BA%E4%B9%8B%E6%89%80%E6%81%B6%EF%BC%8C%E6%95%85%E5%87%A0%E4%BA%8E%E9%81%93%E3%80%82%E5%AE%83%E9%98%90%E6%98%8E%E4%BA%86%E8%B0%A6%E4%B8%8B%E5%8C%85%E5%AE%B9%E3%80%81%E6%BB%8B%E5%85%BB%E4%B8%87%E7%89%A9%E5%8D%B4%E4%B8%8D%E4%BA%89%E5%8A%9F%E5%88%A9%E7%9A%84%E8%87%B3%E9%AB%98%E5%93%81%E5%BE%B7%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk6_l2_q2",
                "section": "listening",
                "prompt": "Đặc trưng lớn nhất của thơ ca thời Đường - Tống là gì?",
                "options": [
                    "Sự dung hợp hoàn hảo giữa tình cảm, cảnh sắc và chiều sâu triết lý",
                    "Chỉ chú trọng vần điệu hình thức mà bỏ qua ý nghĩa",
                    "Chỉ miêu tả cảnh chiến trận hào hùng"
                ],
                "answer": "Sự dung hợp hoàn hảo giữa tình cảm, cảnh sắc và chiều sâu triết lý",
                "transcript": "唐诗宋词的永恒魅力，源于文人骚客将个体的情感寄托、时代的风云变幻与对宇宙生命的哲思巧妙交融，达到了情景交融、天人合一的境界。(Tángshī Sòngcí de yǒnghéng mèilì, yuányú wénrén sāokè jiāng gètǐ de qínggǎn jìtuō, shídài de fēngyún biànhuàn yǔ duì yǔzhòu shēngmìng de zhésī qiǎomiào jiāoróng, dádào le qíngjǐng jiāoróng, tiānrén héyī de jìngjiè.)",
                "explanation": "情景交融、天人合一 biểu thị sự hòa quyện tuyệt đỉnh giữa cảnh sắc, cảm xúc và vũ trụ quan.",
                "audio_url": "/api/tts?text=%E5%94%90%E8%AF%97%E5%AE%8B%E8%AF%8D%E7%9A%84%E6%B0%B8%E6%81%92%E9%AD%85%E5%8A%9B%EF%BC%8C%E6%BA%90%E4%BA%8E%E6%96%87%E4%BA%BA%E9%AA%9A%E5%AE%A2%E5%B0%86%E4%B8%AA%E4%BD%93%E7%9A%84%E6%83%85%E6%84%9F%E5%AF%84%E6%89%98%E3%80%81%E6%97%B6%E4%BB%A3%E7%9A%84%E9%A3%8E%E4%BA%91%E5%8F%98%E5%B9%BB%E4%B8%8E%E5%AF%B9%E5%AE%87%E5%AE%99%E7%94%9F%E5%91%BD%E7%9A%84%E5%93%B2%E6%80%9D%E5%B7%A7%E5%A6%99%E4%BA%A4%E8%9E%8D%EF%BC%8C%E8%BE%BE%E5%88%B0%E4%BA%86%E6%83%85%E6%99%AF%E4%BA%A4%E8%9E%8D%E3%80%81%E5%A4%A9%E4%BA%BA%E5%90%88%E4%B8%80%E7%9A%84%E5%A2%83%E7%95%8C%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk6_l2_q3",
                "section": "listening",
                "prompt": "Hàm ý của câu ngạn ngữ 'Bác quan nhi ước thủ, hậu tích nhi bạc phát' là gì?",
                "options": [
                    "Đọc rộng hiểu nhiều nhưng giữ chắt lọc, tích lũy dồi dào rồi mới phát huy thận trọng",
                    "Càng học nhiều càng hành động vội vàng kiếm lợi",
                    "Chỉ học những điều đơn giản ngắn hạn để đạt kết quả ngay"
                ],
                "answer": "Đọc rộng hiểu nhiều nhưng giữ chắt lọc, tích lũy dồi dào rồi mới phát huy thận trọng",
                "transcript": "苏轼提出的‘博观而约取，厚积而薄发’，告诫治学之人唯有博览群书、去粗取精，在漫长的沉潜积累中夯实根基，方能在关键时刻从容展现实学。(Sū Shì tíchū de ‘Bóguān ér yuēqǔ, hòujī ér bófā’, gàojiè zhìxué zhī rén wéi yǒu bólǎn qúnshū, qùcū qǔjīng, zài màncháng de chénqián jīlěi zhōng hāngshí gēnjī, fāng néng zài guānjiàn shíkè cóngróng zhǎnxiàn shíxué.)",
                "explanation": "厚积而薄发 chỉ việc tích lũy kiến thức sâu dày rồi mới phát tiết tinh hoa vững vàng.",
                "audio_url": "/api/tts?text=%E8%8B%8F%E8%BD%BC%E6%8F%90%E5%87%BA%E7%9A%84%E5%8D%9A%E8%A7%82%E8%80%8C%E7%BA%A6%E5%8F%96%EF%BC%8C%E5%8E%9A%E7%A7%AF%E8%80%8C%E8%96%84%E5%8F%91%EF%BC%8C%E5%91%8A%E8%AF%AB%E6%B2%BB%E5%AD%A6%E4%B9%8B%E4%BA%BA%E5%94%AF%E6%9C%89%E5%8D%9A%E8%A7%88%E7%BE%A4%E4%B9%A6%E3%80%81%E5%8E%BB%E7%B2%97%E5%8F%96%E7%B2%BE%EF%BC%8C%E5%9C%A8%E6%BC%AB%E9%95%BF%E7%9A%84%E6%B2%89%E6%BD%9C%E7%A7%AF%E7%B4%AF%E4%B8%AD%E5%A4%AF%E5%AE%9E%E6%A0%B9%E5%9F%BA%EF%BC%8C%E6%96%B9%E8%83%BD%E5%9C%A8%E5%85%B3%E9%94%AE%E6%97%B6%E5%88%BB%E4%BB%8E%E5%AE%B9%E5%B1%95%E7%8E%B0%E5%AE%9E%E5%AD%A6%E3%80%82",
                "word_id": None
            }
        ]
    },
    {
        "title": "HSK 6 · Nghe hiểu: Phát triển bền vững & Kinh tế toàn cầu",
        "hsk": 6,
        "duration_minutes": 35,
        "questions": [
            {
                "id": "hsk6_l3_q1",
                "section": "listening",
                "prompt": "Mục tiêu then chốt của chiến lược 'Trung hòa Carbon' (碳中和) toàn cầu là gì?",
                "options": [
                    "Cân bằng lượng phát thải khí nhà kính với lượng hấp thụ để kiềm chế biến đổi khí hậu",
                    "Dừng hoàn toàn mọi hoạt động sản xuất công nghiệp nặng",
                    "Chỉ đầu tư vào xuất khẩu năng lượng hóa thạch"
                ],
                "answer": "Cân bằng lượng phát thải khí nhà kính với lượng hấp thụ để kiềm chế biến đổi khí hậu",
                "transcript": "实现碳达峰与碳中和目标，并非遏制经济增长，而是通过能源结构优化与前沿科技创新，重构低碳高效的产业生态体系。(Shíxiàn tàndāfēng yǔ tànzhōnghé mùbiāo, bìngfēi èzhì jīngjì zēngzhǎng, ér shì tōngguò néngyuán jiégòu yōuhuà yǔ qiányán kējì chuàngxīn, chónggòu dītàn gāoxiào de chǎnyè shēngtài tǐxì.)",
                "explanation": "低碳高效的产业生态体系 nghĩa là tái cấu trúc hệ sinh thái công nghiệp phát thải thấp và hiệu quả cao.",
                "audio_url": "/api/tts?text=%E5%AE%9E%E7%8E%B0%E7%A2%B3%E8%BE%BE%E5%B3%B0%E4%B8%8E%E7%A2%B3%E4%B8%AD%E5%92%8C%E7%9B%AE%E6%A0%87%EF%BC%8C%E5%B9%B6%E9%9D%9E%E9%81%8F%E5%88%B6%E7%BB%8F%E6%B5%8E%E5%A2%9E%E9%95%BF%EF%BC%8C%E8%80%8C%E6%98%AF%E9%80%9A%E8%BF%87%E8%83%BD%E6%BA%90%E7%BB%93%E6%9E%84%E4%BC%98%E5%8C%96%E4%B8%8E%E5%89%8D%E6%B2%BF%E7%A7%91%E6%8A%80%E5%88%9B%E6%96%B0%EF%BC%8C%E9%87%8D%E6%9E%84%E4%BD%8E%E7%A2%B3%E9%AB%98%E6%95%88%E7%9A%84%E4%BA%A7%E4%B8%9A%E7%94%9F%E6%80%81%E4%BD%93%E7%B3%BB%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk6_l3_q2",
                "section": "listening",
                "prompt": "Trong bối cảnh toàn cầu hóa phức tạp, chuỗi cung ứng công nghiệp cần được củng cố theo hướng nào?",
                "options": [
                    "Nâng cao khả năng phục hồi, đa dạng hóa và an toàn linh hoạt",
                    "Phụ thuộc duy nhất vào một thị trường nguyên liệu độc quyền",
                    "Hạn chế ứng dụng công nghệ số vào kho vận"
                ],
                "answer": "Nâng cao khả năng phục hồi, đa dạng hóa và an toàn linh hoạt",
                "transcript": "增强产业链供应链的韧性与安全水平，是防范外部不确定性风险、维护宏观经济稳健运行的战略支撑。(Zēngqiáng chǎnyèliàn gōngyìngliàn de rènxìng yǔ ānquán shuǐpíng, shì fángfàn wàibù bùquèdìngxìng fēngxiǎn, wéihù hóngguān jīngjì wěnjiàn yùnxíng de zhànlüè zhīchēng.)",
                "explanation": "产业链供应链的韧性与安全 (độ dẻo dai và mức độ an toàn của chuỗi cung ứng).",
                "audio_url": "/api/tts?text=%E5%A2%9E%E5%BC%BA%E4%BA%A7%E4%B8%9A%E9%93%BE%E4%BE%9B%E5%BA%94%E9%93%BE%E7%9A%84%E9%9F%A7%E6%80%A7%E4%B8%8E%E5%AE%89%E5%85%A8%E6%B0%B4%E5%B9%B3%EF%BC%8C%E6%98%AF%E9%98%B2%E8%8C%83%E5%A4%96%E9%83%A8%E4%B8%8D%E7%A1%AE%E5%AE%9A%E6%80%A7%E9%A3%8E%E9%99%A9%E3%80%81%E7%BB%B4%E6%8A%A4%E5%AE%8F%E8%A7%82%E7%BB%8F%E6%B5%8E%E7%A8%B3%E5%81%A5%E8%BF%90%E8%A1%8C%E7%9A%84%E6%88%98%E7%95%A5%E6%94%AF%E6%92%91%E3%80%82",
                "word_id": None
            },
            {
                "id": "hsk6_l3_q3",
                "section": "listening",
                "prompt": "Ý nghĩa nhân văn của việc bảo tồn di sản văn hóa phi vật thể là gì?",
                "options": [
                    "Kế thừa ký ức lịch sử văn minh và gắn kết đa dạng văn hóa nhân loại",
                    "Thương mại hóa toàn bộ các lễ hội dân gian",
                    "Ngăn cấm người trẻ tiếp cận các làn sóng nghệ thuật mới"
                ],
                "answer": "Kế thừa ký ức lịch sử văn minh và gắn kết đa dạng văn hóa nhân loại",
                "transcript": "非物质文化遗产承载着人类文明演进的活态记忆，保护非遗不仅是守住民族精神根脉，更是促进世界多元文化交流互鉴的重要基石。(Fēiwùzhì wénhuà yíchǎn chéngzài zhe rénlèi wénmíng yǎnjìn de huótài jìyì, bǎohù fēiyí bùjǐn shì shǒuzhù mínzú jīngshén gēnmài, gèng shì cùjìn shìjiè duōyuán wénhuà jiāoliú hùjiàn de zhòngyào jīshí.)",
                "explanation": "守住民族精神根脉 (giữ gìn cội nguồn tinh thần dân tộc) và 促进多元文化交流 (giao lưu đa dạng văn hóa).",
                "audio_url": "/api/tts?text=%E9%9D%9E%E7%89%A9%E8%B4%A8%E6%96%87%E5%8C%96%E9%81%97%E4%BA%A7%E6%89%BF%E8%BD%BD%E7%9D%80%E4%BA%BA%E7%B1%BB%E6%96%87%E6%98%8E%E6%BC%94%E8%BF%9B%E7%9A%84%E6%B4%BB%E6%80%81%E8%AE%B0%E5%BF%86%EF%BC%8C%E4%BF%9D%E6%8A%A4%E9%9D%9E%E9%81%97%E4%B8%8D%E4%BB%85%E6%98%AF%E5%AE%88%E4%BD%8F%E6%B0%91%E6%97%8F%E7%B2%BE%E7%A5%9E%E6%A0%B9%E8%84%89%EF%BC%8C%E6%9B%B4%E6%98%AF%E4%BF%83%E8%BF%9B%E4%B8%96%E7%95%8C%E5%A4%9A%E5%85%83%E6%96%87%E5%8C%96%E4%BA%A4%E6%B5%81%E4%BA%92%E9%89%B4%E7%9A%84%E9%87%8D%E8%A6%81%E5%9F%BA%E7%9F%B3%E3%80%82",
                "word_id": None
            }
        ]
    }
]
