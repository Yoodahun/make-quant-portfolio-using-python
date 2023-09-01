create table kor_profitability #수익성 팩터 데이터 저장
(
    종목코드 varchar(6),
    기준일 date,
    ROE double, # 자기자본 / 당기순이익
    GPA double, #매출총이익 / 자산
    NAV double, # 청산가치 / 시가총액
    CFO double, #영업활동현금흐름 / 자산
    부채비율 double,
    primary key (종목코드, 기준일)
);