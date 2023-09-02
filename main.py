# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
from src.controller.data_controller import DataController

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')
    data_controller = DataController()

    print("------- 크롤링 및 데이터 정제 후 DB추가 로직 실행 ------")
    # print("insert data-----")
    print("기준일 기준 섹터 및 주식 정보 크롤링 후 저장 ----")
    # data_controller.merge_and_insert_crawled_sector_and_stock_indicator_data()
    #
    print("업정 정보 크롤링 및 합치기 후 저장 ------")
    # data_controller.insert_wics_sector_info_data()

    print("수정주가 크롤링 후 저장-----")
    # data_controller.insert_adjust_stock_price()
    print("재무재표 크롤링 후 저장-----")
    # data_controller.merge_and_insert_financial_statement_data()

    print("크롤링한 재무재표를 이용하여 밸류 및 수익성 지표 계신 및 저장-----")
    data_controller.calculate_and_insert_value_factor_data()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
