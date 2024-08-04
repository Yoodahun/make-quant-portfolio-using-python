from src.controller.data_controller import DataController
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('from_date', type=str)

controller = DataController()

print("기준일 기준 섹터 및 주식 정보 크롤링 후 저장 ----")
controller.merge_and_insert_crawled_sector_and_stock_indicator_data()
#
print("업종 정보 크롤링 및 합치기 후 저장 ------")
controller.insert_wics_sector_info_data()

args = parser.parse_args()
print("수정주가 크롤링 후 저장-----")
controller.insert_adjust_stock_price(from_date_input=args.from_date)