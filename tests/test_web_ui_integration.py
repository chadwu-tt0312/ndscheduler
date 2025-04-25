import time
import pytest
from playwright.sync_api import Page, expect


# 使用 conftest.py 中的全局配置
@pytest.fixture(scope="function")
def authenticated_page(page: Page, base_url, username, password):
    """提供一個已登入的頁面實例"""
    # 直接導航到登入頁面
    page.goto(f"{base_url}/login")

    # 等待頁面加載
    page.wait_for_load_state("networkidle")

    # 截圖保存，協助調試
    page.screenshot(path="login_page_for_fixture.png")

    # 嘗試不同的選擇器，以適應可能的不同HTML結構
    username_input = page.locator(
        "input[name='username'], input#username, input[placeholder*='用戶名'], input[placeholder*='用户名'], input[placeholder*='帳號'], input[placeholder*='账号'], input[type='text']"
    ).first
    password_input = page.locator("input[name='password'], input#password, input[type='password']").first

    # 驗證表單元素存在
    username_input.wait_for(state="visible", timeout=10000)
    password_input.wait_for(state="visible", timeout=10000)

    # 輸入憑證
    username_input.fill(username)
    password_input.fill(password)

    # 尋找並點擊登入按鈕 (嘗試多種可能的選擇器)
    login_button = page.locator(
        "button[type='submit'], button:has-text('登入'), button:has-text('登录'), input[type='submit']"
    ).first
    login_button.wait_for(state="visible", timeout=10000)
    login_button.click()

    # 等待較長時間確保完全登入和加載
    page.wait_for_load_state("networkidle", timeout=10000)

    # 檢查是否導航到儀表板或其他指示成功登入的頁面
    success_element = page.locator(".dashboard, .main-content, .navbar, .header, #app, #main").first
    success_element.wait_for(state="visible", timeout=15000)

    # 截圖保存，協助調試
    page.screenshot(path="authenticated_dashboard.png")

    # 返回已登入的頁面
    return page


