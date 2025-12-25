import re
import nbformat
import os
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

# --- Configuration ---
@dataclass
class RubricConfig:
    # Q1 Configuration
    q1_required_regex: str = r""  # 동적으로 설정됨
    q1_min_occurrences: int = 5
    q1_score_max: float = 1.0

    # Q2 Configuration (Bar Chart)
    q2_keywords: Tuple[str, ...] = ("plt.bar", "random", "randint")
    q2_score_max: float = 1.5
    q2_partial_score: float = 0.5  # 키워드는 있지만 실행 실패시 점수

    # Q3 Configuration (CSV Plot)
    q3_keywords: Tuple[str, ...] = ("read_csv", "open", "plt.", "plot", "input")
    q3_score_max: float = 1.5
    q3_partial_score: float = 0.5

    # General
    execution_score_max: float = 1.0
    q_markers: Tuple[str, str, str] = ("1번", "2번", "3번")

@dataclass
class GradeBreakdown:
    q1_score: float
    q2_score: float
    q3_score: float
    execution_score: float
    total: float
    comments: List[str]

# --- Helper Functions ---

def extract_student_info(filename: str):
    """
    파일명에서 이름과 학번을 추출.
    예: '강현규2025042_...' -> name='강현규', id='2025042'
    """
    name_part = filename.replace('.ipynb', '')
    # 한글 이름 추출 (시작 부분)
    name_match = re.match(r'^([가-힣]+)', name_part)
    name = name_match.group(1) if name_match else ""
    
    if name:
        # 이름 뒤의 숫자(학번) 추출
        student_id_match = re.search(rf'{re.escape(name)}\s*(\d+)', name_part)
        student_id = student_id_match.group(1) if student_id_match else ""
    else:
        student_id = ""
        
    return name, student_id

def notebook_full_text(nb: nbformat.NotebookNode) -> str:
    """노트북의 모든 코드 셀 내용을 하나의 문자열로 결합"""
    text = []
    for cell in nb.cells:
        if cell.cell_type == 'code':
            text.append(cell.source)
    return "\n".join(text)

def split_by_markers(nb: nbformat.NotebookNode, markers: Tuple[str, str, str]) -> Dict[str, Dict[str, str]]:
    """
    마크다운 헤더(예: '1번', '2번') 또는 코드 주석(예: '# 1번')을 기준으로 노트북 코드와 출력을 분리.
    Returns: {"q1": {"source": "...", "output": "..."}, ...}
    """
    sections = {
        "q1": {"source": "", "output": ""}, 
        "q2": {"source": "", "output": ""}, 
        "q3": {"source": "", "output": ""}
    }
    current_section = None
    
    for cell in nb.cells:
        content = cell.source
        found_section = None
        
        # 마커 감지 (마크다운 or 코드 셀 주석)
        # 단순 포함 여부보다는, 해당 줄이 마커로 시작하거나 포함하는지 확인
        # 박나혜 학생 케이스: "# 3번 코드작성" -> "3번" 마커 포함
        if markers[0] in content:
            found_section = "q1"
        elif markers[1] in content:
            found_section = "q2"
        elif markers[2] in content:
            found_section = "q3"
            
        # 코드 셀인 경우, 주석(#)이 있는 줄에 마커가 있어야 인정 (오탐 방지)
        # 마크다운 셀은 내용에 있으면 인정
        if found_section:
            if cell.cell_type == 'markdown':
                current_section = found_section
            elif cell.cell_type == 'code':
                # 코드 셀은 주석 라인에서만 마커를 찾음 (간단히 #이 포함된 라인 검사)
                has_marker_in_comment = False
                for line in content.splitlines():
                    if '#' in line and (markers[0] in line or markers[1] in line or markers[2] in line):
                        # 현재 찾은 섹션 마커와 일치하는지 확인
                        if (found_section == "q1" and markers[0] in line) or \
                           (found_section == "q2" and markers[1] in line) or \
                           (found_section == "q3" and markers[2] in line):
                            has_marker_in_comment = True
                            break
                
                if has_marker_in_comment:
                    current_section = found_section

        # 코드 셀 내용을 현재 섹션에 추가
        if cell.cell_type == 'code':
            if current_section:
                sections[current_section]["source"] += "\n" + cell.source
                # 출력 내용도 수집
                for output in cell.get('outputs', []):
                    if output.output_type == 'stream' and 'text' in output:
                        text = output['text']
                        if isinstance(text, list):
                            sections[current_section]["output"] += "".join(text)
                        else:
                            sections[current_section]["output"] += text
                    elif output.output_type == 'execute_result' and 'data' in output:
                        data = output['data']
                        if 'text/plain' in data:
                            text = data['text/plain']
                            if isinstance(text, list):
                                sections[current_section]["output"] += "".join(text)
                            else:
                                sections[current_section]["output"] += text
            
    return sections
            
    return sections

