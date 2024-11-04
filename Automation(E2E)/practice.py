from playwright.sync_api import expect, Page
from abc import ABC, abstractmethod
from contextlib import contextmanager
from functools import wraps
from typing import Generator, Tuple

import pytest, time, logging

USERID = "blank"
USERPASSWORD = "blank"

# logging
logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URL
BASE_URL = "https://www.lotteimall.com"
LOGIN_URL = f"{BASE_URL}/main/viewMain.lotte?dpml_no=1#disp_no=5223317"
ORDER_URL = f"{BASE_URL}/order/searchOrderSheetList.lotte"

class APIMonitor:
    def __init__(self, page: Page):
        self.page = page
        self.api_timings = {}

    def monitor_api_requests(self, url_pattern: str, threshold_ms: int):
        def handle_request(request):
            if url_pattern in request.url:
                start_time = time.time()
                self.api_timings[request.url] = {'start': start_time}

        def handle_response(response):
            if response.request.url in self.api_timings:
                end_time = time.time()
                duration = (end_time - self.api_timings[response.request.url]['start']) * 1000  
                self.api_timings[response.request.url]['duration'] = duration
                if duration > threshold_ms:
                    print(f"{response.request.url} : {duration:.2f}ms, 초과 시간 {threshold_ms}ms")

        self.page.on('request', handle_request)
        self.page.on('response', handle_response)

    def assert_api_performance(self, url_pattern: str, threshold_ms: int):
        slow_apis = [url for url, timing in self.api_timings.items() 
                     if url_pattern in url and timing.get('duration', 0) > threshold_ms]
        
        assert len(slow_apis) == 0, f"초과 시간 {threshold_ms}ms, threshold: {slow_apis}"

class Verifying(ABC):
    def __init__(self):
        self.result_time = 0
        
    @abstractmethod
    def monitoring(self):
        pass

    @contextmanager
    def timeChecker(self):
        start = time.time()
        yield
        end = time.time()
        self.result_time = end - start
        return self.result_time
    

