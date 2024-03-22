from src.controller.data_controller import DataController


controller = DataController()

print("수정주가 크롤링 후 저장-----")
controller.insert_adjust_stock_price()