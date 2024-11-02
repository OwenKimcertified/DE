from playwright.sync_api import expect, Page
from abc import ABC, abstractmethod
from contextlib import contextmanager
from functools import wraps
from typing import Generator, Tuple

import pytest, time, logging

USERID = "blank"
USERPASSWORD = "blank"
logging.basicConfig(level = logging.INFO)

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
                duration = (end_time - self.api_timings[response.request.url]['start']) * 1000  # Convert to ms
                self.api_timings[response.request.url]['duration'] = duration
                if duration > threshold_ms:
                    print(f"API call to {response.request.url} took {duration:.2f}ms, exceeding the {threshold_ms}ms threshold")

        self.page.on('request', handle_request)
        self.page.on('response', handle_response)

    def assert_api_performance(self, url_pattern: str, threshold_ms: int):
        slow_apis = [url for url, timing in self.api_timings.items() 
                     if url_pattern in url and timing.get('duration', 0) > threshold_ms]
        
        assert len(slow_apis) == 0, f"The following APIs exceeded the {threshold_ms}ms threshold: {slow_apis}"

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
        self.page.goto("https://www.lotteimall.com/main/viewMain.lotte?dpml_no=1#disp_no=5223317")
        
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
    
    def searchProductAndOrder(self, search_terms: list):
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
                    logging.info(f"Attempt {attempt} to select all options")

                    for seq in range(selectOptionCategory.count()):
                        option = selectOptionCategory.nth(seq)
                        logging.info(f"Selecting option {seq + 1}")
                        
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
                                logging.info(f"Selected an option for category {seq + 1}")
                                break
                        
                        if not option_selected:
                            all_options_selected = False
                            logging.warning(f"No available option for category {seq + 1}")
                            break

                    if not all_options_selected:
                        logging.info("Resetting options and trying again")
                        self.reset_options(seq)

                if not all_options_selected:
                    logging.error("Failed to select all options after maximum attempts")
            else:
                logging.info("No options to select for this product")

        except Exception as e:
            logging.error(f"An error occurred while selecting options: {str(e)}")

            # 모든 옵션 선택 후 수량 입력 필드 확인 및 증가
            quantity_check = self.page.locator("div.selected_option").all()
            for qc in quantity_check:
                if qc.is_visible() and qc.get_attribute("class").startswith("opt"):
                    break
                else:
                    pass
            
            # # "장바구니 담기" 버튼 클릭
            # cart_button = self.page.locator("a#immCart-btn")
            # if cart_button.is_visible():
            #     cart_button.click()
            #     self.page.wait_for_load_state("networkidle")
            return True
        
        else:
            print("No options found for this product")
            return False        
        
    def GetAverageResult(self) -> float:
        if not self.results:
            print("No results to calculate average.")
            return 0
        
        average = sum(self.results) / len(self.results)
        print(f"Average time: {average:.2f} seconds")
        return average

    def monitor_api_requests(self, url_pattern: str, threshold_ms: int):
        self.api_monitor.monitor_api_requests(url_pattern, threshold_ms)

    def assert_api_performance(self, url_pattern: str, threshold_ms: int):
        self.api_monitor.assert_api_performance(url_pattern, threshold_ms)
        
@pytest.fixture(scope = 'function', autouse = False)
def lotte_imall_tester(page: Page) -> Generator[LotteImallTestOperator, float] :
    page.goto("https://www.lotteimall.com/main/viewMain.lotte?dpml_no=1&tlog=00100_1#disp_no=5223317", wait_until = 'networkidle')
    search_terms = ["아디다스"] 
    tester = LotteImallTestOperator(page)
    ### api monitoring
    tester.monitor_api_requests("/api/", 5000)
    # tester.login()
    tester.searchProductAndOrder(search_terms)
    average_result = tester.GetAverageResult()
    yield tester, average_result

def test_order_payProcess(lotte_imall_tester: float) -> None:
    tester, average_result = lotte_imall_tester
    assert average_result == pytest.approx(5, abs = 1)
    # API 성능 assertion
    tester.assert_api_performance("/api/", 5000)