class LotteImallTestOperator(Verifying):
    def __init__(self, page: Page):
        super().__init__()
        self.page = page
        self.results = []
        self.api_monitor = APIMonitor(page)
        
    def login(self):
        login_status = True
        self.page.goto(BASE_URL)
        
        with self.page.expect_popup() as popup_info:
            self.page.get_by_role("link", name = "로그인 로그인").click()
        popup = popup_info.value

        popup.get_by_placeholder("아이디 또는 이메일주소 입력해주세요").fill(USERID)
        popup.get_by_placeholder("비밀번호를 입력해 주세요").fill(USERPASSWORD)
        popup.get_by_role("link", name = "로그인", exact = True).click()
        
        self.page.reload(wait_until = "networkidle")
        if not self.page.get_by_role("link", name = "로그아웃 로그아웃"):
            login_status = False
        
        return login_status
    
    def searchProductAndOrder(self, search_terms: list[str]):
        for term in search_terms:
            self.page.locator("input#headerQuery.search").fill(term)
            self.page.locator("input#headerQuery.search").press("Enter")
            self.page.wait_for_load_state("networkidle")
            
            product_list = self.page.locator("div.wrap_unitlist").locator("ul").locator("li").all()
            product_found = False
            
            for product in product_list:
                if product_found:
                    break

                try:
                    product.click()
                    self.page.wait_for_load_state("networkidle")

                    if self.selectProductOption():
                        product_found = True
                        self.page.locator("#immOrder-btn").click()
                        with self.timeChecker() as tC:
                            self.page.wait_for_url("https://www.lotteimall.com/order/searchOrderSheetList.lotte", wait_until="networkidle")
                        self.results.append(self.result_time)
                        break
                    else:
                        # 옵션 선택에 실패한 경우, 이전 페이지로 돌아가기
                        self.page.go_back()
                        self.page.wait_for_load_state("networkidle")

                except Exception as e:
                    logging.error(f"상품 처리 중 오류 발생: {str(e)}")
                    # 오류 발생 시 다음 상품으로 넘어감
                    self.page.go_back()
                    self.page.wait_for_load_state("networkidle")
                    continue

            if not product_found:
                logging.warning(f"'{term}' 검색어로 적절한 상품을 찾지 못했습니다.")

    # def select_product_options(self):
    #     selectOptionCategory =  self.page.locator("div.inp_option.inpOptList")
    #     # 옵션 선택지 개수 확인
    #     if selectOptionCategory.count() > 0:
    #         all_options_selected = False
    #         while not all_options_selected:
    #             all_options_selected = True
    #             for seq in range(selectOptionCategory.count()):
    #                 option = selectOptionCategory.nth(seq)
    #                 # 옵션 선택창 활성화 클릭 이벤트
    #                 option.click()
    #                 # 옵션창
    #                 option_detail = option.locator(f"div#optLaySel_{seq}")
    #                 # 옵션 고르기(품절 제외)
    #                 for_choose_option = option_detail.locator("div.wrap_scroll_option").locator("ul").locator("li").all()[1:]
                    
    #                 option_selected = False
    #                 for available in for_choose_option:
    #                     if available.get_attribute("class") == None:
    #                         available.click()
    #                         option_selected = True
    #                         break
                    
    #                 if not option_selected:
    #                     all_options_selected = False
    #                     break  # 현재 옵션에서 선택 가능한 항목이 없으면 처음부터 다시 시작

    #             if not all_options_selected:
    #                 # 이전에 선택한 옵션들을 초기화
    #                 for reset_seq in range(seq):
    #                     selectOptionCategory.nth(reset_seq).click()
    #                     reset_option = selectOptionCategory.nth(reset_seq).locator(f"div#optLaySel_{reset_seq}")
    #                     reset_option.locator("div.wrap_scroll_option").locator("ul").locator("li").first.click()

    def reset_options(self, seq: int):
        selectOptionCategory = self.page.locator("div.inp_option.inpOptList")
        for reset_seq in range(seq):
            selectOptionCategory.nth(reset_seq).click()
            reset_option = selectOptionCategory.nth(reset_seq).locator(f"div#optLaySel_{reset_seq}")
            reset_option.locator("div.wrap_scroll_option").locator("ul").locator("li").first.click()
            self.page.wait_for_timeout(1000) 
    

    def selectProductOption(self):
        try:
            selectOptionCategory = self.page.locator("div.inp_option.inpOptList")
            logging.info(f"Found {selectOptionCategory.count()} option categories")

            if selectOptionCategory.count() > 0:
                all_options_selected = False
                max_attempts = 5
                attempt = 0

                while not all_options_selected and attempt < max_attempts:
                    all_options_selected = True
                    attempt += 1
                    logging.info(f"옵션 선택 시도 횟수 {attempt}")

                    for seq in range(selectOptionCategory.count()):
                        option = selectOptionCategory.nth(seq)
                        logging.info(f"옵션 선택 {seq + 1}")
                        
                        option.click()
                        self.page.wait_for_timeout(1000)  # Wait for option menu to open

                        option_detail = option.locator(f"div#optLaySel_{seq}")
                        for_choose_option = option_detail.locator("div.wrap_scroll_option").locator("ul").locator("li").all()[1:]
                        
                        option_selected = False
                        for available in for_choose_option:
                            if available.get_attribute("class") is None:
                                available.click()
                                self.page.wait_for_timeout(1000)  # Wait for selection to register
                                option_selected = True
                                logging.info(f"옵션 선택 {seq + 1}")
                                break
                        
                        if not option_selected:
                            all_options_selected = False
                            logging.warning(f"옵션 선택지 없음ㅊ {seq + 1}")
                            break

                    if not all_options_selected:
                        logging.info("옵션 선택지 초기화")
                        self.reset_options(seq)

                if not all_options_selected:
                    logging.error("재시도 횟수 초과.")
                    return False

                # 모든 옵션 선택 후 수량 입력 필드 확인 및 증가
                quantity_check = self.page.locator("div.selected_option").all()
                for qc in quantity_check:
                    if qc.is_visible() and qc.get_attribute("class").startswith("opt"):
                        break
                    else:
                        pass

                # "장바구니 담기" 버튼 클릭
                # cart_button = self.page.locator("a#immCart-btn")
                # if cart_button.is_visible():
                #     cart_button.click()
                #     self.page.wait_for_load_state("networkidle")

                return True
            else:
                logging.info("옵션 선택지 업음ㅊ")
                return True

        except Exception as e:
            logging.error(f"옵션 선택 중 에러 발생: {str(e)}")
            return False
        
    def GetAverageResult(self) -> float:
        if not self.results:
            print("계산 할 수 없음.")
            return 0
        
        average = sum(self.results) / len(self.results)
        print(f"평균 시간 : {average:.2f}/sec")
        return average

    def monitor_api_requests(self, url_pattern: str, threshold_ms: int):
        self.api_monitor.monitor_api_requests(url_pattern, threshold_ms)

    def assert_api_performance(self, url_pattern: str, threshold_ms: int):
        self.api_monitor.assert_api_performance(url_pattern, threshold_ms)

    def monitoring(self):
        # Implement the abstract method from Verifying
        pass
        
