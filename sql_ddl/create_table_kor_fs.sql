create table kor_fs( #재무제표 크롤링데이터 정보 저장
    계정 varchar (30),
    기준일 date,
    값 float,
    종목코드 varchar(6),
    공시구분 varchar(1),
    primary key(계정, 기준일, 종목코드, 공시구분)
);