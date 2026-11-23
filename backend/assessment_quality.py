"""Assessment provenance and honest no-score responses, independent of AI services."""
import base64
import json
import math
from difflib import SequenceMatcher


READING_ASSESSED_SQL = """(
    json_extract(CASE WHEN json_valid(feedback_json) THEN feedback_json ELSE '{}' END,
                 '$.assessment_status') = 'assessed'
    AND json_extract(CASE WHEN json_valid(feedback_json) THEN feedback_json ELSE '{}' END,
                     '$.assessment_source') = 'gemini_audio'
    AND json_extract(CASE WHEN json_valid(feedback_json) THEN feedback_json ELSE '{}' END,
                     '$.score_eligible') = 1
)"""


def valid_score(value):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and 0 <= value <= 100)


def has_audio_payload(value):
    if not isinstance(value, str) or not value.strip():
        return False
    payload = value.strip()
    if payload.startswith('data:'):
        header, separator, payload = payload.partition(',')
        if not separator or not header.startswith('data:audio/') or ';base64' not in header:
            return False
    try:
        return bool(base64.b64decode(payload, validate=True))
    except (ValueError, TypeError):
        return False


def transcript_feedback(target, spoken, normalized_target='', normalized_spoken='', has_audio=False):
    """Text similarity is never a pronunciation, tone, or fluency grade."""
    spoken = (spoken or '').strip()
    similarity = None
    if spoken:
        similarity = round(100 * max(SequenceMatcher(None, target, spoken).ratio(),
                                    SequenceMatcher(None, normalized_target, normalized_spoken).ratio()), 1)
    feedback = ('Chưa đánh giá được âm thanh. Văn bản nhận dạng chỉ dùng để bạn đối chiếu, '
                'không đủ để chấm thanh điệu, âm vị hoặc độ trôi chảy.') if spoken else (
                'Chưa đánh giá được bản thu âm. Hãy thử lại khi dịch vụ sẵn sàng.') if has_audio else (
                'Chưa có bản thu âm hợp lệ để đánh giá. Hãy kiểm tra micro và ghi âm lại.')
    return {
        'assessment_status': 'transcript_only' if spoken else 'unavailable',
        'assessment_source': 'transcript' if spoken else 'none',
        'score_eligible': False,
        'accuracy_percent': None,
        'tone_score': None,
        'phoneme_score': None,
        'fluency_score': None,
        'transcript_match_percent': similarity,
        'rating': 'Chưa đánh giá âm thanh',
        'spoken_recognized': spoken,
        'errors': [],
        'corrections': [],
        'general_feedback': feedback,
        'tips_for_mastery': 'Nghe mẫu và ghi âm lại. Kết quả chưa đánh giá không được tính vào điểm hoặc danh sách bài yếu.',
    }


def reading_feedback(feedback):
    if isinstance(feedback, str):
        try:
            feedback = json.loads(feedback)
        except (ValueError, TypeError):
            feedback = {}
    if not isinstance(feedback, dict):
        feedback = {}
    return feedback


def reading_assessment_metadata(feedback):
    feedback = reading_feedback(feedback)
    eligible = (feedback.get('assessment_status') == 'assessed'
                and feedback.get('assessment_source') == 'gemini_audio'
                and feedback.get('score_eligible') is True
                and valid_score(feedback.get('accuracy_percent')))
    return {
        'assessment_status': 'assessed' if eligible else 'legacy_unverified',
        'assessment_source': 'gemini_audio' if eligible else 'unknown',
        'score_eligible': eligible,
    }
