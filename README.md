# Jupyter Notebook Auto Grader

Jupyter Notebook 형식의 학생 과제를 자동으로 채점하는 Python 프로그램입니다.

## 📋 개요

이 프로그램은 교육 현장에서 Jupyter Notebook으로 제출된 Python 과제를 효율적으로 채점하기 위해 개발되었습니다. 코드 실행 결과, 출력물, 그래프 생성 여부 등을 종합적으로 평가하여 자동으로 점수를 산출합니다.

## ✨ 주요 기능

- **자동 채점**: 여러 학생의 노트북 파일을 일괄 처리
- **섹션별 평가**: 문제별(1번, 2번, 3번)로 구분하여 채점
- **다양한 평가 기준**:
  - Q1: 정규표현식 기반 출력물 검증 (학번/이름 출력 확인)
  - Q2: 막대 그래프(Bar Chart) 생성 및 로직 검증
  - Q3: CSV 데이터 시각화 및 데이터 처리 검증
  - 실행 오류 감지 및 부분 점수 부여
- **상세한 피드백**: 각 문제별 감점 사유 및 개선 사항 제공
- **결과 내보내기**: CSV 및 Excel 형식으로 채점 결과 저장

## 🚀 설치 방법

### 필수 요구사항

- Python 3.7 이상
- 필수 라이브러리:
  ```bash
  pip install nbformat pandas openpyxl
  ```

### 설치

```bash
git clone https://github.com/yourusername/jupyter-auto-grader.git
cd jupyter-auto-grader
pip install -r requirements.txt
```

## 📖 사용 방법

### 기본 사용법

1. **폴더 구조 준비**
   ```
   exam/
   ├── batch_grade.py
   ├── 05/                    # 채점할 노트북 파일들
   │   ├── 강현규2025042.ipynb
   │   ├── 김예진2025043.ipynb
   │   └── ...
   └── 10/
       └── ...
   ```

2. **명령행에서 실행**
   ```bash
   python batch_grade.py 05
   ```
   
   또는 인터랙티브 모드:
   ```bash
   python batch_grade.py
   # 프롬프트에서 폴더 이름 입력: 05
   ```

3. **결과 확인**
   - `05결과.csv`: CSV 형식 채점 결과
   - `05결과.xlsx`: Excel 형식 채점 결과

### 파일명 규칙

학생 정보를 자동으로 추출하기 위해 다음 형식을 권장합니다:
- `이름학번.ipynb` (예: `강현규2025042.ipynb`)
- 한글 이름 + 숫자 학번 조합

## 📊 채점 기준

### 배점 (총 5.0점)

| 문제 | 배점 | 평가 항목 |
|------|------|-----------|
| Q1 | 1.0점 | 학번/이름 출력 (5회 이상) |
| Q2 | 1.5점 | 막대 그래프 생성 + 데이터 변수 활용 |
| Q3 | 1.5점 | CSV 데이터 시각화 + 숫자 변환 처리 |
| 실행 | 1.0점 | 오류 없이 실행 완료 |

### 상세 평가 로직

#### Q1: 정규표현식 검증
- 출력물에서 학생의 이름 또는 학번이 5회 이상 출력되었는지 확인
- 미달 시 0점 처리

#### Q2: 막대 그래프
- **만점 (1.5점)**: 그래프 출력 성공 + 데이터 변수 활용 + `plt.bar` 사용
- **감점 사항**:
  - 데이터 변수 미사용 (랜덤값 직접 대입): -1.0점
  - `plt.bar` 대신 다른 차트 사용: -0.5점
- **부분 점수 (0.5점)**: 그래프 미출력이지만 로직 코드 존재

#### Q3: CSV 시각화
- **만점 (1.5점)**: 그래프 출력 성공
- **우수**: Pandas 사용 시 추가 코멘트
- **감점 사항**:
  - Pandas 미사용 시 숫자 변환(`int()`, `float()`) 누락: -0.3점
- **부분 점수 (0.5점)**: 그래프 미출력이지만 파일 읽기 + plot 로직 존재

#### 실행 점수
- **1.0점**: 오류 없이 모든 셀 실행
- **0.5점**: 오류 셀 존재하지만 일부 실행됨
- **0점**: 심각한 실행 오류

## 🔧 커스터마이징

### RubricConfig 클래스 수정

채점 기준을 변경하려면 `RubricConfig` 클래스를 수정하세요:

```python
@dataclass
class RubricConfig:
    q1_min_occurrences: int = 5      # Q1 최소 출력 횟수
    q2_score_max: float = 1.5        # Q2 만점
    q2_partial_score: float = 0.5    # Q2 부분 점수
    q3_score_max: float = 1.5        # Q3 만점
    q3_partial_score: float = 0.5    # Q3 부분 점수
    execution_score_max: float = 1.0 # 실행 점수 만점
    q_markers: Tuple[str, str, str] = ("1번", "2번", "3번")  # 문제 구분 마커
```

### 문제 마커 변경

노트북에서 문제를 구분하는 마커를 변경할 수 있습니다:
```python
cfg = RubricConfig(q_markers=("Problem 1", "Problem 2", "Problem 3"))
grade_folder("./submissions", cfg=cfg)
```

## 📄 출력 형식

### CSV/Excel 컬럼

| 컬럼명 | 설명 |
|--------|------|
| file | 파일명 |
| student_name | 학생 이름 |
| student_id | 학번 |
| Q1(1.0) | Q1 점수 |
| Q2(1.5) | Q2 점수 |
| Q3(1.5) | Q3 점수 |
| Exec(1.0) | 실행 점수 |
| Total(5.0) | 총점 |
| Comments | 상세 피드백 |

### 예시 출력

```
  student_name  Q1(1.0)  Q2(1.5)  Q3(1.5)  Exec(1.0)  Total(5.0)
0      강현규      1.0      1.5      1.5        1.0         5.0
1      김예진      1.0      0.5      1.5        0.5         3.5
2      윤채원      1.0      1.0      1.2        1.0         4.2
```

## 🛠️ 기술 스택

- **Python 3.7+**
- **nbformat**: Jupyter Notebook 파일 파싱
- **pandas**: 데이터 처리 및 결과 저장
- **openpyxl**: Excel 파일 생성
- **정규표현식**: 코드 패턴 분석 및 검증

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여하기

버그 리포트, 기능 제안, Pull Request를 환영합니다!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📧 문의

프로젝트에 대한 문의사항이 있으시면 Issue를 생성해주세요.

## 🙏 감사의 말

이 프로그램은 교육 현장의 실제 요구사항을 반영하여 개발되었습니다. 학생들의 다양한 코딩 스타일과 접근 방식을 공정하게 평가하기 위해 지속적으로 개선하고 있습니다.

---

**Made with ❤️ for educators and students**
