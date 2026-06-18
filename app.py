import streamlit as st
from supabase import create_client, Client

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="시몬고 (Si-Mon-GO)",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
    "auth_page":     "login",   # "login" | "signup"
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── DB Helper Functions ──────────────────────────────────────────────────────
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
            .execute()
            .data
        )
    except Exception:
        return []

def db_get_employer_mission_ids(employer_id: str):
    try:
        res = supabase.table("missions").select("id").eq("employer_id", employer_id).execute()
        return [r["id"] for r in res.data]
    except Exception:
        return []

def db_get_applications_for_employer(employer_id: str):
    try:
        mission_ids = db_get_employer_mission_ids(employer_id)
        if not mission_ids:
            return []
        return (
            supabase.table("applications")
            .select("*, missions(id, title, reward, location_name), profiles(nickname)")
            .in_("mission_id", mission_ids)
            .order("applied_at", desc=True)
            .execute()
            .data
        )
    except Exception:
        return []

def db_get_senior_applications(senior_id: str):
    try:
        return (
            supabase.table("applications")
            .select("*, missions(title, reward, location_name, categories(name))")
            .eq("senior_id", senior_id)
            .order("applied_at", desc=True)
            .execute()
            .data
        )
    except Exception:
        return []

STATUS_LABELS = {
    "APPLIED":   ("🟡", "대기 중"),
    "ACCEPTED":  ("🟢", "매칭 수락됨"),
    "REJECTED":  ("🔴", "거절됨"),
    "SUBMITTED": ("📝", "완료 제출됨 – 고용주 확인 대기 중"),
    "COMPLETED": ("✅", "완료됨"),
    "Pending":   ("🟡", "대기 중"),
}


# ─── AUTH HELPERS ─────────────────────────────────────────────────────────────
def do_login(email: str, password: str):
    """Supabase Auth 로그인 → 프로필 조회 → 세션 설정. 오류 메시지 반환, 성공 시 None."""
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        user = res.user
        if not user:
            return "이메일 또는 비밀번호가 올바르지 않습니다."

        profile = (
            supabase.table("profiles")
            .select("id, nickname, role_type")
            .eq("id", user.id)
            .execute()
            .data
        )
        if not profile:
            return "프로필 정보를 찾을 수 없습니다. 다시 가입해 주세요."

        p = profile[0]
        st.session_state["logged_in"]     = True
        st.session_state["user_id"]       = p["id"]
        st.session_state["user_role"]     = p["role_type"]
        st.session_state["user_nickname"] = p["nickname"]
        return None
    except Exception as e:
        msg = str(e)
        if "Email not confirmed" in msg:
            return "이메일 인증이 필요합니다. 가입 시 받은 인증 메일을 확인해 주세요."
        if "Invalid login credentials" in msg:
            return "이메일 또는 비밀번호가 올바르지 않습니다."
        return "로그인 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."


def do_signup(email: str, password: str, nickname: str, role: str):
    """Supabase Auth 회원가입 → profiles 삽입. 오류 메시지 반환, 성공 시 None."""
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        user = res.user
        if not user:
            return "회원가입 처리 중 오류가 발생했습니다."

        supabase.table("profiles").insert({
            "id":           user.id,
            "email":        email,
            "nickname":     nickname,
            "role_type":    role,
            "phone_number": "000-0000-0000",
        }).execute()

        return None
    except Exception as e:
        msg = str(e)
        if "User already registered" in msg:
            return "이미 가입된 이메일입니다."
        if "Password should be at least" in msg:
            return "비밀번호는 최소 6자 이상이어야 합니다."
        return f"회원가입 중 오류가 발생했습니다: {msg}"