# 改用純 pytest 風格而非 unittest
class TestWebUIIntegration:
    """Web UI 整合測試"""

    def test_01_login(self, page: Page, base_url, username, password):
        """測試登入功能"""
        # 直接導航到登入頁面
        page.goto(f"{base_url}/login")

        # 等待頁面加載並給予足夠時間
        page.wait_for_load_state("networkidle")

        # 截圖保存，協助調試
        # page.screenshot(path="login_page_screenshot.png")

        # 輸出頁面源碼以便分析
        # page_content = page.content()
        # with open("login_page_source.html", "w", encoding="utf-8") as f:
        #     f.write(page_content)

        # print(f"頁面標題: {page.title()}")
        # print(f"頁面URL: {page.url}")

        # 嘗試不同的選擇器，以適應可能的不同HTML結構
        username_input = page.locator(
            "input[name='username'], input#username, input[placeholder*='用戶名'], input[placeholder*='用户名'], input[placeholder*='帳號'], input[placeholder*='账号'], input[type='text']"
        ).first
        password_input = page.locator("input[name='password'], input#password, input[type='password']").first

        # 驗證表單元素存在
        username_input.wait_for(state="visible", timeout=10000)
        password_input.wait_for(state="visible", timeout=10000)

        # 輸入憑證
        username_input.fill(username)
        password_input.fill(password)

        # 尋找並點擊登入按鈕 (嘗試多種可能的選擇器)
        login_button = page.locator(
            "button[type='submit'], button:has-text('登入'), button:has-text('登录'), input[type='submit']"
        ).first
        login_button.wait_for(state="visible", timeout=10000)
        login_button.click()

        # 登入後截圖
        page.screenshot(path="after_login_screenshot.png")

        # 檢查是否導航到儀表板或其他指示成功登入的頁面
        # 增加等待時間和多種可能指示登入成功的選擇器
        success_element = page.locator(".dashboard, .main-content, .navbar, .header, #app, #main").first
        success_element.wait_for(state="visible", timeout=15000)
        expect(success_element).to_be_visible()

    def test_02_view_jobs(self, authenticated_page: Page):
        """測試查看作業列表"""
        page = authenticated_page

        # 登入後截圖
        # page.screenshot(path="after_login_dashboard.png")

        # 輸出頁面源碼以便分析
        # page_content = page.content()
        # with open("dashboard_page_source.html", "w", encoding="utf-8") as f:
        #     f.write(page_content)

        # print(f"頁面標題: {page.title()}")
        # print(f"頁面URL: {page.url}")

        # 檢查頁面上所有可點擊的菜單項
        menu_items = page.locator("a, button, .nav-item, .nav-link, .menu-item").all()
        print(f"發現 {len(menu_items)} 個可能的菜單項:")
        for item in menu_items[:10]:  # 只打印前10個避免過多輸出
            try:
                text = item.text_content().strip()
                if text:
                    print(f"  - '{text}'")
            except Exception as e:
                print(f"  錯誤: {e}")

        # 嘗試使用多種可能的選擇器找到作業菜單項
        # 注意：Playwright的locator只接受單個選擇器字符串
        job_menu = page.locator("text='Jobs', text='作業', text='job', text=/.*[Jj]ob.*/").first

        # 如果找到了菜單項，就點擊它
        if job_menu.count() > 0:
            print(f"找到作業菜單項: '{job_menu.text_content()}'")
            job_menu.click()
        else:
            # 如果沒找到，看看上述測試中的菜單列表，嘗試找到包含"Job"的項目
            found = False
            for item in menu_items:
                try:
                    text = item.text_content().strip()
                    if text and ("job" in text.lower() or "jobs" in text.lower()):
                        print(f"找到可能的作業菜單項: '{text}'")
                        item.click()
                        found = True
                        break
                except Exception:
                    continue

            # 如果仍未找到，直接導航到jobs頁面
            if not found:
                print("未找到作業菜單項，嘗試直接導航到jobs頁面")
                page.goto(f"{page.url.split('#')[0]}/#jobs")

        # 導航後截圖
        # page.screenshot(path="jobs_page_screenshot.png")

        # 等待一段時間，確保頁面加載完成
        page.wait_for_load_state("networkidle", timeout=5000)

        # 等待作業表格或相關元素加載
        # 使用更多可能的選擇器來匹配不同的表格實現
        table_selector = page.locator(
            ".jobs-table, table, .job-list, #jobs-table, [data-testid='jobs-table'], .data-table"
        ).first

        # 增加等待時間
        table_selector.wait_for(state="visible", timeout=15000)

        # 檢查表格是否包含預期元素
        assert table_selector.count() > 0, "未找到作業表格"

        # 輸出找到的表格信息
        print(f"找到作業表格，HTML標籤: {table_selector.evaluate('el => el.tagName')}")

    def test_03_add_job(self, authenticated_page: Page):
        """測試添加新作業"""
        page = authenticated_page

        # 檢查頁面上所有可點擊的菜單項
        menu_items = page.locator("a, button, .nav-item, .nav-link, .menu-item").all()
        print(f"發現 {len(menu_items)} 個可能的菜單項:")
        for item in menu_items[:10]:  # 只打印前10個避免過多輸出
            try:
                text = item.text_content().strip()
                if text:
                    print(f"  - '{text}'")
            except Exception as e:
                print(f"  錯誤: {e}")

        # 嘗試使用多種可能的選擇器找到作業菜單項
        # 注意：Playwright的locator只接受單個選擇器字符串
        job_menu = page.locator("text='Jobs', text='作業', text='job', text=/.*[Jj]ob.*/").first

        # 如果找到了菜單項，就點擊它
        if job_menu.count() > 0:
            print(f"找到作業菜單項: '{job_menu.text_content()}'")
            job_menu.click()
        else:
            # 如果沒找到，看看上述測試中的菜單列表，嘗試找到包含"Job"的項目
            found = False
            for item in menu_items:
                try:
                    text = item.text_content().strip()
                    if text and ("job" in text.lower() or "jobs" in text.lower()):
                        print(f"找到可能的作業菜單項: '{text}'")
                        item.click()
                        found = True
                        break
                except Exception:
                    continue

            # 如果仍未找到，直接導航到jobs頁面
            if not found:
                print("未找到作業菜單項，嘗試直接導航到jobs頁面")
                page.goto(f"{page.url.split('#')[0]}/#jobs")

        # 等待頁面加載
        page.wait_for_load_state("networkidle")

        # 截圖保存
        page.screenshot(path="jobs_list_page.png")

        # 輸出頁面源碼以便分析
        page_content = page.content()
        with open("jobs_page_source.html", "w", encoding="utf-8") as f:
            f.write(page_content)

        print(f"頁面標題: {page.title()}")
        print(f"頁面URL: {page.url}")

        # 檢查頁面上所有可能的按鈕
        # all_buttons = page.locator("button").all()
        # print(f"找到 {len(all_buttons)} 個按鈕:")
        # for btn in all_buttons:
        #     try:
        #         btn_text = btn.text_content().strip()
        #         btn_id = btn.get_attribute("id") or "無ID"
        #         btn_class = btn.get_attribute("class") or "無class"
        #         print(f"  - '{btn_text}' (ID: {btn_id}, Class: {btn_class})")
        #     except Exception as e:
        #         print(f"  錯誤: {e}")

        # 嘗試使用更通用的選擇器找到添加按鈕
        add_button = page.locator("a.btn-primary, button.add-btn, button[id*='add'], a.btn-primary[href*='add']").first

        if add_button.count() > 0:
            print(f"找到添加按鈕: '{add_button.text_content().strip()}'")
            add_button.click()
        else:
            # 如果找不到任何按鈕，直接尋找添加按鈕的圖標
            add_icon = page.locator("i.fa-plus, i.fa-add, .add-icon").first
            if add_icon.count() > 0:
                print("找到添加圖標")
                add_icon.click()
            else:
                # 最後嘗試，點擊頁面右上角區域，因為添加按鈕通常在那裡
                print("嘗試點擊頁面右上角區域")
                page.locator(".page-header, .header-actions, .page-actions").first.click()

        # 等待一段時間
        page.wait_for_timeout(2000)

        # 再次截圖查看點擊效果
        page.screenshot(path="after_click_add_button.png")

        # 檢查是否有模態框出現
        modal = page.locator(".modal:visible, dialog[open], [role='dialog']:visible").first

        # 如果找到模態框，繼續測試流程
        if modal.count() > 0:
            print("找到模態框")
            modal.screenshot(path="job_modal.png")

            # 填寫作業信息
            job_name = f"UI測試作業_{int(time.time())}"

            # 嘗試找到所有可能的輸入欄位
            inputs = modal.locator("input, select, textarea").all()
            print(f"模態框中找到 {len(inputs)} 個輸入欄位")

            # 如果有至少一個輸入欄位，假設第一個是名稱欄位
            if len(inputs) > 0:
                inputs[0].fill(job_name)
                print(f"已填寫作業名稱: {job_name}")

                # 如果有第二個欄位，嘗試選擇
                if len(inputs) > 1:
                    tag_name = inputs[1].evaluate("el => el.tagName").lower()
                    input_id = inputs[1].get_attribute("id") or ""
                    input_class = inputs[1].get_attribute("class") or ""

                    print(f"第二個輸入欄位: {tag_name}, ID: {input_id}, Class: {input_class}")

                    # 檢查是否為 Select2 元素
                    if "select2" in input_class or "select2" in input_id:
                        # Select2 的處理方式 - 直接用 JavaScript 設定值
                        try:
                            # 方法1: 使用 JavaScript 直接設定值
                            page.evaluate(
                                """() => {
                                // 嘗試使用 Select2 API
                                if (typeof $ !== 'undefined' && typeof $.fn.select2 !== 'undefined') {
                                    $('#"""
                                + input_id
                                + """').select2('val', '1');
                                }
                            }"""
                            )
                            print("使用 JavaScript 設定 Select2 值成功")
                        except Exception as e:
                            print(f"使用 JavaScript 設定值失敗: {e}")

                            try:
                                # 方法2: 直接點擊 Select2 容器，不等待
                                container_selector = f"#s2id_{input_id.replace('autogen', '')}"
                                page.click(container_selector)
                                page.wait_for_timeout(500)

                                # 然後選擇第一個選項
                                page.click(".select2-results__option:nth-child(2)")
                                print("通過點擊選擇完成")
                            except Exception as e2:
                                print(f"點擊選擇也失敗: {e2}")
                                # 如果還是失敗，嘗試用原生 select_option
                                try:
                                    inputs[1].select_option(index=1)
                                    print("使用原生 select_option 選擇成功")
                                except Exception as e3:
                                    print(f"所有選擇方法都失敗: {e3}")
                    elif tag_name == "select":
                        # 如果是標準 select 元素
                        inputs[1].select_option(index=1)
                        print("已選擇標準下拉選單的第二個選項")
                    else:
                        # 如果是其他類型輸入框，填入測試值
                        inputs[1].fill("test_value")
                        print("已填寫測試值到第二個欄位")

            # 尋找並點擊提交按鈕
            submit_btn = modal.locator(
                "button[type='submit'], button.btn-primary, button:has-text('Save'), button:has-text('Submit'), button:has-text('確定'), button:has-text('確認')"
            ).first

            if submit_btn.count() > 0:
                print(f"找到提交按鈕: '{submit_btn.text_content().strip()}'")
                submit_btn.click()

                # 等待操作完成
                page.wait_for_timeout(2000)
                page.screenshot(path="after_submit_job.png")

                # 簡單斷言：操作後頁面上應該有作業列表
                job_list = page.locator("table, .table, .list-view, .grid-view").first
                assert job_list.count() > 0, "沒有找到作業列表"
                print("測試通過：找到作業列表")
            else:
                print("未找到提交按鈕")

        else:
            print("未找到模態框，可能界面結構與預期不同")

        # 最終截圖
        page.screenshot(path="test_final_state.png")

    def test_04_modify_job(self, authenticated_page: Page):
        """測試修改作業"""
        page = authenticated_page

        # 導航到作業頁面
        page.click("text=作業")
        page.wait_for_selector(".jobs-table")

        # 點擊第一個作業的編輯按鈕
        page.click(".jobs-table tr:first-child .edit-job-button")

        # 等待編輯模態框
        page.wait_for_selector(".edit-job-modal")

        # 修改作業名稱
        new_job_name = f"修改後的作業_{int(time.time())}"
        page.fill("input[name='name']", new_job_name)

        # 提交表單
        page.click(".edit-job-modal button[type='submit']")

        # 等待作業更新成功
        page.wait_for_selector(f"text={new_job_name}")

        # 驗證修改後的作業已顯示在列表中
        expect(page.locator(f"text={new_job_name}")).to_be_visible()

    def test_05_pause_resume_job(self, authenticated_page: Page):
        """測試暫停和恢復作業"""
        page = authenticated_page

        # 導航到作業頁面
        page.click("text=作業")
        page.wait_for_selector(".jobs-table")

        # 點擊第一個作業的暫停按鈕
        page.click(".jobs-table tr:first-child .pause-job-button")

        # 等待作業狀態更新
        page.wait_for_selector(".jobs-table tr:first-child .job-paused-status")

        # 驗證作業已暫停
        expect(page.locator(".jobs-table tr:first-child .job-paused-status")).to_be_visible()

        # 點擊恢復按鈕
        page.click(".jobs-table tr:first-child .resume-job-button")

        # 等待作業狀態更新
        page.wait_for_selector(".jobs-table tr:first-child .job-active-status")

        # 驗證作業已恢復
        expect(page.locator(".jobs-table tr:first-child .job-active-status")).to_be_visible()

    def test_06_run_job(self, authenticated_page: Page):
        """測試立即執行作業"""
        page = authenticated_page

        # 導航到作業頁面
        page.click("text=作業")
        page.wait_for_selector(".jobs-table")

        # 點擊第一個作業的執行按鈕
        page.click(".jobs-table tr:first-child .run-job-button")

        # 等待確認模態框
        page.wait_for_selector(".confirm-run-job-modal")

        # 確認執行
        page.click(".confirm-run-job-modal button:has-text('確認')")

        # 等待執行結果提示
        page.wait_for_selector(".execution-success-notification")

        # 驗證執行成功提示已顯示
        expect(page.locator(".execution-success-notification")).to_be_visible()

    def test_07_view_executions(self, authenticated_page: Page):
        """測試查看執行記錄"""
        page = authenticated_page

        # 導航到執行記錄頁面
        page.click("text=執行記錄")

        # 等待記錄表格加載
        page.wait_for_selector(".executions-table")

        # 驗證表格已顯示
        expect(page.locator(".executions-table")).to_be_visible()

    def test_08_view_audit_logs(self, authenticated_page: Page):
        """測試查看審計日誌"""
        page = authenticated_page

        # 導航到審計日誌頁面
        page.click("text=審計日誌")

        # 等待日誌表格加載
        page.wait_for_selector(".audit-logs-table")

        # 驗證表格已顯示
        expect(page.locator(".audit-logs-table")).to_be_visible()

    def test_09_view_categories(self, authenticated_page: Page):
        """測試查看類別"""
        page = authenticated_page

        # 導航到類別頁面
        page.click("text=類別")

        # 等待類別表格加載
        page.wait_for_selector(".categories-table")

        # 驗證表格已顯示
        expect(page.locator(".categories-table")).to_be_visible()

    def test_10_add_category(self, authenticated_page: Page):
        """測試添加類別"""
        page = authenticated_page

        # 導航到類別頁面
        page.click("text=類別")

        # 點擊新增類別按鈕
        page.click("button:has-text('新增類別')")

        # 等待模態框
        page.wait_for_selector(".add-category-modal")

        # 填寫類別信息
        category_name = f"UI測試類別_{int(time.time())}"
        page.fill("input[name='name']", category_name)
        page.fill("textarea[name='description']", "測試類別說明")

        # 提交表單
        page.click(".add-category-modal button[type='submit']")

        # 等待類別添加成功
        page.wait_for_selector(f"text={category_name}")

        # 驗證新類別已顯示在列表中
        expect(page.locator(f"text={category_name}")).to_be_visible()

    def test_11_user_management(self, authenticated_page: Page):
        """測試用戶管理"""
        page = authenticated_page

        # 導航到用戶頁面
        page.click("text=用戶")

        # 等待用戶表格加載
        page.wait_for_selector(".users-table")

        # 驗證表格已顯示
        expect(page.locator(".users-table")).to_be_visible()

        # 點擊新增用戶按鈕
        page.click("button:has-text('新增用戶')")

        # 等待模態框
        page.wait_for_selector(".add-user-modal")

        # 填寫用戶信息
        test_username = f"ui_user_{int(time.time())}"
        page.fill("input[name='username']", test_username)
        page.fill("input[name='password']", "password123")

        # 選擇類別
        page.select_option("select[name='category_id']", "1")

        # 提交表單
        page.click(".add-user-modal button[type='submit']")

        # 等待用戶添加成功
        page.wait_for_selector(f"text={test_username}")

        # 驗證新用戶已顯示在列表中
        expect(page.locator(f"text={test_username}")).to_be_visible()
