import os
import re
import requests
from dotenv import load_dotenv

# 1. 환경 변수 로드 (.env 파일 또는 GitHub Secrets)
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# 깃허브 액션에서 전달받을 커밋 메시지 (테스트 시에는 두 번째 인자값이 사용됨)
COMMIT_MESSAGE = os.getenv("COMMIT_MESSAGE", "[MBC-2] #doing 테스트 커밋")

# 2. 노션 API 설정
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# 3. 상태 매핑 테이블 (팀원들과 약속할 키워드)
# 왼쪽: 커밋에 적을 해시태그 / 오른쪽: 노션 '상태' 컬럼의 실제 옵션 이름
STATUS_MAP = {
    "#doing": "진행 중",
    "#wip": "진행 중",
    "#done": "완료",
    "#fix": "완료",
    "#review": "검토 중"
}


def get_page_id_by_task_id(task_id_number):
    """TASK-1에서 숫자 '1'을 받아 해당 페이지의 고유 ID를 반환"""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    # 노션의 'ID' 속성(Unique ID)을 이용해 필터링
    payload = {
        "filter": {
            "property": "ID",
            "unique_id": {
                "equals": int(task_id_number)
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        results = response.json().get("results")
        if results:
            return results[0]["id"]
    else:
        print(f"❌ 페이지 찾기 실패: {response.text}")
    return None


def update_task_status(page_id, new_status):
    """찾은 노션 페이지의 상태를 변경"""
    url = f"https://api.notion.com/v1/pages/{page_id}"

    payload = {
        "properties": {
            "상태": {  # 노션 표의 '상태' 컬럼 이름과 일치해야 함
                "status": {
                    "name": new_status
                }
            }
        }
    }

    response = requests.patch(url, headers=headers, json=payload)
    return response.status_code == 200


def main():
    print(f"🔍 분석 중인 커밋 메시지: {COMMIT_MESSAGE}")

    # A. 태스크 ID 추출 (TASK-123 형식에서 숫자만 쏙!)
    task_match = re.search(r"MBC-(\d+)", COMMIT_MESSAGE.upper())
    if not task_match:
        print("⏭️ MBC ID를 찾을 수 없어 종료합니다.")
        return

    task_number = task_match.group(1)

    # B. 상태 키워드 추출 (.lower()로 대소문자 무시)
    new_status = None
    msg_lower = COMMIT_MESSAGE.lower()
    for keyword, status_name in STATUS_MAP.items():
        if keyword in msg_lower:
            new_status = status_name
            break

    if not new_status:
        print("⏭️ 변경 키워드(#done 등)가 없어 종료합니다.")
        return

    # C. 노션 업데이트 실행
    print(f"⚙️ MBC-{task_number}를 '{new_status}' 상태로 변경 시도 중...")
    page_id = get_page_id_by_task_id(task_number)

    if page_id and update_task_status(page_id, new_status):
        print(f"✅ 성공: 노션 보드 업데이트 완료!")
    else:
        print(f"❌ 실패: 노션에서 해당 작업을 찾지 못했거나 오류가 발생했습니다.")


if __name__ == "__main__":
    main()