# ─── AUTH PAGE STYLE ─────────────────────────────────────────────────────────
AUTH_CSS = """
<style>
/* 전체 배경 */
[data-testid="stAppViewContainer"] {
    background-color: #f7f7f7;
}
/* 인증 카드 */
.auth-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 40px 36px 32px 36px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    margin-top: 48px;
}
/* 브랜드 로고 영역 */
.brand-block {
    margin-bottom: 28px;
}
.brand-name {
    font-size: 26px;
    font-weight: 800;
    color: #ff4b4b;
    letter-spacing: -0.5px;
    line-height: 1.1;
}
.brand-en {
    font-size: 13px;
    font-weight: 500;
    color: #ff4b4b;
    letter-spacing: 1px;
    opacity: 0.7;
}
.brand-tagline {
    font-size: 13px;
    color: #888;
    margin-top: 4px;
}
/* 섹션 제목 */
.auth-title {
    font-size: 20px;
    font-weight: 700;
    color: #111;
    margin-bottom: 20px;
}
/* 구분선 */
.auth-divider {
    border: none;
    border-top: 1px solid #ebebeb;
    margin: 20px 0;
}
/* 전환 링크 영역 */
.auth-switch {
    text-align: center;
    font-size: 13px;
    color: #888;
    margin-top: 16px;
}
/* 역할 선택 박스 */
.role-desc {
    font-size: 12px;
    color: #aaa;
    margin-top: -8px;
    margin-bottom: 12px;
}
</style>
"""

# ─── LOGIN PAGE ───────────────────────────────────────────────────────────────
def show_login():
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        st.markdown("""
<div class="auth-card">
  <div class="brand-block">
    <div class="brand-name">시몬고</div>
    <div class="brand-en">SI-MON-GO</div>
    <div class="brand-tagline">액티브 시니어를 위한 일자리 매칭 플랫폼</div>
  </div>
  <hr class="auth-divider">
  <div class="auth-title">로그인</div>
</div>
""", unsafe_allow_html=True)

        with st.form("login_form"):
            email     = st.text_input("이메일", placeholder="example@email.com", label_visibility="visible")
            password  = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
            login_btn = st.form_submit_button("로그인", type="primary", use_container_width=True)

            if login_btn:
                if not email.strip() or not password.strip():
                    st.error("이메일과 비밀번호를 모두 입력해주세요.")
                else:
                    err = do_login(email.strip(), password.strip())
                    if err:
                        st.error(err)
                    else:
                        st.rerun()

        st.markdown("""
<div class="auth-switch">
    아직 계정이 없으신가요?
</div>
""", unsafe_allow_html=True)
        if st.button("회원가입", use_container_width=True):
            st.session_state["auth_page"] = "signup"
            st.rerun()


# ─── SIGNUP PAGE ──────────────────────────────────────────────────────────────
def show_signup():
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        st.markdown("""
<div class="auth-card">
  <div class="brand-block">
    <div class="brand-name">시몬고</div>
    <div class="brand-en">SI-MON-GO</div>
    <div class="brand-tagline">액티브 시니어를 위한 일자리 매칭 플랫폼</div>
  </div>
  <hr class="auth-divider">
  <div class="auth-title">회원가입</div>
</div>
""", unsafe_allow_html=True)

        with st.form("signup_form"):
            email    = st.text_input("이메일", placeholder="example@email.com")
            password = st.text_input("비밀번호", type="password", placeholder="6자 이상 입력")
            pw_check = st.text_input("비밀번호 확인", type="password", placeholder="비밀번호를 한 번 더 입력")
            nickname = st.text_input("닉네임", placeholder="서비스에서 표시될 이름")

            st.markdown("**나는**")
            role = st.radio(
                "역할",
                options=["Senior", "Employer"],
                format_func=lambda r: "시니어  —  일감을 찾고 있어요" if r == "Senior" else "고용주  —  일손을 구하고 있어요",
                horizontal=False,
                label_visibility="collapsed",
            )

            signup_btn = st.form_submit_button("가입하기", type="primary", use_container_width=True)

            if signup_btn:
                errors = []
                if not email.strip():
                    errors.append("이메일을 입력해주세요.")
                if not password.strip():
                    errors.append("비밀번호를 입력해주세요.")
                elif len(password) < 6:
                    errors.append("비밀번호는 최소 6자 이상이어야 합니다.")
                elif password != pw_check:
                    errors.append("비밀번호가 일치하지 않습니다.")
                if not nickname.strip():
                    errors.append("닉네임을 입력해주세요.")

                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    err = do_signup(email.strip(), password.strip(), nickname.strip(), role)
                    if err:
                        st.error(err)
                    else:
                        st.success("가입이 완료되었습니다. 로그인 페이지로 이동합니다.")
                        st.session_state["auth_page"] = "login"
                        st.rerun()

        st.markdown("""
<div class="auth-switch">
    이미 계정이 있으신가요?
</div>
""", unsafe_allow_html=True)
        if st.button("로그인으로 돌아가기", use_container_width=True):
            st.session_state["auth_page"] = "login"
            st.rerun()


