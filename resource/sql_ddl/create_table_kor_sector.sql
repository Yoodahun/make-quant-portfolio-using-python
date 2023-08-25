create table kor_sector ( # 국내 섹터 정보 저장
    IDX_CD varchar (3), #섹터 코드
    CMP_CD varchar (6), #종목코드
    CMP_KOR varchar (20), # 종목명
    SEC_NM_KOR varchar (10), #섹터명
    기준일 date,
    primary key(CMP_CD, 기준일)
 );