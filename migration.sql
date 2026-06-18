-- ================================================================
-- 시몬고 (Si-Mon-GO) Migration
-- Supabase SQL Editor에서 실행하세요.
-- 기존 스키마(setup SQL)를 실행한 뒤 이 파일을 실행합니다.
-- ================================================================

-- 1) 완료 보고서용 컬럼 추가 (applications 테이블)
ALTER TABLE public.applications
  ADD COLUMN IF NOT EXISTS completion_note      TEXT,
  ADD COLUMN IF NOT EXISTS completion_photo_url TEXT;

-- 2) 시니어 더미 프로필 추가 (앱에서 Senior 역할로 사용)
INSERT INTO public.profiles (id, email, nickname, role_type, phone_number)
VALUES ('cccccccc-cccc-cccc-cccc-cccccccccccc', 'senior1@example.com', '정성 가득 시니어', 'Senior', '010-0000-0001')
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.senior_details (user_id)
VALUES ('cccccccc-cccc-cccc-cccc-cccccccccccc')
ON CONFLICT (user_id) DO NOTHING;

-- 3) RLS 쓰기 정책 추가 (anon 키로 INSERT/UPDATE/DELETE 허용)
--    기존 setup SQL은 SELECT만 허용 → Streamlit에서 데이터 저장이 안 됨

-- missions
CREATE POLICY IF NOT EXISTS "anon insert missions"
  ON public.missions FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY IF NOT EXISTS "anon update missions"
  ON public.missions FOR UPDATE TO anon USING (true);
CREATE POLICY IF NOT EXISTS "anon delete missions"
  ON public.missions FOR DELETE TO anon USING (true);

-- applications
CREATE POLICY IF NOT EXISTS "anon insert applications"
  ON public.applications FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY IF NOT EXISTS "anon update applications"
  ON public.applications FOR UPDATE TO anon USING (true);
CREATE POLICY IF NOT EXISTS "anon delete applications"
  ON public.applications FOR DELETE TO anon USING (true);

-- profiles (시니어 추가 등을 위해)
CREATE POLICY IF NOT EXISTS "anon insert profiles"
  ON public.profiles FOR INSERT TO anon WITH CHECK (true);

-- senior_details
CREATE POLICY IF NOT EXISTS "anon insert senior_details"
  ON public.senior_details FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY IF NOT EXISTS "anon update senior_details"
  ON public.senior_details FOR UPDATE TO anon USING (true);

-- 4) 인증 사진 Storage 버킷 생성 (Public)
INSERT INTO storage.buckets (id, name, public)
VALUES ('mission-photos', 'mission-photos', true)
ON CONFLICT DO NOTHING;

-- Storage RLS: anon 업로드/다운로드 허용
CREATE POLICY IF NOT EXISTS "anon upload mission photos"
  ON storage.objects FOR INSERT TO anon
  WITH CHECK (bucket_id = 'mission-photos');

CREATE POLICY IF NOT EXISTS "anon read mission photos"
  ON storage.objects FOR SELECT TO anon
  USING (bucket_id = 'mission-photos');

CREATE POLICY IF NOT EXISTS "anon update mission photos"
  ON storage.objects FOR UPDATE TO anon
  USING (bucket_id = 'mission-photos');

-- 5) profiles 테이블에 이메일 기반 고용자 계정 추가
INSERT INTO public.profiles (id, email, nickname, role_type, phone_number)
VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'employer1@example.com', '매지리 보안관', 'Employer', '010-1111-1111'),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'employer2@example.com', '원주 사장님',   'Employer', '010-2222-2222')
ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email;