def check_outputs_for_image(nb: nbformat.NotebookNode, section_code: str = "") -> bool:
    """
    노트북 전체 혹은 특정 섹션의 출력에 이미지가 있는지 확인.
    (섹션별 출력 매핑은 어렵으므로, 여기서는 전체 스캔 혹은 심화 로직 필요.
     간단히 전체 스캔 사용 또는 셀 인덱스 기반 매핑 추천. 
     현재는 단순화를 위해 코드 소스가 제공된 경우 해당 소스가 있는 셀의 출력을 확인하도록 개선 가능하지만,
     일단 전체/부분 코드 매칭이 어려우므로 전체 노트북에서 이미지 존재 여부를 확인하되, 
     섹션 분리가 가능하다면 해당 섹션의 셀들만 검사)
    """
    # 섹션 코드가 주어지면 해당 코드를 포함하는 셀만 검색
    # 섹션 코드가 비어있으면(찾지 못했으면) 이미지가 없는 것으로 간주 (오탐 방지)
    if not section_code or not section_code.strip():
        return False

    target_cells = [c for c in nb.cells if c.cell_type == 'code' and c.source.strip() in section_code]
    
    for cell in target_cells:
        if 'outputs' in cell:
            for output in cell['outputs']:
                # display_data 또는 execute_result에 이미지 데이터가 있는지 확인
                data = output.get('data', {})
                if 'image/png' in data or 'image/jpeg' in data:
                    return True
    return False

def count_error_cells(nb: nbformat.NotebookNode) -> int:
    err_count = 0
    for cell in nb.cells:
        if cell.cell_type == 'code':
            for output in cell.get('outputs', []):
                if output.output_type == 'error':
                    err_count += 1
    return err_count

def has_keywords(text: str, keywords: Tuple[str, ...]) -> bool:
    for kw in keywords:
        if kw not in text:
            return False
    return True

def has_any_keyword(text: str, keywords: Tuple[str, ...]) -> bool:
    for kw in keywords:
        if kw in text:
            return True
    return False

# --- Core Grading Logic ---