@pytest.fixture(scope = 'function', autouse = False)
def lotte_imall_tester(page: Page) -> Generator[Tuple[LotteImallTestOperator, float], None, None]:
    page.goto("https://www.lotteimall.com/main/viewMain.lotte?dpml_no=1&tlog=00100_1#disp_no=5223317", wait_until = 'networkidle')
    search_terms = ["아디다스"]
    tester = LotteImallTestOperator(page)
    # tester.login()
    tester.searchProductAndOrder(search_terms)
    average_result = tester.GetAverageResult()
    yield tester, average_result

def test_order_payProcess(lotte_imall_tester: Tuple[LotteImallTestOperator, float]) -> None:
    tester, average_result = lotte_imall_tester
    assert average_result == pytest.approx(5, abs = 1)
    # API 성능 assertion
    tester.assert_api_performance("/api/", 5000)
    
# import pytest
# from playwright.sync_api import sync_playwright

# @pytest.fixture(scope="function", autouse=True)
# def trace_setup_and_teardown():
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         context = browser.new_context()
#         page = context.new_page()
        
#         # 각 테스트 함수마다 tracing을 시작
#         context.tracing.start(screenshots=True, snapshots=True, sources=True)
        
#         yield page  # 테스트 함수에 페이지 객체 전달
        
#         # 각 테스트 함수가 끝나면 tracing을 멈추고 저장
#         context.tracing.stop(path=f"trace_{page.url.split('/')[-1]}.zip")
#         context.close()
#         browser.close()

# def test_scenario_one(trace_setup_and_teardown):
#     page = trace_setup_and_teardown
#     page.goto("https://example.com")
#     # 시나리오 1에 대한 테스트 코드

# def test_scenario_two(trace_setup_and_teardown):
#     page = trace_setup_and_teardown
#     page.goto("https://example.com/another-page")
#     # 시나리오 2에 대한 테스트 코드


# from playwright.sync_api import sync_playwright, expect, Page
# from datetime import datetime
# import csv, mimetypes, time

# def get_resource_type(request):
#     mime_type = request.header_value("content-type")
#     if mime_type:
#         if mime_type.startswith("image/"):
#             return mime_type.split("/")[1]
#         elif mime_type == "text/plain":
#             return "text"
#     return request.resource_type

# def log_request(request):
#     resource_type = get_resource_type(request)
#     if resource_type in ["fetch", "xhr", "stylesheet", "script", "gif", "png", "jpeg", "text"]:
#         log_data = {
#             "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#             "resource_type": resource_type,
#             "url": request.url,
#             "method": request.method,
#             "headers": str(request.headers)
#         }
        
