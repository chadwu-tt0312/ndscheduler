## q-1

Audit Logs 裡面 Description 呈現內容。但是 pub_args 在這次修改並無變更，只有 minute 變更。要如何修正?
diff: old val => new val
pub_args: ('first parameter', {'second parameter': 'can be a dict'}) => ['first parameter', {'second parameter': 'can be a dict'}]
minute: */1 => */10

---

## answer-1

2025-04-10_05-17-audit-logs-change-display-issue.md

---

## q-2

哪裡有用到 format_job_dict_diff() ?
實際的比較邏輯在哪個 function 之中?

---

## q-3 (反覆3次改不了)

Executions & Audit Logs 頁面顯示切換時預設都只會顯示 10 minutes 的資料。即使畫面上選擇的是 12 hours 。需要手動按 Refresh 才會正確更新資料。要如何改善?

---

## q-4

登入頁面目前使用的是 ADMIN_USER 。
- 如何添加資料表用來管理所有使用者(包含 ADMIN_USER)
- 如何讓使用者根據不同 category 可以看到不同 jobs/executions/auditlogs
- 如何讓使用者根據權限 (Read=只能看，Add=可以增加/修改 job)
請先規劃好相關功能步驟，再與我討論過後才開始

---

## answer-4

2025-04-15_00-35-使用者管理系統功能規劃.md

---

## q-5

1. UserCategoryMapping 表格，與 UserPermissions 表格各有何作用? 
2. 如果只想保留 Users 表格 & UserCategories 表格。要如何調整資料表定義?
3. 使用者資料管理介面和 Category 管理介面可以掛在 "Info" 功能列表之下
4. 不需要更細緻的權限控制
5. Category 的層級只有一層
6. 不需要使用者群組
7. 為何需要資料遷移? 新建資料表與現有資料表有哪些需要變更嗎?

---

## q-6

介面規劃中
- 只需要增加"使用者列表"和"Category 列表"
- is_admin=true 的使用者才可以看到"使用者列表"和"Category 列表"
- 並且列表頁面中有新增/編輯功能

---

## q-7

- 添加登入頁面(只有登入功能不需要註冊功能)
- 如何添加資料表用來管理所有使用者
- 如何讓使用者根據不同 category 可以看到不同 jobs/executions/auditlogs
- 如何讓使用者根據權限 (false=只能看，true=可以增加/修改/刪除 job)
- 實作順序建議：
	- 先實作登入功能和使用者資料表和 Categories 資料表
	- 建立基本的權限管理機制
	- 實作 Category 過濾功能
	- 最後完善權限控制系統

Users 資料表：
```
- id (主鍵)
- username (唯一值)
- password (加密儲存)
- is_admin (布林值)
- category_id (外鍵連結到 Categories，可為 null)
- permission
- created_at
- updated_at
```

Categories 資料表：
```
- id (主鍵)
- name (唯一值，例如：Production, Testing, Development)
- description
- created_at
- updated_at
```

請先規劃好相關功能步驟，再與我討論過後才開始實作

---

## answer-7

2025-04-15_06-24-系統登入與權限管理規劃.md

---

## q-8

開始第一階段的實作

---

## q-9

實作 "第二階段：Category 管理與過濾"

---

## answer-9

2025-04-15_08-25-category-management-and-filtering-implementation.md

---

## q-10

- Info 選單中添加兩項 Users & Categories 的頁面入口。
- 只有 is_admin = true 的 user 可以看見並使用。
- 分別用來新增/編輯/刪除/查看 Users。和新增/編輯/刪除/查看 Categories。

---

## q-11

- Info 選單要有登出功能
- user 登出後頁面需要跳轉到 login 頁面
- "user" 登入後看不到 Users 和 Categories

---

## q-12

需要修改的頁面顯示

- navbar 的 "Nextdoor Scheduler" 改為使用 default_settings.py 裡的 WEBSITE_TITLE 設定，並且串接 "@"和username。例如:UMC Scheduler@user。
- 用 "user" (is_admin=true)登入後 info 下拉選單沒有呈現 Users & Categories 的選項，但有呈現 "ndscheduler GitHub page"

---

## answer-12

2025-04-16_00-45-頁面修改與用戶選單問題.md

---

## q-13

圖片中3個紅框，表示3個問題
1. 顯示 WEBSITE_TITLE 但是沒有使用者名稱
2. 當用戶是管理員時依然沒顯示"管理員選單項目"
3. jobs 頁面顯示資料異常(至少有一筆資料)

---

## q-14

console log 如下:
User info from token: null
isAdmin status: null
GET http://localhost:8888/api/v1/categories 500 (Internal Server Error)
Error fetching categories: {"error": {"code": 500, "message": "Internal Server Error"}}

---

## q-15 (沒解決)

紅框內容重複

---

## answer-15

2025-04-16_07-41-頁面重整後紅框內容問題.md

---

## q-16

請詳細說明 jobs 頁面資料顯示的詳細過程。
從切換到 jobs 頁面，然後資料如何取得，如何顯示。一步一步的描述清楚。

---

## answer-16

2025-04-17_00-36-jobs-page-data-display-process.md

---

## q-17 (FAIL)

為何 jobs 頁面資料顯示錯誤(無資料)，實際有一筆。

---

## q-18

jobs & executions & logs 都是用 *.js 檔案處理邏輯，users & categories 卻將邏輯部分寫在 index.html
請參考 jobs & executions & logs 的寫法修改 users & categories

---

## q-9

---

## answer-9

---

## q-9

---

## answer-9

---

## q-9

---

## answer-9

---

## q-9

---

## answer-9
