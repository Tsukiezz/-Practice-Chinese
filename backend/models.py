from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Body(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", allow_inf_nan=False)


class Login(Body):
    email: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=1, max_length=128)


class Register(Login):
    name: str = Field(min_length=2, max_length=60)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        import re
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Email không hợp lệ")
        return value.lower()


class UserUpdate(Body):
    role: Literal["student", "admin"]
    is_active: bool
    version: int = Field(ge=1)


class Point(Body):
    x: float = Field(ge=0, le=1024)
    y: float = Field(ge=0, le=1024)


class Word(Body):
    hanzi: str = Field(min_length=1, max_length=30)
    pinyin: str = Field(min_length=1, max_length=120)
    meaning: str = Field(min_length=1, max_length=300)
    hsk: int = Field(ge=1, le=6)
    example: str = Field(default="", max_length=1000)
    audio_url: str = Field(default="", max_length=1000)
    strokes: list[list[Point]] = Field(default_factory=list, max_length=64)

    @field_validator("audio_url")
    @classmethod
    def valid_url(cls, value):
        from urllib.parse import urlparse
        import re
        if re.fullmatch(r'/media/[a-zA-Z0-9_-]+\.(mp3|wav)', value):
            return value
        if value and (urlparse(value).scheme != "https" or not urlparse(value).netloc):
            raise ValueError("Audio phải là URL HTTPS")
        return value

    @field_validator("strokes")
    @classmethod
    def valid_strokes(cls, value):
        if any(not 2 <= len(stroke) <= 512 for stroke in value):
            raise ValueError("Mỗi nét cần 2–512 điểm, tọa độ 0–1024")
        return value


class WordUpdate(Word):
    version: int = Field(ge=1)


class Question(Body):
    id: str = Field(min_length=1, max_length=40)
    section: Literal["listening", "reading", "writing"]
    prompt: str = Field(min_length=1, max_length=5000)
    options: list[str] = Field(default_factory=list, max_length=10)
    answer: str = Field(min_length=1, max_length=5000)
    audio_url: str = Field(default="", max_length=1000)
    transcript: str = Field(default="", max_length=5000)
    explanation: str = Field(default="", max_length=5000)
    word_id: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_question(self):
        Word.valid_url(self.audio_url)
        if self.section == "listening" and not self.audio_url:
            raise ValueError("Câu nghe cần audio HTTPS")
        if self.options and (len(self.options) < 2 or len(set(self.options)) != len(self.options)
                             or any(not option.strip() for option in self.options) or self.answer not in self.options):
            raise ValueError("Lựa chọn phải khác nhau, không rỗng và chứa đáp án")
        return self


class Exam(Body):
    title: str = Field(min_length=1, max_length=200)
    hsk: int = Field(ge=1, le=6)
    status: Literal["draft", "published", "hidden"] = "draft"
    duration_minutes: int = Field(ge=1, le=240)
    questions: list[Question] = Field(min_length=1, max_length=200)

    @field_validator("questions")
    @classmethod
    def unique_ids(cls, value):
        if len({q.id for q in value}) != len(value):
            raise ValueError("Mã câu hỏi bị trùng")
        return value


class ExamUpdate(Exam):
    version: int = Field(ge=1)


class AIConfig(Body):
    model: str = Field(min_length=1, max_length=120, pattern=r"^[a-zA-Z0-9._:/-]+$")
    system_prompt: str = Field(min_length=1, max_length=10000)
    temperature: float = Field(ge=0, le=2)
    max_tokens: int = Field(ge=1, le=16000)
    enabled: bool
    version: int = Field(ge=1)


class Override(Body):
    score: float = Field(ge=0, le=100)
    reason: str = Field(min_length=5, max_length=2000)
    version: int = Field(ge=1)


class Submission(Body):
    version: int = Field(ge=1)
    answers: dict[str, str] = Field(max_length=200)


class Appeal(Body):
    reason: str = Field(min_length=5, max_length=2000)


class AppealReview(Body):
    version: int = Field(ge=1)
    result_version: int = Field(ge=1)
    score: float = Field(ge=0, le=100)
    response: str = Field(min_length=5, max_length=2000)

class DictionaryLookup(Body):
    query: str = Field(default="", max_length=120)


class WritingSubmission(Body):
    content: str = Field(min_length=1, max_length=10000)


class HandwritingSubmission(Body):
    target: str = Field(min_length=1, max_length=1)
    strokes: list[list[Point]] = Field(min_length=1, max_length=64)

    @field_validator("target")
    @classmethod
    def single_han_character(cls, value):
        codepoint = ord(value)
        if not (0x3400 <= codepoint <= 0x4DBF
                or 0x4E00 <= codepoint <= 0x9FFF
                or 0xF900 <= codepoint <= 0xFAFF
                or 0x20000 <= codepoint <= 0x2EBEF):
            raise ValueError("Luyện nét chỉ hỗ trợ một chữ Hán")
        return value

    @field_validator("strokes")
    @classmethod
    def valid_strokes(cls, value):
        return Word.valid_strokes(value)


class HandwritingGradeDetails(Body):
    wrong_strokes: list[int] = Field(default_factory=list, max_length=64)
    # Keep the three rubric components explicit so Flutter/Admin can explain
    # where the final 0-100 score came from.
    count_score: float = Field(default=0, ge=0, le=100)
    order_position_score: float = Field(default=0, ge=0, le=100)
    direction_score: float = Field(default=0, ge=0, le=100)

    @field_validator("wrong_strokes")
    @classmethod
    def valid_indices(cls, value):
        if any(index < 1 for index in value) or len(value) != len(set(value)):
            raise ValueError("Chỉ số nét sai phải duy nhất và bắt đầu từ 1")
        return value


class HandwritingGradeResponse(Body):
    score: float = Field(ge=0, le=100)
    feedback: str = Field(min_length=1, max_length=2000)
    details: HandwritingGradeDetails


class HandwritingRecognition(Body):
    """Canvas payload shared by Flutter and the handwriting OCR endpoint."""

    strokes: list[list[Point]] = Field(min_length=1, max_length=64)

    @field_validator("strokes")
    @classmethod
    def valid_strokes(cls, value):
        return Word.valid_strokes(value)


class HandwritingWordMatch(Body):
    id: int = Field(ge=1)
    hanzi: str
    pinyin: str
    meaning: str
    hsk: int = Field(ge=1, le=6)
    example: str = ""
    audio_url: str = ""


class HandwritingCandidate(Body):
    hanzi: str = Field(min_length=1, max_length=4)
    confidence: float = Field(ge=0, le=100)
    words: list[HandwritingWordMatch] = Field(default_factory=list, max_length=10)


class HandwritingRecognitionDetails(Body):
    recognized_hanzi: str = Field(min_length=1, max_length=4)
    candidates: list[HandwritingCandidate] = Field(min_length=1, max_length=5)


class HandwritingRecognitionResponse(Body):
    score: float = Field(ge=0, le=100)
    feedback: str = Field(min_length=1, max_length=2000)
    details: HandwritingRecognitionDetails