#         # CSV 파일에 로그 데이터 추가
#         with open('request_log.csv', 'a', newline = '', encoding = 'utf-8-sig') as f:
#             writer = csv.DictWriter(f, fieldnames = log_data.keys())
#             if f.tell() == 0:  # 파일이 비어있으면 헤더 작성
#                 writer.writeheader()
#             writer.writerow(log_data)

#         # 콘솔에 로그 출력 (선택사항)
#         print(f"Resource Type: {resource_type}")
#         print(f"URL: {request.url}")
#         print(f"Method: {request.method}")
#         print(f"Headers: {request.headers}")
#         print("---")

# with sync_playwright() as p:
#     browser = p.chromium.launch(headless = False)
#     context = browser.new_context()
#     page = context.new_page()
    
#     page.goto("https://www.lotteimall.com/main/viewMain.lotte?dpml_no=1#disp_no=5223317")
#     page.locator("input#headerQuery.search").fill("아디다스")
#     page.locator("input#headerQuery.search").press("Enter")
    
#     page.wait_for_load_state("networkidle")    
#     product_list = page.locator("div.wrap_unitlist").locator("ul").locator("li").all()

#     # 상품 리스트 탐색
#     product_found = False
#     for product in product_list:
#         if product_found:
#             break

#         try:
#             # 개별 상품 진입 (상품 상세 페이지로 이동)
#             product.click()
#             page.on("request", log_request)
#             page.wait_for_load_state("networkidle")
            
#             # 옵션 선택 카테고리 찾기
#             selectOptionCategory = page.locator("div.inp_option.inpOptList")
            
#             # 옵션 선택지 개수 확인
#             if selectOptionCategory.count() > 0:
#                 all_options_selected = False
#                 while not all_options_selected:
#                     all_options_selected = True
#                     for seq in range(selectOptionCategory.count()):
#                         option = selectOptionCategory.nth(seq)
#                         # 옵션 선택창 활성화 클릭 이벤트
#                         option.click()
#                         # 옵션창
#                         option_detail = option.locator(f"div#optLaySel_{seq}")
#                         # 옵션 고르기(품절 제외)
#                         for_choose_option = option_detail.locator("div.wrap_scroll_option").locator("ul").locator("li").all()[1:]
                        
#                         option_selected = False
#                         for available in for_choose_option:
#                             if available.get_attribute("class") == None:
#                                 available.click()
#                                 option_selected = True
#                                 break
                        
#                         if not option_selected:
#                             all_options_selected = False
#                             break  # 현재 옵션에서 선택 가능한 항목이 없으면 처음부터 다시 시작

#                     if all_options_selected:
#                         product_found = True
#                         print("모든 옵션이 성공적으로 선택되었습니다.")
#                         break

#                     if not all_options_selected:
#                         # 이전에 선택한 옵션들을 초기화
#                         for reset_seq in range(seq):
#                             selectOptionCategory.nth(reset_seq).click()
#                             reset_option = selectOptionCategory.nth(reset_seq).locator(f"div#optLaySel_{reset_seq}")
#                             reset_option.locator("div.wrap_scroll_option").locator("ul").locator("li").first.click()
#             else:
#                 # 옵션이 없는 경우도 상품을 찾은 것으로 간주
#                 product_found = True
#                 print("옵션이 없는 상품입니다.")

#         except Exception as e:
#             print(f"상품 처리 중 오류 발생: {str(e)}")
#             # 오류 발생 시 다음 상품으로 넘어감
#             continue

#         if product_found:
#             break

#     # 상품을 찾았는지 확인
#     if product_found:
#         print("적절한 상품을 찾았습니다.")
#     else:
#         print("적절한 상품을 찾지 못했습니다.")
#     time.sleep(20)
#         # time.sleep(2)
#         # page.locator("a#immOrder-btn").click()
        
                    
                    
