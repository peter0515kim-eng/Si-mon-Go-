import base64
import streamlit as st
from supabase import create_client, Client

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="시몬고",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── 전체 배경 ── */
[data-testid="stAppViewContainer"] { background: #f4f4f4; }
[data-testid="stHeader"] { background: transparent; }

/* ── 사이드바 ── */
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #ebebeb;
}

/* ── 기본 버튼 (secondary) ── */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    border: 1px solid #e0e0e0;
    background: #fff;
    color: #333;
    transition: all 0.15s;
}
.stButton > button:hover { border-color: #ff4b4b; color: #ff4b4b; }

/* ── Primary 버튼 ── */
.stButton > button[kind="primary"],
.stFormSubmitButton > button {
    background: #ff4b4b !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 15px !important;
}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button:hover {
    background: #e03e3e !important;
}

/* ── 폼 내부 border 제거 ── */
[data-testid="stForm"] {
    border: none !important;
    padding: 0 !important;
    background: transparent !important;
}

/* ── 탭 스타일 ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 2px solid #ebebeb;
}
.stTabs [data-baseweb="tab"] {
    font-weight: 600;
    color: #888;
    padding: 8px 20px;
    border-radius: 0;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
}
.stTabs [aria-selected="true"] {
    color: #ff4b4b !important;
    border-bottom: 2px solid #ff4b4b !important;
    background: transparent !important;
}

/* ── 인증 폼 카드화 ── */
[data-testid="stForm"] {
    background: #fff !important;
    border-radius: 14px !important;
    padding: 36px 36px 28px !important;
    box-shadow: 0 2px 16px rgba(0,0,0,0.07) !important;
    border: none !important;
    margin-top: 40px;
}
.brand-name  { font-size: 28px; font-weight: 900; color: #ff4b4b; letter-spacing: -1px; }
.brand-sub   { font-size: 11px; font-weight: 600; color: #ff4b4b; opacity: .55; letter-spacing: 2px; margin-top: 2px; }
.brand-tag   { font-size: 13px; color: #999; margin-top: 6px; margin-bottom: 24px; }
.auth-divider{ border: none; border-top: 1px solid #f0f0f0; margin: 0 0 24px; }
.auth-section-title { font-size: 18px; font-weight: 700; color: #111; margin-bottom: 16px; }
.auth-foot   { text-align: center; font-size: 13px; color: #aaa; margin-top: 14px; }

/* ── 페이지 헤더 ── */
.page-header {
    padding: 24px 0 16px;
    border-bottom: 2px solid #ebebeb;
    margin-bottom: 24px;
}
.page-header h2 { font-size: 22px; font-weight: 800; color: #111; margin: 0; }
.page-header span { font-size: 13px; color: #999; margin-top: 4px; display: block; }

/* ── 콘텐츠 카드 ── */
.card {
    background: #fff;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06);
    margin-bottom: 12px;
}
.card-title  { font-size: 15px; font-weight: 700; color: #111; margin-bottom: 4px; }
.card-meta   { font-size: 13px; color: #777; margin-bottom: 10px; }
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}
.badge-yellow { background: #fff8e1; color: #f59f00; }
.badge-green  { background: #e6f9f0; color: #1aab6d; }
.badge-red    { background: #fff0f0; color: #ff4b4b; }
.badge-blue   { background: #e8f4ff; color: #3b82f6; }
.badge-gray   { background: #f0f0f0; color: #888; }

/* ── 지표 카드 ── */
[data-testid="stMetric"] {
    background: #fff;
    border-radius: 10px;
    padding: 16px 20px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.05);
}

/* ── 사이드바 브랜드 ── */
.sb-brand    { font-size: 20px; font-weight: 900; color: #ff4b4b; letter-spacing: -0.5px; }
.sb-user     { font-size: 14px; font-weight: 600; color: #222; margin-top: 6px; }
.sb-role     { font-size: 12px; color: #999; margin-top: 2px; }
.sb-notice   { background: #fff8f8; border-left: 3px solid #ff4b4b; border-radius: 0 6px 6px 0;
               padding: 10px 12px; font-size: 12px; color: #555; line-height: 1.6; margin-top: 8px; }
</style>
""", unsafe_allow_html=True)

# ─── Supabase Client ─────────────────────────────────────────────────────────
@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

# ─── Session State Init ──────────────────────────────────────────────────────
for key, default in {
    "logged_in":     False,
    "user_id":       None,
    "user_role":     None,
    "user_nickname": None,
    "auth_page":     "login",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── DB Helpers ───────────────────────────────────────────────────────────────
def db_get_categories():
    try:
        return supabase.table("categories").select("*").order("id").execute().data
    except Exception:
        return []

def db_get_all_missions():
    try:
        return (
            supabase.table("missions")
            .select("*, categories(name)")
            .order("created_at", desc=True)
            .execute().data
        )
    except Exception:
        return []

def db_get_employer_mission_ids(employer_id):
    try:
        res = supabase.table("missions").select("id").eq("employer_id", employer_id).execute()
        return [r["id"] for r in res.data]
    except Exception:
        return []

def db_get_applications_for_employer(employer_id):
    try:
        ids = db_get_employer_mission_ids(employer_id)
        if not ids:
            return []
        return (
            supabase.table("applications")
            .select("*, missions(id, title, reward, location_name), profiles(nickname)")
            .in_("mission_id", ids)
            .order("applied_at", desc=True)
            .execute().data
        )
    except Exception:
        return []

def db_get_senior_applications(senior_id):
    try:
        return (
            supabase.table("applications")
            .select("*, missions(title, reward, location_name, categories(name))")
            .eq("senior_id", senior_id)
            .order("applied_at", desc=True)
            .execute().data
        )
    except Exception:
        return []

STATUS_BADGE = {
    "APPLIED":   ("badge-yellow", "대기 중"),
    "ACCEPTED":  ("badge-green",  "매칭 수락"),
    "REJECTED":  ("badge-red",    "거절됨"),
    "SUBMITTED": ("badge-blue",   "검토 중"),
    "COMPLETED": ("badge-gray",   "완료"),
    "Pending":   ("badge-yellow", "대기 중"),
}

# ─── Auth Helpers ─────────────────────────────────────────────────────────────
def do_login(email, password):
    try:
        res  = supabase.auth.sign_in_with_password({"email": email, "password": password})
        user = res.user
        if not user:
            return "이메일 또는 비밀번호가 올바르지 않습니다."
        prof = (
            supabase.table("profiles")
            .select("id, nickname, role_type")
            .eq("id", user.id)
            .execute().data
        )
        if not prof:
            return "프로필 정보를 찾을 수 없습니다. 다시 가입해 주세요."
        p = prof[0]
        st.session_state.update({
            "logged_in": True, "user_id": p["id"],
            "user_role": p["role_type"], "user_nickname": p["nickname"],
        })
        return None
    except Exception as e:
        msg = str(e)
        if "Email not confirmed" in msg:
            return "이메일 인증이 필요합니다. 인증 메일을 확인해 주세요."
        if "Invalid login credentials" in msg:
            return "이메일 또는 비밀번호가 올바르지 않습니다."
        return "로그인 중 오류가 발생했습니다."

def do_signup(email, password, nickname, role):
    try:
        res  = supabase.auth.sign_up({"email": email, "password": password})
        user = res.user
        if not user:
            return "회원가입 처리 중 오류가 발생했습니다."
        supabase.table("profiles").insert({
            "id": user.id, "email": email,
            "nickname": nickname, "role_type": role,
            "phone_number": "000-0000-0000",
        }).execute()
        return None
    except Exception as e:
        msg = str(e)
        if "User already registered" in msg:
            return "이미 가입된 이메일입니다."
        if "Password should be at least" in msg:
            return "비밀번호는 최소 6자 이상이어야 합니다."
        return f"오류: {msg}"

# ─── Login Page ───────────────────────────────────────────────────────────────
def show_login():
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        with st.form("login_form"):
            st.markdown("""
<div class="brand-name">시몬고</div>
<div class="brand-sub">SI-MON-GO</div>
<div class="brand-tag">액티브 시니어를 위한 일자리 매칭 플랫폼</div>
<hr class="auth-divider">
<div class="auth-section-title">로그인</div>
""", unsafe_allow_html=True)
            email    = st.text_input("이메일", placeholder="example@email.com")
            password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
            btn      = st.form_submit_button("로그인", type="primary", use_container_width=True)
            if btn:
                if not email.strip() or not password.strip():
                    st.error("이메일과 비밀번호를 모두 입력해주세요.")
                else:
                    err = do_login(email.strip(), password.strip())
                    if err:
                        st.error(err)
                    else:
                        st.rerun()

        st.markdown('<div class="auth-foot">아직 계정이 없으신가요?</div>', unsafe_allow_html=True)
        if st.button("회원가입", use_container_width=True):
            st.session_state["auth_page"] = "signup"
            st.rerun()

# ─── Signup Page ──────────────────────────────────────────────────────────────
def show_signup():
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        with st.form("signup_form"):
            st.markdown("""
<div class="brand-name">시몬고</div>
<div class="brand-sub">SI-MON-GO</div>
<div class="brand-tag">액티브 시니어를 위한 일자리 매칭 플랫폼</div>
<hr class="auth-divider">
<div class="auth-section-title">회원가입</div>
""", unsafe_allow_html=True)
            # form content starts inline below
            email    = st.text_input("이메일", placeholder="example@email.com")
            password = st.text_input("비밀번호", type="password", placeholder="6자 이상")
            pw_check = st.text_input("비밀번호 확인", type="password", placeholder="비밀번호를 한 번 더 입력")
            nickname = st.text_input("닉네임", placeholder="서비스에서 표시될 이름")
            st.markdown("**나는**")
            role = st.radio(
                "역할",
                options=["Senior", "Employer"],
                format_func=lambda r: "시니어  —  일감을 찾고 있어요" if r == "Senior" else "고용주  —  일손을 구하고 있어요",
                label_visibility="collapsed",
            )
            btn = st.form_submit_button("가입하기", type="primary", use_container_width=True)
            if btn:
                errors = []
                if not email.strip():       errors.append("이메일을 입력해주세요.")
                if not password.strip():    errors.append("비밀번호를 입력해주세요.")
                elif len(password) < 6:     errors.append("비밀번호는 최소 6자 이상이어야 합니다.")
                elif password != pw_check:  errors.append("비밀번호가 일치하지 않습니다.")
                if not nickname.strip():    errors.append("닉네임을 입력해주세요.")
                if errors:
                    for e in errors: st.error(e)
                else:
                    err = do_signup(email.strip(), password.strip(), nickname.strip(), role)
                    if err:
                        st.error(err)
                    else:
                        st.success("가입 완료! 로그인 페이지로 이동합니다.")
                        st.session_state["auth_page"] = "login"
                        st.rerun()

        st.markdown('<div class="auth-foot">이미 계정이 있으신가요?</div>', unsafe_allow_html=True)
        if st.button("로그인으로 돌아가기", use_container_width=True):
            st.session_state["auth_page"] = "login"
            st.rerun()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
def show_sidebar():
    role_label = "고용주" if st.session_state["user_role"] == "Employer" else "시니어"
    st.sidebar.markdown(f"""
<div class="sb-brand">시몬고</div>
<div class="sb-user">{st.session_state['user_nickname']}</div>
<div class="sb-role">{role_label} 계정</div>
""", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    if st.session_state["user_role"] == "Senior":
        st.sidebar.markdown("""
<div class="sb-notice">
매칭 수락 후 완료 보고를 하지 않으면 성실도 점수가 하락합니다.
성실도가 낮으면 향후 매칭이 제한될 수 있어요.
</div>
""", unsafe_allow_html=True)
        st.sidebar.markdown("")

    if st.sidebar.button("로그아웃", use_container_width=True):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
        st.session_state.update({
            "logged_in": False, "user_id": None,
            "user_role": None, "user_nickname": None, "auth_page": "login",
        })
        st.rerun()

# ─── Employer View ────────────────────────────────────────────────────────────
def show_employer():
    st.markdown("""
<div class="page-header">
  <h2>고용주 대시보드</h2>
  <span>미션을 등록하고 지원자를 관리하세요</span>
</div>
""", unsafe_allow_html=True)

    tab_reg, tab_mgmt = st.tabs(["  미션 등록  ", "  지원자 관리  "])

    # ── 미션 등록 ──
    with tab_reg:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">새 미션 등록</div>', unsafe_allow_html=True)
        categories = db_get_categories()
        if not categories:
            st.warning("카테고리를 불러올 수 없습니다.")
        else:
            cat_map = {c["name"]: c["id"] for c in categories}
            with st.form("form_register_mission", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    title    = st.text_input("미션 제목")
                    cat_name = st.selectbox("카테고리", list(cat_map.keys()))
                    reward   = st.number_input("보상 금액 (원)", min_value=0, step=1000, value=10000)
                with c2:
                    location     = st.text_input("수행 위치")
                    verify_guide = st.text_input("인증 사진 가이드")
                    is_outdoor   = st.toggle("실외 미션")
                description = st.text_area("업무 내용", height=100)
                submitted   = st.form_submit_button("등록하기", type="primary")
                if submitted:
                    if not all([title.strip(), description.strip(), location.strip(), verify_guide.strip()]):
                        st.error("모든 항목을 입력해 주세요.")
                    else:
                        try:
                            supabase.table("missions").insert({
                                "employer_id": st.session_state["user_id"],
                                "category_id": cat_map[cat_name],
                                "title": title.strip(), "description": description.strip(),
                                "reward": reward, "location_name": location.strip(),
                                "is_outdoor": is_outdoor, "verification_guide": verify_guide.strip(),
                            }).execute()
                            st.success("미션이 등록되었습니다!")
                            st.balloons()
                        except Exception:
                            st.error("오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── 지원자 관리 ──
    with tab_mgmt:
        apps = db_get_applications_for_employer(st.session_state["user_id"])
        if not apps:
            st.markdown('<div class="card"><div class="card-meta">아직 지원자가 없습니다.</div></div>', unsafe_allow_html=True)
        else:
            for app in apps:
                mission  = app.get("missions") or {}
                profile  = app.get("profiles") or {}
                status   = app["status"]
                cls, lbl = STATUS_BADGE.get(status, ("badge-gray", status))

                st.markdown(f"""
<div class="card">
  <div class="card-title">{mission.get('title','알 수 없음')}</div>
  <div class="card-meta">
    지원자: <b>{profile.get('nickname','알 수 없음')}</b> &nbsp;|&nbsp;
    보상: <b>{mission.get('reward',0):,}원</b> &nbsp;|&nbsp;
    <span class="badge {cls}">{lbl}</span>
  </div>
</div>
""", unsafe_allow_html=True)

                if status in ("APPLIED", "Pending"):
                    c1, c2, _ = st.columns([1, 1, 6])
                    with c1:
                        if st.button("수락", key=f"acc_{app['id']}", type="primary"):
                            try:
                                supabase.table("applications").update({"status": "ACCEPTED"}).eq("id", app["id"]).execute()
                                st.rerun()
                            except Exception:
                                st.error("오류가 발생했습니다.")
                    with c2:
                        if st.button("거절", key=f"rej_{app['id']}"):
                            try:
                                supabase.table("applications").update({"status": "REJECTED"}).eq("id", app["id"]).execute()
                                st.rerun()
                            except Exception:
                                st.error("오류가 발생했습니다.")

                elif status == "SUBMITTED":
                    note      = app.get("completion_note") or ""
                    photo_url = app.get("completion_photo_url")
                    st.markdown(f'<div style="padding:8px 0;font-size:14px;color:#444;">📝 {note}</div>', unsafe_allow_html=True)
                    if photo_url:
                        try:
                            st.image(photo_url, width=280)
                        except Exception:
                            st.caption(f"사진 로드 실패 — [직접 열기]({photo_url})")
                    else:
                        st.caption("(인증 사진 없음)")
                    if st.button("💰 수령 완료 처리", key=f"pay_{app['id']}", type="primary"):
                        # 1단계: application 상태 업데이트 (핵심)
                        try:
                            supabase.table("applications").update({"status": "COMPLETED"}).eq("id", app["id"]).execute()
                        except Exception as e:
                            st.error(f"완료 처리 실패: {e}")
                            st.stop()
                        # 2단계: 미션 삭제 (실패해도 완료 처리는 유지)
                        mid = mission.get("id") or app.get("mission_id")
                        if mid:
                            try:
                                supabase.table("missions").delete().eq("id", mid).execute()
                            except Exception:
                                pass  # 삭제 실패는 무시 — 완료 처리는 이미 됨
                        st.success("완료 처리되었습니다!")
                        st.balloons()
                        st.rerun()

# ─── Senior View ──────────────────────────────────────────────────────────────
def show_senior():
    st.markdown("""
<div class="page-header">
  <h2>일감 찾기</h2>
  <span>내 주변 미션을 찾고 지원해보세요</span>
</div>
""", unsafe_allow_html=True)

    tab_board, tab_mine = st.tabs(["  일감 보드  ", "  나의 지원 현황  "])

    # ── 일감 보드 ──
    with tab_board:
        all_missions   = db_get_all_missions()
        my_apps        = db_get_senior_applications(st.session_state["user_id"])
        applied_ids    = {a["mission_id"] for a in my_apps}
        accepted_count = sum(1 for a in my_apps if a["status"] in ("ACCEPTED", "SUBMITTED", "COMPLETED"))

        c1, c2, c3 = st.columns(3)
        c1.metric("전체 미션",    f"{len(all_missions)}건")
        c2.metric("내 지원",      f"{len(my_apps)}건")
        c3.metric("매칭 승인",    f"{accepted_count}건")

        st.markdown("<br>", unsafe_allow_html=True)

        if not all_missions:
            st.markdown('<div class="card"><div class="card-meta">현재 등록된 미션이 없습니다.</div></div>', unsafe_allow_html=True)
        else:
            for m in all_missions:
                cat     = (m.get("categories") or {}).get("name", "기타")
                outdoor = m.get("is_outdoor", False)
                applied = m["id"] in applied_ids

                with st.expander(f"**{m.get('title','')}**  ·  {m.get('location_name','')}  ·  {m.get('reward',0):,}원"):
                    cl, cr = st.columns([3, 2])
                    with cl:
                        st.markdown(f"""
**업무 내용**
{m.get('description','')}

**인증 가이드**
{m.get('verification_guide','')}
""")
                    with cr:
                        st.markdown(f"""
**보상** : {m.get('reward',0):,}원
**위치** : {m.get('location_name','')}
**분류** : {cat} · {'실외' if outdoor else '실내'}
""")
                    if applied:
                        st.button("지원 완료", key=f"done_{m['id']}", disabled=True)
                    else:
                        if st.button("지원하기", key=f"apply_{m['id']}", type="primary"):
                            try:
                                supabase.table("applications").insert({
                                    "mission_id": m["id"],
                                    "senior_id":  st.session_state["user_id"],
                                    "status":     "APPLIED",
                                }).execute()
                                st.success("지원이 완료되었습니다!")
                                st.rerun()
                            except Exception:
                                st.error("오류가 발생했습니다.")

    # ── 나의 지원 현황 ──
    with tab_mine:
        my_apps = db_get_senior_applications(st.session_state["user_id"])
        if not my_apps:
            st.markdown('<div class="card"><div class="card-meta">아직 지원한 미션이 없습니다.</div></div>', unsafe_allow_html=True)
        else:
            for app in my_apps:
                mission  = app.get("missions") or {}
                cat      = (mission.get("categories") or {}).get("name", "기타")
                status   = app["status"]
                cls, lbl = STATUS_BADGE.get(status, ("badge-gray", status))

                st.markdown(f"""
<div class="card">
  <div class="card-title">{mission.get('title','알 수 없음')}</div>
  <div class="card-meta">
    {cat} &nbsp;·&nbsp; {mission.get('location_name','')} &nbsp;·&nbsp; {mission.get('reward',0):,}원
    &nbsp;&nbsp;<span class="badge {cls}">{lbl}</span>
  </div>
</div>
""", unsafe_allow_html=True)

                if status == "ACCEPTED":
                    with st.expander("완료 보고서 작성하기"):
                        with st.form(f"comp_{app['id']}"):
                            note  = st.text_area("수행 내용", placeholder="어떤 일을 했는지 자세히 적어주세요")
                            photo = st.file_uploader("인증 사진 (선택)", type=["jpg", "jpeg", "png"])
                            sub   = st.form_submit_button("제출하기", type="primary")
                            if sub:
                                if not note.strip():
                                    st.error("수행 내용을 입력해주세요.")
                                else:
                                    photo_url = None
                                    if photo:
                                        raw = photo.read()
                                        b64 = base64.b64encode(raw).decode()
                                        photo_url = f"data:{photo.type};base64,{b64}"
                                    try:
                                        supabase.table("applications").update({
                                            "status": "SUBMITTED",
                                            "completion_note": note.strip(),
                                            "completion_photo_url": photo_url,
                                        }).eq("id", app["id"]).execute()
                                        st.success("완료 보고서가 제출되었습니다!")
                                        st.rerun()
                                    except Exception:
                                        st.error("오류가 발생했습니다.")

# ─── Main Routing ─────────────────────────────────────────────────────────────
if not st.session_state["logged_in"]:
    if st.session_state["auth_page"] == "signup":
        show_signup()
    else:
        show_login()
else:
    show_sidebar()
    if st.session_state["user_role"] == "Employer":
        show_employer()
    else:
        show_senior()
