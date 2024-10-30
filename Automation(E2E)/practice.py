from playwright.sync_api import sync_playwright, expect, Page
import pytest, time

USERID = "blank"
USERPASSWORD = "blank"

class LotteImallTester:
    def __init__(self, page: Page, user_id: str, user_password: str):
        self.page = page
        self.user_id = user_id
        self.user_password = user_password
        self.results = []

    def login(self):
        self.page.goto("https://www.lotteimall.com/main/viewMain.lotte?dpml_no=1#disp_no=5223317")
        
        with self.page.expect_popup() as popup_info:
            self.page.get_by_role("link", name = "로그인 로그인").click()
        popup = popup_info.value

        popup.get_by_placeholder("아이디 또는 이메일주소 입력해주세요").fill(self.user_id)
        popup.get_by_placeholder("비밀번호를 입력해 주세요").fill(self.user_password)
        popup.get_by_role("link", name = "로그인", exact = True).click()
        
        if not self.is_logged_in():
            raise ValueError("로그인 실패")

    def is_logged_in(self) -> bool:
        login_checker = self.page.locator("div.util_menu").locator("ul").locator("li").first.locator("a").inner_text()
        return login_checker == "로그아웃"

    def search_products(self, search_terms):
        for term in search_terms:
            self.page.locator("input#headerQuery.search").fill(term)
            self.page.locator("input#headerQuery.search").press("Enter")

            product_list = self.page.locator("div.wrap_unitlist").all()

            for product in product_list:
                product.click()
                self.select_product_options()
                self.page.locator("#immOrder-btn").click()

                start = time.time()
                self.page.wait_for_url("https://www.lotteimall.com/order/searchOrderSheetList.lotte", wait_until = "networkidle")
                end = time.time()
                self.results.append(end - start)

    def select_product_options(self):
        select_option = self.page.locator("div.inp_option.inpOptList")

        if select_option.count() > 0:
            for k in range(select_option.count()):
                option = select_option.nth(k)
                option.click()

                option_detail = option.locator(f"div#optLaySel_{k}")
                option_detail.wait_for(state = "visible")

                detail = option_detail.locator("div.wrap_scroll_option").locator("ul").locator("li").all()

                ## ERR
                for choose_one in detail:
                    if choose_one.is_visible():
                        choose_one.click()
                        break
            else:
                print("not option")

    def get_average_result(self) -> float:
        return sum(self.results) / len(self.results) if self.results else 0


@pytest.fixture(scope = 'function', autouse = True)
def test_order_payProcess(page: Page) -> iter:
    search_terms = ["아디다스", "나이키", "냉장고"] 
    tester = LotteImallTester(page, USERID, USERPASSWORD)
    tester.login()
    tester.search_products(search_terms)
    average_result = tester.get_average_result()
    yield average_result


def test_order_payload(test_order_payProcess: iter) -> None:
    assert test_order_payProcess == pytest.approx(5, abs = 1)