# ─── SIDEBAR (로그인 후) ──────────────────────────────────────────────────────
def show_sidebar():
    st.sidebar.title("🎯 시몬고")
    role_label = "👨‍💼 고용주" if st.session_state["user_role"] == "Employer" else "🧑 시니어"
    st.sidebar.markdown(f"**{st.session_state['user_nickname']}** ({role_label})")
    st.sidebar.markdown("---")

    if st.session_state["user_role"] == "Senior":
        st.sidebar.markdown("**📊 성실도 안내**")
        st.sidebar.info(
            "매칭 수락 후 미션을 수행하지 않거나 완료 보고를 미제출하면 "
            "성실도 점수가 하락합니다. 성실도가 낮을 경우 향후 매칭 수락이 "
            "제한될 수 있으니 책임감 있게 참여해 주세요."
        )
        st.sidebar.markdown("---")

    if st.sidebar.button("🚪 로그아웃", use_container_width=True):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
        for key in ["logged_in", "user_id", "user_role", "user_nickname"]:
            st.session_state[key] = None
        st.session_state["logged_in"] = False
        st.session_state["auth_page"] = "login"
        st.rerun()


# ─── EMPLOYER VIEW ────────────────────────────────────────────────────────────
def show_employer():
    st.title("👨‍💼 고용주 관제 대시보드")
    tab_reg, tab_mgmt = st.tabs(["➕ 신규 미션 등록", "📋 지원자 현황 관리"])

    with tab_reg:
        st.subheader("신규 미션 등록 구역")
        categories = db_get_categories()

        if not categories:
            st.warning("⚠️ 카테고리를 불러올 수 없습니다. Supabase 연결을 확인하세요.")
        else:
            cat_map = {c["name"]: c["id"] for c in categories}

            with st.form("form_register_mission", clear_on_submit=True):
                title        = st.text_input("미션 제목")
                cat_name     = st.selectbox("카테고리 선택", list(cat_map.keys()))
                description  = st.text_area("업무 내용")
                reward       = st.number_input("보상 금액 (원)", min_value=0, step=1000, value=10000)
                location     = st.text_input("수행 위치명")
                is_outdoor   = st.toggle("실외 여부 (토글 ON = 실외)")
                verify_guide = st.text_input("인증 사진 가이드")
                submitted    = st.form_submit_button("✅ 미션 등록하기", type="primary")

                if submitted:
                    if not all([title.strip(), description.strip(), location.strip(), verify_guide.strip()]):
                        st.error("❌ 모든 필드를 빠짐없이 입력해 주세요.")
                    else:
                        try:
                            supabase.table("missions").insert({
                                "employer_id":        st.session_state["user_id"],
                                "category_id":        cat_map[cat_name],
                                "title":              title.strip(),
                                "description":        description.strip(),
                                "reward":             reward,
                                "location_name":      location.strip(),
                                "is_outdoor":         is_outdoor,
                                "verification_guide": verify_guide.strip(),
                            }).execute()
                            st.success("🎉 미션이 성공적으로 등록되었습니다!")
                            st.balloons()
                        except Exception:
                            st.error("❌ 작업 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")

    with tab_mgmt:
        st.subheader("지원자 현황 및 매칭 결정")
        apps = db_get_applications_for_employer(st.session_state["user_id"])

        if not apps:
            st.warning("⚠️ 현재 표시할 내역이 존재하지 않습니다.")
        else:
            for app in apps:
                mission     = app.get("missions") or {}
                profile     = app.get("profiles") or {}
                status      = app["status"]
                icon, label = STATUS_LABELS.get(status, ("⚪", status))

                with st.container(border=True):
                    st.markdown(f"**🎯 미션:** {mission.get('title', '알 수 없음')}")
                    st.markdown(f"- 지원 시니어: **{profile.get('nickname', '알 수 없음')}**")
                    st.markdown(f"- 현재 상태: {icon} **{label}**")

                    if status in ("APPLIED", "Pending"):
                        c1, c2, _ = st.columns([1, 1, 5])
                        with c1:
                            if st.button("✅ 수락", key=f"acc_{app['id']}", type="primary"):
                                try:
                                    supabase.table("applications").update(
                                        {"status": "ACCEPTED"}
                                    ).eq("id", app["id"]).execute()
                                    st.rerun()
                                except Exception:
                                    st.error("❌ 작업 중 오류가 발생했습니다.")
                        with c2:
                            if st.button("❌ 거절", key=f"rej_{app['id']}"):
                                try:
                                    supabase.table("applications").update(
                                        {"status": "REJECTED"}
                                    ).eq("id", app["id"]).execute()
                                    st.rerun()
                                except Exception:
                                    st.error("❌ 작업 중 오류가 발생했습니다.")

                    elif status == "SUBMITTED":
                        note      = app.get("completion_note") or ""
                        photo_url = app.get("completion_photo_url")
                        st.markdown(f"**📝 완료 내용:** {note}")
                        if photo_url:
                            st.image(photo_url, caption="시니어 인증 사진", width=300)
                        else:
                            st.caption("(인증 사진 없음)")

                        if st.button("💰 금액 수령 완료", key=f"pay_{app['id']}", type="primary"):
                            try:
                                supabase.table("applications").update(
                                    {"status": "COMPLETED"}
                                ).eq("id", app["id"]).execute()
                                mission_id = mission.get("id") or app.get("mission_id")
                                if mission_id:
                                    supabase.table("missions").delete().eq("id", mission_id).execute()
                                st.success("✅ 금액 수령 완료! 해당 미션이 종료되었습니다.")
                                st.balloons()
                                st.rerun()
                            except Exception:
                                st.error("❌ 작업 중 오류가 발생했습니다.")


