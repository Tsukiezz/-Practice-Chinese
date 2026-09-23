"""Original short lessons, deterministic grading and per-account progress."""
from functools import lru_cache
import json
from pathlib import Path
import time
from typing import Annotated

from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from database import database, row_to_dict
from vocabulary_catalog import normalize


@lru_cache(maxsize=1)
def curriculum():
    return json.loads(Path(__file__).with_name('data').joinpath('lessons.json').read_text(encoding='utf-8'))


def find_lesson(lesson_id):
    for lesson in curriculum()['lessons']:
        if lesson['id'] == lesson_id:
            return lesson
    raise HTTPException(404, 'Không tìm thấy bài học')


def init_lessons():
    with database() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS lesson_progress (
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                lesson_id TEXT NOT NULL,
                stage INTEGER NOT NULL DEFAULT 0 CHECK(stage BETWEEN 0 AND 4),
                best_score INTEGER NOT NULL DEFAULT 0 CHECK(best_score BETWEEN 0 AND 100),
                attempts INTEGER NOT NULL DEFAULT 0,
                completed_at INTEGER,
                updated_at INTEGER NOT NULL,
                PRIMARY KEY(user_id, lesson_id)
            );
        ''')


class LessonStage(BaseModel):
    model_config = ConfigDict(extra='forbid')
    stage: Annotated[int, Field(strict=True, ge=1, le=3)]


class LessonAnswers(BaseModel):
    model_config = ConfigDict(extra='forbid')
    answers: Annotated[dict[str, StrictInt], Field(min_length=4, max_length=4)]


def grade(lesson, body):
    questions = lesson['questions']
    if set(body.answers) != {q['id'] for q in questions}:
        raise HTTPException(422, 'Hãy trả lời đủ các câu hỏi của bài học')
    review = []
    for q in questions:
        choice = body.answers[q['id']]
        if not 0 <= choice < len(q['options']):
            raise HTTPException(422, 'Lựa chọn không hợp lệ')
        review.append({'id': q['id'], 'correct': choice == q['answer'],
                       'answer': q['answer'], 'explanation': q['explanation']})
    score = round(100 * sum(r['correct'] for r in review) / len(review))
    return {'score': score, 'passed': score >= 75, 'review': review}


def register_lessons(app, current_user):
    @app.get('/api/lessons')
    def list_lessons(hsk: int | None = Query(None, ge=1, le=6), search: str = Query('', max_length=120)):
        data = curriculum()
        query = normalize(search.strip())
        items = []
        for lesson in data['lessons']:
            if hsk is not None and lesson['hsk'] != hsk:
                continue
            haystack = normalize(' '.join([lesson['title'], lesson['objective'], lesson['grammar']['pattern'],
                                         *(w['hanzi'] for w in lesson['vocabulary'])]))
            if query and query not in haystack:
                continue
            items.append({k: lesson[k] for k in ('id', 'hsk', 'order', 'title', 'minutes', 'review', 'objective')})
        return {'items': items, 'total': len(items), 'levels': data['levels'], 'edition': data['edition'],
                'description': data['description'], 'course_total': len(data['lessons'])}

    @app.get('/api/lessons/{lesson_id}')
    def detail(lesson_id: str):
        lesson = find_lesson(lesson_id)
        return {**lesson, 'questions': [{k: v for k, v in q.items() if k not in ('answer', 'explanation')}
                                       for q in lesson['questions']]}

    @app.get('/api/me/lessons')
    def progress(user=Depends(current_user)):
        with database() as conn:
            return [dict(r) for r in conn.execute(
                'SELECT lesson_id,stage,best_score,attempts,completed_at,updated_at FROM lesson_progress WHERE user_id=?',
                (user['id'],))]

    @app.put('/api/me/lessons/{lesson_id}/progress')
    def checkpoint(lesson_id: str, body: LessonStage, user=Depends(current_user)):
        find_lesson(lesson_id)
        with database() as conn:
            conn.execute('''INSERT INTO lesson_progress(user_id,lesson_id,stage,updated_at) VALUES(?,?,?,?)
                ON CONFLICT(user_id,lesson_id) DO UPDATE SET
                stage=MAX(stage,excluded.stage),updated_at=excluded.updated_at''',
                (user['id'], lesson_id, body.stage, int(time.time())))
            return row_to_dict(conn.execute('SELECT * FROM lesson_progress WHERE user_id=? AND lesson_id=?',
                                     (user['id'], lesson_id)).fetchone())

    @app.post('/api/me/lessons/{lesson_id}/submit')
    def submit(lesson_id: str, body: LessonAnswers, user=Depends(current_user)):
        result = grade(find_lesson(lesson_id), body)
        now = int(time.time())
        with database() as conn:
            conn.execute('''INSERT INTO lesson_progress
                (user_id,lesson_id,stage,best_score,attempts,completed_at,updated_at) VALUES(?,?,?,?,1,?,?)
                ON CONFLICT(user_id,lesson_id) DO UPDATE SET
                stage=MAX(stage,excluded.stage),best_score=MAX(best_score,excluded.best_score),
                attempts=attempts+1,completed_at=COALESCE(completed_at,excluded.completed_at),updated_at=excluded.updated_at''',
                (user['id'], lesson_id, 4 if result['passed'] else 3, result['score'], now if result['passed'] else None, now))
            result['progress'] = row_to_dict(conn.execute('SELECT * FROM lesson_progress WHERE user_id=? AND lesson_id=?',
                                                           (user['id'], lesson_id)).fetchone())
        return result
