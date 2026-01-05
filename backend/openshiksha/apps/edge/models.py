"""
Edge models - Analytics and Proficiency Tracking

Models will be implemented based on legacy edge app:
- Tick (answer tracking)
- StudentProficiency
- SubjectRoomProficiency
- SubjectRoomQuestionMistake
"""

from django.db import models


# TODO: Implement models based on legacy/edge/models.py
# Key models to preserve:
# - Tick: tracks individual answers
# - Proficiency: base proficiency class
# - StudentProficiency: per-student per-tag proficiency
# - SubjectRoomProficiency: class-level proficiency
# - Algorithm: score = (0.7 * rate) + (0.3 * percentile)