# ─── SENIOR VIEW ──────────────────────────────────────────────────────────────
def show_senior():
    st.title("🎯 시몬고 실시간 미션 보드")
    tab_board, tab_mine = st.tabs(["🔍 일감 찾기 보드", "🎯 나의 지원/매칭 현황"])

    with tab_board:
        all_missions   = db_get_all_missions()
        my_apps        = db_get_senior_applications(st.session_state["user_id"])
        applied_ids    = {a["mission_id"] for a in my_apps}
        accepted_count = sum(
            1 for a in my_apps if a["status"] in ("ACCEPTED", "SUBMITTED", "COMPLETED")
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("전체 모집 미션",   f"{len(all_missions)} 건")
        c2.metric("내가 지원한 미션", f"{len(my_apps)} 건")
        c3.metric("매칭 승인된 미션", f"{accepted_count} 건")

        st.markdown("---")

        if not all_missions:
            st.warning("⚠️ 현재 표시할 내역이 존재하지 않습니다.")
        else:
            st.subheader("📋 오픈 미션 리스트")
            for m in all_missions:
                cat     = (m.get("categories") or {}).get("name", "기타")
                outdoor = m.get("is_outdoor", False)
                applied = m["id"] in applied_ids
                label   = (
                    f"{'🌤️' if outdoor else '🏠'} {cat} / "
                    f"{m.get('location_name', '')} | "
                    f"보상: {m.get('reward', 0):,}원"
                )

                with st.expander(label):
                    col_l, col_r = st.columns(2)
                    with col_l:
                        st.markdown(f"**💰 보상:** {m.get('reward', 0):,}원")
                        st.markdown(f"**📍 위치:** {m.get('location_name', '')}")
                        st.markdown(f"**🏷️ 분류:** {cat} | {'🌤️ 실외' if outdoor else '🏠 실내'}")
                    with col_r:
                        st.markdown(f"**📋 업무 내용:** {m.get('description', '')}")
                        st.markdown(f"**📸 인증 가이드:** {m.get('verification_guide', '')}")

                    if applied:
                        st.button("✅ 지원 완료", key=f"done_{m['id']}", disabled=True)
                    else:
                        if st.button("🙋 미션 지원하기", key=f"apply_{m['id']}", type="primary"):
                            try:
                                supabase.table("applications").insert({
                                    "mission_id": m["id"],
                                    "senior_id":  st.session_state["user_id"],
                                    "status":     "APPLIED",
                                }).execute()
                                st.success("🎉 지원이 완료되었습니다!")
                                st.rerun()
                            except Exception:
                                st.error("❌ 작업 중 오류가 발생했습니다.")

    with tab_mine:
        st.subheader("나의 지원/매칭 현황")
        my_apps = db_get_senior_applications(st.session_state["user_id"])

        if not my_apps:
            st.warning("⚠️ 현재 표시할 내역이 존재하지 않습니다.")
        else:
            for app in my_apps:
                mission     = app.get("missions") or {}
                cat         = (mission.get("categories") or {}).get("name", "기타")
                status      = app["status"]
                icon, label = STATUS_LABELS.get(status, ("⚪", status))

                with st.container(border=True):
                    st.markdown(f"### 🎯 {mission.get('title', '알 수 없음')}")
                    st.markdown(
                        f"- **카테고리:** {cat} | "
                        f"**보상:** {mission.get('reward', 0):,}원 | "
                        f"**장소:** {mission.get('location_name', '')}"
                    )
                    st.markdown(f"- **상태:** {icon} {label}")

                    if status == "ACCEPTED":
                        with st.expander("📋 업무 완료 보고서 작성", expanded=True):
                            with st.form(f"comp_{app['id']}"):
                                note  = st.text_area("수행한 업무 내용을 상세히 작성해주세요")
                                photo = st.file_uploader(
                                    "인증 사진 첨부 (JPG/PNG) — 선택사항",
                                    type=["jpg", "jpeg", "png"],
                                )
                                submit = st.form_submit_button("📤 완료 제출하기", type="primary")

                                if submit:
                                    if not note.strip():
                                        st.error("❌ 완료 내용을 입력해주세요.")
                                    else:
                                        photo_url = None
                                        if photo:
                                            try:
                                                path = f"completions/{app['id']}_{photo.name}"
                                                supabase.storage.from_("mission-photos").upload(
                                                    path,
                                                    photo.read(),
                                                    {"content-type": photo.type, "upsert": "true"},
                                                )
                                                photo_url = supabase.storage.from_(
                                                    "mission-photos"
                                                ).get_public_url(path)
                                            except Exception:
                                                st.warning("⚠️ 사진 업로드에 실패했습니다. 텍스트 내용으로만 제출합니다.")

                                        try:
                                            supabase.table("applications").update({
                                                "status":               "SUBMITTED",
                                                "completion_note":      note.strip(),
                                                "completion_photo_url": photo_url,
                                            }).eq("id", app["id"]).execute()
                                            st.success("✅ 완료 보고서가 제출되었습니다!")
                                            st.rerun()
                                        except Exception:
                                            st.error("❌ 작업 중 오류가 발생했습니다.")


# ─── MAIN ROUTING ─────────────────────────────────────────────────────────────
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