def validate_q2_logic(source_code: str) -> Tuple[float, List[str]]:
    """
    Q2 논리 검증 및 감점 계산:
    1. 데이터 변수(A, B) 활용 여부 -> 미사용 시 1.0점 감점 (결과 0.5점)
    2. plt.bar 사용 여부 -> 미사용(다른 차트) 시 0.5점 감점 (결과 1.0점)
    """
    deduction = 0.0
    issues = []
    
    # 1. 변수 정의 찾기 (A=[], B=[] 등)
    potential_vars = set(re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=', source_code))
    
    # 2. 그래프 함수 호출 찾기 (plt.bar, plt.hist 등)
    plot_calls = re.findall(r'plt\.([a-z]+)\s*\((.*?)\)', source_code, re.DOTALL)
    
    if not plot_calls:
        # 그래프 함수 호출 자체가 없으면 로직 점수 없음 (이미지가 있어도 이상함)
        # 하지만 이미지는 check_outputs_for_image에서 확인했으므로 여기선 감점만 처리
        return 1.5, ["그래프 함수(plt.*) 호출 없음"]
    
    used_funcs = set()
    data_vars_used = False
    
    # 제외할 파이썬 내장/라이브러리 키워드
    common_funcs = {'range', 'len', 'random', 'randint', 'plt', 'list', 'int', 'str', 'lable', 'title', 'legend', 'show', 'rc', 'figure', 'xlabel', 'ylabel'}
    candidates = potential_vars - common_funcs
    
    for func_name, args in plot_calls:
        used_funcs.add(func_name)
        # 인자에 데이터 변수가 있는지 확인
        used_vars_in_args = set(re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)', args))
        if used_vars_in_args.intersection(candidates):
            data_vars_used = True
            
    # 채점 로직 적용
    
    # 기준 1: 데이터 변수를 사용했는가? (김예진 케이스: 랜덤값 직접 대입 시 감점)
    if not data_vars_used:
        # 데이터 변수를 안 썼으면 그래프 종류가 맞아도 큰 감점
        deduction += 1.0
        issues.append("데이터 변수(A, B 등) 미사용(랜덤값 직접 대입 등)")
    
    # 기준 2: bar 차트를 그렸는가? (윤채원 케이스: hist 사용 시 부분 감점)
    elif 'bar' not in used_funcs: # 데이터 변수는 씀
        deduction += 0.5
        issues.append(f"요구된 차트(bar) 미사용 (사용됨: {', '.join(used_funcs)})")
        
    return deduction, issues

def validate_q3_logic(source_code: str) -> Tuple[float, List[str]]:
    """
    Q3 코드 논리 검증 및 감점 계산:
    1. Pandas 사용 여부 확인 -> 사용 시 우수
    2. Pandas 미사용 시(csv 등) -> 데이터 숫자 변환(int, float 등) 필수
       - 누락 시 0.3점 감점
       - 정규식을 사용하여 randint 등의 오탐지 방지
    """
    deduction = 0.0
    issues = []
    
    # 1. Pandas 사용 확인 (우수)
    is_pandas_used = any(kw in source_code for kw in ('pandas', 'pd.read_', 'dataframe', 'read_csv'))
    
    if is_pandas_used:
        return 0.0, ["Pandas 활용 우수"]
        
    # 2. Pandas 미사용 시: 숫자 변환 확인
    # 정규식으로 int(), float() 등 명확한 변환 함수 호출 확인 (randint 오탐지 방지)
    # astype, to_numeric은 문자열 포함으로 충분
    numeric_patterns = [
        r'(^|[^a-zA-Z0-9_])int\s*\(',
        r'(^|[^a-zA-Z0-9_])float\s*\(',
        r'astype',
        r'to_numeric'
    ]
    
    found_conversion = False
    for pat in numeric_patterns:
        if re.search(pat, source_code):
            found_conversion = True
            break
            
    if not found_conversion:
        deduction += 0.3
        issues.append("데이터 숫자 변환(int, float 등) 누락 (-0.3)")
        
    return deduction, issues

def grade_notebook(nb: nbformat.NotebookNode, cfg: RubricConfig) -> GradeBreakdown:
    # full_text = notebook_full_text(nb) # Not used heavily anymore
    parts = split_by_markers(nb, cfg.q_markers)
    
    # 텍스트 확보 (Source Code)
    q1_source = parts["q1"]["source"]
    q2_source = parts["q2"]["source"]
    q3_source = parts["q3"]["source"]

    # 출력 텍스트 확보 (Outputs - for Regex check)
    q1_output = parts["q1"]["output"]
    
    comments = []

    # 1. Q1 Evaluation (Regex Check on OUTPUT)
    q1_hits = 0
    if cfg.q1_required_regex:
        # 출력 결과에서 확인
        q1_hits = len(re.findall(cfg.q1_required_regex, q1_output))
    
    if q1_hits >= cfg.q1_min_occurrences:
        q1_score = cfg.q1_score_max
    else:
        q1_score = 0.0
        if cfg.q1_required_regex:
            comments.append(f"Q1: 출력물에서 '{cfg.q1_required_regex}' 패턴 {cfg.q1_min_occurrences}회 미달 ({q1_hits}회).")
        else:
            comments.append("Q1: 학생 정보 regex 미설정.")

    # 2. Q2 Evaluation (Bar Chart)
    q2_has_image = check_outputs_for_image(nb, q2_source) 
    
    if q2_has_image:
        q2_score = cfg.q2_score_max
        # 로직 검증 (감점 적용)
        deduction, q2_issues = validate_q2_logic(q2_source)
        
        if deduction > 0:
            q2_score = max(0.0, q2_score - deduction)
            
        if q2_issues:
            comments.append(f"Q2: 그래프 출력 완료 ({', '.join(q2_issues)}).")
    else:
        # Partial credit check on SOURCE
        if has_any_keyword(q2_source, ("bar", "plt.bar")) and has_any_keyword(q2_source, ("random", "randint", "append")):
            q2_score = cfg.q2_partial_score
            comments.append("Q2: 그래프 출력 실패, 하지만 로직(bar, random) 발견되어 부분점수 부여.")
        else:
            q2_score = 0.0
            comments.append("Q2: 그래프 출력 없음 및 주요 키워드 누락.")

    # 3. Q3 Evaluation (CSV Plot)
    q3_has_image = check_outputs_for_image(nb, q3_source)
    
    if q3_has_image:
        q3_score = cfg.q3_score_max
        # 추가 로직 검증 (감점 적용)
        deduction, q3_issues = validate_q3_logic(q3_source)
        
        # 음수 방지 및 감점 적용
        if deduction > 0:
            q3_score = max(0.0, q3_score - deduction)
            
        if q3_issues:
            # "Pandas 활용 우수" 같은 메시지도 여기에 포함됨
            comments.append(f"Q3: 그래프 출력 완료 ({', '.join(q3_issues)}).")
        else:
            # 이슈 없고 Pandas도 아니면 그냥 그래프 출력 완료
            comments.append("Q3: 그래프 출력 완료.")
            
    else:
        # Partial credit check on SOURCE
        if has_any_keyword(q3_source, ("read_csv", "open")) and has_any_keyword(q3_source, ("plot", "plt.")):
            q3_score = cfg.q3_partial_score
            comments.append("Q3: 그래프 출력 실패, 하지만 로직(파일읽기, plot) 발견되어 부분점수 부여.")
        else:
            q3_score = 0.0
            comments.append("Q3: 그래프 출력 없음 및 주요 키워드 누락.")

    # 4. Execution Score
    err_count = count_error_cells(nb)
    if err_count == 0:
        execution_score = cfg.execution_score_max
    else:
        # 에러가 있어도 코드가 실행된 흔적(output 존재)이 많으면 점수 참작 가능하지만 단순화:
        # 2번이나 3번에서 부분점수를 받았다면(즉 코드는 짰는데 에러), 실행 점수는 0점 처리하되 총점에서 보전됨.
        # 혹은 에러 개수에 따라 차등? 여기선 0점 혹은 감점 처리.
        # User requested differentiation. Let's start with 0 for errors but comment.
        execution_score = 0.5 # 에러가 있으면 절반만 부여 (기존 로직 유지하되 조금 완화)
        comments.append(f"Execution: 에러 셀 {err_count}개 발견.")

    total = round(q1_score + q2_score + q3_score + execution_score, 2)

    return GradeBreakdown(
        q1_score=q1_score,
        q2_score=q2_score,
        q3_score=q3_score,
        execution_score=execution_score,
        total=total,
        comments=comments
    )

def grade_folder(input_dir: str, output_basename: str = "grading_results", cfg: Optional[RubricConfig] = None) -> None:
    cfg = cfg or RubricConfig()
    p = Path(input_dir)
    
    if not p.exists():
        print(f"Directory not found: {input_dir}")
        return

    rows = []
    
    for ipynb_path in sorted(p.glob("*.ipynb")):
        student_name, student_id = extract_student_info(ipynb_path.name)
        
        # 학생별 Regex 동적 설정
        if student_name and student_id:
            # 이름이나 학번 중 하나라도 포함되면 인정하는 유연한 방식 or 둘 다 포함
            # 문제 요구사항: "학번과 이름을 5번 출력" -> 보통 한 줄에 같이 출력함.
            current_regex = rf"({student_name}|{student_id})"
        else:
            current_regex = r"\d+" # Fallback

        # Rubric 복사 및 업데이트
        student_cfg = RubricConfig(
            q1_required_regex=current_regex,
            q1_min_occurrences=cfg.q1_min_occurrences,
            q2_keywords=cfg.q2_keywords,
            q3_keywords=cfg.q3_keywords,
            q_markers=cfg.q_markers
        )

        try:
            nb = nbformat.read(str(ipynb_path), as_version=4)
            result = grade_notebook(nb, student_cfg)
            
            rows.append({
                "file": ipynb_path.name,
                "student_name": student_name,
                "student_id": student_id,
                "Q1(1.0)": result.q1_score,
                "Q2(1.5)": result.q2_score,
                "Q3(1.5)": result.q3_score,
                "Exec(1.0)": result.execution_score,
                "Total(5.0)": result.total,
                "Comments": " / ".join(result.comments)
            })
        except Exception as e:
            print(f"Error processing {ipynb_path.name}: {e}")
            rows.append({
                "file": ipynb_path.name,
                "student_name": student_name,
                "student_id": student_id,
                "Total(5.0)": 0.0,
                "Comments": f"Processing Error: {str(e)}"
            })

    df = pd.DataFrame(rows)
    
    # Save
    # 결과 파일 경로 설정 (상위 폴더에 '폴더명결과.csv'로 저장)
    output_dir = p.parent
    folder_name = p.name
    
    result_csv = output_dir / f"{folder_name}결과.csv"
    result_xlsx = output_dir / f"{folder_name}결과.xlsx"
    
    df.to_csv(result_csv, index=False, encoding="utf-8-sig")
    df.to_excel(result_xlsx, index=False)
    
    print(f"\nGrading Complete. Results saved to:\n - {result_csv}\n - {result_xlsx}")
    print("\nPreview:")
    print(df[["student_name", "Q1(1.0)", "Q2(1.5)", "Q3(1.5)", "Exec(1.0)", "Total(5.0)"]])

if __name__ == "__main__":
    import sys
    
    print("=== Jupyter Notebook 채점 프로그램 ===")
    print("현재 위치:", Path.cwd())
    
    # 1. 명령행 인자가 있으면 그것을 사용
    if len(sys.argv) > 1:
        target_name = sys.argv[1]
    else:
        # 2. 없으면 사용자 입력 받기
        target_name = input("채점할 폴더 이름을 입력하세요 (예: 05, 10): ").strip()
        
    if not target_name:
        print("폴더 이름이 입력되지 않았습니다.")
    else:
        # 현재 경로 기준 하위 폴더 탐색
        base_dir = Path.cwd()
        target_dir = base_dir / target_name
        
        if target_dir.exists() and target_dir.is_dir():
            print(f"'{target_name}' 폴더 채점을 시작합니다...")
            try:
                grade_folder(str(target_dir))
                print("\n[완료] 채점이 성공적으로 끝났습니다.")
            except Exception as e:
                print(f"\n[오류] 채점 중 문제가 발생했습니다: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"\n[오류] 폴더를 찾을 수 없습니다: {target_dir}")
            print("경로를 확인해주세요.")

    # 실행 파일로 실행 시 바로 닫히지 않도록 대기
    input("\n종료하려면 엔터 키를 누르세요...")
