"""Safe provider diagnostics; never expose provider response bodies or keys."""
import logging

import httpx
from fastapi import HTTPException


class AIProviderError(ValueError):
    def __init__(self, code, status, message):
        super().__init__(message)
        self.code, self.status = code, status


def provider_error(status):
    if status == 429:
        return AIProviderError('quota', 429, 'AI đã chạm hạn mức yêu cầu. Vui lòng thử lại sau; quản trị viên cần kiểm tra quota Gemini.')
    if status in (401, 403):
        return AIProviderError('credentials', 503, 'Khóa AI không hợp lệ hoặc không có quyền. Vui lòng báo quản trị viên kiểm tra GEMINI_API_KEY trên máy chủ.')
    if status == 404:
        return AIProviderError('model', 503, 'Model AI không còn khả dụng. Quản trị viên cần chọn model khác trong Cấu hình AI.')
    if status >= 500:
        return AIProviderError('overloaded', 503, 'Dịch vụ AI đang quá tải. Vui lòng chờ một lát rồi thử lại; bài này chưa được chấm.')
    return AIProviderError('request', 502, 'AI chưa xử lý được yêu cầu. Vui lòng báo quản trị viên kiểm tra cấu hình AI.')


def ai_http_error(error, fallback):
    if isinstance(error, httpx.HTTPStatusError):
        error = provider_error(error.response.status_code)
    if isinstance(error, httpx.TransportError):
        error = AIProviderError('timeout', 504, 'AI phản hồi chậm hoặc tạm mất kết nối. Vui lòng thử lại sau.')
    if isinstance(error, AIProviderError):
        logging.getLogger('hanzigo.ai').warning('AI provider failure: %s', error.code)
        return HTTPException(error.status, str(error))
    logging.getLogger('hanzigo.ai').warning('AI provider failure: invalid_response')
    return HTTPException(502, fallback)
