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
if "user_role" not in st.session_state:
    st.session_state["user_role"] = "Employer"
if "user_id" not in st.session_state:
    st.session_state["user_id"] = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

# ─── Sidebar ─────────────────────────────────────────────────────────────────
st.sidebar.title("🎯 시몬고 제어 센터")
st.sidebar.caption("사용자 역할을 선택하세요.")

selected = st.sidebar.radio(
    "역할 전환",
    ["고용자(Employer)", "시니어(Senior)"],
    index=0 if st.session_state["user_role"] == "Employer" else 1,
)

new_role = "Employer" if selected == "고용자(Employer)" else "Senior"
if new_role != st.session_state["user_role"]:
    st.session_state["user_role"] = new_role
    st.session_state["user_id"] = (
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        if new_role == "Employer"
        else "cccccccc-cccc-cccc-cccc-cccccccccccc"
    )
    st.rerun()

if st.session_state["user_role"] == "Senior":
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📊 시니어 성실도 지표**")
    st.sidebar.latex(
        r"Sincerity\_Score = \left(\frac{N_{valid}}{N_{total}}\right) \times 100"
    )
    st.sidebar.caption(
        "N_total: 총 기대 핑 수 / N_valid: 허용 반경 내 유효 위치 핑 수"
    )

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
        res = (
            supabase.table("missions")
            .select("id")
            .eq("employer_id", employer_id)
            .execute()
        )
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
}


# ─── EMPLOYER VIEW ────────────────────────────────────────────────────────────
if st.session_state["user_role"] == "Employer":
    st.title("👨‍💼 고용주 관제 대시보드")
    tab_reg, tab_mgmt = st.tabs(["➕ 신규 미션 등록", "📋 지원자 현황 관리"])

    # ── Tab 1: Mission Registration ──────────────────────────────────────────
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

    # ── Tab 2: Applicant Management ──────────────────────────────────────────
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

                    if status == "APPLIED":
                        c1, c2, _ = st.columns([1, 1, 5])
                        with c1:
                            if st.button("✅ 수락", key=f"acc_{app['id']}", type="primary"):
                                try:
                                    supabase.table("applications").update(
                                        {"status": "ACCEPTED"}
                                    ).eq("id", app["id"]).execute()
                                    st.rerun()
                                except Exception:
                                    st.error("❌ 작업 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")
                        with c2:
                            if st.button("❌ 거절", key=f"rej_{app['id']}"):
                                try:
                                    supabase.table("applications").update(
                                        {"status": "REJECTED"}
                                    ).eq("id", app["id"]).execute()
                                    st.rerun()
                                except Exception:
                                    st.error("❌ 작업 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")

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
                                # Mission auto-delete after payment (ON DELETE CASCADE cleans up applications)
                                mission_id = (app.get("missions") or {}).get("id") or app.get("mission_id")
                                if mission_id:
                                    supabase.table("missions").delete().eq("id", mission_id).execute()
                                st.success("✅ 금액 수령 완료! 해당 미션이 종료되었습니다.")
                                st.balloons()
                                st.rerun()
                            except Exception:
                                st.error("❌ 작업 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")


# ─── SENIOR VIEW ──────────────────────────────────────────────────────────────
else:
    st.title("🎯 시몬고 실시간 미션 보드")
    tab_board, tab_mine = st.tabs(["🔍 일감 찾기 보드", "🎯 나의 지원/매칭 현황"])

    # ── Tab 1: Mission Board ─────────────────────────────────────────────────
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
                weather = "🌤️ 실외" if outdoor else "🏠 실내"
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
                        st.markdown(f"**🏷️ 분류:** {cat} | {weather}")
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
                                st.error("❌ 작업 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")

    # ── Tab 2: My Applications ───────────────────────────────────────────────
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

                    # Completion report form — shown only for ACCEPTED missions
                    if status == "ACCEPTED":
                        with st.expander("📋 업무 완료 보고서 작성", expanded=True):
                            with st.form(f"comp_{app['id']}"):
                                note   = st.text_area("수행한 업무 내용을 상세히 작성해주세요")
                                photo  = st.file_uploader(
                                    "인증 사진 첨부 (JPG/PNG)",
                                    type=["jpg", "jpeg", "png"],
                                )
                                submit = st.form_submit_button("📤 완료 제출하기", type="primary")

                                if submit:
                                    if not note.strip():
                                        st.error("❌ 완료 내용을 입력해주세요.")
                                    else:
                                        try:
                                            photo_url = None
                                            if photo:
                                                path = f"completions/{app['id']}_{photo.name}"
                                                supabase.storage.from_("mission-photos").upload(
                                                    path,
                                                    photo.read(),
                                                    {"content-type": photo.type, "upsert": "true"},
                                                )
                                                photo_url = supabase.storage.from_(
                                                    "mission-photos"
                                                ).get_public_url(path)

                                            supabase.table("applications").update({
                                                "status":               "SUBMITTED",
                                                "completion_note":      note.strip(),
                                                "completion_photo_url": photo_url,
                                            }).eq("id", app["id"]).execute()
                                            st.success("✅ 완료 보고서가 제출되었습니다!")
                                            st.rerun()
                                        except Exception:
                                            st.error(
                                                "❌ 작업 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
                                            )
