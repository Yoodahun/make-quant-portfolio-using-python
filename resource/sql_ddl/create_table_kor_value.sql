create table kor_value #밸류팩터 데이터 저장
(
    종목코드 varchar(6),
    기준일 date,
    지표 varchar(6),
    값 double,
    primary key (종목코드, 기준일, 지표)
);