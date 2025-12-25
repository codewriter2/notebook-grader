# 빠른 시작 가이드 (Quick Start Guide)

이 가이드는 프로그래밍 경험이 적은 사용자를 위한 단계별 설치 및 사용 가이드입니다.

## 📥 1단계: 프로그램 다운로드

### 방법 A: ZIP 파일로 다운로드 (가장 쉬움)

1. 웹브라우저에서 https://github.com/codewriter2/notebook-grader 접속
2. 초록색 **`Code`** 버튼 클릭
3. **`Download ZIP`** 클릭
4. 다운로드된 `notebook-grader-main.zip` 파일을 원하는 위치에 압축 해제
   - 예: `C:\Users\내이름\Documents\notebook-grader-main`

### 방법 B: Git 사용 (개발자용)

```bash
git clone https://github.com/codewriter2/notebook-grader.git
cd notebook-grader
```

## 📁 4단계: 폴더 구조 준비

프로그램이 있는 폴더에 학생 제출물 폴더를 만듭니다:

```
notebook-grader-main/
├── batch_grade.py          ← 채점 프로그램
├── README.md
├── requirements.txt
└── 05/                     ← 학생 제출물 폴더 (새로 만들기)
    ├── 강현규2025042.ipynb
    ├── 김예진2025043.ipynb
    └── 박나혜2025044.ipynb
```

**폴더 이름 예시**: `05`, `10`, `midterm`, `final` 등 자유롭게 설정

---

## ▶️ 5단계: 채점 실행

### 방법 1: 명령행 인자 사용

```bash
python batch_grade.py 05
```

### 방법 2: 대화형 실행

```bash
python batch_grade.py
```
그 다음 프롬프트에서 폴더 이름 입력:
```
채점할 폴더 이름을 입력하세요 (예: 05, 10): 05
```

### 방법 3: 더블클릭 실행 (Windows)

1. `batch_grade.py` 파일을 더블클릭
2. 폴더 이름 입력 (예: `05`)
3. 엔터 키 누르기

---

## 📊 6단계: 결과 확인

채점이 완료되면 다음 파일들이 생성됩니다:

```
notebook-grader-main/
├── 05/                     ← 학생 제출물
├── 05결과.csv              ← 채점 결과 (CSV)
└── 05결과.xlsx             ← 채점 결과 (Excel)
```

### Excel 파일 열기

1. `05결과.xlsx` 파일을 Excel로 열기
2. 다음 정보 확인:
   - 학생 이름, 학번
   - Q1, Q2, Q3 각 문제별 점수
   - 실행 점수
   - 총점
   - 상세 피드백 (Comments 열)

---

## 🔧 문제 해결

### Q: "파일을 찾을 수 없습니다" 오류
**A**: 현재 폴더 위치 확인
```bash
# 현재 위치 확인
pwd          # Mac/Linux
cd           # Windows

# 올바른 폴더로 이동
cd C:\Users\내이름\Documents\notebook-grader-main
```

### Q: "모듈을 찾을 수 없습니다" 오류
**A**: 패키지 재설치
```bash
pip install --upgrade nbformat pandas openpyxl
```

### Q: 학생 이름이 제대로 인식되지 않음
**A**: 파일명 형식 확인
- ✅ 올바른 예: `강현규2025042.ipynb`
- ❌ 잘못된 예: `2025042_강현규.ipynb`, `강현규.ipynb`

### Q: 채점 결과가 이상함
**A**: 학생 노트북에 문제 마커 확인
- 노트북에 `1번`, `2번`, `3번` 마크다운 또는 주석이 있어야 함
- 예: `# 1번`, `## 2번 문제`

---

## 💡 팁

### 여러 폴더 한 번에 채점하기

```bash
python batch_grade.py 05
python batch_grade.py 10
python batch_grade.py 11
```

### 결과 파일 백업

채점 결과는 덮어쓰기되므로 중요한 결과는 별도 폴더에 백업하세요:
```
backups/
├── 2024-12-25_05결과.xlsx
└── 2024-12-25_10결과.xlsx
```

### 채점 기준 변경

`batch_grade.py` 파일의 `RubricConfig` 클래스를 수정하면 배점을 변경할 수 있습니다.
(자세한 내용은 README.md 참조)

---

## 📞 도움이 필요하신가요?

- GitHub Issues: https://github.com/codewriter2/notebook-grader/issues
- 상세 문서: README.md 파일 참조

---

**이제 자동 채점을 시작하세요! 🚀**
