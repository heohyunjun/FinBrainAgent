# utils/logger.py
import os
import logging
from datetime import datetime

# 로그 디렉토리 생성
log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(log_dir, exist_ok=True)

# 오늘 날짜 기준 로그 파일 경로
today = datetime.now().strftime("%Y-%m-%d")
log_path = os.path.join(log_dir, f"{today}.log")

# 커스텀 로거 정의
logger = logging.getLogger("FinBrainLogger")
logger.setLevel(logging.DEBUG)  # 로그 레벨 지정

# 핸들러 중복 추가 방지 (FastAPI reload 시 여러 번 설정될 수 있음)
if not logger.hasHandlers():
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    # 콘솔 출력 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 파일 핸들러
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    # 핸들러 등록
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

# 루트로 전파되지 않도록 설정 (중복 방지)
logger.propagate = False
