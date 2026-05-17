import logging
import os
import tempfile

from django.conf import settings
from better_profanity import profanity

logger = logging.getLogger(__name__)

profanity.load_censor_words()


def text_is_clean(text: str) -> bool:
    """Return False if the text contains profanity."""
    if not getattr(settings, 'MODERATION_PROFANITY_ENABLED', True):
        return True
    return not profanity.contains_profanity(text or '')


def image_is_clean(image_file) -> bool:
    """
    Return False if the image contains explicit nudity.
    Writes the uploaded file to a temp path because NudeDetector requires a file path,
    then resets the file pointer so Django can still save it afterward.
    """
    if not getattr(settings, 'MODERATION_NUDITY_ENABLED', True):
        return True

    try:
        from nudenet import NudeDetector
    except ImportError:
        logger.warning('nudenet is not installed — nudity check skipped.')
        return True

    blocked = getattr(settings, 'NUDENET_BLOCKED_LABELS', [])
    threshold = float(getattr(settings, 'NUDENET_SCORE_THRESHOLD', 0.6))

    suffix = os.path.splitext(image_file.name)[1] or '.jpg'
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            for chunk in image_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        image_file.seek(0)

        detector = NudeDetector()
        results = detector.detect(tmp_path)
        for detection in results:
            if detection.get('class') in blocked and detection.get('score', 0) >= threshold:
                return False
        return True
    except Exception:
        logger.exception('Nudity check failed for "%s" — treating as clean.', image_file.name)
        return True
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
